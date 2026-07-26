from __future__ import annotations

import pytest
from open_webui.extensions.creations.models import (
    CreationMediaItem,
    CreationPost,
    CreationPostMedia,
    CreationPostReaction,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


async def _seed_creation(session, *, creation_id: str = 'creation-1', user_id: str = 'user-1') -> None:
    session.add(
        CreationMediaItem(
            id=creation_id,
            user_id=user_id,
            kind='image',
            file_id=f'file-{creation_id}',
            prompt='a quiet lake',
            task='text-to-image',
            source='web',
            batch_id='batch-1',
            soft_deleted=False,
            created_at=10,
            updated_at=10,
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_post_media_and_reaction_uniqueness(creation_sessions) -> None:
    async with creation_sessions() as session:
        await _seed_creation(session)
        session.add(
            CreationPost(
                id='post-1',
                user_id='user-1',
                status='published',
                show_prompt=True,
                like_count=0,
                favorite_count=0,
                published_at=20,
                created_at=20,
                updated_at=20,
            )
        )
        session.add(CreationPostMedia(post_id='post-1', creation_id='creation-1', position=0, created_at=20))
        session.add(CreationPostReaction(post_id='post-1', user_id='viewer-1', kind='like', created_at=21))
        await session.commit()

        session.add(CreationPostReaction(post_id='post-1', user_id='viewer-1', kind='like', created_at=22))
        with pytest.raises(IntegrityError):
            await session.commit()

    async with creation_sessions() as session:
        posts = (await session.execute(select(CreationPost))).scalars().all()
        assert [post.id for post in posts] == ['post-1']


@pytest.mark.asyncio
async def test_one_creation_cannot_back_multiple_posts(creation_sessions) -> None:
    async with creation_sessions() as session:
        await _seed_creation(session)
        for post_id in ('post-1', 'post-2'):
            session.add(
                CreationPost(
                    id=post_id,
                    user_id='user-1',
                    status='published',
                    show_prompt=True,
                    like_count=0,
                    favorite_count=0,
                    published_at=20,
                    created_at=20,
                    updated_at=20,
                )
            )
        session.add_all(
            [
                CreationPostMedia(post_id='post-1', creation_id='creation-1', position=0, created_at=20),
                CreationPostMedia(post_id='post-2', creation_id='creation-1', position=0, created_at=20),
            ]
        )
        with pytest.raises(IntegrityError):
            await session.commit()
