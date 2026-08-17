from __future__ import annotations

import asyncio
import os
import time
from types import SimpleNamespace

import pytest
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition, VideoAssetInput
from open_webui.extensions.videos import executor, service
from open_webui.extensions.videos.executor import (
    FalVideoExecutor,
    MockVideoExecutor,
    VideoExecutionError,
    enforce_fal_video_policy,
    extract_fal_video_url,
    inject_fal_asset_urls,
    resolve_video_executor,
)
from open_webui.extensions.videos.schemas import VideoAssetReference, VideoTaskResponse


def _definition(*, task: str = 'text-to-video', assets: list[VideoAssetInput] | None = None):
    return FalVideoModelDefinition(
        id=f'fal-ai/example/{task}',
        public_id=f'example-{task}',
        name='Example Video',
        provider='example',
        task=task,
        asset_inputs=assets,
    )


def _task(*, task: str = 'text-to-video', assets: tuple[VideoAssetReference, ...] = ()):
    return VideoTaskResponse(
        id='task-1',
        status='running',
        task=task,
        prompt='A paper boat',
        model_id=f'example-{task}',
        params={'duration': '5'},
        assets=assets,
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )


def _request(*, key: str = ''):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(config=SimpleNamespace(FAL_API_KEY=key))))


def test_resolve_executor_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv('VIDEO_GENERATION_ENGINE', raising=False)
    assert isinstance(resolve_video_executor(_request()), MockVideoExecutor)


def test_resolve_executor_requires_explicit_fal_key(monkeypatch) -> None:
    monkeypatch.setenv('VIDEO_GENERATION_ENGINE', 'fal')
    monkeypatch.setattr(executor, 'FAL_API_KEY', '')
    with pytest.raises(VideoExecutionError) as captured:
        resolve_video_executor(_request())
    assert captured.value.code == 'video_fal_not_configured'


def test_resolve_executor_uses_dedicated_fal_settings(monkeypatch) -> None:
    monkeypatch.setenv('VIDEO_GENERATION_ENGINE', 'fal')
    monkeypatch.setenv('VIDEO_GENERATION_FAL_API_KEY', 'video-key')
    monkeypatch.setenv('VIDEO_GENERATION_FAL_TIMEOUT_SECONDS', '1200')
    resolved = resolve_video_executor(_request(key='image-key'))
    assert isinstance(resolved, FalVideoExecutor)
    assert resolved.api_key == 'video-key'
    assert resolved.timeout_seconds == 1200


def test_fal_policy_enforces_allowlist_and_per_request_credit_cap(monkeypatch) -> None:
    monkeypatch.setenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', 'allowed-model, second-model')
    monkeypatch.setenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', '100')

    enforce_fal_video_policy(model_id='allowed-model', charged_credits=100)
    with pytest.raises(VideoExecutionError) as disallowed:
        enforce_fal_video_policy(model_id='other-model', charged_credits=1)
    assert disallowed.value.code == 'video_fal_model_not_allowed'
    with pytest.raises(VideoExecutionError) as too_expensive:
        enforce_fal_video_policy(model_id='allowed-model', charged_credits=101)
    assert too_expensive.value.code == 'video_fal_cost_limit_exceeded'


def test_fal_policy_rejects_invalid_credit_limit(monkeypatch) -> None:
    monkeypatch.delenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', raising=False)
    monkeypatch.setenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', 'invalid')

    with pytest.raises(VideoExecutionError) as captured:
        enforce_fal_video_policy(model_id='any-model', charged_credits=1)
    assert captured.value.code == 'video_fal_policy_invalid'


def test_video_runtime_diagnostics_never_exposes_api_key(monkeypatch) -> None:
    monkeypatch.setenv('VIDEO_GENERATION_ENGINE', 'fal')
    monkeypatch.setenv('VIDEO_GENERATION_FAL_API_KEY', 'super-secret-key')
    monkeypatch.setenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', 'model-b,model-a')
    monkeypatch.setenv('VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS', '4')

    diagnostics = executor.video_runtime_diagnostics(_request())

    assert diagnostics['engine'] == 'fal'
    assert diagnostics['fal_api_key_configured'] is True
    assert diagnostics['allowed_models'] == ['model-a', 'model-b']
    assert diagnostics['delivery_max_attempts'] == 4
    assert 'super-secret-key' not in repr(diagnostics)


