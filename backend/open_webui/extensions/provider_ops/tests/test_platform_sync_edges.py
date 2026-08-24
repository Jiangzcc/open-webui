import asyncio
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.provider_ops import platform_sync
from open_webui.extensions.tests.async_test_support import AsyncContext


@pytest.mark.asyncio
async def test_heartbeat_write_stop_and_transient_error_paths(monkeypatch) -> None:
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(rowcount=None)),
        commit=AsyncMock(),
    )
    assert (
        await platform_sync._write_sync_heartbeat(
            lambda: AsyncContext(session),
            'run',
        )
        is False
    )

    await platform_sync._stop_heartbeat(None)
    task = asyncio.create_task(asyncio.Event().wait())
    await platform_sync._stop_heartbeat(task)
    assert task.cancelled()

    monkeypatch.setattr(platform_sync.asyncio, 'sleep', AsyncMock())
    monkeypatch.setattr(
        platform_sync,
        '_write_sync_heartbeat',
        AsyncMock(side_effect=[RuntimeError('database'), False]),
    )
    await platform_sync._heartbeat_sync_run(object(), 'run')
    assert platform_sync._write_sync_heartbeat.await_count == 2


def test_usage_and_analytics_rows_normalize_provider_values() -> None:
    usage_item = SimpleNamespace(
        auth_method_structured=None,
        endpoint_id='model',
        unit='seconds',
        unit_price=Decimal('0.1'),
        percent_discount=None,
        quantity=Decimal('2'),
        cost_subtotal=Decimal('0.2'),
        cost_discount=Decimal('0'),
        cost_total=Decimal('0.2'),
        currency='usd',
    )
    bucket = SimpleNamespace(bucket='2026-01-01T00:00:00Z', results=(usage_item,))
    row = list(platform_sync._usage_rows((bucket,), 'day', 1))[0]
    assert row.currency == 'USD'
    assert row.api_key_id is None

    analytics_item = SimpleNamespace(
        endpoint_id='model',
        model_dump=lambda **_kwargs: {'requests': 2},
    )
    bucket.results = (analytics_item,)
    row = list(platform_sync._analytics_rows((bucket,), 'day', 1))[0]
    assert row.metrics_json == {'requests': 2}


def test_record_upserts_update_existing_rows() -> None:
    billing_row = SimpleNamespace()
    event = SimpleNamespace(
        cost_total=Decimal('1'),
        timestamp='2026-01-01T00:00:00Z',
        endpoint_id='model',
        unit='request',
        unit_price=Decimal('1'),
        output_units=None,
        cost_subtotal=Decimal('1'),
        cost_discount=Decimal('0'),
        percent_discount=None,
        cost_estimate_nano_usd=Decimal('1000000000'),
        auth_method_structured=None,
    )
    session = SimpleNamespace(add=lambda _row: None)
    platform_sync._upsert_billing_event(
        session,
        {'request': billing_row},
        'request',
        event,
        1,
    )
    assert billing_row.currency == 'USD'

    request_row = SimpleNamespace()
    record = SimpleNamespace(
        endpoint_id='model',
        sent_at='2026-01-01T00:00:00Z',
        started_at='2026-01-01T00:00:01Z',
        ended_at='2026-01-01T00:00:02Z',
        status_code=200,
        duration=Decimal('1'),
    )
    platform_sync._upsert_request_record(
        session,
        {'request': request_row},
        'request',
        record,
        1,
    )
    assert request_row.status_code == 200


@pytest.mark.asyncio
async def test_fail_sync_run_reraises_original_when_run_was_not_persisted() -> None:
    error = RuntimeError('sync')
    session = SimpleNamespace(
        rollback=AsyncMock(),
        get=AsyncMock(return_value=None),
    )
    with pytest.raises(RuntimeError, match='sync'):
        await platform_sync._fail_sync_run(session, 'missing', error)
