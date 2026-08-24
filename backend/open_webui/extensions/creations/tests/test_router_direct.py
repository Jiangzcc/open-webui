from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse
from open_webui.extensions.creations import router

USER = SimpleNamespace(id='user-1')
SESSION = object()


@pytest.mark.asyncio
async def test_generation_task_route_helpers_cover_slot_and_scheduler_outcomes(monkeypatch) -> None:
    release = AsyncMock()
    schedule = Mock()
    monkeypatch.setattr(router, 'release_image_generation_slot', release)
    monkeypatch.setattr(router, 'fail_generation_task_scheduling', AsyncMock())
    monkeypatch.setattr(router, 'schedule_generation_task', schedule)
    request = SimpleNamespace(app=object())
    task = SimpleNamespace(id='task-1')

    await router._schedule_created_image_task(
        request,
        task,
        created=False,
        user=USER,
        form=object(),
        kind='text-to-image',
    )
    release.assert_awaited_once_with(USER.id)

    release.reset_mock()
    schedule.reset_mock()
    await router._schedule_created_image_task(
        request,
        task,
        created=True,
        user=USER,
        form=object(),
        kind='text-to-image',
    )
    schedule.assert_called_once()
    await schedule.call_args.kwargs['on_finished']()
    release.assert_awaited_once_with(USER.id)

    def scheduling_failure(*_args, **_kwargs):
        raise RuntimeError

    monkeypatch.setattr(router, 'schedule_generation_task', scheduling_failure)
    with pytest.raises(RuntimeError):
        await router._schedule_created_image_task(
            request,
            task,
            created=True,
            user=USER,
            form=object(),
            kind='text-to-image',
        )
    router.fail_generation_task_scheduling.assert_awaited_once_with(request.app, task.id, USER.id)


@pytest.mark.asyncio
async def test_reserved_task_releases_slot_for_conflict_and_storage_failure(monkeypatch) -> None:
    release = AsyncMock()
    monkeypatch.setattr(router, 'release_image_generation_slot', release)

    async def conflict(*_args, **_kwargs):
        raise router.IdempotencyPayloadConflictError

    monkeypatch.setattr(router, 'create_generation_task', conflict)
    with pytest.raises(HTTPException) as captured:
        await router._create_reserved_image_task(
            SESSION,
            user_id=USER.id,
            key='key',
            kind='text-to-image',
            payload={},
        )
    assert captured.value.status_code == 409

    monkeypatch.setattr(router, 'create_generation_task', AsyncMock(side_effect=RuntimeError('db')))
    with pytest.raises(RuntimeError):
        await router._create_reserved_image_task(
            SESSION,
            user_id=USER.id,
            key='key',
            kind='text-to-image',
            payload={},
        )
    assert release.await_count == 2


@pytest.mark.asyncio
async def test_personal_media_routes_cover_success_and_not_found(monkeypatch) -> None:
    marker = object()
    monkeypatch.setattr(router, 'list_generation_tasks', AsyncMock(return_value=marker))
    assert await router.list_image_generation_tasks(user=USER, session=SESSION) is marker
    router.list_generation_tasks.side_effect = ValueError
    assert isinstance(await router.list_image_generation_tasks(user=USER, session=SESSION), JSONResponse)

    monkeypatch.setattr(router, 'get_generation_task', AsyncMock(return_value=None))
    with pytest.raises(HTTPException):
        await router.get_image_generation_task('missing', user=USER, session=SESSION)
    terminal = SimpleNamespace(status='succeeded')
    router.get_generation_task.return_value = terminal
    assert await router.get_image_generation_task('task', user=USER, session=SESSION) is terminal

    router.get_generation_task.return_value = SimpleNamespace(status='running')
    with pytest.raises(HTTPException) as active:
        await router.delete_image_generation_task('task', user=USER, session=SESSION)
    assert active.value.status_code == 409
    router.get_generation_task.return_value = terminal
    monkeypatch.setattr(router, 'delete_generation_task', AsyncMock(return_value=False))
    with pytest.raises(HTTPException):
        await router.delete_image_generation_task('task', user=USER, session=SESSION)
    router.delete_generation_task.return_value = True
    assert await router.delete_image_generation_task('task', user=USER, session=SESSION) is None

    monkeypatch.setattr(router, 'list_personal_creations', AsyncMock(return_value=marker))
    assert await router.list_media(user=USER, session=SESSION) is marker
    router.list_personal_creations.side_effect = ValueError
    assert isinstance(await router.list_media(user=USER, session=SESSION), JSONResponse)

    monkeypatch.setattr(router, 'get_personal_detail', AsyncMock(return_value=None))
    with pytest.raises(HTTPException):
        await router.get_media('missing', user=USER, session=SESSION)
    router.get_personal_detail.return_value = marker
    assert await router.get_media('id', user=USER, session=SESSION) is marker

    monkeypatch.setattr(router, 'update_caption', AsyncMock(return_value=marker))
    assert await router.update_media('id', {'caption': 'updated'}, user=USER, session=SESSION) is marker
    router.update_caption.return_value = None
    with pytest.raises(HTTPException):
        await router.update_media('id', {'caption': 'updated'}, user=USER, session=SESSION)
    assert isinstance(await router.update_media('id', {'unexpected': True}, user=USER, session=SESSION), JSONResponse)

    monkeypatch.setattr(router, 'soft_delete', AsyncMock(return_value=False))
    with pytest.raises(HTTPException):
        await router.delete_media('id', user=USER, session=SESSION)
    router.soft_delete.return_value = True
    assert await router.delete_media('id', user=USER, session=SESSION) is None

    monkeypatch.setattr(router, 'soft_delete_many', AsyncMock(return_value=('one',)))
    form = SimpleNamespace(ids=('one',))
    assert (await router.bulk_delete_media(form, user=USER, session=SESSION)).removed_ids == ('one',)


