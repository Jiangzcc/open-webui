from __future__ import annotations

import pytest
from open_webui.extensions.creations.generation_tasks import (
    create_generation_task,
    get_generation_task,
    list_generation_tasks,
)
from open_webui.extensions.creations.schemas import decode_keyset_cursor


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
