from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException
from open_webui.extensions.provider_ops.db import ProviderOpsBase
from open_webui.extensions.provider_ops.models import (
    ProviderBillingEvent,
    ProviderInvocation,
    ProviderPriceSnapshot,
    ProviderRequestRecord,
    ProviderSyncRun,
)
from open_webui.extensions.provider_ops.platform_queries import get_provider_overview
from open_webui.extensions.provider_ops.platform_sync import (
    _record_billing_events,
    _record_prices,
    _record_requests,
    _relevant_endpoint_ids,
    sync_fal_platform,
)
from open_webui.extensions.provider_ops.providers.fal_platform import (
    FalBillingEvent,
    FalPlatformError,
    FalPrice,
    FalRequestRecord,
)
from open_webui.extensions.provider_ops.schemas import ProviderSyncForm
from sqlalchemy import select
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
    assert overview.unbilled_success_count == 0
    assert Decimal(overview.exact_costs['USD']) == Decimal('0.075')
    assert Decimal(overview.matched_exact_costs['USD']) == Decimal('0.045')
    await engine.dispose()


@pytest.mark.asyncio
async def test_record_prices_deduplicates_on_repeated_sync(tmp_path) -> None:
    """修复 1：_record_prices 批量去重查询曾用 entry[4]（unit）而非 entry[3]（endpoint_id）
    构建 endpoint_ids，导致 IN 子句用计费单位匹配 provider_model_id，查询永远返回空集，
    每次同步都全量重复插入价格快照行。"""
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    prices = (
        FalPrice(
            endpoint_id='fal-ai/flux-pro',
            unit_price=Decimal('0.025'),
            unit='second',
            currency='USD',
        ),
        FalPrice(
            endpoint_id='fal-ai/flux-dev',
            unit_price=Decimal('0.010'),
            unit='second',
            currency='USD',
        ),
    )

    async with sessions() as session:
        first_count = await _record_prices(session, prices, synced_at=100)
        await session.commit()
        second_count = await _record_prices(session, prices, synced_at=200)
        await session.commit()

        rows = (
            await session.scalars(select(ProviderPriceSnapshot).where(ProviderPriceSnapshot.provider == 'fal'))
        ).all()

    assert first_count == 2
    assert second_count == 2
    assert len(rows) == 2  # 不应有重复行
    for row in rows:
        assert row.last_seen_at == 200  # 第二次同步只更新 last_seen_at
    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_clears_stale_running_and_proceeds(monkeypatch, tmp_path) -> None:
    """修复 2：进程崩溃后 status='running' 的行不会被 except 块标记为 failed，
    导致后续所有同步被 409 永久阻塞。stale 清理应将僵尸行标记为 failed 后继续。"""
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    class FakeClient:
        def __init__(self, _key):
            pass

        async def prices(self, _endpoint_ids):
            return ()

        async def requests(self, _endpoint_ids, **kwargs):
            return ()

        async def analytics(self, _endpoint_ids, **kwargs):
            return ()

        async def usage(self, **kwargs):
            return ()

        async def billing_events(self, **kwargs):
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
        # 创建一个僵尸 running 行：started_at=0 远超 stale 阈值
        session.add(
            ProviderSyncRun(
                id='stale-run',
                provider='fal',
                status='running',
                resources_json=['pricing'],
                counts_json=None,
                error_code=None,
                window_start_at=0,
                window_end_at=0,
                started_at=0,
                completed_at=None,
            )
        )
        await session.commit()

        result = await sync_fal_platform(session, ProviderSyncForm())

        # 僵尸行应被标记为 failed
        stale = await session.get(ProviderSyncRun, 'stale-run')
        assert stale.status == 'failed'
        assert stale.error_code == 'provider_sync_stale'
        assert stale.completed_at is not None

    # 新同步应成功执行
    assert result.status == 'succeeded'
    assert result.id != 'stale-run'
    await engine.dispose()


