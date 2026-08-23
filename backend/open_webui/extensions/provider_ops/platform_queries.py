"""provider_ops 平台数据的查询读取（运营中心展示侧）。

从 platform_sync.py 拆出（复盘：超长文件拆分）。同步写入与编排保留在
platform_sync.py；本模块只做只读查询，不依赖同步侧的客户端与心跳逻辑。
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ProviderAnalyticsBucket,
    ProviderBillingEvent,
    ProviderInvocation,
    ProviderPriceSnapshot,
    ProviderRequestRecord,
    ProviderSyncRun,
    ProviderUsageBucket,
)
from .schemas import (
    ProviderAnalyticsItem,
    ProviderAnalyticsList,
    ProviderBillingEventItem,
    ProviderBillingEventList,
    ProviderOverview,
    ProviderPriceItem,
    ProviderPriceList,
    ProviderRequestRecordItem,
    ProviderRequestRecordList,
    ProviderUsageItem,
    ProviderUsageList,
)


def _decimal(value: Decimal) -> str:
    return format(value, 'f')


def _matched_request_ids(provider: str):
    """本 provider 全部 invocation 的 provider_request_id 子查询。

    不限定 created_at 时间窗：窗口内的计费事件/请求记录可能关联窗口外创建的
    invocation（如跨天长任务），限定 created_at 会少计 matched。
    """
    return select(ProviderInvocation.provider_request_id).where(
        ProviderInvocation.provider == provider,
        ProviderInvocation.provider_request_id.is_not(None),
    )


async def list_provider_prices(session: AsyncSession, *, provider: str, limit: int) -> ProviderPriceList:
    rows = (
        await session.scalars(
            select(ProviderPriceSnapshot)
            .where(ProviderPriceSnapshot.provider == provider)
            .order_by(ProviderPriceSnapshot.last_seen_at.desc(), ProviderPriceSnapshot.id.desc())
            .limit(limit)
        )
    ).all()
    return ProviderPriceList(
        items=tuple(
            ProviderPriceItem(
                provider=row.provider,
                provider_model_id=row.provider_model_id,
                unit_price=row.unit_price,
                unit=row.unit,
                currency=row.currency,
                first_seen_at=row.first_seen_at,
                last_seen_at=row.last_seen_at,
            )
            for row in rows
        )
    )


async def get_provider_overview(
    session: AsyncSession,
    *,
    provider: str,
    since_ms: int,
    until_ms: int,
) -> ProviderOverview:
    active_statuses = ('created', 'submitted', 'queued', 'running')
    invocation_stats = (
        await session.execute(
            select(
                func.count(ProviderInvocation.id),
                func.sum(case((ProviderInvocation.status == 'succeeded', 1), else_=0)),
                func.sum(case((ProviderInvocation.status == 'failed', 1), else_=0)),
                func.sum(case((ProviderInvocation.status.in_(active_statuses), 1), else_=0)),
                func.avg(ProviderInvocation.execution_duration_ms),
            ).where(
                ProviderInvocation.provider == provider,
                ProviderInvocation.created_at >= since_ms,
                ProviderInvocation.created_at < until_ms,
            )
        )
    ).one()

    matched_request_ids = _matched_request_ids(provider)
    provider_request_stats = (
        await session.execute(
            select(
                func.count(ProviderRequestRecord.id),
                func.sum(
                    case(
                        (ProviderRequestRecord.provider_request_id.in_(matched_request_ids), 1),
                        else_=0,
                    )
                ),
            ).where(
                ProviderRequestRecord.provider == provider,
                ProviderRequestRecord.started_at >= since_ms,
                ProviderRequestRecord.started_at < until_ms,
            )
        )
    ).one()

    billing_result = await session.stream(
        select(
            ProviderBillingEvent.currency,
            ProviderBillingEvent.cost_total,
            ProviderBillingEvent.provider_request_id.in_(matched_request_ids).label('matched'),
        ).where(
            ProviderBillingEvent.provider == provider,
            ProviderBillingEvent.event_at >= since_ms,
            ProviderBillingEvent.event_at < until_ms,
        )
    )
    exact_cost_values: dict[str, Decimal] = {}
    matched_cost_values: dict[str, Decimal] = {}
    billing_event_count = 0
    matched_billing_event_count = 0
    async for currency, cost_total, matched in billing_result:
        cost = Decimal(cost_total)
        exact_cost_values[currency] = exact_cost_values.get(currency, Decimal(0)) + cost
        billing_event_count += 1
        if matched:
            matched_cost_values[currency] = matched_cost_values.get(currency, Decimal(0)) + cost
            matched_billing_event_count += 1
    last_sync = await session.scalar(
        select(ProviderSyncRun)
        .where(ProviderSyncRun.provider == provider)
        .order_by(ProviderSyncRun.started_at.desc(), ProviderSyncRun.id.desc())
        .limit(1)
    )
    exact_costs = {currency: _decimal(total) for currency, total in exact_cost_values.items()}
    matched_exact_costs = {
        currency: _decimal(matched_cost_values.get(currency, Decimal(0))) for currency in exact_cost_values
    }
    unbilled_success_count = int(
        await session.scalar(
            select(func.count(ProviderInvocation.id)).where(
                ProviderInvocation.provider == provider,
                ProviderInvocation.status == 'succeeded',
                ProviderInvocation.created_at >= since_ms,
                ProviderInvocation.created_at < until_ms,
                ProviderInvocation.actual_cost_total.is_(None),
            )
        )
        or 0
    )
    return ProviderOverview(
        provider=provider,
        window_start_at=since_ms,
        window_end_at=until_ms,
        invocation_count=invocation_stats[0] or 0,
        success_count=invocation_stats[1] or 0,
        failed_count=invocation_stats[2] or 0,
        active_count=invocation_stats[3] or 0,
        average_duration_ms=float(invocation_stats[4]) if invocation_stats[4] is not None else None,
        provider_request_count=provider_request_stats[0] or 0,
        matched_provider_request_count=provider_request_stats[1] or 0,
        billing_event_count=billing_event_count,
        matched_billing_event_count=matched_billing_event_count,
        unbilled_success_count=unbilled_success_count,
        exact_costs=exact_costs,
        matched_exact_costs=matched_exact_costs,
        last_sync_status=last_sync.status if last_sync is not None else None,
        last_synced_at=last_sync.completed_at if last_sync is not None else None,
    )


async def list_provider_usage(session: AsyncSession, *, provider: str, since_ms: int, limit: int) -> ProviderUsageList:
    rows = (
        await session.scalars(
            select(ProviderUsageBucket)
            .where(ProviderUsageBucket.provider == provider, ProviderUsageBucket.bucket_start_at >= since_ms)
            .order_by(ProviderUsageBucket.bucket_start_at.desc(), ProviderUsageBucket.id.desc())
            .limit(limit)
        )
    ).all()
    return ProviderUsageList(
        items=tuple(
            ProviderUsageItem(
                provider=row.provider,
                provider_model_id=row.provider_model_id,
                timeframe=row.timeframe,
                bucket_start=row.bucket_start,
                api_key_id=row.api_key_id,
                unit=row.unit,
                quantity=row.quantity,
                unit_price=row.unit_price,
                percent_discount=row.percent_discount,
                cost_subtotal=row.cost_subtotal,
                cost_discount=row.cost_discount,
                cost_total=row.cost_total,
                currency=row.currency,
                synced_at=row.synced_at,
            )
            for row in rows
        )
    )


async def list_provider_billing_events(
    session: AsyncSession,
    *,
    provider: str,
    since_ms: int,
    limit: int,
) -> ProviderBillingEventList:
    matched_request_ids = _matched_request_ids(provider)
    rows = (
        await session.execute(
            select(
                ProviderBillingEvent,
                ProviderBillingEvent.provider_request_id.in_(matched_request_ids).label('matched_invocation'),
            )
            .where(
                ProviderBillingEvent.provider == provider,
                ProviderBillingEvent.event_at >= since_ms,
            )
            .order_by(ProviderBillingEvent.event_at.desc(), ProviderBillingEvent.id.desc())
            .limit(limit)
        )
    ).all()
    return ProviderBillingEventList(
        items=tuple(
            ProviderBillingEventItem(
                provider=row.provider,
                provider_request_id=row.provider_request_id,
                provider_model_id=row.provider_model_id,
                event_timestamp=row.event_timestamp,
                api_key_id=row.api_key_id,
                output_units=row.output_units,
                unit_price=row.unit_price,
                percent_discount=row.percent_discount,
                cost_subtotal=row.cost_subtotal,
                cost_discount=row.cost_discount,
                cost_total=row.cost_total,
                cost_nano_usd=row.cost_nano_usd,
                currency=row.currency,
                matched_invocation=matched,
                synced_at=row.synced_at,
            )
            for row, matched in rows
        )
    )


async def list_provider_requests(
    session: AsyncSession,
    *,
    provider: str,
    since_ms: int,
    limit: int,
) -> ProviderRequestRecordList:
    matched_request_ids = _matched_request_ids(provider)
    rows = (
        await session.execute(
            select(
                ProviderRequestRecord,
                ProviderRequestRecord.provider_request_id.in_(matched_request_ids).label('matched_invocation'),
            )
            .where(
                ProviderRequestRecord.provider == provider,
                ProviderRequestRecord.started_at >= since_ms,
            )
            .order_by(ProviderRequestRecord.started_at.desc(), ProviderRequestRecord.id.desc())
            .limit(limit)
        )
    ).all()
    return ProviderRequestRecordList(
        items=tuple(
            ProviderRequestRecordItem(
                provider=row.provider,
                provider_request_id=row.provider_request_id,
                provider_model_id=row.provider_model_id,
                sent_at=row.sent_at,
                started_at=row.started_at,
                ended_at=row.ended_at,
                status_code=row.status_code,
                duration_ms=row.duration_ms,
                matched_invocation=matched,
                synced_at=row.synced_at,
            )
            for row, matched in rows
        )
    )


async def list_provider_analytics(
    session: AsyncSession, *, provider: str, since_ms: int, limit: int
) -> ProviderAnalyticsList:
    rows = (
        await session.scalars(
            select(ProviderAnalyticsBucket)
            .where(
                ProviderAnalyticsBucket.provider == provider,
                ProviderAnalyticsBucket.bucket_start_at >= since_ms,
            )
            .order_by(ProviderAnalyticsBucket.bucket_start_at.desc(), ProviderAnalyticsBucket.id.desc())
            .limit(limit)
        )
    ).all()
    return ProviderAnalyticsList(
        items=tuple(
            ProviderAnalyticsItem(
                provider=row.provider,
                provider_model_id=row.provider_model_id,
                timeframe=row.timeframe,
                bucket_start=row.bucket_start,
                metrics=row.metrics_json,
                synced_at=row.synced_at,
            )
            for row in rows
        )
    )


__all__ = [
    'get_provider_overview',
    'list_provider_analytics',
    'list_provider_billing_events',
    'list_provider_prices',
    'list_provider_requests',
    'list_provider_usage',
]