def test_extract_fal_video_url_supports_nested_and_direct_results() -> None:
    assert extract_fal_video_url({'video': {'url': 'https://fal.media/video.mp4'}}) == 'https://fal.media/video.mp4'
    assert extract_fal_video_url({'data': {'video': 'https://fal.media/video.mp4'}}) == 'https://fal.media/video.mp4'
    assert extract_fal_video_url({'url': 'https://fal.media/video.mp4'}) == 'https://fal.media/video.mp4'
    assert extract_fal_video_url({}) is None


@pytest.mark.asyncio
async def test_asset_files_are_uploaded_and_injected_into_provider_payload(monkeypatch, tmp_path) -> None:
    first = tmp_path / 'first.png'
    last = tmp_path / 'last.png'
    first.write_bytes(b'first')
    last.write_bytes(b'last')
    files = {
        'first': SimpleNamespace(path=str(first), filename='first.png', meta={'content_type': 'image/png'}),
        'last': SimpleNamespace(path=str(last), filename='last.png', meta={'content_type': 'image/png'}),
    }

    async def get_file(file_id, user_id):
        assert user_id == 'user-1'
        return files[file_id]

    uploaded: list[str] = []

    async def upload(**kwargs):
        uploaded.append(kwargs['filename'])
        return f'https://fal.media/{kwargs["filename"]}'

    monkeypatch.setattr(executor.Files, 'get_file_by_id_and_user_id', get_file)
    monkeypatch.setattr(executor.Storage, 'get_file', lambda value: value)
    monkeypatch.setattr(executor, 'upload_file_to_fal', upload)
    definition = _definition(
        task='image-to-video',
        assets=[
            VideoAssetInput(
                role='start_image',
                field='image_url',
                required=True,
                mime_types=['image/png'],
                max_bytes=1024,
            ),
            VideoAssetInput(
                role='end_image',
                field='end_image_url',
                mime_types=['image/png'],
                max_bytes=1024,
            ),
        ],
    )
    task = _task(
        task='image-to-video',
        assets=(
            VideoAssetReference(role='start_image', file_id='first'),
            VideoAssetReference(role='end_image', file_id='last'),
        ),
    )
    payload: dict[str, object] = {'prompt': task.prompt}
    await inject_fal_asset_urls(
        payload,
        task,
        definition,
        user_id='user-1',
        api_key='key',
        storage_base_url='https://rest.fal.ai',
        upload_lifetime_seconds=3600,
    )
    assert uploaded == ['first.png', 'last.png']
    assert payload['image_url'] == 'https://fal.media/first.png'
    assert payload['end_image_url'] == 'https://fal.media/last.png'


@pytest.mark.asyncio
async def test_real_executor_records_invocation_and_downloads_result(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}
    observer = object()

    async def start(**kwargs):
        calls['invocation'] = kwargs
        return observer

    async def run(model, payload, api_key, base_url, **kwargs):
        calls['queue'] = (model, payload, api_key, base_url, kwargs)
        return {'video': {'url': 'https://fal.media/result.mp4'}}

    result_path = tmp_path / 'result.mp4'
    result_path.write_bytes(b'\x00\x00\x00\x18ftypmp42video')

    async def download(url, *, max_bytes):
        calls['download'] = (url, max_bytes)
        return result_path, 'application/octet-stream'

    monkeypatch.setattr(executor, 'try_start_provider_invocation', start)
    monkeypatch.setattr(executor, 'run_fal_queue', run)
    monkeypatch.setattr(executor, 'download_fal_video', download)
    real = FalVideoExecutor('key', 'https://queue.fal.run', 'https://rest.fal.ai', 900, 1024, 3600)
    task = _task()
    result = await real.invoke(_request(), SimpleNamespace(id='user-1'), task, _definition(), {'prompt': task.prompt})
    assert result.content_type == 'video/mp4'
    assert result.duration_seconds == 5
    assert calls['invocation']['task_id'] == 'task-1'
    assert calls['queue'][4] == {'observer': observer, 'timeout_seconds': 900}