@pytest.mark.asyncio
async def test_publication_and_discovery_routes_cover_service_outcomes(monkeypatch) -> None:
    marker = object()
    monkeypatch.setattr(router, 'publish_creation', AsyncMock(return_value=marker))
    assert await router.publish_media('id', object(), user=USER, session=SESSION) is marker
    router.publish_creation.side_effect = ValueError('invalid publication')
    with pytest.raises(HTTPException) as invalid:
        await router.publish_media('id', object(), user=USER, session=SESSION)
    assert invalid.value.status_code == 422
    router.publish_creation.side_effect = None
    router.publish_creation.return_value = None
    with pytest.raises(HTTPException):
        await router.publish_media('id', object(), user=USER, session=SESSION)

    monkeypatch.setattr(router, 'withdraw_creation', AsyncMock(return_value=False))
    with pytest.raises(HTTPException):
        await router.withdraw_media('id', user=USER, session=SESSION)
    router.withdraw_creation.return_value = True
    assert await router.withdraw_media('id', user=USER, session=SESSION) is None

    for route_name, service_name in (
        ('list_discover_posts', 'list_discovery_posts'),
        ('list_discover_favorites', 'list_favorite_posts'),
    ):
        service = AsyncMock(return_value=marker)
        monkeypatch.setattr(router, service_name, service)
        assert await getattr(router, route_name)(user=USER, session=SESSION) is marker
        service.side_effect = ValueError
        assert isinstance(await getattr(router, route_name)(user=USER, session=SESSION), JSONResponse)

    monkeypatch.setattr(router, 'get_discovery_post', AsyncMock(return_value=None))
    with pytest.raises(HTTPException):
        await router.get_discover_post('post', user=USER, session=SESSION)
    router.get_discovery_post.return_value = marker
    assert await router.get_discover_post('post', user=USER, session=SESSION) is marker

    monkeypatch.setattr(router, 'set_reaction', AsyncMock(return_value=None))
    for route_call in (router.add_discover_reaction, router.remove_discover_reaction):
        with pytest.raises(HTTPException):
            await route_call('post', 'like', user=USER, session=SESSION)
        router.set_reaction.return_value = marker
        assert await route_call('post', 'like', user=USER, session=SESSION) is marker
        router.set_reaction.return_value = None


@pytest.mark.asyncio
async def test_discovery_file_routes_cover_file_and_storage_failures(monkeypatch, tmp_path: Path) -> None:
    for route_call, lookup_name in (
        (router.get_discover_post_content, 'get_published_content_file'),
        (router.get_discover_post_poster, 'get_published_poster_file'),
    ):
        lookup = AsyncMock(return_value=None)
        monkeypatch.setattr(router, lookup_name, lookup)
        with pytest.raises(HTTPException) as missing:
            await route_call('post', user=USER, session=SESSION)
        assert missing.value.status_code == 404

        media = tmp_path / f'{lookup_name}.bin'
        media.write_bytes(b'data')
        lookup.return_value = SimpleNamespace(path='storage-key', meta={'content_type': 'application/octet-stream'})
        monkeypatch.setattr(router.Storage, 'get_file', lambda _path: str(media))
        assert isinstance(await route_call('post', user=USER, session=SESSION), FileResponse)

        monkeypatch.setattr(router.Storage, 'get_file', lambda _path: str(tmp_path / 'missing'))
        with pytest.raises(HTTPException) as absent:
            await route_call('post', user=USER, session=SESSION)
        assert absent.value.status_code == 404

        monkeypatch.setattr(router.Storage, 'get_file', lambda _path: (_ for _ in ()).throw(RuntimeError('storage')))
        with pytest.raises(HTTPException) as failed:
            await route_call('post', user=USER, session=SESSION)
        assert failed.value.status_code == 400


