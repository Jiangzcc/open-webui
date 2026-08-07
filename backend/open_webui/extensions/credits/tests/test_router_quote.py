import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from .router_test_support import AuthenticatedUser


def _stub_openai_image_config(monkeypatch, credits_router) -> None:
    monkeypatch.setattr(
        credits_router.prepare_generation_call.__globals__['compat'],
        'get_runtime_image_config',
        AsyncMock(
            return_value=SimpleNamespace(
                IMAGE_GENERATION_ENGINE='openai',
                IMAGE_GENERATION_MODEL='model-a',
                IMAGE_EDIT_ENGINE='openai',
                IMAGE_EDIT_MODEL='model-a',
                IMAGE_SIZE='1024x1024',
                IMAGE_EDIT_SIZE='512x512',
            )
        ),
    )


def test_image_quote_request_accepts_one_remote_reference() -> None:
    from open_webui.extensions.credits.router import ImageQuoteRequest

    quote = ImageQuoteRequest.model_validate(
        {
            'resource_id': 'model-a',
            'action': 'image-to-image',
            'prompt': 'safe test prompt',
            'image': 'https://images.example.test/reference.png',
        }
    )

    assert quote.image == 'https://images.example.test/reference.png'


def test_image_quote_request_rejects_too_many_references() -> None:
    from open_webui.extensions.credits.router import ImageQuoteRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ImageQuoteRequest.model_validate(
            {
                'resource_id': 'model-a',
                'action': 'image-to-image',
                'prompt': 'safe test prompt',
                'image': ['file-id'] * 9,
            }
        )


def test_quote_rejects_invalid_image_count_before_adapter() -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    with pytest.raises(CreditError, match='Price rule is incomplete'):
        credits_router._quote_image_input(
            {
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'prompt': 'safe test prompt',
                'dimensions': {'image_count': True},
            }
        )


def test_quote_returns_price_and_current_balance_without_writing_usage(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def quote(_session, user, payload):
        assert user.id == 'user-1'
        assert payload['resource_id'] == 'model-a'
        return {
            'balance': 10,
            'sufficient': True,
            'exempt': False,
            'configured': True,
            'factors': [],
            'charged_credits': 3,
            'error': None,
        }

    monkeypatch.setattr(credits_router, 'quote_image', quote)

    response = TestClient(app).post(
        '/api/v1/credits/quotes/image',
        json={'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
    )

    assert response.status_code == 200
    assert response.json()['charged_credits'] == 3
    assert response.json()['sufficient'] is True


def test_admin_video_quote_maps_model_and_computes_the_regular_price(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    price_calls = []

    async def balance(_session, _user_id):
        return 10

    async def price(_session, service_type, resource_id, action):
        price_calls.append((service_type, resource_id, action))
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda _price, dimensions: type('Quote', (), {'charged_credits': dimensions['duration'], 'factors': ()})(),
    )

    result = asyncio.run(
        credits_router.quote_video(
            object(),
            credits_router.CreditUserSnapshot(id='admin-1', name='Admin', email='admin@example.test', role='admin'),
            credits_router.VideoQuoteRequest.model_validate(
                {
                    'resource_id': 'kling-video-v3-pro',
                    'action': 'text-to-video',
                    'dimensions': {'duration': '5', 'resolution': '1080p'},
                }
            ),
        )
    )

    assert result['charged_credits'] == 5
    assert result['exempt'] is False
    assert price_calls == [('video', 'fal-ai/kling-video/v3/pro/text-to-video', 'text-to-video')]


def test_video_quote_rejects_fractional_duration_before_pricing() -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    with pytest.raises(CreditError, match='Price rule is incomplete'):
        credits_router._normalize_video_quote_dimensions({'duration': '5.5'})


def test_video_quote_preserves_auto_duration_for_exact_map_pricing() -> None:
    from open_webui.extensions.credits import router as credits_router

    assert credits_router._normalize_video_quote_dimensions({'duration': 'auto'}) == {'duration': 'auto'}
    assert credits_router._normalize_video_quote_dimensions({'duration': '0'}) == {'duration': '0'}


def test_quote_endpoint_uses_the_image_adapter(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='user-1', name='User One', email='user-1@example.test'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def prepare(request, image_input, metadata, user):
        assert metadata is None
        assert user.id == 'user-1'
        assert image_input.model == 'model-a'
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'normalized-request-hash',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda *_: type('Quote', (), {'charged_credits': 3, 'factors': ()})(),
    )

    response = TestClient(app).post(
        '/api/v1/credits/quotes/image',
        json={'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
    )

    assert response.status_code == 200
    assert response.json()['charged_credits'] == 3


def test_quote_uses_the_edit_adapter_for_image_to_image_requests(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    calls = []

    async def prepare_edit(_request, image_input, _metadata, _user):
        calls.append(image_input.image)
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'image-to-image',
                        'dimensions': {},
                        'request_hash': 'edit-request',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_edit_call', prepare_edit)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda *_: type('Quote', (), {'charged_credits': 3, 'factors': ()})(),
    )

    result = asyncio.run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {
                'resource_id': 'model-a',
                'action': 'image-to-image',
                'prompt': 'safe test prompt',
                'image': 'reference-file',
                'dimensions': {},
            },
        )
    )

    assert result['charged_credits'] == 3
    assert calls == ['reference-file']


def test_quote_cache_recomputes_after_ttl_expiry(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    compute_calls = []
    clock = [100.0]

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'cache-expiry',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    def compute(_price, _dimensions):
        compute_calls.append(clock[0])
        return type('Quote', (), {'charged_credits': 3, 'factors': ()})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'time', lambda: clock[0])
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(credits_router, 'compute_price', compute)
    payload = {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}}
    user = AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test')

    asyncio.run(credits_router.quote_image(Session(), user, payload))
    clock[0] += credits_router.CREDIT_QUOTE_CACHE_TTL_SECONDS + 1
    asyncio.run(credits_router.quote_image(Session(), user, payload))

    assert compute_calls == [100.0, 106.0]