@pytest.mark.asyncio
async def test_real_executor_maps_provider_timeout(monkeypatch) -> None:
    async def start(**_kwargs):
        return None

    async def timeout(*_args, **_kwargs):
        from open_webui.utils.images.fal import FalImageError

        raise FalImageError('fal.ai request timed out')

    monkeypatch.setattr(executor, 'try_start_provider_invocation', start)
    monkeypatch.setattr(executor, 'run_fal_queue', timeout)
    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
    with pytest.raises(VideoExecutionError) as captured:
        await real.invoke(_request(), SimpleNamespace(id='user-1'), _task(), _definition(), {})
    assert captured.value.code == 'video_provider_timeout'
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_real_executor_preserves_completed_provider_error_state(monkeypatch) -> None:
    async def start(**_kwargs):
        return None

    async def completed_result_failure(*_args, **_kwargs):
        from open_webui.utils.images.fal import FalImageError

        error = FalImageError('fal.ai request failed: temporary response failure', status_code=503)
        error.provider_submitted = True
        error.provider_completed = True
        raise error

    monkeypatch.setattr(executor, 'try_start_provider_invocation', start)
    monkeypatch.setattr(executor, 'run_fal_queue', completed_result_failure)
    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

    with pytest.raises(VideoExecutionError) as captured:
        await real.invoke(_request(), SimpleNamespace(id='user-1'), _task(), _definition(), {})

    assert captured.value.code == 'video_provider_failed'
    assert captured.value.provider_submitted is True
    assert captured.value.provider_completed is True
    assert captured.value.retryable is True


@pytest.mark.asyncio
async def test_real_executor_marks_post_provider_download_failure_as_completed(monkeypatch) -> None:
    async def start(**_kwargs):
        return None

    async def run(*_args, **_kwargs):
        return {'video': {'url': 'https://fal.media/result.mp4'}}

    async def download(*_args, **_kwargs):
        raise VideoExecutionError('video_result_download_failed')

    monkeypatch.setattr(executor, 'try_start_provider_invocation', start)
    monkeypatch.setattr(executor, 'run_fal_queue', run)
    monkeypatch.setattr(executor, 'download_fal_video', download)
    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

    with pytest.raises(VideoExecutionError) as captured:
        await real.invoke(_request(), SimpleNamespace(id='user-1'), _task(), _definition(), {})

    assert captured.value.code == 'video_result_download_failed'
    assert captured.value.provider_completed is True


