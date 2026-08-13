from __future__ import annotations

import pytest
from open_webui.extensions.provider_ops.providers.fal_platform import FalPlatformClient, FalPlatformError


class _Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def json(self, content_type=None):
        return self.payload


class _Session:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        page = self.pages.pop(0)
        if isinstance(page, tuple):
            return _Response(page[1], status=page[0])
        return _Response(page)


async def _value(value):
    return value


@pytest.mark.asyncio
async def test_prices_split_not_found_batches_and_keep_valid_endpoint_prices(monkeypatch) -> None:
    session = _Session(
        [
            (404, {'error': {'type': 'not_found', 'message': 'Resource not found'}}),
            {
                'prices': [
                    {
                        'endpoint_id': 'fal-ai/valid',
                        'unit_price': 0.025,
                        'unit': 'image',
                        'currency': 'USD',
                    }
                ],
                'next_cursor': None,
                'has_more': False,
            },
            (404, {'error': {'type': 'not_found', 'message': 'Resource not found'}}),
        ]
    )
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    monkeypatch.setattr(platform, 'get_session', lambda: _value(session))
    prices = await FalPlatformClient('api-key').prices(('fal-ai/valid', 'fal-ai/unpriced'))

    assert [price.endpoint_id for price in prices] == ['fal-ai/valid']
    assert [call[1]['params'] for call in session.calls] == [
        [('endpoint_id', 'fal-ai/valid'), ('endpoint_id', 'fal-ai/unpriced')],
        [('endpoint_id', 'fal-ai/valid')],
        [('endpoint_id', 'fal-ai/unpriced')],
    ]


@pytest.mark.asyncio
async def test_nonstandard_platform_error_includes_http_status(monkeypatch) -> None:
    session = _Session([(429, {'detail': 'rate limit exceeded'})])
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    monkeypatch.setattr(platform, 'get_session', lambda: _value(session))

    with pytest.raises(FalPlatformError) as captured:
        await FalPlatformClient('api-key').prices(('fal-ai/example',))

    assert captured.value.code == 'provider_platform_http_429'
    assert captured.value.status_code == 429


@pytest.mark.asyncio
async def test_billing_events_are_paginated_and_keep_exact_request_cost(monkeypatch) -> None:
    session = _Session(
        [
            {
                'billing_events': [
                    {
                        'request_id': 'request-1',
                        'endpoint_id': 'fal-ai/example',
                        'timestamp': '2026-08-13T10:00:00Z',
                        'output_units': 2,
                        'unit_price': 0.025,
                        'percent_discount': 10,
                        'cost_subtotal': 0.05,
                        'cost_discount': 0.005,
                        'cost_total': 0.045,
                        'cost_estimate_nano_usd': 45000000,
                        'auth_method_structured': {'detail': 'Production', 'api_key_id': 'key-1'},
                    }
                ],
                'next_cursor': 'next-page',
            },
            {'billing_events': [], 'next_cursor': None},
        ]
    )
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    monkeypatch.setattr(platform, 'get_session', lambda: _value(session))
    events = await FalPlatformClient('admin-key').billing_events(
        start='2026-08-13T00:00:00Z', end='2026-08-14T00:00:00Z'
    )

    assert len(events) == 1
    assert events[0].request_id == 'request-1'
    assert str(events[0].cost_total) == '0.045'
    assert session.calls[1][1]['params'][-1] == ('cursor', 'next-page')
    assert session.calls[0][1]['headers'] == {'Authorization': 'Key admin-key'}


@pytest.mark.asyncio
async def test_requests_use_endpoint_batches_without_request_payload_expansion(monkeypatch) -> None:
    session = _Session(
        [
            {
                'items': [
                    {
                        'request_id': 'request-1',
                        'endpoint_id': 'fal-ai/example',
                        'started_at': '2026-08-13T10:00:01Z',
                        'sent_at': '2026-08-13T10:00:00Z',
                        'ended_at': '2026-08-13T10:00:03Z',
                        'status_code': 200,
                        'duration': 2,
                        'json_input': {'prompt': 'must not be retained'},
                        'json_output': {'url': 'must not be retained'},
                    }
                ],
                'next_cursor': None,
            }
        ]
    )
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    monkeypatch.setattr(platform, 'get_session', lambda: _value(session))
    records = await FalPlatformClient('api-key').requests(
        ('fal-ai/example',),
        start='2026-08-13T00:00:00Z',
        end='2026-08-14T00:00:00Z',
    )

    assert records[0].model_dump() == {
        'request_id': 'request-1',
        'endpoint_id': 'fal-ai/example',
        'started_at': '2026-08-13T10:00:01Z',
        'sent_at': '2026-08-13T10:00:00Z',
        'ended_at': '2026-08-13T10:00:03Z',
        'status_code': 200,
        'duration': records[0].duration,
    }
    params = session.calls[0][1]['params']
    assert ('endpoint_id', 'fal-ai/example') in params
    assert ('limit', '100') in params
    assert not any(name == 'expand' for name, _value in params)
