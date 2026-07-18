import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .router_test_support import AuthenticatedUser


def test_public_fal_catalog_uses_stable_public_ids_without_leaking_provider_routes() -> None:
    from open_webui.utils.images import fal_models

    public = fal_models.public_fal_image_models('fal-ai/z-image/turbo')

    assert public
    serialized = json.dumps(public)
    assert 'fal-ai/' not in serialized
    assert all(not item['id'].startswith(('fal-ai/', 'google/', 'openai/', 'xai/')) for item in public)
    assert all(
        not item.get('edit_model', '').startswith(('fal-ai/', 'google/', 'openai/', 'xai/')) for item in public
    )
    assert all(
        not item.get('generation_model', '').startswith(('fal-ai/', 'google/', 'openai/', 'xai/'))
        for item in public
    )
    assert sum(item.get('is_default') is True for item in public) == 1

    by_id = {item['id']: item for item in public}
    assert by_id['z-image-turbo']['is_default'] is True
    assert by_id['nano-banana']['edit_model'] == 'nano-banana/edit'
    assert by_id['nano-banana/edit']['generation_model'] == 'nano-banana'
    assert 'internal_model' not in serialized
    assert 'provider' not in serialized


def test_public_fal_model_mapping_is_bidirectional_and_fail_closed() -> None:
    from open_webui.utils.images import fal_models

    assert fal_models.internal_fal_image_model_id('z-image-turbo') == 'fal-ai/z-image/turbo'
    assert fal_models.internal_fal_image_model_id('nano-banana/edit') == 'fal-ai/nano-banana/edit'
    assert fal_models.internal_fal_image_model_id('unknown-model') is None
    assert fal_models.public_fal_image_model_id('fal-ai/z-image/turbo') == 'z-image-turbo'
    assert fal_models.public_fal_image_model_id('fal-ai/nano-banana/edit') == 'nano-banana/edit'
    assert fal_models.public_fal_image_model_id('fal-ai/unknown/model') is None


def test_fal_model_resolution_maps_public_ids_to_provider_ids() -> None:
    from open_webui.utils.images import fal

    assert fal.get_fal_generation_model('z-image-turbo') == 'fal-ai/z-image/turbo'
    assert fal.get_fal_generation_model('nano-banana/edit') == 'fal-ai/nano-banana'
    assert fal.get_fal_edit_model('nano-banana/edit') == 'fal-ai/nano-banana/edit'
    assert fal.get_fal_edit_model('nano-banana') == 'fal-ai/nano-banana/edit'


@pytest.mark.asyncio
async def test_prepare_generation_maps_public_fal_model_id_to_internal_resource(monkeypatch) -> None:
    from open_webui.extensions.credits import compat, image_adapter

    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(
            return_value=SimpleNamespace(
                IMAGE_GENERATION_ENGINE='fal',
                IMAGE_GENERATION_MODEL='',
                IMAGE_EDIT_ENGINE='fal',
                IMAGE_EDIT_MODEL='',
                IMAGE_SIZE='1024x1024',
                IMAGE_EDIT_SIZE='512x512',
            )
        ),
    )

    prepared = await image_adapter.prepare_generation_call(
        SimpleNamespace(headers={}),
        compat.CompatImageInput(
            model='z-image-turbo',
            prompt='safe test prompt',
            image=None,
            size=None,
            resolution=None,
            aspect_ratio=None,
            quality=None,
            image_count=1,
            extra={},
        ),
        None,
        SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user'),
    )

    assert prepared.billing.resource_id == 'fal-ai/z-image/turbo'
    assert prepared.provider_input.model == 'fal-ai/z-image/turbo'