@pytest.mark.asyncio
async def test_video_download_retries_only_retryable_delivery_failures(monkeypatch, tmp_path) -> None:
    attempts = 0
    result_path = tmp_path / 'result.mp4'
    result_path.write_bytes(b'video')

    async def download(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise VideoExecutionError('video_result_download_failed', retryable=True)
        return result_path, 'video/mp4'

    async def no_wait(_seconds):
        return None

    monkeypatch.setenv('VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS', '3')
    monkeypatch.setattr(executor, 'download_fal_video', download)
    monkeypatch.setattr(executor.asyncio, 'sleep', no_wait)

    returned_path, content_type = await executor.download_fal_video_with_retry(
        'https://fal.media/result.mp4', max_bytes=1024
    )

    assert (returned_path, content_type, attempts) == (result_path, 'video/mp4', 3)


@pytest.mark.asyncio
async def test_stale_video_temp_cleanup_preserves_recent_files(monkeypatch, tmp_path) -> None:
    stale = tmp_path / 'open-webui-fal-video-stale.mp4'
    recent = tmp_path / 'open-webui-fal-video-recent.mp4'
    unrelated = tmp_path / 'other.mp4'
    for path in (stale, recent, unrelated):
        path.write_bytes(b'x')
    old = time.time() - 120
    os.utime(stale, (old, old))
    monkeypatch.setattr(executor.tempfile, 'gettempdir', lambda: str(tmp_path))

    removed = await executor.cleanup_stale_fal_video_temp_files(max_age_seconds=60)

    assert removed == 1
    assert not stale.exists()
    assert recent.exists()
    assert unrelated.exists()


@pytest.mark.asyncio
async def test_real_executor_preserves_shutdown_cancellation(monkeypatch) -> None:
    async def start(**_kwargs):
        return None

    async def cancel(*_args, **_kwargs):
        raise asyncio.CancelledError

    monkeypatch.setattr(executor, 'try_start_provider_invocation', start)
    monkeypatch.setattr(executor, 'run_fal_queue', cancel)
    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
    with pytest.raises(asyncio.CancelledError):
        await real.invoke(_request(), SimpleNamespace(id='user-1'), _task(), _definition(), {})


@pytest.mark.asyncio
async def test_fal_storage_upload_uses_initiate_then_signed_put(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, object]] = []

    class Response:
        def __init__(self, payload=None):
            self.status = 200
            self._payload = payload

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def json(self, **_kwargs):
            return self._payload

        async def text(self):
            return ''

    class Session:
        def post(self, url, **kwargs):
            calls.append(('post', (url, kwargs)))
            return Response({'upload_url': 'https://signed.example/upload', 'file_url': 'https://fal.media/input.png'})

        def put(self, url, **kwargs):
            calls.append(('put', (url, kwargs)))
            return Response()

    async def get_fake_session():
        return Session()

    monkeypatch.setattr(executor, 'get_session', get_fake_session)
    source = tmp_path / 'input.png'
    source.write_bytes(b'png')
    result = await executor.upload_file_to_fal(
        path=source,
        filename='input.png',
        content_type='image/png',
        api_key='secret',
        storage_base_url='https://rest.fal.ai',
        upload_lifetime_seconds=3600,
    )
    assert result == 'https://fal.media/input.png'
    assert [kind for kind, _detail in calls] == ['post', 'put']
    post_headers = calls[0][1][1]['headers']
    assert post_headers['Authorization'] == 'Key secret'
    assert '3600' in post_headers['X-Fal-Object-Lifecycle-Preference']


