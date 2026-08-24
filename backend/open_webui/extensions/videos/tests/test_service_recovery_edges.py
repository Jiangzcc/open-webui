import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.tests.async_test_support import (
    AsyncContext,
)
from open_webui.extensions.tests.async_test_support import (
    TransactionalSession as _Session,
)
from open_webui.extensions.videos import service
from open_webui.extensions.videos.catalog import VideoInputError
from open_webui.extensions.videos.execution_types import VideoExecutionError

REQUEST = SimpleNamespace(
    app=SimpleNamespace(url_path_for=lambda _name, *, id: f'/files/{id}')
)
USER = SimpleNamespace(id='user')


@pytest.mark.asyncio
async def test_task_state_usage_and_delivery_attempt_writes(monkeypatch) -> None:
    session = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    monkeypatch.setattr(service, 'creation_session', lambda: AsyncContext(session))
    await service._set_task_state('task', 'running')
    await service._set_task_usage_id('task', 'usage', 'fal')
    await service._increment_delivery_attempts('task')
    assert session.execute.await_count == 3
    assert session.commit.await_count == 3

    persist = AsyncMock()
    increment = AsyncMock()
    monkeypatch.setattr(service, '_persist_provider_result_url', persist)
    monkeypatch.setattr(service, '_increment_delivery_attempts', increment)
    await service._persist_provider_result_for_delivery('task', 'https://result')
    persist.assert_awaited_once_with('task', 'https://result')
    increment.assert_awaited_once_with('task')


@pytest.mark.asyncio
async def test_failure_settlement_continues_across_independent_write_errors(monkeypatch) -> None:
    monkeypatch.setattr(service, 'mark_video_usage_failed', AsyncMock(side_effect=RuntimeError))
    monkeypatch.setattr(service, '_set_task_state', AsyncMock(side_effect=RuntimeError))
    monkeypatch.setattr(service, '_publish_video_task_event', AsyncMock(side_effect=RuntimeError))
    await service._try_settle_video_task_failure(
        REQUEST,
        'task',
        'user',
        error_code='failed',
        usage_id='usage',
        restore_prepaid=True,
        context='test',
    )
    service._publish_video_task_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_new_execution_returns_for_missing_row_and_rejects_replay(monkeypatch) -> None:
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    monkeypatch.setattr(service, 'creation_session', lambda: AsyncContext(session))
    monkeypatch.setattr(service, '_set_task_state', AsyncMock())
    monkeypatch.setattr(service, '_publish_video_task_event', AsyncMock())
    state = service._VideoRunState()
    await service._execute_new_video_task(state, 'task', REQUEST, USER, 'user')

    session.scalar.return_value = SimpleNamespace()
    monkeypatch.setattr(service, '_response', lambda _row: SimpleNamespace())
    monkeypatch.setattr(
        service,
        'resolve_video_executor',
        AsyncMock(return_value=SimpleNamespace(mode='mock')),
    )
    monkeypatch.setattr(
        service,
        'begin_video_usage',
        AsyncMock(return_value=SimpleNamespace(outcome='succeeded')),
    )
    with pytest.raises(RuntimeError, match='unexpected'):
        await service._execute_new_video_task(state, 'task', REQUEST, USER, 'user')


@pytest.mark.asyncio
async def test_terminal_usage_lookup_and_cancellation_recovery_edges(monkeypatch) -> None:
    session = SimpleNamespace(scalar=AsyncMock(side_effect=RuntimeError))
    monkeypatch.setattr(service, 'credit_session', lambda: AsyncContext(session))
    assert await service._persisted_usage_succeeded('usage', 'task') is False

    settle = AsyncMock(side_effect=RuntimeError)
    monkeypatch.setattr(service, '_settle_video_task_success', settle)
    state = service._VideoRunState(usage_id='usage', usage_succeeded=True, result={'url': '/file'})
    await service._handle_run_cancellation(
        state,
        asyncio.CancelledError(),
        REQUEST,
        'task',
        'user',
    )

    state = service._VideoRunState(usage_id='usage')
    error = asyncio.CancelledError()
    error.provider_submitted = True
    monkeypatch.setattr(service, '_set_task_state', AsyncMock(side_effect=RuntimeError))
    await service._handle_run_cancellation(state, error, REQUEST, 'task', 'user')


@pytest.mark.asyncio
async def test_unexpected_run_error_restores_success_or_cleans_partial_result(monkeypatch) -> None:
    monkeypatch.setattr(service, '_settle_video_task_success', AsyncMock(side_effect=RuntimeError))
    state = service._VideoRunState(usage_succeeded=True, result={'url': '/file'})
    await service._handle_unexpected_run_error(state, REQUEST, 'task', 'user')

    cleanup = AsyncMock()
    failure = AsyncMock()
    monkeypatch.setattr(service, '_cleanup_result_files', cleanup)
    monkeypatch.setattr(service, '_try_settle_video_task_failure', failure)
    state = service._VideoRunState(output=SimpleNamespace(), result={'url': '/file'})
    await service._handle_unexpected_run_error(state, REQUEST, 'task', 'user')
    cleanup.assert_awaited_once()
    assert failure.await_args.kwargs['error_code'] == 'video_delivery_failed'