def test_quote_rejects_an_invalid_payload_mapping() -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    with pytest.raises(CreditError, match='Credit service is unavailable'):
        asyncio.run(
            credits_router.quote_image(
                object(),
                AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
                {'resource_id': 1, 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
            )
        )


def test_quote_returns_insufficient_balance_state(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'insufficient-balance',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 2

    async def price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(
        credits_router,
        'compute_price',
        lambda *_: type('Quote', (), {'charged_credits': 3, 'factors': ()})(),
    )

    result = asyncio.run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result['balance'] == 2
    assert result['sufficient'] is False
    assert result['charged_credits'] == 3


def test_quote_cache_isolated_by_user_and_invalidated_by_price_version(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    calls = []
    price = type('Price', (), {'updated_at': 1, 'enabled': True})()

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': {},
                        'request_hash': 'same-normalized-request',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def configured_price(_session, _service_type, _resource_id, _action):
        return price

    def compute(_price, _dimensions):
        calls.append(_price.updated_at)
        return type('Quote', (), {'charged_credits': 3, 'factors': ()})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', configured_price)
    monkeypatch.setattr(credits_router, 'compute_price', compute)
    payload = {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}}

    user_one = AuthenticatedUser('user-1', 'User One', 'user-1@example.test')
    user_two = AuthenticatedUser('user-2', 'User Two', 'user-2@example.test')

    asyncio.run(credits_router.quote_image(Session(), user_one, payload))
    asyncio.run(credits_router.quote_image(Session(), user_one, payload))
    asyncio.run(credits_router.quote_image(Session(), user_two, payload))
    price.updated_at = 2
    asyncio.run(credits_router.quote_image(Session(), user_one, payload))

    assert calls == [1, 1, 2]


def test_quote_prices_the_adapter_normalized_dimensions(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    normalized_dimensions = {
        'size': '1024x1024',
        'resolution': 'default',
        'aspect_ratio': 'default',
        'quality': 'hd',
        'image_count': 1,
    }
    received_dimensions = []

    async def prepare(_request, _image_input, _metadata, _user):
        return type(
            'Prepared',
            (),
            {
                'billing': type(
                    'Billing',
                    (),
                    {
                        'service_type': 'image',
                        'resource_id': 'model-a',
                        'action': 'text-to-image',
                        'dimensions': normalized_dimensions,
                        'request_hash': 'normalized-dimensions-test',
                    },
                )()
            },
        )()

    async def balance(_session, _user_id):
        return 10

    async def price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1, 'enabled': True})()

    def compute(_price, dimensions):
        received_dimensions.append(dict(dimensions))
        return type('Quote', (), {'charged_credits': 3, 'factors': ()})()

    credits_router._quote_cache.clear()
    monkeypatch.setattr(credits_router, 'prepare_generation_call', prepare)
    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', price)
    monkeypatch.setattr(credits_router, 'compute_price', compute)

    result = asyncio.run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'prompt': 'safe test prompt',
                'dimensions': {'quality': 'hd'},
            },
        )
    )

    assert result['charged_credits'] == 3
    assert received_dimensions == [normalized_dimensions]


