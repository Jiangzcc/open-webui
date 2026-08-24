import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.creations import generation_tasks as tasks
from open_webui.extensions.creations.models import ImageGenerationTask
from open_webui.extensions.tests.async_test_support import AsyncContext
from sqlalchemy.exc import IntegrityError


def _task(**changes):
    values = {
        'id': 'task-1',
        'user_id': 'user-1',
        'idempotency_key': 'key',
        'payload_sha256': tasks._payload_sha256({'prompt': 'prompt'}),
        'kind': 'text-to-image',
        'prompt': 'prompt',
        'model_id': 'model',
        'params_json': {},
        'expected_count': 1,
        'status': 'queued',
        'execution_mode': None,
        'result_json': None,
        'error_code': None,
        'created_at': 1,
        'started_at': None,
        'completed_at': None,
        'updated_at': 1,
    }
    values.update(changes)
    return ImageGenerationTask(**values)


@pytest.mark.asyncio
async def test_idempotent_lookup_and_create_conflict_paths(monkeypatch) -> None:
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    assert await tasks.get_generation_task_by_idempotency_key(
        session,
        'user-1',
        'key',
        kind='text-to-image',
        payload={'prompt': 'prompt'},
    ) is None
    session.scalar.return_value = _task()
    with pytest.raises(tasks.IdempotencyPayloadConflictError):
        await tasks.get_generation_task_by_idempotency_key(
            session,
            'user-1',
            'key',
            kind='image-to-image',
            payload={'prompt': 'prompt'},
        )

    conflict = IntegrityError('statement', {}, Exception('duplicate'))
    session = SimpleNamespace(add=Mock(), commit=AsyncMock(side_effect=conflict), rollback=AsyncMock())
    monkeypatch.setattr(tasks, '_task_by_idempotency_key', AsyncMock(return_value=None))
    with pytest.raises(IntegrityError):
        await tasks.create_generation_task(
            session,
            user_id='user-1',
            idempotency_key='key',
            kind='text-to-image',
            payload={'prompt': 'prompt'},
        )
    raced = _task(kind='image-to-image')
    tasks._task_by_idempotency_key.return_value = raced
    with pytest.raises(tasks.IdempotencyPayloadConflictError):
        await tasks.create_generation_task(
            session,
            user_id='user-1',
            idempotency_key='key',
            kind='text-to-image',
            payload={'prompt': 'prompt'},
        )


@pytest.mark.asyncio
async def test_missing_delete_and_filtered_task_listing() -> None:
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    assert await tasks.delete_generation_task(session, 'user-1', 'missing') is False

    rows = [_task(id='second', created_at=2), _task(id='first', created_at=1)]
    result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: rows),
    )
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    page = await tasks.list_generation_tasks(
        session,
        'user-1',
        1,
        cursor=tasks.encode_keyset_cursor(3, 'cursor'),
        since=1,
    )
    assert len(page.items) == 1
    assert page.next_cursor is not None


@pytest.mark.asyncio
async def test_state_writes_scheduling_failure_and_execution_mode(monkeypatch) -> None:
    session = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    monkeypatch.setattr(tasks, 'creation_session', lambda: AsyncContext(session))
    monkeypatch.setattr(tasks, '_publish_image_task_event', AsyncMock())
    await tasks.fail_generation_task_scheduling(object(), 'task-1', 'user-1')
    assert session.execute.await_count == 1
    tasks._publish_image_task_event.assert_awaited_once()

    await tasks.set_image_task_execution_mode(None, 'real')
    await tasks.set_image_task_execution_mode('task-1', 'real')
    assert session.execute.await_count == 2


@pytest.mark.asyncio
async def test_completed_creation_lookup_handles_database_and_request_edges(monkeypatch) -> None:
    session = SimpleNamespace(execute=AsyncMock(side_effect=RuntimeError('database')))
    monkeypatch.setattr(tasks, 'creation_session', lambda: AsyncContext(session))
    request = SimpleNamespace(app=SimpleNamespace(url_path_for=lambda _name, *, id: f'/files/{id}'))
    assert await tasks._completed_result_from_creations(request, 'task', 'user') is None

    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))
    session.execute = AsyncMock(return_value=result)
    assert await tasks._completed_result_from_creations(request, 'task', 'user') is None
    result.scalars = lambda: SimpleNamespace(all=lambda: [SimpleNamespace(file_id='file')])
    assert await tasks._completed_result_from_creations(SimpleNamespace(), 'task', 'user') is None
    assert await tasks._completed_result_from_creations(request, 'task', 'user') == [
        {'url': '/files/file'}
    ]


def test_public_result_and_error_code_only_expose_stable_fields() -> None:
    assert tasks._public_result(None) == []
    assert tasks._public_result([None, {'url': 1}, {'url': '/file', 'secret': 'hidden'}]) == [
        {'url': '/file'}
    ]
    assert tasks._error_code(SimpleNamespace(code='x' * 100)) == 'x' * 64
    assert tasks._error_code(RuntimeError()) == 'image_generation_failed'


@pytest.mark.asyncio
async def test_provider_dispatch_and_completed_restore_failures(monkeypatch) -> None:
    import open_webui.routers.images as image_router

    edit = AsyncMock(return_value='edit')
    generation = AsyncMock(return_value='generation')
    monkeypatch.setattr(image_router, 'image_edits', edit)
    monkeypatch.setattr(image_router, 'image_generations', generation)
    request = SimpleNamespace(app=SimpleNamespace())
    assert await tasks._invoke_generation_provider(
        'task', request, SimpleNamespace(), object(), 'image-to-image'
    ) == 'edit'
    assert await tasks._invoke_generation_provider(
        'task', request, SimpleNamespace(), object(), 'text-to-image'
    ) == 'generation'

    monkeypatch.setattr(tasks, '_completed_result_from_creations', AsyncMock(return_value=None))
    assert await tasks._restore_completed_image_task(request, 'task', 'user', None) is False
    monkeypatch.setattr(tasks, '_set_task_state', AsyncMock(side_effect=RuntimeError('write')))
    monkeypatch.setattr(tasks, '_publish_image_task_event', AsyncMock())
    assert await tasks._restore_completed_image_task(
        request,
        'task',
        'user',
        [{'url': '/file'}],
    ) is True
    tasks._publish_image_task_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_restart_cleanup_and_shutdown(monkeypatch) -> None:
    result = SimpleNamespace(rowcount=None)
    session = SimpleNamespace(execute=AsyncMock(return_value=result), commit=AsyncMock())
    monkeypatch.setattr(tasks, 'creation_session', lambda: AsyncContext(session))
    assert await tasks.fail_incomplete_generation_tasks() == 0

    completed = asyncio.create_task(asyncio.sleep(0))
    await completed
    running = {'task': completed}
    app = SimpleNamespace(state=SimpleNamespace(creation_generation_tasks=running))
    await tasks.shutdown_generation_tasks(app)
    assert running == {}
    await tasks.shutdown_generation_tasks(SimpleNamespace(state=SimpleNamespace()))
