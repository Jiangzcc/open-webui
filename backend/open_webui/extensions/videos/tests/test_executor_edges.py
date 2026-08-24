import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.fal_images.errors import FalImageError
from open_webui.extensions.videos import executor, video_result
from open_webui.extensions.videos.execution_types import VideoExecutionError

from .task_test_support import video_task


def _executor() -> executor.FalVideoExecutor:
    return executor.FalVideoExecutor(
        'fake-key',
        'https://queue.test',
        'https://storage.test',
        10,
        1024,
        60,
    )


@pytest.mark.asyncio
async def test_provider_result_maps_generic_submission_boundaries(monkeypatch) -> None:
    real = _executor()
    error = RuntimeError('provider')
    error.provider_submitted = True
    monkeypatch.setattr(executor, 'run_fal_queue', AsyncMock(side_effect=error))
    with pytest.raises(VideoExecutionError) as captured:
        await real._provider_result(SimpleNamespace(id='model'), {}, object())
    assert captured.value.provider_submitted is True
    assert captured.value.retryable is True

    fal_error = FalImageError('timed out', status_code=504)
    monkeypatch.setattr(executor, 'run_fal_queue', AsyncMock(side_effect=fal_error))
    with pytest.raises(VideoExecutionError) as captured:
        await real._provider_result(SimpleNamespace(id='model'), {}, object())
    assert captured.value.code == 'video_provider_timeout'


@pytest.mark.asyncio
async def test_download_output_rejects_mime_and_removes_partial_file(monkeypatch, tmp_path) -> None:
    real = _executor()
    path = tmp_path / 'result.bin'
    path.write_bytes(b'not-mp4')
    monkeypatch.setattr(
        executor,
        'download_fal_video_with_retry',
        AsyncMock(return_value=(path, 'application/octet-stream')),
    )
    removed = AsyncMock()
    monkeypatch.setattr(executor.video_result, 'remove_file', removed)
    with pytest.raises(VideoExecutionError, match='type'):
        await real._download_output(
            video_task(),
            SimpleNamespace(output_mime_types=['video/mp4']),
            'https://result.test/video',
        )
    removed.assert_awaited_once_with(path)

    path.write_bytes(b'0000ftyp0000')
    executor.download_fal_video_with_retry = AsyncMock(return_value=(path, 'video/webm'))
    with pytest.raises(VideoExecutionError, match='type'):
        await real._download_output(
            video_task(),
            SimpleNamespace(output_mime_types=['video/mp4']),
            'https://result.test/video',
        )


@pytest.mark.asyncio
async def test_completed_provider_output_requires_a_result_url(monkeypatch) -> None:
    real = _executor()
    monkeypatch.setattr(executor, 'extract_fal_video_url', lambda *_args: None)
    with pytest.raises(VideoExecutionError, match='missing'):
        await real._completed_provider_output(
            video_task(),
            SimpleNamespace(output_field='video'),
            {},
            None,
            None,
        )


@pytest.mark.asyncio
async def test_completed_delivery_error_mapping_keeps_paid_boundary(monkeypatch) -> None:
    real = _executor()
    cancellation = asyncio.CancelledError()
    for error, expected in (
        (cancellation, asyncio.CancelledError),
        (VideoExecutionError('video_result_missing'), VideoExecutionError),
        (RuntimeError('delivery'), VideoExecutionError),
    ):
        monkeypatch.setattr(
            executor.FalVideoExecutor,
            '_completed_provider_output',
            AsyncMock(side_effect=error),
        )
        with pytest.raises(expected) as captured:
            await real._deliver_invocation_result(
                video_task(),
                SimpleNamespace(),
                {},
                None,
                None,
            )
        assert captured.value.provider_completed is True


@pytest.mark.asyncio
async def test_resume_error_mapping_covers_cancel_provider_and_delivery(monkeypatch) -> None:
    real = _executor()
    context = executor.ResumeContext(observer=None)
    monkeypatch.setattr(executor, 'mark_observer_failed_if_pending', AsyncMock())
    errors = (
        asyncio.CancelledError(),
        VideoExecutionError('video_result_missing'),
        FalImageError('timed out', status_code=504),
        RuntimeError('delivery'),
    )
    for error in errors:
        with pytest.raises((asyncio.CancelledError, VideoExecutionError)) as captured:
            await real._raise_resume_error(context, error, result_url='https://result')
        assert captured.value.provider_submitted is True


@pytest.mark.asyncio
async def test_executor_resolution_and_diagnostics_reject_invalid_configuration(monkeypatch) -> None:
    monkeypatch.setattr(executor, 'get_video_fal_settings', AsyncMock(return_value=(True, None)))
    monkeypatch.setenv('VIDEO_GENERATION_MOCK_SCENARIO', 'invalid')
    with pytest.raises(VideoExecutionError, match='scenario'):
        await executor.resolve_video_executor()
    monkeypatch.setattr(executor, 'get_video_fal_settings', AsyncMock(return_value=(False, None)))
    with pytest.raises(VideoExecutionError, match='configured'):
        await executor.resolve_video_executor()

    monkeypatch.setenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', '-1')
    diagnostics = await executor.video_runtime_diagnostics(
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(video_generation_tasks=[])))
    )
    assert diagnostics['configuration_error'] == 'video_fal_not_configured'
    assert diagnostics['max_credits_per_request'] is None
    assert diagnostics['active_task_count'] == 0


@pytest.mark.asyncio
async def test_upload_once_maps_transport_errors_and_always_closes(monkeypatch, tmp_path) -> None:
    session = SimpleNamespace(close=AsyncMock())
    monkeypatch.setattr(executor, '_transfer_session', lambda: session)
    monkeypatch.setattr(
        executor,
        '_initiate_fal_storage_upload',
        AsyncMock(side_effect=RuntimeError('transport')),
    )
    with pytest.raises(VideoExecutionError) as captured:
        await executor._upload_file_to_fal_once(
            path=tmp_path / 'file',
            filename='file',
            content_type='video/mp4',
            api_key='fake',
            storage_base_url='https://storage.test',
            upload_lifetime_seconds=60,
        )
    assert captured.value.retryable is True
    session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_download_and_retry_helpers_reject_unsafe_urls_and_stop_on_terminal_error(
    monkeypatch,
    tmp_path,
) -> None:
    with pytest.raises(VideoExecutionError, match='url'):
        await executor.download_fal_video('http://unsafe.test/video', max_bytes=10)

    terminal = VideoExecutionError('video_result_download_failed', retryable=False)
    monkeypatch.setattr(executor, 'download_fal_video', AsyncMock(side_effect=terminal))
    with pytest.raises(VideoExecutionError):
        await executor.download_fal_video_with_retry('https://safe.test/video', max_bytes=10)

    path = tmp_path / 'video.mp4'
    path.write_bytes(b'0000ftyp0000')
    assert video_result.looks_like_mp4_file(path) is True
    assert video_result.task_duration_seconds(SimpleNamespace(params={'duration': 'bad'})) is None
    monkeypatch.setattr(video_result.asyncio, 'to_thread', AsyncMock(side_effect=RuntimeError))
    await video_result.remove_file(path)


def test_safe_https_url_returns_false_for_invalid_values() -> None:
    assert video_result.is_safe_https_url('https://safe.test/path') is True
    assert video_result.is_safe_https_url('http://unsafe.test/path') is False
