from __future__ import annotations

import pytest
from open_webui.extensions.creations import service
from open_webui.extensions.creations.models import CreationMediaItem, CreationPost, CreationPostMedia
from open_webui.extensions.creations.service import (
    get_admin_detail,
    get_personal_detail,
    list_admin_creations,
    list_personal_creations,
    soft_delete,
    soft_delete_many,
    update_caption,
)
from open_webui.extensions.creations.tests.conftest import make_file, make_user


class _FakeFiles:
    def __init__(self, files):
        self._files = {f.id: f for f in files}

    async def get_files_by_ids(self, ids):
        return [self._files[i] for i in ids if i in self._files]


class _FakeUsers:
    def __init__(self, users):
        self._users = {u.id: u for u in users}

    async def get_users_by_ids(self, ids):
        return [self._users[i] for i in ids if i in self._users]


class _CountingUsers(_FakeUsers):
    def __init__(self, users):
        super().__init__(users)
        self.calls = 0

    async def get_users_by_ids(self, ids):
        self.calls += 1
        return await super().get_users_by_ids(ids)


def _item(
    *,
    cid: str = 'c1',
    user_id: str = 'user-1',
    file_id: str = 'file-1',
    task: str = 'text-to-image',
    source: str = 'web',
    batch_id: str = 'batch-1',
    created_at: int = 100,
    caption: str | None = None,
    soft_deleted: bool = False,
    reference_file_ids: list[str] | None = None,
    model_id: str | None = 'z-image-turbo',
    model_name_snapshot: str | None = 'Z Image Turbo',
    prompt: str = 'a calm river',
    kind: str = 'image',
) -> CreationMediaItem:
    return CreationMediaItem(
        id=cid,
        user_id=user_id,
        kind=kind,
        file_id=file_id,
        duration_seconds=5 if kind == 'video' else None,
        caption=caption,
        prompt=prompt,
        negative_prompt=None,
        model_id=model_id,
        model_name_snapshot=model_name_snapshot,
        task=task,
        params_json={'image_count': 1},
        reference_file_ids_json=list(reference_file_ids) if reference_file_ids else None,
        source=source,
        batch_id=batch_id,
        soft_deleted=soft_deleted,
        created_at=created_at,
        updated_at=created_at,
    )


async def _seed(sessions, items):
    async with sessions() as session, session.begin():
        for item in items:
            session.add(item)


async def _seed_publication(sessions, *, creation_id: str, user_id: str, status: str = 'published'):
    async with sessions() as session, session.begin():
        session.add(
            CreationPost(
                id=f'post-{creation_id}',
                user_id=user_id,
                status=status,
                title=None,
                description=None,
                show_prompt=True,
                like_count=0,
                favorite_count=0,
                published_at=200,
                created_at=200,
                updated_at=200,
            )
        )
        session.add(
            CreationPostMedia(
                post_id=f'post-{creation_id}',
                position=0,
                creation_id=creation_id,
                created_at=200,
            )
        )


@pytest.mark.asyncio
async def test_personal_list_returns_only_own_visible_creations(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions,
        [
            _item(cid='mine-1', user_id='user-1', file_id='f1', created_at=10),
            _item(cid='mine-2', user_id='user-1', file_id='f2', created_at=20),
            _item(cid='theirs', user_id='user-2', file_id='f3', created_at=30),
            _item(cid='hidden', user_id='user-1', file_id='f4', created_at=40, soft_deleted=True),
        ],
    )
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('f1', 'user-1'), make_file('f2', 'user-1')]))

    async with creation_sessions() as session:
        response = await list_personal_creations(session, 'user-1', 20, None)

    assert [item.id for item in response.items] == ['mine-2', 'mine-1']
    assert response.next_cursor is None
    assert all(item.availability == 'available' for item in response.items)


@pytest.mark.asyncio
async def test_personal_and_admin_lists_filter_media_kind(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions,
        [
            _item(cid='image', file_id='fi', created_at=10),
            _item(
                cid='video',
                file_id='fv',
                created_at=20,
                kind='video',
                task='text-to-video',
            ),
        ],
    )
    monkeypatch.setattr(
        service,
        'Files',
        _FakeFiles([make_file('fi', 'user-1'), make_file('fv', 'user-1', 'video/mp4')]),
    )
    monkeypatch.setattr(service, 'Users', _FakeUsers([make_user('user-1')]))

    async with creation_sessions() as session:
        personal = await list_personal_creations(session, 'user-1', 20, None, kind='video')
        admin = await list_admin_creations(session, 20, None, kind='video')

    assert [item.id for item in personal.items] == ['video']
    assert [item.id for item in admin.items] == ['video']


@pytest.mark.asyncio
async def test_pagination_uses_compound_cursor_without_duplicates(creation_sessions, monkeypatch) -> None:
    same_second = 500
    items = [_item(cid=f'c{i}', user_id='user-1', file_id=f'f{i}', created_at=same_second) for i in range(5)]
    await _seed(creation_sessions, items)
    monkeypatch.setattr(service, 'Files', _FakeFiles([]))

    async with creation_sessions() as session:
        first = await list_personal_creations(session, 'user-1', 2, None)
        second = await list_personal_creations(session, 'user-1', 2, first.next_cursor)

    ids = [item.id for item in first.items] + [item.id for item in second.items]
    assert len(ids) == len(set(ids))
    assert first.next_cursor is not None
    assert second.next_cursor is not None


