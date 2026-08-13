from __future__ import annotations

import datetime as dt
import hashlib
from decimal import Decimal
from time import time
from uuid import uuid4

from open_webui.models.config import Config
from sqlalchemy import case, delete, func, select, update
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
from .providers.fal_platform import (
    FalAnalyticsBucket,
    FalBillingEvent,
    FalPlatformClient,
    FalPlatformError,
    FalRequestRecord,
    FalUsageBucket,
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
    ProviderSyncForm,
    ProviderSyncResult,
    ProviderUsageItem,
    ProviderUsageList,
)

_PROVIDER = 'fal'


def _now_ms() -> int:
    return int(time() * 1000)


def _iso(epoch_ms: int) -> str:
    return dt.datetime.fromtimestamp(epoch_ms / 1000, tz=dt.UTC).isoformat().replace('+00:00', 'Z')


def _epoch_ms(value: str) -> int:
    return int(dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)


def _decimal(value: Decimal) -> str:
    return format(value, 'f')


def _stable_id(*parts: object) -> str:
    return hashlib.sha256('\0'.join('' if part is None else str(part) for part in parts).encode()).hexdigest()


def _relevant_endpoint_ids(
    local_endpoint_ids: tuple[str, ...],
    billing_events: tuple[FalBillingEvent, ...],
    usage: tuple[FalUsageBucket, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *local_endpoint_ids,
                *(event.endpoint_id for event in billing_events),
                *(item.endpoint_id for bucket in usage for item in bucket.results),
            )
        )
    )


async def _provider_call(resource: str, call):
    try:
        return await call()
    except FalPlatformError as error:
        raise FalPlatformError(
            f'{resource}_{error.code}'[:64],
            status_code=error.status_code,
        ) from error


