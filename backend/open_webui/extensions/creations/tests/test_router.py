from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from open_webui.extensions.creations import discovery_service, service
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.router import router as creations_router
from open_webui.extensions.creations.tests.conftest import (
    FakeFiles as _FakeFiles,
)
from open_webui.extensions.creations.tests.conftest import (
    FakeUsers as _FakeUsers,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession


def _build_app(sessions) -> FastAPI:
    app = FastAPI()
    app.include_router(creations_router)

    async def _session_override() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_creation_session] = _session_override
    return app


def _seed_item(
    sessions,
    *,
    cid: str,
    user_id: str,
    file_id: str,
    created_at: int = 100,
    soft_deleted: bool = False,
    reference_file_ids: list[str] | None = None,
):
    item = CreationMediaItem(
        id=cid,
        user_id=user_id,
        kind='image',
        file_id=file_id,
        caption=None,
        prompt='p',
        negative_prompt=None,
        model_id='z-image-turbo',
        model_name_snapshot='Z Image Turbo',
        task='text-to-image',
        params_json={'image_count': 1},
        reference_file_ids_json=list(reference_file_ids) if reference_file_ids else None,
        source='web',
        batch_id='batch-1',
        soft_deleted=soft_deleted,
        created_at=created_at,
        updated_at=created_at,
    )

    async def _go():
        async with sessions() as session, session.begin():
            session.add(item)

    import asyncio

    asyncio.run(_go())


def _file(fid, uid):
    return SimpleNamespace(id=fid, user_id=uid, created_at=100, meta={'content_type': 'image/png', 'size': 1})


def _user(uid, name='Someone', email='s@example.com', role='user'):
    return SimpleNamespace(id=uid, name=name, email=email, role=role, profile_image_url='/a.png')


@pytest.fixture
def app_and_client(creation_sessions, monkeypatch):
    app = _build_app(creation_sessions)
    monkeypatch.setattr(service, 'Files', _FakeFiles([]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([]))
    with TestClient(app) as client:
        yield app, client


@pytest.fixture
def user_override(app_and_client):
    app, _ = app_and_client

    def register(*, id, role='user', name='User', email='user@example.com'):
        user = SimpleNamespace(id=id, role=role, name=name, email=email, profile_image_url='/u.png')
        app.dependency_overrides[get_verified_user] = lambda: user
        return user

    return register


@pytest.fixture
def admin_override(app_and_client):
    app, _ = app_and_client

    def register(*, id='admin-1', name='Admin', email='admin@example.com'):
        admin = SimpleNamespace(id=id, role='admin', name=name, email=email, profile_image_url='/a.png')
        app.dependency_overrides[get_admin_user] = lambda: admin
        # an admin is also a verified user; personal routes must authenticate them
        # and then refuse cross-owner mutations at the service layer (404).
        app.dependency_overrides[get_verified_user] = lambda: admin
        return admin

    return register


def test_personal_list_never_returns_another_users_creation(
    app_and_client, user_override, creation_sessions, monkeypatch
) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='creation-user-1', user_id='user-1', file_id='fu', created_at=10)
    _seed_item(creation_sessions, cid='creation-user-2', user_id='user-2', file_id='fo', created_at=20)
    monkeypatch.setattr(service, 'Files', _FakeFiles([_file('fu', 'user-1')]))

    response = client.get('/api/v1/creations/media')
    assert response.status_code == 200
    assert [item['id'] for item in response.json()['items']] == ['creation-user-1']


def test_non_admin_cannot_upgrade_to_global_scope(app_and_client, user_override) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    assert client.get('/api/v1/creations/admin/media').status_code == 401
    assert client.post('/api/v1/creations/admin/media/c1/publish', json={}).status_code == 401
    assert client.delete('/api/v1/creations/admin/media/c1/publish').status_code == 401
    assert client.delete('/api/v1/creations/admin/media/c1').status_code == 401
    response = client.get('/api/v1/creations/media?scope=all')
    assert response.status_code == 422


