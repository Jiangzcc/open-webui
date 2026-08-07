from __future__ import annotations

import pytest
from open_webui.extensions.creations import discovery_service
from open_webui.extensions.creations.models import (
    CreationMediaItem,
    CreationPost,
    DiscoveryCategorySetting,
)
from open_webui.extensions.creations.schemas import (
    DiscoveryCategoryCreateForm,
    DiscoveryCategoryUpdateForm,
    DiscoveryOperationForm,
    PublishCreationForm,
)
from open_webui.extensions.creations.tests.conftest import make_file, make_user


async def _seed_creation(
    sessions,
    *,
    creation_id: str = 'creation-1',
    user_id: str = 'author-1',
    file_id: str = 'file-1',
    created_at: int = 10,
    kind: str = 'image',
) -> None:
    async with sessions() as session:
        session.add(
            CreationMediaItem(
                id=creation_id,
                user_id=user_id,
                kind=kind,
                file_id=file_id,
                duration_seconds=5 if kind == 'video' else None,
                caption='A caption',
                prompt='a cinematic quiet lake at dusk',
                negative_prompt='noise',
                model_id='public/model',
                model_name_snapshot='Public Model',
                task='text-to-video' if kind == 'video' else 'text-to-image',
                params_json={'size': '1024x1024'},
                source='web',
                batch_id='batch-1',
                soft_deleted=False,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        await session.commit()


def _bind_repositories(monkeypatch, *, files, users) -> None:
    class FakeFiles:
        async def get_files_by_ids(self, ids):
            return [file for file in files if file.id in ids]

    class FakeUsers:
        async def get_users_by_ids(self, ids):
            return [user for user in users if user.id in ids]

    monkeypatch.setattr(discovery_service, 'Files', FakeFiles())
    monkeypatch.setattr(discovery_service, 'Users', FakeUsers())


@pytest.mark.asyncio
async def test_category_settings_are_ordered_filtered_and_updatable(creation_sessions) -> None:
    async with creation_sessions() as session:
        other = await session.get(DiscoveryCategorySetting, 'other')
        assert other is not None
        other.enabled = False
        await session.commit()

        public_items = await discovery_service.list_discovery_categories(session)
        admin_items = await discovery_service.list_discovery_categories(session, include_disabled=True)
        updated = await discovery_service.update_discovery_category(
            session,
            'other',
            DiscoveryCategoryUpdateForm(display_name='综合', enabled=True, sort_order=5),
        )
        with pytest.raises(ValueError, match='default category cannot be disabled'):
            await discovery_service.update_discovery_category(
                session,
                'other',
                DiscoveryCategoryUpdateForm(enabled=False),
            )
        created = await discovery_service.create_discovery_category(
            session,
            DiscoveryCategoryCreateForm(display_name='摄影', enabled=True, sort_order=15),
        )
        deleted = await discovery_service.delete_discovery_category(session, created.id)
        protected = await discovery_service.delete_discovery_category(session, 'other')

        session.add(
            CreationPost(
                id='post-portrait',
                user_id='author-1',
                status='published',
                title=None,
                description=None,
                show_prompt=True,
                category='portrait',
                featured_at=None,
                featured_rank=1000,
                like_count=0,
                favorite_count=0,
                published_at=1,
                created_at=1,
                updated_at=1,
            )
        )
        await session.commit()
        in_use = await discovery_service.delete_discovery_category(session, 'portrait')
        with pytest.raises(ValueError, match='invalid discovery category'):
            await discovery_service.update_discovery_operation(
                session,
                'post-portrait',
                DiscoveryOperationForm(category='missing-category'),
            )

    assert public_items[0].id == 'portrait'
    assert all(item.id != 'other' for item in public_items)
    assert admin_items[-1].id == 'other'
    assert updated is not None
    assert (updated.display_name, updated.enabled, updated.sort_order) == ('综合', True, 5)
    assert created.id.startswith('category_')
    assert deleted == 'deleted'
    assert protected == 'protected'
    assert in_use == 'in_use'


@pytest.mark.asyncio
async def test_owner_can_publish_and_republish_same_creation(creation_sessions, monkeypatch) -> None:
    await _seed_creation(creation_sessions)
    _bind_repositories(
        monkeypatch,
        files=[make_file('file-1', 'author-1')],
        users=[make_user('author-1', name='Author')],
    )

    async with creation_sessions() as session:
        first = await discovery_service.publish_creation(
            session,
            'author-1',
            'creation-1',
            PublishCreationForm(title='First title', show_prompt=False, category='portrait'),
        )
        second = await discovery_service.publish_creation(
            session,
            'author-1',
            'creation-1',
            PublishCreationForm(title='Updated title', show_prompt=True),
        )

    assert first is not None
    assert second is not None
    assert second.post_id == first.post_id
    assert second.title == 'Updated title'
    assert second.status == 'published'
    assert first.category == 'portrait'
    assert second.category == 'portrait'


@pytest.mark.asyncio
async def test_stranger_cannot_publish_creation(creation_sessions) -> None:
    await _seed_creation(creation_sessions)
    async with creation_sessions() as session:
        result = await discovery_service.publish_creation(
            session,
            'stranger',
            'creation-1',
            PublishCreationForm(),
        )
    assert result is None


@pytest.mark.asyncio
async def test_feed_hides_withdrawn_posts_and_prompt_when_disabled(creation_sessions, monkeypatch) -> None:
    await _seed_creation(creation_sessions, creation_id='c1', file_id='f1', created_at=20)
    await _seed_creation(creation_sessions, creation_id='c2', file_id='f2', created_at=10)
    _bind_repositories(
        monkeypatch,
        files=[make_file('f1', 'author-1'), make_file('f2', 'author-1')],
        users=[make_user('author-1', name='Author')],
    )
    async with creation_sessions() as session:
        first = await discovery_service.publish_creation(
            session, 'author-1', 'c1', PublishCreationForm(show_prompt=False)
        )
        second = await discovery_service.publish_creation(session, 'author-1', 'c2', PublishCreationForm())
        assert first and second
        await discovery_service.withdraw_creation(session, 'author-1', 'c2')
        feed = await discovery_service.list_discovery_posts(session, 'viewer-1', 20, None, 'latest')
        detail = await discovery_service.get_discovery_post(session, 'viewer-1', first.post_id)

    assert [item.id for item in feed.items] == [first.post_id]
    assert feed.items[0].prompt_preview is None
    assert detail is not None
    assert detail.model_id == 'public/model'
    assert detail.prompt is None
    assert detail.negative_prompt is None
    assert detail.params == {'size': '1024x1024'}


@pytest.mark.asyncio
async def test_discovery_feed_filters_image_and_video(creation_sessions, monkeypatch) -> None:
    await _seed_creation(creation_sessions, creation_id='image', file_id='fi', created_at=10)
    await _seed_creation(
        creation_sessions,
        creation_id='video',
        file_id='fv',
        created_at=20,
        kind='video',
    )
    _bind_repositories(
        monkeypatch,
        files=[make_file('fi', 'author-1'), make_file('fv', 'author-1', 'video/mp4')],
        users=[make_user('author-1')],
    )
    async with creation_sessions() as session:
        image_post = await discovery_service.publish_creation(session, 'author-1', 'image', PublishCreationForm())
        video_post = await discovery_service.publish_creation(session, 'author-1', 'video', PublishCreationForm())
        image_feed = await discovery_service.list_discovery_posts(
            session, 'viewer', 20, None, 'latest', media_kind='image'
        )
        video_feed = await discovery_service.list_discovery_posts(
            session, 'viewer', 20, None, 'latest', media_kind='video'
        )

    assert image_post and video_post
    assert [item.id for item in image_feed.items] == [image_post.post_id]
    assert [item.id for item in video_feed.items] == [video_post.post_id]


@pytest.mark.asyncio
async def test_reactions_are_idempotent_and_favorites_feed_is_scoped(creation_sessions, monkeypatch) -> None:
    await _seed_creation(creation_sessions)
    _bind_repositories(
        monkeypatch,
        files=[make_file('file-1', 'author-1')],
        users=[make_user('author-1', name='Author')],
    )
    async with creation_sessions() as session:
        publication = await discovery_service.publish_creation(session, 'author-1', 'creation-1', PublishCreationForm())
        assert publication
        first = await discovery_service.set_reaction(session, 'viewer-1', publication.post_id, 'like', True)
        repeated = await discovery_service.set_reaction(session, 'viewer-1', publication.post_id, 'like', True)
        favorite = await discovery_service.set_reaction(session, 'viewer-1', publication.post_id, 'favorite', True)
        other_favorites = await discovery_service.list_favorite_posts(session, 'other-viewer', 20, None)
        own_favorites = await discovery_service.list_favorite_posts(session, 'viewer-1', 20, None)
        removed = await discovery_service.set_reaction(session, 'viewer-1', publication.post_id, 'like', False)

    assert first and repeated and favorite and removed
    assert first.like_count == repeated.like_count == 1
    assert favorite.favorite_count == 1
    assert other_favorites.items == ()
    assert [item.id for item in own_favorites.items] == [publication.post_id]
    assert removed.active is False
    assert removed.like_count == 0


@pytest.mark.asyncio
async def test_soft_deleted_creation_cannot_receive_new_reactions(creation_sessions, monkeypatch) -> None:
    await _seed_creation(creation_sessions)
    _bind_repositories(
        monkeypatch,
        files=[make_file('file-1', 'author-1')],
        users=[make_user('author-1', name='Author')],
    )
    async with creation_sessions() as session:
        publication = await discovery_service.publish_creation(session, 'author-1', 'creation-1', PublishCreationForm())
        assert publication
        item = await session.get(CreationMediaItem, 'creation-1')
        assert item
        item.soft_deleted = True
        await session.commit()
        reaction = await discovery_service.set_reaction(session, 'viewer-1', publication.post_id, 'like', True)

    assert reaction is None
