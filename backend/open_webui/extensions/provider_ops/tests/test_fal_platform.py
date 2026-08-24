from __future__ import annotations

import pytest
from open_webui.extensions.provider_ops.providers.fal_platform import FalPlatformClient, FalPlatformError
from open_webui.extensions.tests.http_test_support import AsyncJsonResponse as _Response


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


@pytest.mark.asyncio
async def test_usage_and_analytics_paginate_and_preserve_decimal_metrics(monkeypatch) -> None:
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    usage_session = _Session(
        [
            {
                'time_series': [
                    {
                        'bucket': '2026-08-13T10:00:00Z',
                        'results': [
                            {
                                'endpoint_id': 'fal-ai/example',
                                'unit': 'image',
                                'quantity': 2,
                                'unit_price': '0.1',
                                'cost_subtotal': '0.2',
                                'cost_discount': '0',
                                'cost_total': '0.2',
                                'currency': 'USD',
                            }
                        ],
                    }
                ],
                'next_cursor': 'next',
            },
            {'time_series': [], 'next_cursor': None},
        ]
    )
    monkeypatch.setattr(platform, 'get_session', lambda: _value(usage_session))
    usage = await FalPlatformClient('api-key').usage(start='start', end='end', timeframe='hour')
    assert len(usage) == 1
    assert usage_session.calls[1][1]['params'][-1] == ('cursor', 'next')

    analytics_session = _Session(
        [
            {
                'time_series': [
                    {
                        'bucket': '2026-08-13T10:00:00Z',
                        'results': [
                            {
                                'endpoint_id': 'fal-ai/example',
                                'request_count': 3,
                                'success_count': 2,
                            }
                        ],
                    }
                ],
                'next_cursor': None,
            }
        ]
    )
    monkeypatch.setattr(platform, 'get_session', lambda: _value(analytics_session))
    analytics = await FalPlatformClient('api-key').analytics(
        ('fal-ai/example',),
        start='start',
        end='end',
        timeframe='hour',
    )
    assert analytics[0].results[0].request_count == 3
    assert ('expand', 'request_count') in analytics_session.calls[0][1]['params']


@pytest.mark.asyncio
async def test_platform_rejects_bad_credentials_payloads_and_cursor_loops(monkeypatch) -> None:
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    with pytest.raises(FalPlatformError) as missing:
        FalPlatformClient('')
    assert missing.value.code == 'provider_credentials_missing'

    monkeypatch.setattr(platform, 'get_session', lambda: _value(_Session([['not', 'mapping']])))
    with pytest.raises(FalPlatformError) as invalid_payload:
        await FalPlatformClient('key')._get('/path', [])
    assert invalid_payload.value.code == 'provider_platform_invalid_response'

    loop_pages = [
        {'billing_events': [], 'next_cursor': 'same'},
        {'billing_events': [], 'next_cursor': 'same'},
    ]
    monkeypatch.setattr(platform, 'get_session', lambda: _value(_Session(loop_pages)))
    with pytest.raises(FalPlatformError) as loop:
        await FalPlatformClient('key').billing_events(start='start', end='end')
    assert loop.value.code == 'provider_platform_cursor_loop'

    monkeypatch.setattr(platform, '_MAX_PAGES', 1)
    monkeypatch.setattr(
        platform,
        'get_session',
        lambda: _value(_Session([{'items': [], 'next_cursor': 'more'}])),
    )
    with pytest.raises(FalPlatformError) as limit:
        await FalPlatformClient('key').requests(('model',), start='start', end='end')
    assert limit.value.code == 'provider_platform_page_limit'


@pytest.mark.asyncio
async def test_invalid_platform_models_map_to_stable_error(monkeypatch) -> None:
    import open_webui.extensions.provider_ops.providers.fal_platform as platform

    monkeypatch.setattr(
        platform,
        'get_session',
        lambda: _value(_Session([{'prices': [{'endpoint_id': None}]}])),
    )
    with pytest.raises(FalPlatformError) as invalid:
        await FalPlatformClient('key').prices(('model',))
    assert invalid.value.code == 'provider_platform_invalid_response'
