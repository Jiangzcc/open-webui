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
    assert all(not item.get('edit_model', '').startswith(('fal-ai/', 'google/', 'openai/', 'xai/')) for item in public)
    assert all(
        not item.get('generation_model', '').startswith(('fal-ai/', 'google/', 'openai/', 'xai/')) for item in public
    )
    assert sum(item.get('is_default') is True for item in public) == 1

    by_id = {item['id']: item for item in public}

    # z-image exposes fixed pixel buckets directly as resolutions instead of routing
    # through an aspect-ratio abstraction; neither aspect_ratios nor aspect_ratio_sizes
    # should survive into the public catalog for this model.
    z_image = by_id['z-image-turbo']
    assert z_image['is_default'] is True
    assert z_image['resolutions'] == ['1024x1024', '512x512', '1024x576', '576x1024', '1024x768', '768x1024']
    assert z_image.get('aspect_ratios') in ([], None)
    assert 'aspect_ratio_sizes' not in z_image
    assert z_image['edit_model'] == 'z-image-turbo/edit'
    assert by_id['z-image-turbo/edit']['generation_model'] == 'z-image-turbo'

    assert by_id['nano-banana-pro']['aspect_ratios']
    assert by_id['nano-banana-pro']['resolutions'] == ['1K', '2K', '4K']
    assert by_id['nano-banana']['edit_model'] == 'nano-banana/edit'
    assert by_id['nano-banana/edit']['generation_model'] == 'nano-banana'
    assert 'internal_model' not in serialized
    # provider 是仅用于展示的厂商 slug，必须通过净化而不泄露内部 fal 路由。
    assert all(
        item['provider']
        and not item['provider'].startswith(('fal-ai/', 'google/', 'openai/', 'xai/'))
        for item in public
    )


def test_public_fal_catalog_exposes_openai_quality_without_leaking_option_fields() -> None:
    from open_webui.utils.images import fal_models

    public = fal_models.public_fal_image_models('fal-ai/z-image/turbo')
    by_id = {item['id']: item for item in public}
    serialized = json.dumps(public)

    # OpenAI models declare a `quality` option internally; the public catalog lifts it
    # into flat `quality_options` + `default_quality` fields instead of leaking the
    # heterogeneous `option_fields` machinery (which also carries background /
    # input_fidelity / safety_tolerance knobs that belong to admins/providers, not users).
    openai_model = by_id['gpt-image-2']
    assert openai_model['quality_options'] == ['low', 'medium', 'high']
    assert openai_model['default_quality'] == 'low'

    # Models without a quality knob must not advertise one, and no model should leak the
    # internal option_fields envelope.
    assert 'quality_options' not in by_id['z-image-turbo']
    assert 'quality_options' not in by_id['nano-banana-pro']
    assert 'option_fields' not in serialized
    assert 'background' not in serialized
    assert 'input_fidelity' not in serialized


def test_public_fal_catalog_exposes_only_curated_advanced_image_fields() -> None:
    from open_webui.utils.images import fal_models

    public = fal_models.public_fal_image_models('fal-ai/z-image/turbo')
    by_id = {item['id']: item for item in public}

    turbo_fields = {item['field']: item for item in by_id['z-image-turbo']['advanced_fields']}
    assert turbo_fields == {
        'seed': {'field': 'seed', 'kind': 'integer'},
        'steps': {'field': 'steps', 'kind': 'integer', 'min': 1, 'max': 8},
    }

    flux_edit_fields = {
        item['field']: item for item in by_id['flux-2-klein-4b-base-edit']['advanced_fields']
    }
    assert {'seed', 'steps', 'guidance_scale', 'negative_prompt'} <= flux_edit_fields.keys()

    serialized = json.dumps(public)
    assert 'sync_mode' not in serialized
    assert 'enable_safety_checker' not in serialized
    assert 'safety_tolerance' not in serialized


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
    assert fal.get_fal_edit_model('z-image-turbo') == 'fal-ai/z-image/turbo/image-to-image'
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


