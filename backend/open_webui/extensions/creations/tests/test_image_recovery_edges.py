import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import image_recovery
from open_webui.extensions.tests.async_test_support import (
    AsyncContext,
)
from open_webui.extensions.tests.async_test_support import (
    TransactionalSession as _Session,
)

from .test_image_recovery_direct import _request, _task, _usage


@pytest.mark.asyncio
async def test_delivery_attempt_increment_and_active_task_lookup(monkeypatch) -> None:
    session = SimpleNamespace(
        execute=AsyncMock(),
        commit=AsyncMock(),
        scalar=AsyncMock(return_value=None),
        get=AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        image_recovery,
        'creation_session',
        lambda: AsyncContext(session),
    )
    assert await image_recovery._increment_delivery_attempts('task') == 0

    monkeypatch.setattr(image_recovery, 'credit_session', lambda: AsyncContext(session))
    assert await image_recovery._load_active_task_and_usage('missing') == (None, None)
    session.get.return_value = _task(status='succeeded')
    assert await image_recovery._load_active_task_and_usage('terminal') == (None, None)
    active = _task()
    usage = _usage()
    session.get.return_value = active
    session.scalar.return_value = usage
    assert await image_recovery._load_active_task_and_usage('task') == (active, usage)


@pytest.mark.asyncio
async def test_failure_and_existing_creation_settlement_edges(monkeypatch) -> None:
    mark_failed = AsyncMock()
    set_state = AsyncMock()
    publish = AsyncMock()
    monkeypatch.setattr(image_recovery, 'mark_usage_failed', mark_failed)
    monkeypatch.setattr(image_recovery, '_set_task_state', set_state)
    monkeypatch.setattr(image_recovery, '_publish_image_task_event', publish)
    await image_recovery._fail_usage_and_task(
        _request(),
        _task(),
        _usage(),
        'failed',
        restore_prepaid=False,
    )
    mark_failed.assert_awaited_once()
    await image_recovery._fail_usage_and_task(
        _request(),
        _task(),
        _usage(status='failed'),
        'failed',
        restore_prepaid=False,
    )
    assert mark_failed.await_count == 1

    session = _Session()
    monkeypatch.setattr(image_recovery, 'credit_session', lambda: AsyncContext(session))
    monkeypatch.setattr(
        image_recovery,
        'mark_usage_succeeded_in_session',
        AsyncMock(return_value=0),
    )
    with pytest.raises(RuntimeError, match='transition'):
        await image_recovery._settle_existing_creation(
            _request(),
            _task(),
            _usage(),
            [{'url': '/file'}],
        )
    with pytest.raises(RuntimeError, match='incompatible'):
        await image_recovery._settle_existing_creation(
            _request(),
            _task(),
            _usage(status='failed'),
            [{'url': '/file'}],
        )


@pytest.mark.asyncio
async def test_perform_recovery_rejects_deleted_user(monkeypatch) -> None:
    monkeypatch.setattr(
        image_recovery.Users,
        'get_user_by_id',
        AsyncMock(return_value=None),
    )
    with pytest.raises(RuntimeError, match='no longer exists'):
        await image_recovery._perform_image_recovery(
            image_recovery._RecoveryRun(),
            _request(),
            _task(),
            _usage(),
            object(),
        )


@pytest.mark.asyncio
async def test_recover_generation_cancellation_cleans_uncommitted_batch(monkeypatch) -> None:
    task = _task()
    usage = _usage()
    monkeypatch.setattr(
        image_recovery,
        '_load_active_task_and_usage',
        AsyncMock(return_value=(task, usage)),
    )
    monkeypatch.setattr(image_recovery, '_recovery_already_resolved', AsyncMock(return_value=False))
    monkeypatch.setattr(image_recovery, '_load_usable_provider_state', AsyncMock(return_value=object()))
    monkeypatch.setattr(
        image_recovery,
        '_perform_image_recovery',
        AsyncMock(side_effect=asyncio.CancelledError),
    )
    cleanup = AsyncMock()
    monkeypatch.setattr(image_recovery, '_cleanup_batch', cleanup)
    with pytest.raises(asyncio.CancelledError):
        await image_recovery.recover_generation_task(task.id, _request())
    cleanup.assert_awaited_once_with(None)


@pytest.mark.asyncio
async def test_incomplete_recovery_scheduler_skips_running_and_removes_finished(monkeypatch) -> None:
    rows = [SimpleNamespace(id='running'), SimpleNamespace(id='new')]
    session = SimpleNamespace(
        scalars=AsyncMock(
            return_value=SimpleNamespace(all=lambda: rows)
        )
    )
    monkeypatch.setattr(image_recovery, 'creation_session', lambda: AsyncContext(session))
    blocker = asyncio.create_task(asyncio.Event().wait())
    running = {'running': blocker}
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(creation_generation_tasks=running))
    )
    monkeypatch.setattr(image_recovery, 'recover_generation_task', AsyncMock())
    assert await image_recovery.recover_incomplete_generation_tasks(request) == 1
    worker = running['new']
    await worker
    await asyncio.sleep(0)
    assert 'new' not in running
    blocker.cancel()
    await asyncio.gather(blocker, return_exceptions=True)