@pytest.mark.asyncio
async def test_existing_creation_and_usage_settlement_edges(monkeypatch) -> None:
    session = _Session(scalar=AsyncMock(return_value=None))
    monkeypatch.setattr(service, 'creation_session', lambda: AsyncContext(session))
    assert await service._existing_creation_result(REQUEST, 'task', 'user') is None
    session.scalar.return_value = SimpleNamespace(duration_seconds=0)
    assert await service._existing_creation_result(REQUEST, 'task', 'user') is None

    state = service._VideoRecoveryState(usage_id='usage')
    monkeypatch.setattr(service, '_existing_creation_result', AsyncMock(return_value=None))
    assert await service._settle_existing_video_result(state, REQUEST, 'task', 'user') is False

    existing = {'url': '/file'}
    monkeypatch.setattr(service, '_existing_creation_result', AsyncMock(return_value=existing))
    monkeypatch.setattr(service, 'credit_session', lambda: AsyncContext(session))
    session.scalar.return_value = 'invoking'
    monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', AsyncMock(return_value=0))
    with pytest.raises(RuntimeError, match='transition'):
        await service._settle_existing_video_result(state, REQUEST, 'task', 'user')
    session.scalar.return_value = 'failed'
    with pytest.raises(VideoExecutionError):
        await service._settle_existing_video_result(state, REQUEST, 'task', 'user')


@pytest.mark.asyncio
async def test_provider_resume_and_recovery_dispatch_edges(monkeypatch) -> None:
    state = service._VideoRecoveryState(row=SimpleNamespace(execution_mode='mock'))
    monkeypatch.setattr(service, '_run_mock_scenario', AsyncMock())
    await service._resume_video_provider(state, 'task', object())
    state.row.execution_mode = 'fal'
    monkeypatch.setattr(service, '_resume_fal_video_output', AsyncMock())
    await service._resume_video_provider(state, 'task', object())
    state.row.execution_mode = None
    with pytest.raises(VideoExecutionError, match='state'):
        await service._resume_video_provider(state, 'task', object())

    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    monkeypatch.setattr(service, 'creation_session', lambda: AsyncContext(session))
    state = service._VideoRecoveryState()
    await service._execute_video_recovery(state, 'task', REQUEST, USER, 'user')
    session.scalar.return_value = SimpleNamespace(status='queued')
    monkeypatch.setattr(service, 'run_video_task', AsyncMock())
    await service._execute_video_recovery(state, 'task', REQUEST, USER, 'user')
    service.run_video_task.assert_awaited_once()

    session.scalar.return_value = SimpleNamespace(status='running', usage_id=None)
    monkeypatch.setattr(service, '_response', lambda _row: object())
    monkeypatch.setattr(service, '_task_has_provider_submission', lambda _row: False)
    with pytest.raises(VideoExecutionError, match='state'):
        await service._execute_video_recovery(state, 'task', REQUEST, USER, 'user')


@pytest.mark.asyncio
async def test_recovery_error_handlers_preserve_terminal_success_and_input_policy(monkeypatch) -> None:
    settle = AsyncMock(side_effect=RuntimeError)
    monkeypatch.setattr(service, '_settle_video_task_success', settle)
    state = service._VideoRecoveryState(
        usage_succeeded=True,
        result={'url': '/file'},
    )
    await service._handle_unexpected_recovery_error(state, REQUEST, 'task', 'user')

    failure = AsyncMock()
    monkeypatch.setattr(service, '_try_settle_video_task_failure', failure)
    state = service._VideoRecoveryState(
        row=SimpleNamespace(execution_mode='mock'),
        usage_id='usage',
        provider_was_submitted=False,
    )
    await service._handle_recovery_input_error(
        state,
        VideoInputError('invalid'),
        REQUEST,
        'task',
        'user',
    )
    assert failure.await_args.kwargs['restore_prepaid'] is True


@pytest.mark.asyncio
async def test_recovery_loop_handles_missing_users_slots_and_scheduler_races(monkeypatch) -> None:
    rows = [
        SimpleNamespace(id='missing', user_id='missing', status='running'),
        SimpleNamespace(id='busy', user_id='busy', status='running'),
        SimpleNamespace(id='scheduled', user_id='ok', status='running'),
        SimpleNamespace(id='raced', user_id='race', status='running'),
    ]
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    monkeypatch.setattr(service, 'creation_session', lambda: AsyncContext(session))
    users = {
        'missing': None,
        'busy': SimpleNamespace(id='busy'),
        'ok': SimpleNamespace(id='ok'),
        'race': SimpleNamespace(id='race'),
    }
    monkeypatch.setattr(
        service.Users,
        'get_user_by_id',
        AsyncMock(side_effect=lambda user_id: users[user_id]),
    )
    monkeypatch.setattr(service, '_set_task_state', AsyncMock())
    acquire = AsyncMock(side_effect=[CreditError(code='rate_limited'), None, None])
    monkeypatch.setattr(service, 'acquire_video_generation_slot', acquire)
    monkeypatch.setattr(
        service,
        'schedule_video_recovery_task',
        Mock(side_effect=[True, False]),
    )
    release = AsyncMock()
    monkeypatch.setattr(service, 'release_video_generation_slot', release)
    assert await service.recover_incomplete_video_tasks(REQUEST) == 1
    release.assert_awaited_once_with('race')