def test_public_fal_image_models_include_hosting_for_alibaba():
    from open_webui.utils.images.fal_models import public_fal_image_models

    models = public_fal_image_models(default_model='fal-ai/z-image/turbo')
    by_id = {m['id']: m for m in models}
    qwen = by_id.get('qwen-image')
    assert qwen is not None
    assert qwen['hosting'] == 'serverless'
    qwen2_pro = by_id.get('qwen-image-2-pro')
    assert qwen2_pro is not None
    assert qwen2_pro['hosting'] == 'proxy'


def test_legacy_models_keep_hosting_absent_or_filled():
    from open_webui.utils.images.fal_models import public_fal_image_models

    models = public_fal_image_models(default_model='fal-ai/z-image/turbo')
    by_id = {m['id']: m for m in models}
    # z-image-turbo 是 Task1 改造后也带 hosting 的(existing 旧模型在 _alibaba_model 改造后会带 hosting)
    turbo = by_id.get('z-image-turbo')
    assert turbo is not None
    assert turbo.get('hosting') == 'serverless'


@pytest.mark.asyncio
async def test_images_models_enriches_public_fal_catalog_with_enabled_base_prices(monkeypatch) -> None:
    import open_webui.routers.images as images
    from open_webui.extensions.credits.models import CreditPrice
    from open_webui.extensions.model_ops.models import ImageModelOperation

    async def fal_config():
        return SimpleNamespace(IMAGE_GENERATION_ENGINE='fal', IMAGE_GENERATION_MODEL='fal-ai/qwen-image')

    class Scalars:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class Session:
        """Fake async session.

        get_models now issues two scalars() calls:
        1. get_enabled_prices -> CreditPrice rows
        2. apply_model_operations -> ImageModelOperation rows (no overrides seeded)
        Distinguish them by the statement's queried entity so each returns the
        right type instead of uniformly returning CreditPrice objects.
        """

        async def scalars(self, statement):
            entity = statement.column_descriptions[0]['entity'] if statement.column_descriptions else None
            if entity is ImageModelOperation:
                return Scalars([])
            return Scalars(
                [
                    CreditPrice(
                        service_type='image',
                        resource_id='fal-ai/qwen-image',
                        action='text-to-image',
                        base_price='4',
                        enabled=True,
                    )
                ]
            )

    monkeypatch.setattr(images, 'get_image_config', fal_config)

    result = await images.get_models(
        SimpleNamespace(),
        user=SimpleNamespace(role='user'),
        db=Session(),
    )

    qwen = next(model for model in result if model['id'] == 'qwen-image')
    assert qwen['base_price'] == '4'


@pytest.mark.asyncio
async def test_images_models_attaches_base_price_for_admin_internal_ids(monkeypatch) -> None:
    """管理员看到的模型列表用内部 fal 路由作 id（get_fal_image_models legacy dicts），
    而非公共 id。若 base_price 注入只能解析公共 id，admin 视图会丢失所有价格，
    呈现「积分未配置」，而同模型在普通用户视图（公共 id）反而有价 —— 这是二开
    回归点。默认 resolver 必须双向：公共→内部，内部→原样。"""
    import open_webui.routers.images as images
    from open_webui.extensions.credits.models import CreditPrice
    from open_webui.extensions.model_ops.models import ImageModelOperation

    async def fal_config():
        return SimpleNamespace(IMAGE_GENERATION_ENGINE='fal', IMAGE_GENERATION_MODEL='fal-ai/qwen-image')

    class Scalars:
        def __init__(self, rows):
            self._rows = rows

        def all(self):
            return self._rows

    class Session:
        async def scalars(self, statement):
            entity = statement.column_descriptions[0]['entity'] if statement.column_descriptions else None
            if entity is ImageModelOperation:
                return Scalars([])
            return Scalars(
                [
                    CreditPrice(
                        service_type='image',
                        resource_id='fal-ai/qwen-image',
                        action='text-to-image',
                        base_price='4',
                        enabled=True,
                    )
                ]
            )

    monkeypatch.setattr(images, 'get_image_config', fal_config)

    result = await images.get_models(
        SimpleNamespace(),
        user=SimpleNamespace(role='admin'),
        db=Session(),
    )

    # admin 列表保留内部 fal 路由作 id；base_price 必须仍能注入。
    qwen = next(model for model in result if model['id'] == 'fal-ai/qwen-image')
    assert qwen['base_price'] == '4'
