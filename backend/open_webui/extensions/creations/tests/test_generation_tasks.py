from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import generation_tasks
from open_webui.extensions.creations.generation_tasks import (
    cancel_generation_task,
    create_generation_task,
    delete_generation_task,
    get_generation_task,
    list_generation_tasks,
    schedule_generation_task,
)
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.schemas import decode_keyset_cursor
from open_webui.extensions.credits.models import CreditUsage
from sqlalchemy import select, update


@pytest.mark.asyncio
async def test_generation_task_is_idempotent_and_user_scoped(creation_sessions) -> None:
    async with creation_sessions() as session:
        first, created = await create_generation_task(
            session,
            user_id='user-1',
            idempotency_key='request-1',
            kind='text-to-image',
            payload={
                'prompt': 'quiet lake',
                'model': 'fal/model',
                'n': 2,
                'aspect_ratio': '16:9',
            },
        )
        replay, replay_created = await create_generation_task(
            session,
            user_id='user-1',
            idempotency_key='request-1',
            kind='text-to-image',
            payload={'prompt': 'different prompt'},
        )

    assert created is True
    assert replay_created is False
    assert replay.id == first.id
    assert first.expected_count == 2
    assert first.params == {'model': 'fal/model', 'n': 2, 'aspect_ratio': '16:9'}

    async with creation_sessions() as session:
        assert await get_generation_task(session, 'other-user', first.id) is None
        own = await get_generation_task(session, 'user-1', first.id)
        listing = await list_generation_tasks(session, 'user-1', 20)
    assert own is not None and own.prompt == 'quiet lake'
    assert [item.id for item in listing.items] == [first.id]


@pytest.mark.asyncio
async def test_generation_task_does_not_persist_reference_data_urls(creation_sessions) -> None:
    async with creation_sessions() as session:
        task, _ = await create_generation_task(
            session,
            user_id='user-1',
            idempotency_key='request-2',
            kind='image-to-image',
            payload={
                'prompt': 'restyle',
                'image': 'data:image/png;base64,secret-pixels',
                'n': 1,
                'resolution': '1K',
            },
        )
    assert task.params == {'n': 1, 'resolution': '1K'}


@pytest.mark.asyncio
async def test_list_generation_tasks_paginates_by_cursor(creation_sessions) -> None:
    # 同秒创建的 3 个任务也能靠 (created_at, id) 组合正确分页：
    # 第一页 limit=2 拿前两条并返回 next_cursor，第二页拿最后一条且无更多。
    ids: list[str] = []
    async with creation_sessions() as session:
        for n in range(3):
            task, _ = await create_generation_task(
                session,
                user_id='user-paged',
                idempotency_key=f'page-{n}',
                kind='text-to-image',
                payload={'prompt': f'p{n}'},
            )
            ids.append(task.id)

    async with creation_sessions() as session:
        first_page = await list_generation_tasks(session, 'user-paged', 2)
    assert len(first_page.items) == 2
    assert first_page.next_cursor is not None
    page_ids = {item.id for item in first_page.items}
    assert page_ids.issubset(set(ids))
    # 游标锁定的正是第一页最后一条，翻页无重复无遗漏。
    _, cursor_id = decode_keyset_cursor(first_page.next_cursor)
    assert cursor_id in page_ids

    async with creation_sessions() as session:
        second_page = await list_generation_tasks(session, 'user-paged', 2, first_page.next_cursor)
    assert len(second_page.items) == 1
    assert second_page.next_cursor is None
    assert {item.id for item in second_page.items} == set(ids) - page_ids


@pytest.mark.asyncio
async def test_list_generation_tasks_no_cursor_when_count_equals_page_size(
    creation_sessions,
) -> None:
    # 总条数恰为页大小整数倍时，末页不得返回 next_cursor（旧 ==limit 实现会误判）。
    async with creation_sessions() as session:
        for n in range(2):
            await create_generation_task(
                session,
                user_id='user-aligned',
                idempotency_key=f'aligned-{n}',
                kind='text-to-image',
                payload={'prompt': f'p{n}'},
            )

    async with creation_sessions() as session:
        result = await list_generation_tasks(session, 'user-aligned', 2)
    assert len(result.items) == 2
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_list_generation_tasks_rejects_malformed_cursor(creation_sessions) -> None:
    async with creation_sessions() as session:
        with pytest.raises(ValueError):
            await list_generation_tasks(session, 'user-paged', 2, 'not-a-valid-cursor')


