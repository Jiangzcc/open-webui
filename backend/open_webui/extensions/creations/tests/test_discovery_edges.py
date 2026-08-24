from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import discovery_service as service
from open_webui.extensions.creations.models import CreationPost, DiscoveryCategorySetting
from open_webui.extensions.creations.schemas import (
    DiscoveryCategoryUpdateForm,
    DiscoveryOperationForm,
    PublishCreationForm,
)
from sqlalchemy.exc import IntegrityError


def _post(**changes):
    values = {
        'id': 'post-1',
        'user_id': 'user-1',
        'status': 'published',
        'title': None,
        'description': None,
        'show_prompt': True,
        'category': 'other',
        'featured_at': None,
        'featured_rank': 1000,
        'like_count': 1,
        'favorite_count': 2,
        'published_at': 10,
        'created_at': 10,
        'updated_at': 10,
    }
    values.update(changes)
    return CreationPost(**values)


def test_repository_binders_cursor_and_prompt_helpers(monkeypatch) -> None:
    monkeypatch.setattr(service, 'Files', None)
    monkeypatch.setattr(service, 'Users', None)
    assert service._bind_files() is not None
    assert service._bind_users() is not None

    item = SimpleNamespace(prompt='  a   long prompt  ')
    assert service._prompt_preview(item, False) is None
    assert service._prompt_preview(item, True) == 'a long prompt'
    item.prompt = 'x' * 300
    assert service._prompt_preview(item, True).endswith('…')

    cursor = service._encode_cursor(3, 4, 'post')
    assert service._decode_cursor(cursor) == (3, 4, 'post')
    for invalid in ('not-json', service._encode_cursor(3, 4, 5)):
        with pytest.raises(ValueError, match='invalid discovery cursor'):
            service._decode_cursor(invalid)


@pytest.mark.asyncio
async def test_category_validation_and_publication_conflict_paths(monkeypatch) -> None:
    monkeypatch.setattr(service, '_category_exists', AsyncMock(return_value=False))
    with pytest.raises(ValueError, match='invalid discovery category'):
        await service._validated_category(object(), 'other', allow_hidden=False)

    conflict = IntegrityError('statement', {}, Exception('duplicate'))
    session = SimpleNamespace(
        commit=AsyncMock(side_effect=conflict),
        rollback=AsyncMock(),
    )
    post = _post()
    with pytest.raises(IntegrityError):
        await service._commit_new_publication(
            session,
            post,
            'user-1',
            'creation-1',
            created_post=False,
        )

    for winner in (None, _post(user_id='other')):
        monkeypatch.setattr(service, '_post_for_creation', AsyncMock(return_value=winner))
        with pytest.raises(IntegrityError):
            await service._commit_new_publication(
                session,
                post,
                'user-1',
                'creation-1',
                created_post=True,
            )
    winner = _post()
    monkeypatch.setattr(service, '_post_for_creation', AsyncMock(return_value=winner))
    assert await service._commit_new_publication(
        session,
        post,
        'user-1',
        'creation-1',
        created_post=True,
    ) is winner


@pytest.mark.asyncio
async def test_publish_update_and_withdraw_edge_paths(monkeypatch) -> None:
    hidden = _post(status='hidden')
    monkeypatch.setattr(
        service,
        '_owned_publishable_item',
        AsyncMock(return_value=SimpleNamespace()),
    )
    monkeypatch.setattr(service, '_post_for_creation', AsyncMock(return_value=hidden))
    assert await service.publish_creation(
        object(),
        'user-1',
        'creation-1',
        PublishCreationForm(),
    ) is None

    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(scalar_one_or_none=lambda: None)
        ),
        commit=AsyncMock(),
    )
    assert await service.withdraw_creation(session, 'user-1', 'creation-1') is False
    post = _post(status='published', featured_at=2)
    session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: post)
    assert await service.withdraw_creation(session, 'user-1', 'creation-1') is True
    assert post.status == 'withdrawn'
    assert post.featured_at is None
    session.commit.assert_awaited_once()