def test_quote_preserves_admin_role_without_forcing_an_exemption(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    app = FastAPI()
    app.include_router(credits_router.router)
    app.dependency_overrides[credits_router.get_verified_user] = lambda: AuthenticatedUser(
        id='admin-1', name='Admin', email='admin@example.test', role='admin'
    )
    app.dependency_overrides[credits_router.get_async_session] = lambda: object()

    async def quote(_session, user, _payload):
        assert user.role == 'admin'
        return {
            'balance': 10,
            'sufficient': True,
            'exempt': False,
            'configured': False,
            'factors': [],
            'charged_credits': 0,
            'error': None,
        }

    monkeypatch.setattr(credits_router, 'quote_image', quote)

    response = TestClient(app).post(
        '/api/v1/credits/quotes/image',
        json={'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
    )

    assert response.status_code == 200
    assert response.json()['exempt'] is False


def test_quote_returns_incomplete_price_state(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router
    from open_webui.extensions.credits.errors import CreditError

    class Session:
        pass

    async def balance(_session, _user_id):
        return 4

    async def configured_price(_session, _service_type, _resource_id, _action):
        return type('Price', (), {'updated_at': 1})()

    def incomplete(_price, _dimensions):
        raise CreditError(code='price_rule_incomplete')

    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', configured_price)
    monkeypatch.setattr(credits_router, 'compute_price', incomplete)
    _stub_openai_image_config(monkeypatch, credits_router)

    result = __import__('asyncio').run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result['configured'] is False
    assert result['error'] == 'price_rule_incomplete'


def test_quote_returns_not_configured_state(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    async def balance(_session, _user_id):
        return 4

    async def no_price(_session, _service_type, _resource_id, _action):
        return None

    monkeypatch.setattr(credits_router, 'get_balance_if_exists', balance)
    monkeypatch.setattr(credits_router, 'get_enabled_price', no_price)
    _stub_openai_image_config(monkeypatch, credits_router)

    result = __import__('asyncio').run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result == {
        'balance': 4,
        'sufficient': False,
        'exempt': False,
        'configured': False,
        'factors': [],
        'charged_credits': None,
        'error': 'price_not_configured',
    }


def test_quote_does_not_create_an_account(monkeypatch) -> None:
    from open_webui.extensions.credits import router as credits_router

    class Session:
        pass

    async def no_account_creation(session, user_id):
        assert isinstance(session, Session)
        assert user_id == 'user-1'
        return 7

    async def configured_price(_session, service_type, resource_id, action):
        assert (service_type, resource_id, action) == ('image', 'model-a', 'text-to-image')
        return type(
            'Price',
            (),
            {
                'service_type': 'image',
                'resource_id': 'model-a',
                'action': 'text-to-image',
                'base_price': '1',
                'rules': {'schema_version': 1, 'dimensions': []},
                'enabled': True,
                'updated_at': 1,
            },
        )()

    monkeypatch.setattr(credits_router, 'get_balance_if_exists', no_account_creation)
    monkeypatch.setattr(credits_router, 'get_enabled_price', configured_price)
    _stub_openai_image_config(monkeypatch, credits_router)

    async def compute(_price, _dimensions):
        raise AssertionError('compute_price must remain synchronous')

    result = __import__('asyncio').run(
        credits_router.quote_image(
            Session(),
            AuthenticatedUser(id='user-1', name='User One', email='user-1@example.test'),
            {'resource_id': 'model-a', 'action': 'text-to-image', 'prompt': 'safe test prompt', 'dimensions': {}},
        )
    )

    assert result['balance'] == 7
