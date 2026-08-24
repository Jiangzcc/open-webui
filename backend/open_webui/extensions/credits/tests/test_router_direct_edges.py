from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits import router
from open_webui.extensions.credits.errors import CreditError

USER = SimpleNamespace(id='user-1')
SESSION = object()


def test_quote_input_normalization_and_validation(monkeypatch) -> None:
    normalize = Mock(return_value=7)
    monkeypatch.setattr(router, 'normalize_video_duration_dimension', normalize)
    assert router._normalize_video_quote_dimensions({'duration': '7', 'quality': 'hd'}) == {
        'duration': 7,
        'quality': 'hd',
    }

    with pytest.raises(CreditError):
        router._quote_image_input({'resource_id': 'model', 'dimensions': {}, 'prompt': None})
    with pytest.raises(CreditError):
        router._quote_image_input(
            {
                'resource_id': 'model',
                'dimensions': {'image_count': True},
                'prompt': 'prompt',
            }
        )
    image_input = router._quote_image_input(
        {
            'resource_id': 'model',
            'dimensions': {'image_count': 2, 'custom': 'value'},
            'prompt': 'prompt',
            'image': ['first', 'second'],
        }
    )
    assert image_input.image == ('first', 'second')
    assert image_input.extra == {'custom': 'value'}


@pytest.mark.asyncio
async def test_quote_image_propagates_non_configuration_credit_errors(monkeypatch) -> None:
    billing = SimpleNamespace(
        service_type='image',
        resource_id='model',
        action='text-to-image',
        dimensions={},
        request_hash='hash',
    )
    monkeypatch.setattr(router, '_prepare_quote_call', AsyncMock(return_value=SimpleNamespace(billing=billing)))
    monkeypatch.setattr(router, 'get_enabled_price', AsyncMock(return_value=SimpleNamespace(id='p', updated_at=1)))
    monkeypatch.setattr(router, 'get_balance_if_exists', AsyncMock(return_value=0))
    monkeypatch.setattr(router, '_cached_quote', AsyncMock(return_value=None))
    monkeypatch.setattr(router, 'compute_price', Mock(side_effect=CreditError(code='credit_service_unavailable')))

    with pytest.raises(CreditError) as captured:
        await router.quote_image(
            SESSION,
            USER,
            {'resource_id': 'model', 'action': 'text-to-image', 'dimensions': {}, 'prompt': 'prompt'},
        )
    assert captured.value.code == 'credit_service_unavailable'


@pytest.mark.asyncio
async def test_video_quote_rejects_catalog_mismatches_and_handles_unconfigured_price(monkeypatch) -> None:
    import open_webui.extensions.fal_catalog as catalog_module

    request = router.VideoQuoteRequest(resource_id='public', action='text-to-video')
    monkeypatch.setattr(
        catalog_module,
        'load_video_catalog_cached',
        lambda: SimpleNamespace(public_to_internal={}, definitions=[]),
    )
    with pytest.raises(CreditError):
        await router.quote_video(SESSION, USER, request)

    catalog = SimpleNamespace(public_to_internal={'public': 'internal'}, definitions=[])
    monkeypatch.setattr(catalog_module, 'load_video_catalog_cached', lambda: catalog)
    with pytest.raises(CreditError):
        await router.quote_video(SESSION, USER, request)

    catalog.definitions = [SimpleNamespace(id='internal', task='image-to-video')]
    with pytest.raises(CreditError):
        await router.quote_video(SESSION, USER, request)

    catalog.definitions = [SimpleNamespace(id='internal', task='text-to-video')]
    monkeypatch.setattr(router, 'get_balance_if_exists', AsyncMock(return_value=4))
    monkeypatch.setattr(router, 'get_enabled_price', AsyncMock(return_value=None))
    result = await router.quote_video(SESSION, USER, request)
    assert result['configured'] is False
    assert result['balance'] == 4


