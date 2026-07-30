from __future__ import annotations

import pytest
from open_webui.extensions.creations.generation_tasks import (
    create_generation_task,
    get_generation_task,
    list_generation_tasks,
)


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