@pytest.mark.asyncio
async def test_fal_storage_upload_retries_transient_failures(monkeypatch, tmp_path) -> None:
    attempts = 0
    source = tmp_path / 'input.png'
    source.write_bytes(b'png')

    async def upload_once(**_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise VideoExecutionError('video_asset_upload_failed', retryable=True)
        return 'https://fal.media/input.png'

    async def no_wait(_seconds):
        return None

    monkeypatch.setenv('VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS', '3')
    monkeypatch.setattr(executor, '_upload_file_to_fal_once', upload_once)
    monkeypatch.setattr(executor.asyncio, 'sleep', no_wait)

    result = await executor.upload_file_to_fal(
        path=source,
        filename='input.png',
        content_type='image/png',
        api_key='secret',
        storage_base_url='https://rest.fal.ai',
        upload_lifetime_seconds=3600,
    )

    assert result == 'https://fal.media/input.png'
    assert attempts == 3


@pytest.mark.asyncio
async def test_run_video_task_dispatches_to_real_executor(monkeypatch, tmp_path) -> None:  # noqa: C901
    states: list[str] = []
    invoked = False

    class Context:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        def begin(self):
            return self

    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
    result_path = tmp_path / 'result.mp4'
    result_path.write_bytes(b'video')

    async def invoke(self, *_args, **_kwargs):
        nonlocal invoked
        invoked = True
        return executor.VideoExecutionOutput(result_path, 'video/mp4', 5)

    async def set_state(_task_id, status, **_kwargs):
        states.append(status)

    async def get_task(*_args, **_kwargs):
        return _task()

    async def begin_usage(*_args, **_kwargs):
        return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

    async def no_op(*_args, **_kwargs):
        return None

    async def finalize(*_args, **_kwargs):
        return {'url': '/api/v1/files/result/content'}

    async def succeed(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(FalVideoExecutor, 'invoke', invoke)
    monkeypatch.setattr(service, 'resolve_video_executor', lambda _request: real)
    monkeypatch.setattr(service, '_set_task_state', set_state)
    monkeypatch.setattr(service, '_publish_video_task_event', no_op)
    monkeypatch.setattr(service, 'creation_session', lambda: Context())
    monkeypatch.setattr(service, 'credit_session', lambda: Context())
    monkeypatch.setattr(service, 'get_video_task', get_task)
    monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
    monkeypatch.setattr(service, '_set_task_usage_id', no_op)
    monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
    monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
    monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission: (_definition(), {}, {}))
    monkeypatch.setattr(service, '_finalize_real_video', finalize)
    monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
    await service.run_video_task('task-1', _request(), SimpleNamespace(id='user-1'))
    assert invoked is True
    assert states == ['running', 'succeeded']
    assert not result_path.exists()


@pytest.mark.asyncio
async def test_real_delivery_failure_keeps_prepaid_charge_for_reconciliation(  # noqa: C901
    monkeypatch, tmp_path
) -> None:
    states: list[tuple[str, str | None]] = []
    failure: dict[str, object] = {}

    class Context:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        def begin(self):
            return self

    real = FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
    result_path = tmp_path / 'result.mp4'
    result_path.write_bytes(b'video')

    async def invoke(self, *_args, **_kwargs):
        return executor.VideoExecutionOutput(result_path, 'video/mp4', 5)

    async def set_state(_task_id, status, **kwargs):
        states.append((status, kwargs.get('error_code')))

    async def get_task(*_args, **_kwargs):
        return _task()

    async def begin_usage(*_args, **_kwargs):
        return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

    async def no_op(*_args, **_kwargs):
        return None

    async def fail_delivery(*_args, **_kwargs):
        raise RuntimeError('local storage unavailable')

    async def mark_failed(usage_id, code, *, restore_prepaid=True):
        failure.update(usage_id=usage_id, code=code, restore_prepaid=restore_prepaid)

    monkeypatch.setattr(FalVideoExecutor, 'invoke', invoke)
    monkeypatch.setattr(service, 'resolve_video_executor', lambda _request: real)
    monkeypatch.setattr(service, '_set_task_state', set_state)
    monkeypatch.setattr(service, '_publish_video_task_event', no_op)
    monkeypatch.setattr(service, 'creation_session', lambda: Context())
    monkeypatch.setattr(service, 'credit_session', lambda: Context())
    monkeypatch.setattr(service, 'get_video_task', get_task)
    monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
    monkeypatch.setattr(service, '_set_task_usage_id', no_op)
    monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
    monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
    monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission: (_definition(), {}, {}))
    monkeypatch.setattr(service, '_finalize_real_video', fail_delivery)
    monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed)

    await service.run_video_task('task-1', _request(), SimpleNamespace(id='user-1'))

    assert states == [('running', None), ('failed', 'video_delivery_failed')]
    assert failure == {
        'usage_id': 'usage-1',
        'code': 'video_delivery_failed',
        'restore_prepaid': False,
    }
    assert not result_path.exists()


@pytest.mark.asyncio
async def test_orphan_cleanup_removes_storage_payload_and_file_row(monkeypatch) -> None:
    deleted_payloads: list[str] = []
    deleted_rows: list[str] = []
    file = SimpleNamespace(id='file-1', path='generated/file-1.mp4')

    monkeypatch.setattr(service.Storage, 'delete_file', deleted_payloads.append)

    async def delete_row(file_id):
        deleted_rows.append(file_id)
        return True

    monkeypatch.setattr(service.Files, 'delete_file_by_id', delete_row)

    await service._cleanup_generated_files([file])

    assert deleted_payloads == ['generated/file-1.mp4']
    assert deleted_rows == ['file-1']