@pytest.mark.asyncio
async def test_cancel_generation_task_is_owner_scoped_and_terminal(creation_sessions, monkeypatch) -> None:
    async with creation_sessions() as session:
        task, _ = await create_generation_task(
            session,
            user_id='user-cancel',
            idempotency_key='cancel-1',
            kind='text-to-image',
            payload={'prompt': 'long running'},
        )

    @asynccontextmanager
    async def test_creation_session():
        async with creation_sessions() as session:
            yield session

    started = asyncio.Event()

    async def wait_until_cancelled(*_args):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(generation_tasks, 'creation_session', test_creation_session)
    monkeypatch.setattr(generation_tasks, 'run_generation_task', wait_until_cancelled)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(creation_generation_tasks={})))
    schedule_generation_task(
        request,
        task_id=task.id,
        user=SimpleNamespace(id='user-cancel'),
        form=SimpleNamespace(),
        kind='text-to-image',
    )
    await started.wait()

    async with creation_sessions() as session:
        assert await cancel_generation_task(request, session, 'other-user', task.id) is None
    async with creation_sessions() as session:
        cancelled = await cancel_generation_task(request, session, 'user-cancel', task.id)

    assert cancelled is not None
    assert cancelled.status == 'failed'
    assert cancelled.error_code == 'generation_cancelled'
    assert task.id not in request.app.state.creation_generation_tasks


@pytest.mark.asyncio
async def test_event_publish_failure_does_not_change_generated_image_success(monkeypatch) -> None:
    from open_webui.extensions.creations import events
    from open_webui.routers import images

    states: list[str] = []

    async def set_state(_task_id, *, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
        states.append(status)

    async def generated(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return [{'url': '/api/v1/files/result-1/content'}]

    async def failed_publish(*_args, **_kwargs) -> None:
        raise RuntimeError('event bus unavailable')

    monkeypatch.setattr(generation_tasks, '_set_task_state', set_state)
    monkeypatch.setattr(images, 'image_generations', generated)
    monkeypatch.setattr(events, 'publish_generation_event', failed_publish)

    await generation_tasks.run_generation_task(
        'task-1',
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())),
        SimpleNamespace(id='user-1'),
        object(),
        'text-to-image',
    )

    assert states == ['running', 'succeeded']


@pytest.mark.asyncio
async def test_image_cleanup_failure_does_not_mask_shutdown_cancellation(monkeypatch) -> None:
    from open_webui.routers import images

    states: list[str] = []

    async def set_state(_task_id, *, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
        states.append(status)
        if status == 'failed':
            raise RuntimeError('database unavailable')

    async def cancelled_generation(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise asyncio.CancelledError

    monkeypatch.setattr(generation_tasks, '_set_task_state', set_state)
    monkeypatch.setattr(generation_tasks, '_publish_image_task_event', AsyncMock())
    monkeypatch.setattr(images, 'image_generations', cancelled_generation)

    with pytest.raises(asyncio.CancelledError):
        await generation_tasks.run_generation_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())),
            SimpleNamespace(id='user-1'),
            object(),
            'text-to-image',
        )

    assert states == ['running', 'failed']


@pytest.mark.asyncio
async def test_delete_generation_task_soft_deletes_new_and_legacy_creation_batches(creation_sessions) -> None:
    async with creation_sessions() as session:
        task, _ = await create_generation_task(
            session,
            user_id='user-delete',
            idempotency_key='delete-key',
            kind='text-to-image',
            payload={'prompt': 'delete this batch'},
        )
    async with creation_sessions() as session, session.begin():
        await session.execute(
            update(generation_tasks.ImageGenerationTask)
            .where(generation_tasks.ImageGenerationTask.id == task.id)
            .values(status='succeeded')
        )
        session.add(
            CreditUsage(
                id='legacy-usage',
                user_id='user-delete',
                idempotency_key='delete-key',
                request_hash='a' * 64,
                service_type='image',
                resource_id='model',
                action='text-to-image',
                channel='web',
                status='succeeded',
                exempt=False,
                charged_credits=0,
                created_at=1,
                updated_at=1,
            )
        )
        for creation_id, batch_id in (('new-batch', task.id), ('legacy-batch', 'legacy-usage')):
            session.add(
                CreationMediaItem(
                    id=creation_id,
                    user_id='user-delete',
                    kind='image',
                    file_id=f'file-{creation_id}',
                    prompt='p',
                    model_id='model',
                    task='text-to-image',
                    source='web',
                    batch_id=batch_id,
                    soft_deleted=False,
                    created_at=1,
                    updated_at=1,
                )
            )

    async with creation_sessions() as session:
        assert await delete_generation_task(session, 'user-delete', task.id) is True
    async with creation_sessions() as session:
        assert await get_generation_task(session, 'user-delete', task.id) is None
        creations = list(
            (
                await session.scalars(
                    select(CreationMediaItem).where(CreationMediaItem.id.in_(('new-batch', 'legacy-batch')))
                )
            ).all()
        )
    assert {item.id for item in creations} == {'new-batch', 'legacy-batch'}
    assert all(item.soft_deleted for item in creations)