@pytest.mark.asyncio
async def test_personal_list_rejects_invalid_cursor(creation_sessions) -> None:
    async with creation_sessions() as session:
        with pytest.raises(ValueError):
            await list_personal_creations(session, 'user-1', 20, 'not-a-real-cursor')


@pytest.mark.asyncio
async def test_personal_list_filters_search_task_publication_and_oldest_sort(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions,
        [
            _item(
                cid='published-edit',
                user_id='user-1',
                file_id='f1',
                task='image-to-image',
                prompt='misty mountain',
                created_at=30,
            ),
            _item(
                cid='draft-edit',
                user_id='user-1',
                file_id='f2',
                task='image-to-image',
                caption='Misty draft',
                created_at=10,
            ),
            _item(
                cid='published-text',
                user_id='user-1',
                file_id='f3',
                task='text-to-image',
                prompt='misty valley',
                created_at=20,
            ),
        ],
    )
    await _seed_publication(creation_sessions, creation_id='published-edit', user_id='user-1')
    await _seed_publication(creation_sessions, creation_id='published-text', user_id='user-1')
    monkeypatch.setattr(service, 'Files', _FakeFiles([]))

    async with creation_sessions() as session:
        published = await list_personal_creations(
            session,
            'user-1',
            20,
            None,
            search='MISTY',
            task='image-to-image',
            publication_status='published',
        )
        unpublished = await list_personal_creations(
            session,
            'user-1',
            20,
            None,
            task='image-to-image',
            publication_status='unpublished',
            sort='oldest',
        )

    assert [item.id for item in published.items] == ['published-edit']
    assert published.items[0].publication_status == 'published'
    assert [item.id for item in unpublished.items] == ['draft-edit']
    assert unpublished.items[0].publication_status is None


@pytest.mark.asyncio
async def test_admin_list_batches_owner_lookup_once_and_shows_deleted_owner(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions,
        [
            _item(cid='alive', user_id='user-1', file_id='fa', created_at=10),
            _item(cid='orphaned', user_id='ghost', file_id='fg', created_at=20),
        ],
    )
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('fa', 'user-1'), make_file('fg', 'ghost')]))
    counting = _CountingUsers([make_user('user-1')])
    monkeypatch.setattr(service, 'Users', counting)

    async with creation_sessions() as session:
        response = await list_admin_creations(session, 20, None)

    owners = {item.id: item.owner for item in response.items}
    assert owners['orphaned'].deleted is True
    assert owners['orphaned'].user_id == 'ghost'
    assert owners['alive'].deleted is False
    assert owners['alive'].name == 'Some User'
    assert counting.calls == 1


@pytest.mark.asyncio
async def test_admin_list_excludes_soft_deleted(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions,
        [
            _item(cid='kept', user_id='user-1', file_id='fk', created_at=10),
            _item(cid='gone', user_id='user-1', file_id='fd', created_at=20, soft_deleted=True),
        ],
    )
    monkeypatch.setattr(service, 'Files', _FakeFiles([]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([make_user('user-1')]))

    async with creation_sessions() as session:
        response = await list_admin_creations(session, 20, None)

    assert [item.id for item in response.items] == ['kept']


@pytest.mark.asyncio
async def test_personal_detail_projects_ordered_references_and_missing_placeholders(
    creation_sessions, monkeypatch
) -> None:
    await _seed(
        creation_sessions,
        [
            _item(
                cid='c1', user_id='user-1', file_id='f-res', reference_file_ids=['r1', 'rMissing', 'r3'], created_at=10
            )
        ],
    )
    monkeypatch.setattr(
        service,
        'Files',
        _FakeFiles([make_file('f-res', 'user-1'), make_file('r1', 'user-1'), make_file('r3', 'user-1')]),
    )

    async with creation_sessions() as session:
        detail = await get_personal_detail(session, 'user-1', 'c1')

    assert detail is not None
    assert [ref.position for ref in detail.references] == [0, 1, 2]
    availabilities = [ref.availability for ref in detail.references]
    assert availabilities == ['available', 'missing', 'available']
    assert detail.references[1].content_url is None
    assert detail.references[1].mime_type is None
    assert detail.prompt == 'a calm river'
    assert detail.source == 'web'
    assert detail.batch_id == 'batch-1'


@pytest.mark.asyncio
async def test_personal_detail_returns_none_for_other_users_creation(creation_sessions) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-2', file_id='fx')])
    async with creation_sessions() as session:
        assert await get_personal_detail(session, 'user-1', 'c1') is None


@pytest.mark.asyncio
async def test_update_caption_normalizes_and_refreshes_timestamp(creation_sessions, monkeypatch) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-1', file_id='f1', created_at=10)])
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('f1', 'user-1')]))

    async with creation_sessions() as session:
        detail = await update_caption(session, 'user-1', 'c1', '   hello world   ')

    assert detail is not None
    assert detail.caption == 'hello world'

    async with creation_sessions() as session:
        blank = await update_caption(session, 'user-1', 'c1', '   ')
    assert blank is not None
    assert blank.caption is None