def test_admin_global_list_includes_deleted_owner_and_supports_management(
    app_and_client, admin_override, creation_sessions, monkeypatch
) -> None:
    app, client = app_and_client
    admin_override(id='admin-1')
    _seed_item(creation_sessions, cid='user-creation', user_id='user-1', file_id='fu', created_at=10)
    _seed_item(creation_sessions, cid='orphaned-creation', user_id='ghost', file_id='fg', created_at=20)
    monkeypatch.setattr(service, 'Files', _FakeFiles([_file('fu', 'user-1'), _file('fg', 'ghost')]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([_user('user-1')]))
    monkeypatch.setattr(
        discovery_service,
        'Files',
        _FakeFiles([_file('fu', 'user-1'), _file('fg', 'ghost')]),
    )

    response = client.get('/api/v1/creations/admin/media')
    assert response.status_code == 200
    owners = {item['id']: item['owner'] for item in response.json()['items']}
    assert owners['orphaned-creation']['deleted'] is True
    assert owners['orphaned-creation']['user_id'] == 'ghost'

    # admin cannot mutate via personal routes (owner mismatch -> 404)
    assert client.patch('/api/v1/creations/media/user-creation', json={'caption': 'admin overwrite'}).status_code == 404
    assert client.delete('/api/v1/creations/media/user-creation').status_code == 404

    # Caption editing remains owner-only; admin management uses explicit routes.
    assert client.patch('/api/v1/creations/admin/media/user-creation', json={'caption': 'x'}).status_code == 405

    published = client.post(
        '/api/v1/creations/admin/media/user-creation/publish',
        json={'title': 'Admin selected', 'show_prompt': True},
    )
    assert published.status_code == 200
    assert published.json()['status'] == 'published'
    assert published.json()['title'] == 'Admin selected'

    withdrawn = client.delete('/api/v1/creations/admin/media/user-creation/publish')
    assert withdrawn.status_code == 204

    removed = client.delete('/api/v1/creations/admin/media/user-creation')
    assert removed.status_code == 204
    assert client.get('/api/v1/creations/admin/media/user-creation').status_code == 404


def test_same_second_cursor_has_no_duplicates(app_and_client, user_override, creation_sessions, monkeypatch) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    for i in range(5):
        _seed_item(creation_sessions, cid=f'c{i}', user_id='user-1', file_id=f'f{i}', created_at=500)
    monkeypatch.setattr(service, 'Files', _FakeFiles([]))

    first = client.get('/api/v1/creations/media?limit=2').json()
    second = client.get('/api/v1/creations/media', params={'limit': 2, 'cursor': first['next_cursor']}).json()
    ids = [item['id'] for item in first['items'] + second['items']]
    assert len(ids) == len(set(ids))


def test_malformed_cursor_returns_422(app_and_client, user_override) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    assert client.get('/api/v1/creations/media', params={'cursor': 'not-valid'}).status_code == 422


def test_limit_bounds_are_validated(app_and_client, user_override) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    assert client.get('/api/v1/creations/media?limit=0').status_code == 422
    assert client.get('/api/v1/creations/media?limit=101').status_code == 422


def test_personal_detail_returns_404_for_stranger(app_and_client, user_override, creation_sessions) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='c1', user_id='user-2', file_id='fx')
    assert client.get('/api/v1/creations/media/c1').status_code == 404


def test_patch_rejects_extra_fields(app_and_client, user_override, creation_sessions) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='c1', user_id='user-1', file_id='f1')
    response = client.patch('/api/v1/creations/media/c1', json={'caption': 'hi', 'file_id': 'steal'})
    assert response.status_code == 422


def test_patch_rejects_non_string_caption(app_and_client, user_override, creation_sessions) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='c1', user_id='user-1', file_id='f1')

    response = client.patch('/api/v1/creations/media/c1', json={'caption': 123})

    assert response.status_code == 422


def test_owner_can_update_caption_and_remove(app_and_client, user_override, creation_sessions, monkeypatch) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='c1', user_id='user-1', file_id='f1')
    monkeypatch.setattr(service, 'Files', _FakeFiles([_file('f1', 'user-1')]))

    patched = client.patch('/api/v1/creations/media/c1', json={'caption': '  note  '})
    assert patched.status_code == 200
    assert patched.json()['caption'] == 'note'

    deleted = client.delete('/api/v1/creations/media/c1')
    assert deleted.status_code == 204
    # idempotent
    assert client.delete('/api/v1/creations/media/c1').status_code == 204
    # invisible after deletion
    assert client.get('/api/v1/creations/media/c1').status_code == 404


def test_owner_can_bulk_remove_without_touching_other_users_items(
    app_and_client, user_override, creation_sessions
) -> None:
    _, client = app_and_client
    user_override(id='user-1', role='user')
    _seed_item(creation_sessions, cid='mine-1', user_id='user-1', file_id='f1')
    _seed_item(creation_sessions, cid='mine-2', user_id='user-1', file_id='f2')
    _seed_item(creation_sessions, cid='theirs', user_id='user-2', file_id='f3')

    response = client.post(
        '/api/v1/creations/media/bulk-delete',
        json={'ids': ['mine-1', 'theirs', 'mine-2']},
    )

    assert response.status_code == 200
    assert set(response.json()['removed_ids']) == {'mine-1', 'mine-2'}
    assert client.get('/api/v1/creations/media/theirs').status_code == 404


def test_admin_detail_exposes_full_payload_for_other_user(
    app_and_client, admin_override, creation_sessions, monkeypatch
) -> None:
    _, client = app_and_client
    admin_override(id='admin-1')
    _seed_item(creation_sessions, cid='c1', user_id='user-1', file_id='f1', reference_file_ids=['r1'], created_at=10)
    monkeypatch.setattr(service, 'Files', _FakeFiles([_file('f1', 'user-1'), _file('r1', 'user-1')]))
    monkeypatch.setattr(service, 'Users', _FakeUsers([_user('user-1', name='Ada')]))

    response = client.get('/api/v1/creations/admin/media/c1')
    assert response.status_code == 200
    body = response.json()
    assert body['owner']['name'] == 'Ada'
    assert body['prompt'] == 'p'
    assert [ref['position'] for ref in body['references']] == [0]
    assert 'file_id' not in body