def test_feed_query_helpers_cover_all_sorts_and_cursors() -> None:
    stmt = service._visible_posts_stmt()
    stmt = service._apply_feed_filters(stmt, 'other', 'image')
    popularity = service.CreationPost.favorite_count * 2 + service.CreationPost.like_count
    cursor = service._encode_cursor(3, 4, 'post')
    for sort in ('featured', 'popular', 'newest'):
        assert service._apply_discovery_cursor(stmt, sort, cursor, popularity) is not None
        assert service._order_discovery_posts(stmt, sort, popularity) is not None

    rows = [(_post(id='first'),), (_post(id='second'),)]
    assert service._discovery_next_cursor(rows[:1], rows[:1], 1, 'newest') is None
    for sort in ('featured', 'popular', 'newest'):
        assert service._discovery_next_cursor(rows, rows[:1], 1, sort) is not None


@pytest.mark.asyncio
async def test_discovery_operation_and_category_mutation_edges(monkeypatch) -> None:
    session = SimpleNamespace(get=AsyncMock(return_value=None), commit=AsyncMock())
    assert await service.update_discovery_operation(
        session,
        'missing',
        DiscoveryOperationForm(featured=True),
    ) is None

    post = _post(status='withdrawn')
    session.get.return_value = post
    with pytest.raises(ValueError, match='only published'):
        await service.update_discovery_operation(
            session,
            post.id,
            DiscoveryOperationForm(featured=True),
        )
    post.status = 'published'
    with pytest.raises(ValueError, match='featured rank'):
        await service.update_discovery_operation(
            session,
            post.id,
            DiscoveryOperationForm(featured_rank=4),
        )
    result = await service.update_discovery_operation(
        session,
        post.id,
        DiscoveryOperationForm(featured=True, featured_rank=4),
    )
    assert result.featured is True
    assert result.featured_rank == 4

    session.get.return_value = None
    assert await service.update_discovery_category(
        session,
        'other',
        DiscoveryCategoryUpdateForm(enabled=True),
    ) is None
    category = DiscoveryCategorySetting(
        id='other',
        display_name='Other',
        enabled=True,
        sort_order=1,
        updated_at=1,
    )
    session.get.return_value = category
    with pytest.raises(ValueError, match='cannot be disabled'):
        await service.update_discovery_category(
            session,
            'other',
            DiscoveryCategoryUpdateForm(enabled=False),
        )


@pytest.mark.asyncio
async def test_category_deletion_and_published_file_boundaries(monkeypatch) -> None:
    session = SimpleNamespace(
        get=AsyncMock(return_value=None),
        scalar=AsyncMock(),
        delete=AsyncMock(),
        commit=AsyncMock(),
    )
    assert await service.delete_discovery_category(session, 'other') == 'not_found'
    session.get.return_value = SimpleNamespace(id='other')
    assert await service.delete_discovery_category(session, 'other') == 'protected'
    session.get.return_value = SimpleNamespace(id='custom')
    session.scalar.return_value = 1
    assert await service.delete_discovery_category(session, 'custom') == 'in_use'
    session.scalar.return_value = 0
    assert await service.delete_discovery_category(session, 'custom') == 'deleted'

    execute = AsyncMock(return_value=SimpleNamespace(first=lambda: None))
    session = SimpleNamespace(execute=execute)
    assert await service.get_published_content_file(session, 'missing') is None
    assert await service.get_published_poster_file(session, 'missing') is None

    item = SimpleNamespace(file_id='file', poster_file_id=None, user_id='owner')
    execute.return_value = SimpleNamespace(first=lambda: (_post(), item))
    monkeypatch.setattr(service, '_load_files', AsyncMock(return_value={}))
    assert await service.get_published_content_file(session, 'post') is None
    assert await service.get_published_poster_file(session, 'post') is None

    item.poster_file_id = 'poster'
    wrong_owner = SimpleNamespace(user_id='other')
    service._load_files.return_value = {'file': wrong_owner, 'poster': wrong_owner}
    assert await service.get_published_content_file(session, 'post') is None
    assert await service.get_published_poster_file(session, 'post') is None
