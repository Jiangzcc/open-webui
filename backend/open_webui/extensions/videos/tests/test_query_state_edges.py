import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.tests.async_test_support import AsyncContext
from open_webui.extensions.videos import queries, task_state
from open_webui.extensions.videos.execution_types import VideoExecutionError
from open_webui.extensions.videos.schemas import VideoAssetReference, VideoTaskSubmitForm
from sqlalchemy.exc import IntegrityError


@pytest.mark.asyncio
async def test_video_asset_validation_rejects_missing_type_and_size(monkeypatch) -> None:
    submission = VideoTaskSubmitForm(
        task='image-to-video',
        model='model',
        assets=(VideoAssetReference(role='start_image', file_id='file'),),
    )
    constraint = SimpleNamespace(
        role='start_image',
        mime_types=['image/png'],
        max_bytes=10,
    )
    definition = SimpleNamespace(asset_inputs=[constraint])
    lookup = AsyncMock(return_value=None)
    monkeypatch.setattr(queries.Files, 'get_file_by_id_and_user_id', lookup)
    with pytest.raises(ValueError, match='not_found'):
        await queries.validate_video_assets(submission, definition, 'user')

    lookup.return_value = SimpleNamespace(meta={'content_type': 'image/jpeg', 'size': 1})
    with pytest.raises(ValueError, match='type'):
        await queries.validate_video_assets(submission, definition, 'user')
    lookup.return_value = SimpleNamespace(meta={'content_type': 'image/png', 'size': 11})
    with pytest.raises(ValueError, match='large'):
        await queries.validate_video_assets(submission, definition, 'user')
    lookup.return_value = SimpleNamespace(meta=None)
    with pytest.raises(ValueError, match='type'):
        await queries.validate_video_assets(submission, definition, 'user')


@pytest.mark.asyncio
async def test_video_task_insert_conflict_requires_a_persisted_winner(monkeypatch) -> None:
    conflict = IntegrityError('statement', {}, Exception('duplicate'))
    session = SimpleNamespace(
        add=lambda _task: None,
        commit=AsyncMock(side_effect=conflict),
        rollback=AsyncMock(),
    )
    monkeypatch.setattr(queries, '_video_task_by_key', AsyncMock(return_value=None))
    monkeypatch.setattr(
        queries,
        'build_video_provider_payload',
        lambda _submission: (
            SimpleNamespace(model_dump=lambda **_kwargs: {}),
            {},
            {},
        ),
    )
    monkeypatch.setattr(queries, 'validate_video_assets', AsyncMock())
    submission = VideoTaskSubmitForm(task='text-to-video', model='model')
    with pytest.raises(IntegrityError):
        await queries.create_video_task(
            session,
            user_id='user',
            idempotency_key='key',
            submission=submission,
        )


@pytest.mark.asyncio
async def test_task_state_persistence_retries_then_succeeds_and_preserves_cancel(monkeypatch) -> None:
    attempts = 0

    class Session:
        async def execute(self, _statement):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError('database')

        async def commit(self):
            return None

    monkeypatch.setattr(task_state, 'creation_session', lambda: AsyncContext(Session()))
    monkeypatch.setattr(task_state.asyncio, 'sleep', AsyncMock())
    await task_state.persist_task_recovery_values('task', {'updated_at': 1})
    assert attempts == 3

    class CancelledSession:
        async def execute(self, _statement):
            raise asyncio.CancelledError

    monkeypatch.setattr(
        task_state,
        'creation_session',
        lambda: AsyncContext(CancelledSession()),
    )
    with pytest.raises(asyncio.CancelledError):
        await task_state.persist_task_recovery_values('task', {})


@pytest.mark.asyncio
async def test_task_state_persistence_exhaustion_and_invalid_result_url(monkeypatch) -> None:
    session = SimpleNamespace(execute=AsyncMock(side_effect=RuntimeError('database')))
    monkeypatch.setattr(task_state, 'creation_session', lambda: AsyncContext(session))
    monkeypatch.setattr(task_state.asyncio, 'sleep', AsyncMock())
    with pytest.raises(RuntimeError, match='database'):
        await task_state.persist_task_recovery_values('task', {})

    with pytest.raises(VideoExecutionError) as captured:
        await task_state.persist_provider_result_url('task', 'http://unsafe')
    assert captured.value.provider_completed is True


@pytest.mark.asyncio
async def test_provider_state_backfill_failure_does_not_hide_fallback(monkeypatch) -> None:
    fallback = SimpleNamespace(
        provider_request_id='request',
        status_url='https://status',
        response_url='https://response',
        result_url='https://result',
    )
    monkeypatch.setattr(task_state, 'load_provider_recovery_state', AsyncMock(return_value=fallback))
    monkeypatch.setattr(
        task_state,
        'persist_task_recovery_values',
        AsyncMock(side_effect=RuntimeError('database')),
    )
    values = await task_state.merged_provider_recovery_values(
        'task',
        SimpleNamespace(
            provider_request_id=None,
            provider_status_url=None,
            provider_response_url=None,
            provider_result_url=None,
        ),
    )
    assert values == (
        'request',
        'https://status',
        'https://response',
        'https://result',
        True,
    )
