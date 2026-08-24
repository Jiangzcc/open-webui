from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.provider_ops import router

SESSION = object()


@pytest.mark.asyncio
async def test_provider_ops_read_routes_delegate_with_bounded_windows(monkeypatch) -> None:
    marker = object()
    monkeypatch.setattr(router, 'time', lambda: 1000.0)
    cases = (
        ('get_admin_provider_invocations', 'list_provider_invocations', {}),
        ('get_admin_provider_model_summary', 'summarize_provider_models', {}),
        ('get_admin_provider_overview', 'get_provider_overview', {}),
        ('get_admin_provider_prices', 'list_provider_prices', {}),
        ('get_admin_provider_billing_events', 'list_provider_billing_events', {}),
        ('get_admin_provider_requests', 'list_provider_requests', {}),
        ('get_admin_provider_usage', 'list_provider_usage', {}),
        ('get_admin_provider_analytics', 'list_provider_analytics', {}),
    )
    for route_name, service_name, kwargs in cases:
        service = AsyncMock(return_value=marker)
        monkeypatch.setattr(router, service_name, service)
        assert await getattr(router, route_name)(session=SESSION, **kwargs) is marker
        service.assert_awaited_once()

    sync = AsyncMock(return_value=marker)
    monkeypatch.setattr(router, 'sync_fal_platform', sync)
    assert await router.post_admin_fal_platform_sync(object(), session=SESSION) is marker


@pytest.mark.asyncio
async def test_fal_runtime_config_masks_existing_keys_and_updates_only_new_values(monkeypatch) -> None:
    values = {
        'image_generation.fal.api_key': 'secret',
        'video_generation.fal.mock_enabled': True,
    }
    monkeypatch.setattr(router.Config, 'get_many', AsyncMock(return_value=values))
    config = await router._read_fal_runtime_config()
    assert config.image_generation_api_key == router._MASKED_FAL_API_KEY
    assert config.video_mock_enabled is True

    upsert = AsyncMock()
    publish = AsyncMock()
    monkeypatch.setattr(router.Config, 'upsert', upsert)
    monkeypatch.setattr(router, 'publish_event', publish)
    request = SimpleNamespace(scope={})
    user = SimpleNamespace(id='admin')
    await router.update_admin_fal_runtime_config(request, config, user=user)
    assert request.scope['audit_redact_bodies'] == {'request'}
    assert 'image_generation.fal.api_key' not in upsert.await_args.args[0]
    publish.assert_awaited_once()
