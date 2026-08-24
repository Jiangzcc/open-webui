import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.tests.async_test_support import wait_until_cancelled
from open_webui.extensions.videos import service
from open_webui.extensions.videos.executor import FalVideoExecutor, VideoExecutionError


def _request():
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(video_generation_tasks={})))


@pytest.mark.asyncio
async def test_failure_settlement_attempts_all_three_independent_steps(monkeypatch) -> None:
    usage = AsyncMock(side_effect=RuntimeError('usage'))
    state = AsyncMock(side_effect=RuntimeError('task'))
    publish = AsyncMock(side_effect=RuntimeError('event'))
    monkeypatch.setattr(service, 'mark_video_usage_failed', usage)
    monkeypatch.setattr(service, '_set_task_state', state)
    monkeypatch.setattr(service, '_publish_video_task_event', publish)
    await service._try_settle_video_task_failure(
        _request(),
        'task',
        'user',
        error_code='failed',
        usage_id='usage',
        restore_prepaid=False,
        context='test',
    )
    usage.assert_awaited_once()
    state.assert_awaited_once()
    publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_resource_finalizer_cancels_heartbeat_and_deletes_temp_file(monkeypatch, tmp_path: Path) -> None:
    started = asyncio.Event()

    async def heartbeat():
        await wait_until_cancelled(started)

    task = asyncio.create_task(heartbeat())
    await started.wait()
    path = tmp_path / 'result.mp4'
    path.write_bytes(b'video')
    output = SimpleNamespace(video_path=path)
    await service._finalize_task_resources(task, output, task_id='task', context='temporary')
    assert task.cancelled()
    assert not path.exists()

    monkeypatch.setattr(service.asyncio, 'to_thread', AsyncMock(side_effect=RuntimeError('delete')))
    await service._finalize_task_resources(None, output, task_id='task', context='temporary')


@pytest.mark.asyncio
async def test_schedule_failure_and_success_helpers(monkeypatch) -> None:
    set_state = AsyncMock()
    publish = AsyncMock()
    monkeypatch.setattr(service, '_set_task_state', set_state)
    monkeypatch.setattr(service, '_publish_video_task_event', publish)
    await service.fail_video_task_scheduling(object(), 'task', 'user')
    set_state.assert_awaited_once_with('task', 'failed', error_code='video_scheduling_failed')
    publish.assert_awaited_once()

    tracked = Mock()
    monkeypatch.setattr(service, 'schedule_tracked_task', tracked)
    request = _request()
    service.schedule_video_task(request, 'task', SimpleNamespace(id='user'))
    tracked.assert_called_once()
    tracked.reset_mock()
    assert service.schedule_video_recovery_task(request, 'task', SimpleNamespace(id='user')) is True
    request.app.state.video_generation_tasks['task'] = object()
    assert service.schedule_video_recovery_task(request, 'task', SimpleNamespace(id='user')) is False


@pytest.mark.asyncio
async def test_queued_admission_classifies_permanent_and_temporary_failures(monkeypatch) -> None:
    row = SimpleNamespace(id='task', model_id='model')
    user = SimpleNamespace(id='user')
    context = _AsyncContext(object())
    monkeypatch.setattr(service, 'get_async_db', lambda: context)
    ensure = AsyncMock(side_effect=HTTPException(status_code=503, detail={'code': 'disabled'}))
    monkeypatch.setattr(service, 'ensure_model_enabled', ensure)
    assert await service._queued_task_rejection_code(row, user) == 'disabled'

    ensure.side_effect = RuntimeError('db')
    assert await service._queued_task_rejection_code(row, user) is None
    ensure.side_effect = None
    monkeypatch.setattr(service, '_response', lambda _row: object())
    monkeypatch.setattr(service, '_submission_from_task', lambda _task: object())
    quote = AsyncMock(side_effect=service.VideoInputError('removed'))
    monkeypatch.setattr(service, 'quote_video_usage', quote)
    assert await service._queued_task_rejection_code(row, user) == 'unknown_video_model'

    quote.side_effect = CreditError(code='price_not_configured')
    assert await service._queued_task_rejection_code(row, user) is None
    quote.side_effect = None
    quote.return_value = SimpleNamespace(charged_credits=3)
    resolve = AsyncMock(side_effect=VideoExecutionError('temporary'))
    monkeypatch.setattr(service, 'resolve_video_executor', resolve)
    assert await service._queued_task_rejection_code(row, user) is None

    resolve.side_effect = None
    resolve.return_value = FalVideoExecutor('fake', 'https://queue.test', 'https://storage.test', 1, 1, 1)
    policy = Mock(side_effect=VideoExecutionError('policy'))
    monkeypatch.setattr(service, 'enforce_fal_video_policy', policy)
    assert await service._queued_task_rejection_code(row, user) == 'policy'


@pytest.mark.asyncio
async def test_shutdown_cancels_and_clears_tracked_workers() -> None:
    started = asyncio.Event()

    async def worker():
        await wait_until_cancelled(started)

    task = asyncio.create_task(worker())
    await started.wait()
    running = {'task': task}
    app = SimpleNamespace(state=SimpleNamespace(video_generation_tasks=running))
    await service.shutdown_video_tasks(app)
    assert task.cancelled()
    assert running == {}


class _AsyncContext:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_args):
        return None
