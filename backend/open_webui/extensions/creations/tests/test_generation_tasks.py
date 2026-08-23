from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import generation_tasks
from open_webui.extensions.creations.generation_tasks import (
    IdempotencyPayloadConflictError,
    create_generation_task,
    delete_generation_task,
    get_generation_task,
    list_generation_tasks,
    schedule_generation_task,
)
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.schemas import decode_keyset_cursor
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
        # 同键同载荷才幂等复用（网络失败后的安全重试）。
        replay, replay_created = await create_generation_task(
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
        # 同键不同载荷必须拒绝，而不是静默复用旧任务丢弃新载荷。
        with pytest.raises(IdempotencyPayloadConflictError):
            await create_generation_task(
                session,
                user_id='user-1',
                idempotency_key='request-1',
                kind='text-to-image',
                payload={'prompt': 'different prompt'},
            )
        with pytest.raises(IdempotencyPayloadConflictError):
            await create_generation_task(
                session,
                user_id='user-1',
                idempotency_key='request-1',
                kind='image-to-image',
                payload={
                    'prompt': 'quiet lake',
                    'model': 'fal/model',
                    'n': 2,
                    'aspect_ratio': '16:9',
                },
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
async def test_schedule_generation_task_retries_cleanup_before_worker_finishes(monkeypatch) -> None:
    attempts = 0

    async def generated(*_args, **_kwargs) -> None:
        return None

    async def release() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError('transient cleanup failure')

    monkeypatch.setattr(generation_tasks, 'run_generation_task', generated)
    app = SimpleNamespace(state=SimpleNamespace(creation_generation_tasks={}))
    schedule_generation_task(
        SimpleNamespace(app=app),
        task_id='task-cleanup',
        user=object(),
        form=object(),
        kind='text-to-image',
        on_finished=release,
    )
    worker = app.state.creation_generation_tasks['task-cleanup']

    await worker
    await asyncio.sleep(0)

    assert attempts == 2
    assert app.state.creation_generation_tasks == {}
    assert not hasattr(generation_tasks, '_pending_callbacks')


def test_image_generation_router_has_no_user_cancel_endpoint() -> None:
    from open_webui.extensions.creations.router import router

    assert not any(route.path.endswith('/cancel') for route in router.routes)


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

    async def no_committed_creations(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(generation_tasks, '_set_task_state', set_state)
    monkeypatch.setattr(generation_tasks, '_publish_image_task_event', AsyncMock())
    monkeypatch.setattr(generation_tasks, '_completed_result_from_creations', no_committed_creations)
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
async def test_cancelled_task_restores_succeeded_when_billing_already_committed(monkeypatch) -> None:
    """复盘 P1：取消落在计费 finalize 已提交、结果未返回的窗口时，任务必须
    按 creation 捕获行恢复 succeeded，而不是误标 failed（已扣费+作品已生成，
    标 failed 会诱导用户重试并二次扣费）。"""
    from open_webui.routers import images

    states: list[tuple[str, dict | None]] = []

    async def set_state(_task_id, *, status, result=None, **_kwargs) -> None:  # type: ignore[no-untyped-def]
        states.append((status, result))

    async def cancelled_generation(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise asyncio.CancelledError

    async def committed_creations(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return [{'url': '/api/v1/files/file-1/content'}]

    monkeypatch.setattr(generation_tasks, '_set_task_state', set_state)
    monkeypatch.setattr(generation_tasks, '_publish_image_task_event', AsyncMock())
    monkeypatch.setattr(generation_tasks, '_completed_result_from_creations', committed_creations)
    monkeypatch.setattr(images, 'image_generations', cancelled_generation)

    with pytest.raises(asyncio.CancelledError):
        await generation_tasks.run_generation_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())),
            SimpleNamespace(id='user-1'),
            object(),
            'text-to-image',
        )

    assert states == [('running', None), ('succeeded', [{'url': '/api/v1/files/file-1/content'}])]


@pytest.mark.asyncio
async def test_delete_generation_task_soft_deletes_own_batch_only(creation_sessions) -> None:
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
        # 复盘：未上线无历史包袱，legacy usage 批次兼容清理已删——只按
        # task.id 批次清理；其它批次的行不受影响。
        for creation_id, batch_id in ((task.id, task.id), ('other-batch', 'other-batch')):
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
                    select(CreationMediaItem).where(CreationMediaItem.id.in_((task.id, 'other-batch')))
                )
            ).all()
        )
    soft_deleted_by_id = {item.id: item.soft_deleted for item in creations}
    assert soft_deleted_by_id == {task.id: True, 'other-batch': False}


def _make_creation(creation_id: str, *, batch_id: str, user_id: str, created_at: int) -> CreationMediaItem:
    return CreationMediaItem(
        id=creation_id,
        user_id=user_id,
        kind='image',
        file_id=f'file-{creation_id}',
        prompt='p',
        model_id='model',
        task='text-to-image',
        source='web',
        batch_id=batch_id,
        soft_deleted=False,
        created_at=created_at,
        updated_at=created_at,
    )


@pytest.mark.asyncio
async def test_completed_result_from_creations_reads_captured_rows(creation_sessions, monkeypatch) -> None:
    """关停终态核对：creation 行（batch_id=task_id）按 created_at 顺序恢复结果 URL。"""
    async with creation_sessions() as session, session.begin():
        for creation_id, created_at in (('c1', 1), ('c2', 2)):
            session.add(_make_creation(creation_id, batch_id='task-1', user_id='user-1', created_at=created_at))
        # 其它任务批次与软删行不得计入。
        session.add(_make_creation('other-task', batch_id='task-2', user_id='user-1', created_at=3))
        soft_deleted_row = _make_creation('c3', batch_id='task-1', user_id='user-1', created_at=3)
        soft_deleted_row.soft_deleted = True
        session.add(soft_deleted_row)

    monkeypatch.setattr(generation_tasks, 'creation_session', creation_sessions)
    request = SimpleNamespace(
        app=SimpleNamespace(url_path_for=lambda name, id: f'/api/v1/files/{id}/content')
    )

    result = await generation_tasks._completed_result_from_creations(request, 'task-1', 'user-1')

    assert result == [
        {'url': '/api/v1/files/file-c1/content'},
        {'url': '/api/v1/files/file-c2/content'},
    ]


@pytest.mark.asyncio
async def test_completed_result_from_creations_returns_none_without_rows(creation_sessions, monkeypatch) -> None:
    monkeypatch.setattr(generation_tasks, 'creation_session', creation_sessions)
    request = SimpleNamespace(app=SimpleNamespace(url_path_for=lambda name, id: ''))

    assert await generation_tasks._completed_result_from_creations(request, 'task-1', 'user-1') is None


@pytest.mark.asyncio
async def test_completed_result_from_creations_swallows_db_failure(monkeypatch) -> None:
    """DB 不可用时退回 None（失败路径），不能把取消异常替换成次生 DB 异常。"""

    def broken_session():
        raise RuntimeError('db unavailable')

    monkeypatch.setattr(generation_tasks, 'creation_session', broken_session)
    request = SimpleNamespace(app=SimpleNamespace(url_path_for=lambda name, id: ''))

    assert await generation_tasks._completed_result_from_creations(request, 'task-1', 'user-1') is None
