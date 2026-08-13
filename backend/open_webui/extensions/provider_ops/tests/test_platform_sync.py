from __future__ import annotations

from decimal import Decimal

import pytest
from open_webui.extensions.provider_ops.db import ProviderOpsBase
from open_webui.extensions.provider_ops.models import ProviderBillingEvent, ProviderInvocation, ProviderRequestRecord
from open_webui.extensions.provider_ops.platform_sync import (
    _record_billing_events,
    _record_requests,
    _relevant_endpoint_ids,
    get_provider_overview,
    sync_fal_platform,
)
from open_webui.extensions.provider_ops.providers.fal_platform import (
    FalBillingEvent,
    FalPlatformError,
    FalRequestRecord,
)
from open_webui.extensions.provider_ops.schemas import ProviderSyncForm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_authoritative_request_metadata_reconciles_local_invocation(tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sessions() as session:
        session.add(
            ProviderInvocation(
                id='invocation-1',
                task_id='task-1',
                user_id='user-1',
                media_kind='image',
                provider='fal',
                provider_model_id='fal-ai/example',
                attempt_no=1,
                provider_request_id='request-1',
                status='unknown',
                input_sha256='0' * 64,
                created_at=1,
                updated_at=1,
            )
        )
        await session.commit()
        count, matched = await _record_requests(
            session,
            (
                FalRequestRecord(
                    request_id='request-1',
                    endpoint_id='fal-ai/example',
                    sent_at='2026-08-13T10:00:00Z',
                    started_at='2026-08-13T10:00:01Z',
                    ended_at='2026-08-13T10:00:03Z',
                    status_code=200,
                    duration=Decimal('2.125'),
                ),
            ),
            synced_at=123,
        )
        await session.commit()

        invocation = await session.get(ProviderInvocation, 'invocation-1')
        assert (count, matched) == (1, 1)
        assert invocation.status == 'succeeded'
        assert invocation.status_code == 200
        assert invocation.execution_duration_ms == 2125
        assert invocation.submitted_at == 1786615200000
        assert invocation.provider_started_at == 1786615201000
        assert invocation.provider_completed_at == 1786615203000
        request = await session.scalar(
            ProviderRequestRecord.__table__.select().where(ProviderRequestRecord.provider_request_id == 'request-1')
        )
        assert request is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_billing_event_sets_exact_discounted_cost_on_invocation(tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sessions() as session:
        session.add(
            ProviderInvocation(
                id='invocation-1',
                task_id='task-1',
                user_id='user-1',
                media_kind='image',
                provider='fal',
                provider_model_id='fal-ai/example',
                attempt_no=1,
                provider_request_id='request-1',
                status='succeeded',
                input_sha256='0' * 64,
                created_at=1,
                updated_at=1,
            )
        )
        await session.commit()
        count, matched = await _record_billing_events(
            session,
            (
                FalBillingEvent(
                    request_id='request-1',
                    endpoint_id='fal-ai/example',
                    timestamp='2026-08-13T10:00:03Z',
                    output_units=Decimal('2'),
                    unit_price=Decimal('0.025'),
                    percent_discount=Decimal('10'),
                    cost_subtotal=Decimal('0.05'),
                    cost_discount=Decimal('0.005'),
                    cost_total=Decimal('0.045'),
                    cost_estimate_nano_usd=Decimal('45000000'),
                ),
            ),
            synced_at=123,
        )
        await session.commit()

        invocation = await session.get(ProviderInvocation, 'invocation-1')
        assert (count, matched) == (1, 1)
        assert invocation.actual_cost_total == '0.045'
        assert invocation.actual_cost_currency == 'USD'
        assert invocation.cost_accuracy == 'exact'
        event = await session.scalar(
            ProviderBillingEvent.__table__.select().where(ProviderBillingEvent.provider_request_id == 'request-1')
        )
        assert event is not None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_routes_admin_only_apis_to_admin_key(monkeypatch, tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    calls: list[tuple[str, str]] = []

    class FakeClient:
        def __init__(self, key):
            self.key = key

        async def prices(self, endpoint_ids):
            calls.append(('pricing', self.key))
            return ()

        async def requests(self, endpoint_ids, **kwargs):
            calls.append(('requests', self.key))
            return ()

        async def analytics(self, endpoint_ids, **kwargs):
            calls.append(('analytics', self.key))
            return ()

        async def usage(self, **kwargs):
            calls.append(('usage', self.key))
            return ()

        async def billing_events(self, **kwargs):
            calls.append(('billing_events', self.key))
            return ()

    async def get_many(*_keys):
        return {
            'image_generation.fal.api_key': 'api-key',
            'provider_ops.fal.admin_api_key': 'admin-key',
        }

    import open_webui.extensions.provider_ops.platform_sync as platform_sync

    monkeypatch.setattr(platform_sync, 'FalPlatformClient', FakeClient)
    monkeypatch.setattr(platform_sync.Config, 'get_many', get_many)
    async with sessions() as session:
        result = await sync_fal_platform(session, ProviderSyncForm())

    assert result.status == 'succeeded'
    assert dict(calls) == {
        'pricing': 'api-key',
        'requests': 'api-key',
        'analytics': 'api-key',
        'usage': 'admin-key',
        'billing_events': 'admin-key',
    }
    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_returns_failed_result_after_rollback_with_expiring_session(monkeypatch, tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=True)

    class FailingClient:
        def __init__(self, _key):
            pass

        async def prices(self, _endpoint_ids):
            raise FalPlatformError('not_found', status_code=404)

    async def get_many(*_keys):
        return {
            'image_generation.fal.api_key': 'api-key',
            'provider_ops.fal.admin_api_key': '',
        }

    import open_webui.extensions.provider_ops.platform_sync as platform_sync

    monkeypatch.setattr(platform_sync, 'FalPlatformClient', FailingClient)
    monkeypatch.setattr(platform_sync.Config, 'get_many', get_many)
    async with sessions() as session:
        result = await sync_fal_platform(
            session,
            ProviderSyncForm(resources=('pricing',)),
        )

    assert result.status == 'failed'
    assert result.error_code == 'pricing_not_found'
    assert result.completed_at is not None
    await engine.dispose()


def test_relevant_endpoint_ids_only_include_observed_provider_models() -> None:
    billing_event = FalBillingEvent(
        request_id='request-1',
        endpoint_id='fal-ai/from-billing',
        timestamp='2026-08-13T10:00:03Z',
        cost_subtotal=Decimal('0.05'),
        cost_discount=Decimal('0'),
        cost_total=Decimal('0.05'),
        cost_estimate_nano_usd=Decimal('50000000'),
    )

    assert _relevant_endpoint_ids(
        ('fal-ai/local', 'fal-ai/from-billing'),
        (billing_event,),
        (),
    ) == ('fal-ai/local', 'fal-ai/from-billing')


@pytest.mark.asyncio
async def test_overview_aggregates_complete_window_and_separates_matched_cost(tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sessions() as session:
        for invocation_id, request_id, status in (
            ('invocation-1', 'request-1', 'succeeded'),
            ('invocation-2', None, 'failed'),
        ):
            session.add(
                ProviderInvocation(
                    id=invocation_id,
                    task_id=invocation_id,
                    user_id='user-1',
                    media_kind='image',
                    provider='fal',
                    provider_model_id='fal-ai/example',
                    attempt_no=1,
                    provider_request_id=request_id,
                    status=status,
                    input_sha256='0' * 64,
                    created_at=100,
                    execution_duration_ms=2000,
                    updated_at=100,
                )
            )
        await session.commit()
        await _record_requests(
            session,
            tuple(
                FalRequestRecord(
                    request_id=request_id,
                    endpoint_id='fal-ai/example',
                    sent_at='2026-08-13T10:00:00Z',
                    started_at='2026-08-13T10:00:01Z',
                    ended_at='2026-08-13T10:00:03Z',
                    status_code=200,
                    duration=Decimal('2'),
                )
                for request_id in ('request-1', 'request-unmatched')
            ),
            synced_at=123,
        )
        await _record_billing_events(
            session,
            tuple(
                FalBillingEvent(
                    request_id=request_id,
                    endpoint_id='fal-ai/example',
                    timestamp='2026-08-13T10:00:03Z',
                    output_units=Decimal('1'),
                    unit_price=cost,
                    cost_subtotal=cost,
                    cost_discount=Decimal('0'),
                    cost_total=cost,
                    cost_estimate_nano_usd=cost * Decimal('1000000000'),
                )
                for request_id, cost in (
                    ('request-1', Decimal('0.045')),
                    ('request-unmatched', Decimal('0.030')),
                )
            ),
            synced_at=123,
        )
        await session.commit()

        overview = await get_provider_overview(
            session,
            provider='fal',
            since_ms=0,
            until_ms=2000000000000,
        )

    assert overview.invocation_count == 2
    assert overview.success_count == 1
    assert overview.failed_count == 1
    assert overview.provider_request_count == 2
    assert overview.matched_provider_request_count == 1
    assert overview.billing_event_count == 2
    assert overview.matched_billing_event_count == 1
    assert Decimal(overview.exact_costs['USD']) == Decimal('0.075')
    assert Decimal(overview.matched_exact_costs['USD']) == Decimal('0.045')
    await engine.dispose()