@pytest.mark.asyncio
async def test_admin_routes_cover_success_conflict_and_not_found(monkeypatch) -> None:
    marker = object()
    monkeypatch.setattr(router, 'list_admin_creations', AsyncMock(return_value=marker))
    assert await router.list_admin_media(user=USER, session=SESSION) is marker
    router.list_admin_creations.side_effect = ValueError
    assert isinstance(await router.list_admin_media(user=USER, session=SESSION), JSONResponse)

    monkeypatch.setattr(router, 'list_discovery_categories', AsyncMock(return_value=marker))
    assert await router.list_discover_categories(session=SESSION) is marker
    assert await router.list_admin_discover_categories(session=SESSION) is marker
    monkeypatch.setattr(router, 'create_discovery_category', AsyncMock(return_value=marker))
    assert await router.create_admin_discover_category(object(), session=SESSION) is marker

    monkeypatch.setattr(router, 'update_discovery_operation', AsyncMock(return_value=marker))
    assert await router.update_admin_discovery_post('post', object(), session=SESSION) is marker
    router.update_discovery_operation.side_effect = ValueError('bad op')
    with pytest.raises(HTTPException):
        await router.update_admin_discovery_post('post', object(), session=SESSION)
    router.update_discovery_operation.side_effect = None
    router.update_discovery_operation.return_value = None
    with pytest.raises(HTTPException):
        await router.update_admin_discovery_post('post', object(), session=SESSION)

    monkeypatch.setattr(router, 'update_discovery_category', AsyncMock(return_value=marker))
    assert await router.update_admin_discover_category('featured', object(), session=SESSION) is marker
    router.update_discovery_category.side_effect = ValueError('duplicate')
    with pytest.raises(HTTPException) as duplicate:
        await router.update_admin_discover_category('featured', object(), session=SESSION)
    assert duplicate.value.status_code == 409
    router.update_discovery_category.side_effect = None
    router.update_discovery_category.return_value = None
    with pytest.raises(HTTPException):
        await router.update_admin_discover_category('featured', object(), session=SESSION)

    delete_category = AsyncMock()
    monkeypatch.setattr(router, 'delete_discovery_category', delete_category)
    for outcome, expected in (('not_found', 404), ('protected', 409), ('in_use', 409)):
        delete_category.return_value = outcome
        with pytest.raises(HTTPException) as captured:
            await router.delete_admin_discover_category('featured', session=SESSION)
        assert captured.value.status_code == expected
    delete_category.return_value = 'deleted'
    assert await router.delete_admin_discover_category('featured', session=SESSION) is None

    detail = SimpleNamespace(owner=SimpleNamespace(user_id='owner-1'))
    monkeypatch.setattr(router, 'get_admin_detail', AsyncMock(return_value=None))
    with pytest.raises(HTTPException):
        await router.get_admin_media('id', user=USER, session=SESSION)
    router.get_admin_detail.return_value = detail
    assert await router.get_admin_media('id', user=USER, session=SESSION) is detail

    monkeypatch.setattr(router, 'publish_creation', AsyncMock(return_value=marker))
    assert await router.publish_admin_media('id', object(), user=USER, session=SESSION) is marker
    router.publish_creation.side_effect = ValueError('invalid')
    with pytest.raises(HTTPException):
        await router.publish_admin_media('id', object(), user=USER, session=SESSION)
    router.publish_creation.side_effect = None
    router.publish_creation.return_value = None
    with pytest.raises(HTTPException):
        await router.publish_admin_media('id', object(), user=USER, session=SESSION)

    monkeypatch.setattr(router, 'withdraw_creation', AsyncMock(return_value=False))
    with pytest.raises(HTTPException):
        await router.withdraw_admin_media('id', user=USER, session=SESSION)
    router.withdraw_creation.return_value = True
    assert await router.withdraw_admin_media('id', user=USER, session=SESSION) is None

    monkeypatch.setattr(router, 'soft_delete', AsyncMock(return_value=False))
    with pytest.raises(HTTPException):
        await router.delete_admin_media('id', user=USER, session=SESSION)
    router.soft_delete.return_value = True
    assert await router.delete_admin_media('id', user=USER, session=SESSION) is None
