from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from open_webui.extensions.creations import discovery_service
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.router import router
from open_webui.utils.auth import get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession


class FakeFiles:
    def __init__(self, files):
        self.files = {file.id: file for file in files}

    async def get_files_by_ids(self, ids):
        return [self.files[file_id] for file_id in ids if file_id in self.files]


class FakeUsers:
    async def get_users_by_ids(self, ids):
        return [SimpleNamespace(id=user_id, name='Author', profile_image_url='/avatar.png') for user_id in ids]


def _seed(sessions) -> None:
    async def go():
        async with sessions() as session:
            session.add(
                CreationMediaItem(
                    id='creation-1',
                    user_id='author-1',
                    kind='image',
                    file_id='file-1',
                    caption=None,
                    prompt='a bright forest',
                    task='text-to-image',
                    source='web',
                    batch_id='batch-1',
                    soft_deleted=False,
                    created_at=10,
                    updated_at=10,
                )
            )
            await session.commit()

    asyncio.run(go())


@pytest.fixture
def discovery_client(creation_sessions, monkeypatch):
    app = FastAPI()
    app.include_router(router)

    async def session_override() -> AsyncIterator[AsyncSession]:
        async with creation_sessions() as session:
            yield session

    app.dependency_overrides[get_creation_session] = session_override
    monkeypatch.setattr(
        discovery_service,
        'Files',
        FakeFiles(
            [
                SimpleNamespace(
                    id='file-1',
                    user_id='author-1',
                    path='unused.png',
                    filename='image.png',
                    meta={'content_type': 'image/png'},
                )
            ]
        ),
    )
    monkeypatch.setattr(discovery_service, 'Users', FakeUsers())
    with TestClient(app) as client:
        yield app, client


def _login(app: FastAPI, user_id: str) -> None:
    app.dependency_overrides[get_verified_user] = lambda: SimpleNamespace(id=user_id, role='user')


def test_publish_feed_reactions_and_withdraw(discovery_client, creation_sessions) -> None:
    app, client = discovery_client
    _seed(creation_sessions)
    _login(app, 'author-1')

    published = client.post(
        '/api/v1/creations/media/creation-1/publish',
        json={'title': 'Forest', 'show_prompt': True},
    )
    assert published.status_code == 200
    post_id = published.json()['post_id']

    _login(app, 'viewer-1')
    feed = client.get('/api/v1/creations/discover/posts?sort=latest')
    assert feed.status_code == 200
    assert feed.json()['items'][0]['id'] == post_id
    assert 'email' not in feed.json()['items'][0]['owner']

    liked = client.put(f'/api/v1/creations/discover/posts/{post_id}/reactions/like')
    favorite = client.put(f'/api/v1/creations/discover/posts/{post_id}/reactions/favorite')
    assert liked.json()['like_count'] == 1
    assert favorite.json()['favorite_count'] == 1
    assert client.get('/api/v1/creations/discover/favorites').json()['items'][0]['favorited'] is True

    _login(app, 'author-1')
    assert client.delete('/api/v1/creations/media/creation-1/publish').status_code == 204
    _login(app, 'viewer-1')
    assert client.get('/api/v1/creations/discover/posts').json()['items'] == []


def test_stranger_cannot_publish_or_withdraw(discovery_client, creation_sessions) -> None:
    app, client = discovery_client
    _seed(creation_sessions)
    _login(app, 'viewer-1')

    assert client.post('/api/v1/creations/media/creation-1/publish', json={}).status_code == 404
    assert client.delete('/api/v1/creations/media/creation-1/publish').status_code == 404


def test_discovery_rejects_invalid_sort_and_reaction_kind(discovery_client) -> None:
    app, client = discovery_client
    _login(app, 'viewer-1')

    assert client.get('/api/v1/creations/discover/posts?sort=random').status_code == 422
    assert client.put('/api/v1/creations/discover/posts/nope/reactions/clap').status_code == 422
