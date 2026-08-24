from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.provider_ops import tracing
from open_webui.extensions.videos import provider_observer, task_state
from open_webui.extensions.videos.execution_types import VideoExecutionError


def _row(**changes):
    values = {
        'provider_request_id': None,
        'provider_status_url': None,
        'provider_response_url': None,
        'provider_result_url': None,
        'provider_definition_json': {
            'id': 'fal-ai/model',
            'public_id': 'model',
            'name': 'Model',
            'provider': 'fal',
            'task': 'text-to-video',
        },
        'provider_payload_json': {'prompt': 'safe'},
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_provider_snapshot_validation_and_submission_detection() -> None:
    definition, payload = task_state.provider_execution_snapshot(_row())
    assert definition.id == 'fal-ai/model'
    assert payload == {'prompt': 'safe'}
    assert task_state.task_has_provider_submission(_row()) is False
    assert task_state.task_has_provider_submission(_row(provider_request_id='request')) is True
    with pytest.raises(VideoExecutionError):
        task_state.provider_execution_snapshot(_row(provider_payload_json=None))
    with pytest.raises(VideoExecutionError):
        task_state.provider_execution_snapshot(_row(provider_definition_json={'invalid': True}))
    assert task_state._provider_url({'url': 'http://unsafe'}, 'url') is None
    assert task_state._provider_url({'url': 'https://safe.test'}, 'url') == 'https://safe.test'


@pytest.mark.asyncio
async def test_provider_recovery_persistence_and_fallback_merge(monkeypatch) -> None:
    persist = AsyncMock()
    monkeypatch.setattr(task_state, 'persist_task_recovery_values', persist)
    monkeypatch.setattr(task_state, '_now', lambda: 1)
    await task_state.persist_provider_submission(
        'task',
        {
            'request_id': 'r' * 200,
            'status_url': 'https://queue.test/status',
            'response_url': 'http://unsafe',
        },
    )
    values = persist.await_args.args[1]
    assert len(values['provider_request_id']) == 128
    assert values['provider_response_url'] is None

    await task_state.persist_provider_result_url('task', 'https://media.test/result.mp4')
    with pytest.raises(VideoExecutionError):
        await task_state.persist_provider_result_url('task', 'http://unsafe')

    fallback = SimpleNamespace(
        provider_request_id='request',
        status_url='https://queue.test/status',
        response_url='https://queue.test/result',
        result_url='https://media.test/result.mp4',
    )
    monkeypatch.setattr(task_state, 'load_provider_recovery_state', AsyncMock(return_value=fallback))
    merged = await task_state.merged_provider_recovery_values('task', _row())
    assert merged == (
        'request',
        'https://queue.test/status',
        'https://queue.test/result',
        'https://media.test/result.mp4',
        True,
    )

    persist.side_effect = RuntimeError('backfill')
    assert (await task_state.merged_provider_recovery_values('task', _row()))[-1] is True


@pytest.mark.asyncio
async def test_provider_observer_forwards_callbacks_and_swallows_diagnostic_failure() -> None:
    base = SimpleNamespace(
        submitted=AsyncMock(),
        status=AsyncMock(),
        succeeded=AsyncMock(),
        failed=AsyncMock(),
        result_available=AsyncMock(),
    )
    submitted = AsyncMock()
    observer = provider_observer.VideoProviderObserver(base, submitted)
    payload = {'request_id': 'request'}
    await observer.submitted(payload)
    await observer.status(payload)
    await observer.succeeded()
    error = RuntimeError('provider')
    await observer.failed(error)
    base.submitted.assert_awaited_once_with(payload)
    submitted.assert_awaited_once_with(payload)

    result = AsyncMock()
    await provider_observer.record_provider_result_url(base, result, 'https://media.test')
    base.result_available.assert_awaited_once()
    result.assert_awaited_once()

    await provider_observer.mark_observer_failed_if_pending(None, error, terminal_notified=False)
    await provider_observer.mark_observer_failed_if_pending(base, error, terminal_notified=True)
    base.failed.side_effect = RuntimeError('diagnostic db')
    await provider_observer.mark_observer_failed_if_pending(base, error, terminal_notified=False)


def test_provider_observer_protocol_is_importable() -> None:
    assert tracing.ProviderInvocationObserver.__name__ == 'ProviderInvocationObserver'