@pytest.mark.asyncio
async def test_overview_matches_invocation_created_before_window(tmp_path) -> None:
    """修复 3：matched_request_ids 子查询曾限定 created_at 时间窗，导致窗口内的计费事件
    若关联窗口外创建的 invocation 不被计为 matched。移除 created_at 过滤后应正确计数。"""
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sessions() as session:
        # invocation 创建于窗口外（created_at=50），但关联的 billing event 在窗口内
        session.add(
            ProviderInvocation(
                id='invocation-old',
                task_id='task-1',
                user_id='user-1',
                media_kind='image',
                provider='fal',
                provider_model_id='fal-ai/example',
                attempt_no=1,
                provider_request_id='request-old',
                status='succeeded',
                input_sha256='0' * 64,
                created_at=50,
                updated_at=50,
            )
        )
        await session.commit()

        # billing event 的 event_at 在窗口 [1786615200000, 1786615205000) 内
        await _record_billing_events(
            session,
            (
                FalBillingEvent(
                    request_id='request-old',
                    endpoint_id='fal-ai/example',
                    timestamp='2026-08-13T10:00:03Z',
                    cost_subtotal=Decimal('0.045'),
                    cost_discount=Decimal('0'),
                    cost_total=Decimal('0.045'),
                    cost_estimate_nano_usd=Decimal('45000000'),
                ),
            ),
            synced_at=123,
        )
        await session.commit()

        overview = await get_provider_overview(
            session,
            provider='fal',
            since_ms=1786615200000,
            until_ms=1786615205000,
        )

    # invocation 创建于窗口外，不计入 invocation_count
    assert overview.invocation_count == 0
    # 但 billing event 在窗口内，应被计为 matched（因为关联的 invocation 存在）
    assert overview.billing_event_count == 1
    assert overview.matched_billing_event_count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_record_requests_does_not_set_completed_at_without_status(tmp_path) -> None:
    """修复 4：_record_requests 重构将嵌套条件拆为两个独立 if，导致 completed_at
    在 status=None 但 ended_at 有值时也被更新。恢复嵌套后应与原始逻辑一致。"""
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
                completed_at=None,
            )
        )
        await session.commit()
        await _record_requests(
            session,
            (
                FalRequestRecord(
                    request_id='request-1',
                    endpoint_id='fal-ai/example',
                    sent_at='2026-08-13T10:00:00Z',
                    started_at='2026-08-13T10:00:01Z',
                    ended_at='2026-08-13T10:00:03Z',
                    status_code=None,
                    duration=Decimal('2'),
                ),
            ),
            synced_at=123,
        )
        await session.commit()

        invocation = await session.get(ProviderInvocation, 'invocation-1')
        # status_code=None → status=None → completed_at 不应被更新
        assert invocation.completed_at is None
        # 但 provider_completed_at 应该被更新（它不受 status 条件约束）
        assert invocation.provider_completed_at is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_record_requests_updates_large_input_in_bounded_batches(monkeypatch, tmp_path) -> None:
    """大量请求必须拆成多个 CASE UPDATE，避免超过数据库单语句绑定参数上限。"""
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import open_webui.extensions.provider_ops.platform_sync as platform_sync

    monkeypatch.setattr(platform_sync, '_SYNC_WRITE_BATCH_SIZE', 2)
    records = tuple(
        FalRequestRecord(
            request_id=f'request-{index}',
            endpoint_id='fal-ai/example',
            sent_at='2026-08-13T10:00:00Z',
            started_at='2026-08-13T10:00:01Z',
            ended_at='2026-08-13T10:00:03Z',
            status_code=200,
            duration=Decimal('2'),
        )
        for index in range(5)
    )

    async with sessions() as session:
        session.add_all(
            ProviderInvocation(
                id=f'invocation-{index}',
                task_id=f'task-{index}',
                user_id='user-1',
                media_kind='image',
                provider='fal',
                provider_model_id='fal-ai/example',
                attempt_no=1,
                provider_request_id=f'request-{index}',
                status='unknown',
                input_sha256='0' * 64,
                created_at=1,
                updated_at=1,
            )
            for index in range(5)
        )
        await session.commit()
        assert await _record_requests(session, records, synced_at=123) == (5, 5)
        await session.commit()
        statuses = (await session.scalars(select(ProviderInvocation.status).order_by(ProviderInvocation.id))).all()

    assert statuses == ['succeeded'] * 5
    await engine.dispose()


@pytest.mark.asyncio
async def test_sync_keeps_old_run_with_fresh_heartbeat_and_rejects_concurrent_start(tmp_path) -> None:
    """started_at 很旧但心跳仍新鲜的长同步不能被误杀；唯一索引应拒绝第二个 running。"""
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import open_webui.extensions.provider_ops.platform_sync as platform_sync

    heartbeat_at = platform_sync._now_ms()
    async with sessions() as session:
        session.add(
            ProviderSyncRun(
                id='long-running-sync',
                provider='fal',
                status='running',
                resources_json=['pricing'],
                counts_json=None,
                error_code=None,
                window_start_at=0,
                window_end_at=0,
                started_at=0,
                heartbeat_at=heartbeat_at,
                completed_at=None,
            )
        )
        await session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await sync_fal_platform(session, ProviderSyncForm())

        persisted = await session.get(ProviderSyncRun, 'long-running-sync')
        assert persisted.status == 'running'
        assert persisted.heartbeat_at == heartbeat_at

    assert exc_info.value.status_code == 409
    await engine.dispose()