def _sync_result(row: ProviderSyncRun) -> ProviderSyncResult:
    return ProviderSyncResult(
        id=row.id,
        provider=row.provider,
        status=row.status,
        resources=tuple(row.resources_json),
        counts=row.counts_json,
        error_code=row.error_code,
        window_start_at=row.window_start_at,
        window_end_at=row.window_end_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


async def _record_prices(session: AsyncSession, prices, synced_at: int) -> int:
    count = 0
    for price in prices:
        unit_price = _decimal(price.unit_price)
        existing = await session.scalar(
            select(ProviderPriceSnapshot).where(
                ProviderPriceSnapshot.provider == _PROVIDER,
                ProviderPriceSnapshot.provider_model_id == price.endpoint_id,
                ProviderPriceSnapshot.unit == price.unit,
                ProviderPriceSnapshot.currency == price.currency.upper(),
                ProviderPriceSnapshot.unit_price == unit_price,
            )
        )
        if existing is None:
            session.add(
                ProviderPriceSnapshot(
                    id=uuid4().hex,
                    provider=_PROVIDER,
                    provider_model_id=price.endpoint_id,
                    unit_price=unit_price,
                    unit=price.unit,
                    currency=price.currency.upper(),
                    first_seen_at=synced_at,
                    last_seen_at=synced_at,
                )
            )
        else:
            existing.last_seen_at = synced_at
        count += 1
    return count


def _usage_rows(buckets: tuple[FalUsageBucket, ...], timeframe: str, synced_at: int):
    for bucket in buckets:
        bucket_at = _epoch_ms(bucket.bucket)
        for item in bucket.results:
            api_key_id = item.auth_method_structured.api_key_id if item.auth_method_structured else None
            yield ProviderUsageBucket(
                id=_stable_id(
                    _PROVIDER,
                    item.endpoint_id,
                    timeframe,
                    bucket.bucket,
                    api_key_id,
                    item.unit,
                    item.unit_price,
                    item.percent_discount,
                    item.currency,
                ),
                provider=_PROVIDER,
                provider_model_id=item.endpoint_id,
                timeframe=timeframe,
                bucket_start=bucket.bucket,
                bucket_start_at=bucket_at,
                api_key_id=api_key_id,
                unit=item.unit,
                quantity=_decimal(item.quantity),
                unit_price=_decimal(item.unit_price),
                percent_discount=_decimal(item.percent_discount) if item.percent_discount is not None else None,
                cost_subtotal=_decimal(item.cost_subtotal),
                cost_discount=_decimal(item.cost_discount),
                cost_total=_decimal(item.cost_total),
                currency=item.currency.upper(),
                synced_at=synced_at,
            )


def _analytics_rows(buckets: tuple[FalAnalyticsBucket, ...], timeframe: str, synced_at: int):
    for bucket in buckets:
        bucket_at = _epoch_ms(bucket.bucket)
        for item in bucket.results:
            metrics = item.model_dump(exclude={'endpoint_id'}, exclude_none=True)
            yield ProviderAnalyticsBucket(
                id=_stable_id(_PROVIDER, item.endpoint_id, timeframe, bucket.bucket),
                provider=_PROVIDER,
                provider_model_id=item.endpoint_id,
                timeframe=timeframe,
                bucket_start=bucket.bucket,
                bucket_start_at=bucket_at,
                metrics_json=metrics,
                synced_at=synced_at,
            )


async def _record_billing_events(
    session: AsyncSession,
    events: tuple[FalBillingEvent, ...],
    synced_at: int,
) -> tuple[int, int]:
    matched = 0
    unique_events = {event.request_id: event for event in events}
    for event in unique_events.values():
        event_at = _epoch_ms(event.timestamp)
        api_key_id = event.auth_method_structured.api_key_id if event.auth_method_structured else None
        row = await session.scalar(
            select(ProviderBillingEvent).where(
                ProviderBillingEvent.provider == _PROVIDER,
                ProviderBillingEvent.provider_request_id == event.request_id,
            )
        )
        values = {
            'provider_model_id': event.endpoint_id,
            'event_timestamp': event.timestamp,
            'event_at': event_at,
            'api_key_id': api_key_id,
            'output_units': _decimal(event.output_units) if event.output_units is not None else None,
            'unit_price': _decimal(event.unit_price) if event.unit_price is not None else None,
            'percent_discount': _decimal(event.percent_discount) if event.percent_discount is not None else None,
            'cost_subtotal': _decimal(event.cost_subtotal),
            'cost_discount': _decimal(event.cost_discount),
            'cost_total': _decimal(event.cost_total),
            'cost_nano_usd': _decimal(event.cost_estimate_nano_usd),
            'currency': 'USD',
            'synced_at': synced_at,
        }
        if row is None:
            session.add(
                ProviderBillingEvent(
                    id=uuid4().hex,
                    provider=_PROVIDER,
                    provider_request_id=event.request_id,
                    **values,
                )
            )
        else:
            for field, value in values.items():
                setattr(row, field, value)
        result = await session.execute(
            update(ProviderInvocation)
            .where(
                ProviderInvocation.provider == _PROVIDER,
                ProviderInvocation.provider_request_id == event.request_id,
            )
            .values(
                actual_cost_total=_decimal(event.cost_total),
                actual_cost_currency='USD',
                cost_accuracy='exact',
                billing_event_at=event_at,
                updated_at=synced_at,
            )
        )
        matched += result.rowcount or 0
    return len(unique_events), matched


def _status_from_http(status_code: int | None) -> str | None:
    if status_code is None:
        return None
    return 'succeeded' if 200 <= status_code < 300 else 'failed'


async def _record_requests(
    session: AsyncSession,
    records: tuple[FalRequestRecord, ...],
    synced_at: int,
) -> tuple[int, int]:
    matched = 0
    unique_records = {record.request_id: record for record in records}
    for record in unique_records.values():
        sent_at = _epoch_ms(record.sent_at)
        started_at = _epoch_ms(record.started_at)
        ended_at = _epoch_ms(record.ended_at) if record.ended_at is not None else None
        duration_ms = int(record.duration * 1000) if record.duration is not None else None
        row = await session.scalar(
            select(ProviderRequestRecord).where(
                ProviderRequestRecord.provider == _PROVIDER,
                ProviderRequestRecord.provider_request_id == record.request_id,
            )
        )
        values = {
            'provider_model_id': record.endpoint_id,
            'sent_at': sent_at,
            'started_at': started_at,
            'ended_at': ended_at,
            'status_code': record.status_code,
            'duration_ms': duration_ms,
            'synced_at': synced_at,
        }
        if row is None:
            session.add(
                ProviderRequestRecord(
                    id=uuid4().hex,
                    provider=_PROVIDER,
                    provider_request_id=record.request_id,
                    **values,
                )
            )
        else:
            for field, value in values.items():
                setattr(row, field, value)

        invocation_values = {
            'submitted_at': sent_at,
            'provider_started_at': started_at,
            'provider_completed_at': ended_at,
            'status_code': record.status_code,
            'execution_duration_ms': duration_ms,
            'updated_at': synced_at,
        }
        status = _status_from_http(record.status_code)
        if status is not None:
            invocation_values['status'] = status
            if ended_at is not None:
                invocation_values['completed_at'] = ended_at
        result = await session.execute(
            update(ProviderInvocation)
            .where(
                ProviderInvocation.provider == _PROVIDER,
                ProviderInvocation.provider_request_id == record.request_id,
            )
            .values(**invocation_values)
        )
        matched += result.rowcount or 0
    return len(unique_records), matched


async def sync_fal_platform(session: AsyncSession, form: ProviderSyncForm) -> ProviderSyncResult:
    resources = tuple(dict.fromkeys(form.resources))
    now = _now_ms()
    window_start_at = now - form.window_hours * 60 * 60 * 1000
    run = ProviderSyncRun(
        id=uuid4().hex,
        provider=_PROVIDER,
        status='running',
        resources_json=list(resources),
        counts_json=None,
        error_code=None,
        window_start_at=window_start_at,
        window_end_at=now,
        started_at=now,
        completed_at=None,
    )
    run_id = run.id
    session.add(run)
    await session.commit()
    await session.refresh(run)

    try:
        keys = await Config.get_many('image_generation.fal.api_key', 'provider_ops.fal.admin_api_key')
        api_key = str(keys.get('image_generation.fal.api_key') or '')
        admin_api_key = str(keys.get('provider_ops.fal.admin_api_key') or '')
        api_client = (
            FalPlatformClient(api_key)
            if any(resource in resources for resource in ('pricing', 'requests', 'analytics'))
            else None
        )
        admin_client = (
            FalPlatformClient(admin_api_key)
            if any(resource in resources for resource in ('billing_events', 'usage'))
            else None
        )
        local_endpoint_ids = (
            await session.scalars(
                select(ProviderInvocation.provider_model_id).where(ProviderInvocation.provider == _PROVIDER).distinct()
            )
        ).all()
        counts: dict[str, int] = {}
        start = _iso(window_start_at)
        end = _iso(now)

        billing_events = (
            await _provider_call(
                'billing_events',
                lambda: admin_client.billing_events(start=start, end=end),
            )
            if admin_client is not None and 'billing_events' in resources
            else ()
        )
        usage = (
            await _provider_call(
                'usage',
                lambda: admin_client.usage(start=start, end=end, timeframe=form.timeframe),
            )
            if admin_client is not None and 'usage' in resources
            else ()
        )
        endpoint_ids = _relevant_endpoint_ids(tuple(local_endpoint_ids), billing_events, usage)
        prices = (
            await _provider_call('pricing', lambda: api_client.prices(endpoint_ids))
            if api_client is not None and 'pricing' in resources
            else ()
        )
        requests = (
            await _provider_call(
                'requests',
                lambda: api_client.requests(endpoint_ids, start=start, end=end),
            )
            if api_client is not None and 'requests' in resources
            else ()
        )
        analytics = (
            await _provider_call(
                'analytics',
                lambda: api_client.analytics(endpoint_ids, start=start, end=end, timeframe=form.timeframe),
            )
            if api_client is not None and 'analytics' in resources
            else ()
        )

        synced_at = _now_ms()
        if 'pricing' in resources:
            counts['pricing'] = await _record_prices(session, prices, synced_at)
            counts['pricing_unavailable'] = max(0, len(endpoint_ids) - len(prices))
        if 'requests' in resources:
            counts['requests'], counts['requests_matched'] = await _record_requests(session, requests, synced_at)
        if 'billing_events' in resources:
            counts['billing_events'], counts['billing_events_matched'] = await _record_billing_events(
                session, billing_events, synced_at
            )
        if 'usage' in resources:
            await session.execute(
                delete(ProviderUsageBucket).where(
                    ProviderUsageBucket.provider == _PROVIDER,
                    ProviderUsageBucket.timeframe == form.timeframe,
                    ProviderUsageBucket.bucket_start_at >= window_start_at,
                    ProviderUsageBucket.bucket_start_at < now,
                )
            )
            usage_rows = tuple(_usage_rows(usage, form.timeframe, synced_at))
            session.add_all(usage_rows)
            counts['usage'] = len(usage_rows)
        if 'analytics' in resources:
            await session.execute(
                delete(ProviderAnalyticsBucket).where(
                    ProviderAnalyticsBucket.provider == _PROVIDER,
                    ProviderAnalyticsBucket.timeframe == form.timeframe,
                    ProviderAnalyticsBucket.bucket_start_at >= window_start_at,
                    ProviderAnalyticsBucket.bucket_start_at < now,
                )
            )
            analytics_rows = tuple(_analytics_rows(analytics, form.timeframe, synced_at))
            session.add_all(analytics_rows)
            counts['analytics'] = len(analytics_rows)
        run.status = 'succeeded'
        run.counts_json = counts
        run.completed_at = _now_ms()
        result = _sync_result(run)
        await session.commit()
        return result
    except Exception as error:
        await session.rollback()
        persisted = await session.get(ProviderSyncRun, run_id)
        if persisted is None:
            raise
        persisted.status = 'failed'
        persisted.error_code = (
            error.code[:64] if isinstance(error, FalPlatformError) else 'provider_platform_sync_failed'
        )
        persisted.completed_at = _now_ms()
        result = _sync_result(persisted)
        await session.commit()
        return result


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

    matched_request_ids = select(ProviderInvocation.provider_request_id).where(
        ProviderInvocation.provider == provider,
        ProviderInvocation.provider_request_id.is_not(None),
    )
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
    matched_request_ids = select(ProviderInvocation.provider_request_id).where(
        ProviderInvocation.provider == provider,
        ProviderInvocation.provider_request_id.is_not(None),
    )
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
    matched_request_ids = select(ProviderInvocation.provider_request_id).where(
        ProviderInvocation.provider == provider,
        ProviderInvocation.provider_request_id.is_not(None),
    )
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
    'list_provider_analytics',
    'list_provider_billing_events',
    'list_provider_prices',
    'list_provider_requests',
    'list_provider_usage',
    'get_provider_overview',
    'sync_fal_platform',
]
