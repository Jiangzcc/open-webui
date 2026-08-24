from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import image_recovery


def _task(**changes):
    values = {
        'id': 'task-1',
        'user_id': 'user-1',
        'kind': 'text-to-image',
        'status': 'running',
        'prompt': 'Prompt',
        'params_json': {'negative_prompt': 'blur', 'size': '1024x1024'},
        'execution_mode': 'fal',
        'delivery_attempts': 0,
        'idempotency_key': 'key-1',
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _usage(**changes):
    values = {
        'id': 'usage-1',
        'status': 'invoking',
        'resource_id': 'fal-ai/z-image/turbo',
        'channel': 'web',
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _request():
    return SimpleNamespace(app=SimpleNamespace())


def test_capture_context_and_credentials_use_persisted_snapshots() -> None:
    context = image_recovery._capture_context(_task(), _usage())
    assert context.negative_prompt == 'blur'
    assert context.params == {'size': '1024x1024'}
    assert context.batch_id == 'task-1'

    config = SimpleNamespace(
        FAL_API_KEY='generation-key',
        FAL_API_BASE_URL='https://queue.test',
        IMAGES_EDIT_FAL_API_KEY='edit-key',
        IMAGES_EDIT_FAL_API_BASE_URL='https://edit.test',
    )
    assert image_recovery._fal_credentials(config, 'text-to-image') == (
        'generation-key',
        'https://queue.test',
    )
    assert image_recovery._fal_credentials(config, 'image-to-image') == ('edit-key', 'https://edit.test')
    with pytest.raises(RuntimeError):
        image_recovery._fal_credentials(SimpleNamespace(), 'text-to-image')


@pytest.mark.asyncio
async def test_cleanup_batch_resolves_only_existing_file_ids(monkeypatch) -> None:
    existing = object()
    lookup = AsyncMock(side_effect=[existing, None])
    cleanup = AsyncMock()
    monkeypatch.setattr(image_recovery.Files, 'get_file_by_id', lookup)
    monkeypatch.setattr(image_recovery, 'cleanup_uploaded_files', cleanup)
    await image_recovery._cleanup_batch(None)
    await image_recovery._cleanup_batch(
        SimpleNamespace(
            images=(
                SimpleNamespace(file_id='one'),
                SimpleNamespace(file_id='two'),
                SimpleNamespace(file_id=None),
            )
        )
    )
    cleanup.assert_awaited_once_with([existing])


@pytest.mark.asyncio
async def test_recovery_resolution_classifies_all_persisted_states(monkeypatch) -> None:
    fail = AsyncMock()
    settle = AsyncMock()
    completed = AsyncMock(return_value=None)
    monkeypatch.setattr(image_recovery, '_fail_usage_and_task', fail)
    monkeypatch.setattr(image_recovery, '_settle_existing_creation', settle)
    monkeypatch.setattr(image_recovery, '_completed_result_from_creations', completed)
    request = _request()

    assert await image_recovery._recovery_already_resolved(request, _task(status='queued'), _usage()) is True
    assert fail.call_args.kwargs['restore_prepaid'] is True
    fail.reset_mock()
    assert await image_recovery._recovery_already_resolved(request, _task(), None) is True
    assert fail.await_count == 1

    completed.return_value = [{'url': '/content'}]
    assert await image_recovery._recovery_already_resolved(request, _task(), _usage()) is True
    settle.assert_awaited_once()
    completed.return_value = None
    assert await image_recovery._recovery_already_resolved(request, _task(), _usage()) is False

    assert await image_recovery._recovery_already_resolved(
        request,
        _task(execution_mode='mock'),
        _usage(status='debited'),
    ) is True
    assert fail.call_args.kwargs['restore_prepaid'] is True


@pytest.mark.asyncio
async def test_provider_state_and_failure_retry_policy(monkeypatch) -> None:
    fail = AsyncMock()
    state_loader = AsyncMock(return_value=None)
    monkeypatch.setattr(image_recovery, '_fail_usage_and_task', fail)
    monkeypatch.setattr(image_recovery, 'load_provider_recovery_state', state_loader)
    request = _request()
    task = _task()
    usage = _usage()
    assert await image_recovery._load_usable_provider_state(request, task, usage) is None

    state_loader.return_value = SimpleNamespace(response_url='https://queue.test/result')
    task.delivery_attempts = image_recovery._IMAGE_DELIVERY_MAX_ATTEMPTS
    assert await image_recovery._load_usable_provider_state(request, task, usage) is None
    task.delivery_attempts = 0
    assert await image_recovery._load_usable_provider_state(request, task, usage) is state_loader.return_value

    cleanup = AsyncMock()
    set_state = AsyncMock()
    completed = AsyncMock(return_value=[{'url': '/content'}])
    monkeypatch.setattr(image_recovery, '_cleanup_batch', cleanup)
    monkeypatch.setattr(image_recovery, '_set_task_state', set_state)
    monkeypatch.setattr(image_recovery, '_completed_result_from_creations', completed)
    run = image_recovery._RecoveryRun(terminal_committed=True)
    await image_recovery._handle_image_recovery_failure(run, request, task, usage)
    set_state.assert_awaited_once()

    set_state.reset_mock()
    run = image_recovery._RecoveryRun(attempts=1)
    await image_recovery._handle_image_recovery_failure(run, request, task, usage)
    cleanup.assert_awaited()
    set_state.assert_awaited_once_with(task.id, status='running', error_code='image_delivery_pending')

    run.attempts = image_recovery._IMAGE_DELIVERY_MAX_ATTEMPTS
    await image_recovery._handle_image_recovery_failure(run, request, task, usage)
    assert fail.await_count >= 1


@pytest.mark.asyncio
async def test_recover_generation_task_orchestrates_resume_without_new_post(monkeypatch) -> None:
    task = _task()
    usage = _usage()
    monkeypatch.setattr(image_recovery, '_load_active_task_and_usage', AsyncMock(return_value=(None, None)))
    assert await image_recovery.recover_generation_task('missing', _request()) is None

    monkeypatch.setattr(image_recovery, '_load_active_task_and_usage', AsyncMock(return_value=(task, usage)))
    resolved = AsyncMock(return_value=True)
    monkeypatch.setattr(image_recovery, '_recovery_already_resolved', resolved)
    assert await image_recovery.recover_generation_task(task.id, _request()) is None

    resolved.return_value = False
    state_loader = AsyncMock(return_value=None)
    monkeypatch.setattr(image_recovery, '_load_usable_provider_state', state_loader)
    assert await image_recovery.recover_generation_task(task.id, _request()) is None

    state = object()
    state_loader.return_value = state
    perform = AsyncMock(side_effect=RuntimeError('delivery'))
    handle = AsyncMock()
    monkeypatch.setattr(image_recovery, '_perform_image_recovery', perform)
    monkeypatch.setattr(image_recovery, '_handle_image_recovery_failure', handle)
    await image_recovery.recover_generation_task(task.id, _request())
    handle.assert_awaited_once()