@pytest.mark.asyncio
async def test_real_executor_resume_polls_existing_request_without_generation_post(monkeypatch, tmp_path) -> None:
    calls: dict[str, object] = {}

    async def unexpected_submit(*_args, **_kwargs):
        raise AssertionError('recovery must not submit a second generation request')

    async def resume_queue(**kwargs):
        calls['resume'] = kwargs
        return {'video': {'url': 'https://fal.media/recovered.mp4'}}

    result_path = tmp_path / 'recovered.mp4'
    result_path.write_bytes(b'\x00\x00\x00\x18ftypmp42video')

    async def download(url, *, max_bytes):
        calls['download'] = (url, max_bytes)
        return result_path, 'video/mp4'

    monkeypatch.setattr(executor, 'run_fal_queue', unexpected_submit)
    monkeypatch.setattr(executor, 'resume_fal_queue', resume_queue)
    monkeypatch.setattr(executor, 'download_fal_video_with_retry', download)
    real = FalVideoExecutor('key', 'https://queue.fal.run', 'https://rest.fal.ai', 900, 1024, 3600)

    output = await real.resume(
        _task(),
        _definition(),
        status_url='https://queue.fal.run/status/request-1',
        response_url='https://queue.fal.run/response/request-1',
        result_url=None,
    )

    assert output.content_type == 'video/mp4'
    assert calls['resume']['response_url'].endswith('/request-1')
    assert calls['download'] == ('https://fal.media/recovered.mp4', 1024)


@pytest.mark.asyncio
async def test_real_executor_resume_delivers_persisted_result_without_queue_poll(monkeypatch, tmp_path) -> None:
    async def unexpected_poll(**_kwargs):
        raise AssertionError('persisted result URL should skip provider polling')

    result_path = tmp_path / 'persisted.mp4'
    result_path.write_bytes(b'\x00\x00\x00\x18ftypmp42video')

    async def download(_url, *, max_bytes):
        assert max_bytes == 1024
        return result_path, 'video/mp4'

    monkeypatch.setattr(executor, 'resume_fal_queue', unexpected_poll)
    monkeypatch.setattr(executor, 'download_fal_video_with_retry', download)
    real = FalVideoExecutor('key', 'https://queue.fal.run', 'https://rest.fal.ai', 900, 1024, 3600)

    output = await real.resume(
        _task(),
        _definition(),
        status_url=None,
        response_url=None,
        result_url='https://fal.media/persisted.mp4',
    )

    assert output.duration_seconds == 5


@pytest.mark.asyncio
async def test_real_executor_refreshes_expired_persisted_result_url(monkeypatch, tmp_path) -> None:
    downloads: list[str] = []
    persisted: list[str] = []
    result_path = tmp_path / 'refreshed.mp4'
    result_path.write_bytes(b'\x00\x00\x00\x18ftypmp42video')

    async def resume_queue(**kwargs):
        assert kwargs['status_url'] is None
        return {'video': {'url': 'https://fal.media/refreshed.mp4'}}

    async def download(url, *, max_bytes):
        assert max_bytes == 1024
        downloads.append(url)
        if len(downloads) == 1:
            raise VideoExecutionError('video_result_download_failed')
        return result_path, 'video/mp4'

    async def persist(url):
        persisted.append(url)

    monkeypatch.setattr(executor, 'resume_fal_queue', resume_queue)
    monkeypatch.setattr(executor, 'download_fal_video_with_retry', download)
    real = FalVideoExecutor('key', 'https://queue.fal.run', 'https://rest.fal.ai', 900, 1024, 3600)

    output = await real.resume(
        _task(),
        _definition(),
        status_url=None,
        response_url='https://queue.fal.run/response/request-1',
        result_url='https://fal.media/expired.mp4',
        on_result_url=persist,
    )

    assert output.content_type == 'video/mp4'
    assert downloads == ['https://fal.media/expired.mp4', 'https://fal.media/refreshed.mp4']
    assert persisted == ['https://fal.media/refreshed.mp4']


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('scenario', 'expected_code'),
    [
        ('provider_timeout', 'video_provider_timeout'),
        ('rate_limit', 'video_provider_rate_limited'),
        ('malformed_result', 'video_result_missing'),
        ('oversized_result', 'video_result_too_large'),
        ('delivery_failure', 'video_delivery_failed'),
    ],
)
async def test_mock_fault_scenarios_are_deterministic_and_refundable(monkeypatch, scenario, expected_code) -> None:
    async def no_delay(_seconds):
        return None

    monkeypatch.setenv('VIDEO_GENERATION_MOCK_SCENARIO', scenario)
    monkeypatch.setattr(service.asyncio, 'sleep', no_delay)

    with pytest.raises(VideoExecutionError) as caught:
        await service._run_mock_scenario()

    assert caught.value.code == expected_code
    assert caught.value.provider_completed is False