@pytest.mark.asyncio
async def test_prepare_edit_maps_public_fal_model_id_to_internal_resource(monkeypatch) -> None:
    from open_webui.extensions.credits import compat, image_adapter

    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(
            return_value=SimpleNamespace(
                IMAGE_GENERATION_ENGINE='fal',
                IMAGE_GENERATION_MODEL='',
                IMAGE_EDIT_ENGINE='fal',
                IMAGE_EDIT_MODEL='',
                IMAGE_SIZE='1024x1024',
                IMAGE_EDIT_SIZE='512x512',
            )
        ),
    )

    prepared = await image_adapter.prepare_edit_call(
        SimpleNamespace(headers={}),
        compat.CompatImageInput(
            model='nano-banana/edit',
            prompt='safe test prompt',
            image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
            size=None,
            resolution=None,
            aspect_ratio=None,
            quality=None,
            image_count=1,
            extra={},
        ),
        None,
        SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user'),
    )

    assert prepared.billing.resource_id == 'fal-ai/nano-banana/edit'
    assert prepared.provider_input.model == 'fal-ai/nano-banana/edit'


@pytest.mark.asyncio
async def test_prepare_generation_rejects_unknown_public_fal_model_id(monkeypatch) -> None:
    from open_webui.extensions.credits import compat, image_adapter
    from open_webui.extensions.credits.errors import CreditError

    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(
            return_value=SimpleNamespace(
                IMAGE_GENERATION_ENGINE='fal',
                IMAGE_GENERATION_MODEL='',
                IMAGE_EDIT_ENGINE='fal',
                IMAGE_EDIT_MODEL='',
                IMAGE_SIZE='1024x1024',
                IMAGE_EDIT_SIZE='512x512',
            )
        ),
    )

    with pytest.raises(CreditError) as exc:
        await image_adapter.prepare_generation_call(
            SimpleNamespace(headers={}),
            compat.CompatImageInput(
                model='unknown-model',
                prompt='safe test prompt',
                image=None,
                size=None,
                resolution=None,
                aspect_ratio=None,
                quality=None,
                image_count=1,
                extra={},
            ),
            None,
            SimpleNamespace(id='user-1', name='User', email='user@example.test', role='user'),
        )

    assert exc.value.code == 'price_rule_incomplete'
    assert 'unknown-model' not in json.dumps(exc.value.to_envelope())


def test_user_ledger_serializes_public_resource_ids_and_sanitized_snapshots(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.schemas import LedgerItem

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    item = LedgerItem(
        id='ledger-1',
        user_id='user-1',
        amount=-3,
        balance_before=10,
        balance_after=7,
        entry_type='consumption',
        reason_code=None,
        note=None,
        user_name_snapshot=None,
        user_email_snapshot=None,
        operator_id=None,
        operator_name_snapshot=None,
        operator_email_snapshot=None,
        request_source='web',
        request_id='request-1',
        service_type='image',
        resource_id='fal-ai/z-image/turbo',
        action='text-to-image',
        usage_status='succeeded',
        pricing_snapshot={
            'service_type': 'image',
            'resource_id': 'fal-ai/z-image/turbo',
            'action': 'text-to-image',
            'charged_credits': 3,
        },
        metadata_snapshot={'request': 'internal'},
        created_at=1,
    )

    async def ledger(_session, user_id, _query):
        assert user_id == 'user-1'
        return type('Page', (), {'items': (item,), 'next_cursor': None})()

    monkeypatch.setattr(credits_router, 'list_user_ledger', ledger)

    response = TestClient(app).get('/api/v1/credits/me/ledger')

    assert response.status_code == 200
    body = response.json()
    assert body['items'][0]['resource_id'] == 'z-image-turbo'
    assert body['items'][0]['pricing_snapshot'] == {'charged_credits': 3}
    assert body['items'][0]['metadata_snapshot'] is None
    assert 'fal-ai/' not in json.dumps(body)


def test_user_credit_errors_do_not_echo_internal_resource_context(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def unavailable(_session, _user):
        raise CreditError(
            code='price_not_configured',
            context={'service_type': 'image', 'resource_id': 'fal-ai/z-image/turbo', 'action': 'text-to-image'},
        )

    monkeypatch.setattr(credits_router, 'get_balance', unavailable)

    response = TestClient(app).get('/api/v1/credits/me')

    assert response.status_code == 409
    assert response.json()['context'] == {}
    assert 'fal-ai/' not in json.dumps(response.json())