@pytest.mark.asyncio
async def test_update_caption_returns_none_for_stranger(creation_sessions) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-2', file_id='fx')])
    async with creation_sessions() as session:
        assert await update_caption(session, 'user-1', 'c1', 'x') is None


@pytest.mark.asyncio
async def test_soft_delete_is_idempotent_for_owner(creation_sessions) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-1', file_id='f1')])
    async with creation_sessions() as session:
        assert await soft_delete(session, 'user-1', 'c1') is True
    async with creation_sessions() as session:
        assert await soft_delete(session, 'user-1', 'c1') is True


@pytest.mark.asyncio
async def test_soft_delete_returns_false_for_stranger(creation_sessions) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-2', file_id='fx')])
    async with creation_sessions() as session:
        assert await soft_delete(session, 'user-1', 'c1') is False


@pytest.mark.asyncio
async def test_soft_delete_many_only_removes_owned_visible_items_and_withdraws_publication(
    creation_sessions,
) -> None:
    await _seed(
        creation_sessions,
        [
            _item(cid='owned', user_id='user-1', file_id='f1'),
            _item(cid='already-gone', user_id='user-1', file_id='f2', soft_deleted=True),
            _item(cid='stranger', user_id='user-2', file_id='f3'),
        ],
    )
    await _seed_publication(creation_sessions, creation_id='owned', user_id='user-1')

    async with creation_sessions() as session:
        removed = await soft_delete_many(session, 'user-1', ('owned', 'already-gone', 'stranger', 'missing'))

    assert removed == ('owned',)
    async with creation_sessions() as session:
        owned = await session.get(CreationMediaItem, 'owned')
        post = await session.get(CreationPost, 'post-owned')
    assert owned.soft_deleted is True
    assert post.status == 'withdrawn'


@pytest.mark.asyncio
async def test_admin_detail_includes_owner(creation_sessions, monkeypatch) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-7', file_id='f1', created_at=10)])
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('f1', 'user-7')]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([make_user('user-7', name='Ada')]))

    async with creation_sessions() as session:
        detail = await get_admin_detail(session, 'c1')

    assert detail is not None
    assert detail.owner.name == 'Ada'
    assert detail.owner.deleted is False


@pytest.mark.asyncio
async def test_list_summary_excludes_sensitive_fields(creation_sessions, monkeypatch) -> None:
    await _seed(creation_sessions, [_item(cid='c1', user_id='user-1', file_id='f1', reference_file_ids=['r1'])])
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('f1', 'user-1')]))

    async with creation_sessions() as session:
        response = await list_personal_creations(session, 'user-1', 20, None)

    dumped = response.items[0].model_dump()
    forbidden = {'prompt', 'negative_prompt', 'params', 'references', 'batch_id', 'file_id', 'model_id', 'source'}
    assert forbidden.isdisjoint(dumped.keys())


@pytest.mark.asyncio
async def test_list_summary_surfaces_a_clipped_prompt_preview(creation_sessions, monkeypatch) -> None:
    long_prompt = 'loves quiet rivers ' * 40  # well over the 200-char clip ceiling
    await _seed(
        creation_sessions,
        [
            _item(cid='plain', user_id='user-1', file_id='fp', prompt='a calm river', created_at=30),
            _item(cid='long', user_id='user-1', file_id='fl', prompt=long_prompt, created_at=20),
            _item(cid='blankish', user_id='user-1', file_id='fb', prompt='\n  a   stormy\nsea  ', created_at=10),
        ],
    )
    monkeypatch.setattr(
        service, 'Files', _FakeFiles([make_file('fp', 'user-1'), make_file('fl', 'user-1'), make_file('fb', 'user-1')])
    )

    async with creation_sessions() as session:
        response = await list_personal_creations(session, 'user-1', 20, None)

    by_id = {item.id: item for item in response.items}
    # Short prompt passes through verbatim.
    assert by_id['plain'].prompt_preview == 'a calm river'
    # Long prompt is clipped to the ceiling and terminated with an ellipsis.
    assert len(by_id['long'].prompt_preview) == 200
    assert by_id['long'].prompt_preview.endswith('…')
    # Newlines/runs collapse to single spaces so the card overlay stays tidy.
    assert by_id['blankish'].prompt_preview == 'a stormy sea'


@pytest.mark.asyncio
async def test_admin_list_summary_also_carries_prompt_preview(creation_sessions, monkeypatch) -> None:
    await _seed(
        creation_sessions, [_item(cid='c1', user_id='user-1', file_id='f1', prompt='misty mountains', created_at=10)]
    )
    monkeypatch.setattr(service, 'Files', _FakeFiles([make_file('f1', 'user-1')]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([make_user('user-1')]))

    async with creation_sessions() as session:
        response = await list_admin_creations(session, 20, None)

    assert response.items[0].prompt_preview == 'misty mountains'