@pytest.mark.asyncio
async def test_public_credit_routes_map_expected_and_unexpected_failures(monkeypatch) -> None:
    monkeypatch.setattr(router, '_user_snapshot', lambda _user: USER)
    monkeypatch.setattr(router, '_enforce_rate_limit', AsyncMock())
    public_error = Mock(return_value='public-error')
    unexpected = Mock(return_value='unexpected')
    monkeypatch.setattr(router, '_public_user_error_response', public_error)
    monkeypatch.setattr(router, '_unexpected_error_response', unexpected)

    image_request = router.ImageQuoteRequest(
        resource_id='model',
        action='text-to-image',
        prompt='prompt',
    )
    monkeypatch.setattr(router, 'quote_image', AsyncMock(side_effect=CreditError(code='credit_service_unavailable')))
    assert await router.get_image_credit_quote(image_request, user=USER, session=SESSION) == 'public-error'
    monkeypatch.setattr(router, 'quote_image', AsyncMock(side_effect=RuntimeError))
    assert await router.get_image_credit_quote(image_request, user=USER, session=SESSION) == 'unexpected'

    monkeypatch.setattr(router, 'get_balance', AsyncMock(side_effect=CreditError(code='credit_service_unavailable')))
    assert await router.get_my_credits(user=USER, session=SESSION) == 'public-error'
    monkeypatch.setattr(router, 'get_balance', AsyncMock(side_effect=RuntimeError))
    assert await router.get_my_credits(user=USER, session=SESSION) == 'unexpected'


@pytest.mark.asyncio
async def test_video_ledger_and_redemption_routes_cover_failure_envelopes(monkeypatch) -> None:
    monkeypatch.setattr(router, '_user_snapshot', lambda _user: USER)
    monkeypatch.setattr(router, '_enforce_rate_limit', AsyncMock())
    monkeypatch.setattr(router, '_public_user_error_response', lambda _error: 'public-error')
    monkeypatch.setattr(router, '_unexpected_error_response', lambda _error: 'unexpected')
    request = router.VideoQuoteRequest(resource_id='model', action='text-to-video')

    monkeypatch.setattr(router, 'quote_video', AsyncMock(side_effect=CreditError(code='price_rule_incomplete')))
    monkeypatch.setattr(router, 'get_balance_if_exists', AsyncMock(return_value=3))
    result = await router.get_video_credit_quote(request, user=USER, session=SESSION)
    assert result['balance'] == 3
    monkeypatch.setattr(router, 'get_balance_if_exists', AsyncMock(side_effect=RuntimeError))
    assert await router.get_video_credit_quote(request, user=USER, session=SESSION) == 'unexpected'

    monkeypatch.setattr(router, 'quote_video', AsyncMock(side_effect=CreditError(code='credit_service_unavailable')))
    assert await router.get_video_credit_quote(request, user=USER, session=SESSION) == 'public-error'
    for error in (TypeError(), RuntimeError()):
        monkeypatch.setattr(router, 'quote_video', AsyncMock(side_effect=error))
        assert await router.get_video_credit_quote(request, user=USER, session=SESSION) == 'unexpected'

    monkeypatch.setattr(
        router,
        'list_user_ledger',
        AsyncMock(side_effect=CreditError(code='credit_service_unavailable')),
    )
    assert await router.get_my_credit_ledger(SimpleNamespace(), user=USER, session=SESSION) == 'public-error'
    monkeypatch.setattr(router, 'list_user_ledger', AsyncMock(side_effect=RuntimeError))
    assert await router.get_my_credit_ledger(SimpleNamespace(), user=USER, session=SESSION) == 'unexpected'

    request_context = SimpleNamespace()
    monkeypatch.setattr(router, '_audit_context', lambda _request: SimpleNamespace())
    monkeypatch.setattr(router, 'redeem_code', AsyncMock(side_effect=CreditError(code='credit_service_unavailable')))
    assert await router.redeem_my_credit_code(
        request_context,
        'code',
        user=USER,
        session=SESSION,
    ) == 'public-error'
    monkeypatch.setattr(router, 'redeem_code', AsyncMock(side_effect=RuntimeError))
    assert await router.redeem_my_credit_code(
        request_context,
        'code',
        user=USER,
        session=SESSION,
    ) == 'unexpected'
