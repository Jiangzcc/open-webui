from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.provider_ops import router as provider_router
from open_webui.extensions.provider_ops.schemas import FalRuntimeConfig


@pytest.mark.asyncio
async def test_read_fal_runtime_config_maps_storage_keys(monkeypatch) -> None:
    async def fake_get_many(*keys: str) -> dict[str, object]:
        return {
            'image_generation.fal.api_base_url': 'https://queue.fal.run',
            'image_generation.fal.api_key': 'image-key',
            'image_generation.fal.mock_enabled': True,
            'video_generation.fal.api_key': '',
            'video_generation.fal.mock_enabled': False,
        }

    monkeypatch.setattr(provider_router.Config, 'get_many', fake_get_many)

    config = await provider_router._read_fal_runtime_config()

    assert config == FalRuntimeConfig(
        image_generation_api_base_url='https://queue.fal.run',
        image_generation_api_key='********',
        image_edit_api_base_url='',
        image_edit_api_key='',
        video_api_key='',
        image_mock_enabled=True,
        video_mock_enabled=False,
    )


@pytest.mark.asyncio
async def test_update_fal_runtime_config_persists_and_publishes(monkeypatch) -> None:
    persisted: dict[str, object] = {}

    async def fake_get_many(*keys: str) -> dict[str, object]:
        return dict(persisted)

    async def fake_upsert(updates: dict) -> None:
        persisted.update(updates)

    published: list[dict[str, object]] = []

    async def fake_publish_event(request: object, event: object, **kwargs: object) -> None:
        published.append({'event': event, **kwargs})

    monkeypatch.setattr(provider_router.Config, 'get_many', fake_get_many)
    monkeypatch.setattr(provider_router.Config, 'upsert', fake_upsert)
    monkeypatch.setattr(provider_router, 'publish_event', fake_publish_event)

    form = FalRuntimeConfig(
        image_generation_api_base_url='https://queue.fal.run',
        image_generation_api_key='image-key',
        image_edit_api_base_url='',
        image_edit_api_key='',
        video_api_key='video-key',
        image_mock_enabled=False,
        video_mock_enabled=True,
    )

    request = SimpleNamespace(scope={})
    result = await provider_router.update_admin_fal_runtime_config(
        request=request,
        form=form,
        user=object(),
    )

    assert persisted['image_generation.fal.api_key'] == 'image-key'
    assert persisted['image_generation.fal.mock_enabled'] is False
    assert persisted['video_generation.fal.api_key'] == 'video-key'
    assert persisted['video_generation.fal.mock_enabled'] is True
    assert result.video_api_key == '********'
    assert result.video_mock_enabled is True
    assert published and published[0]['subject_id'] == 'fal-runtime-config'
    assert request.scope['audit_redact_bodies'] == {'request'}



@pytest.mark.asyncio
async def test_update_fal_runtime_config_preserves_masked_keys(monkeypatch) -> None:
    persisted = {
        'image_generation.fal.api_key': 'existing-image-key',
        'video_generation.fal.api_key': 'existing-video-key',
    }

    async def fake_get_many(*keys: str) -> dict[str, object]:
        return dict(persisted)

    async def fake_upsert(updates: dict[str, object]) -> None:
        persisted.update(updates)

    monkeypatch.setattr(provider_router.Config, 'get_many', fake_get_many)
    monkeypatch.setattr(provider_router.Config, 'upsert', fake_upsert)
    monkeypatch.setattr(provider_router, 'publish_event', AsyncMock())

    result = await provider_router.update_admin_fal_runtime_config(
        request=SimpleNamespace(scope={}),
        form=FalRuntimeConfig(
            image_generation_api_base_url='https://queue.fal.run',
            image_generation_api_key='********',
            image_edit_api_base_url='',
            image_edit_api_key='',
            video_api_key='********',
            image_mock_enabled=True,
            video_mock_enabled=True,
        ),
        user=object(),
    )

    assert persisted['image_generation.fal.api_key'] == 'existing-image-key'
    assert persisted['video_generation.fal.api_key'] == 'existing-video-key'
    assert result.image_generation_api_key == '********'
    assert result.video_api_key == '********'


@pytest.mark.parametrize('value', ['http://queue.fal.run', 'https://user@queue.fal.run', 'https://queue.fal.run?q=1'])
def test_fal_runtime_config_rejects_unsafe_base_urls(value: str) -> None:
    with pytest.raises(ValueError):
        FalRuntimeConfig(
            image_generation_api_base_url=value,
            image_generation_api_key='',
            image_edit_api_base_url='',
            image_edit_api_key='',
            video_api_key='',
            image_mock_enabled=True,
            video_mock_enabled=True,
        )
