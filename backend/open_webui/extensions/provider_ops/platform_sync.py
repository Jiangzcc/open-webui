from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import logging
from dataclasses import dataclass
from decimal import Decimal
from time import time
from uuid import uuid4

from fastapi import HTTPException
from open_webui.models.config import Config
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from .schemas import ProviderSyncForm, ProviderSyncResult

_PROVIDER = 'fal'
_SYNC_WRITE_BATCH_SIZE = 50
_SYNC_HEARTBEAT_INTERVAL_SECONDS = 60
# 心跳超过此阈值未更新的 running 行视为僵尸（进程崩溃后残留）。长时间同步会持续
# 更新 heartbeat_at，因此不会仅因 started_at 超过两小时而被误杀。
_SYNC_STALE_MS = 2 * 60 * 60 * 1000  # 2 小时
log = logging.getLogger(__name__)


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


def _batches(items: tuple, size: int | None = None):
    size = size or _SYNC_WRITE_BATCH_SIZE
    for offset in range(0, len(items), size):
        yield items[offset : offset + size]


async def _heartbeat_sync_run(bind, run_id: str) -> None:
    sessions = async_sessionmaker(bind, class_=AsyncSession, expire_on_commit=False)
    while True:
        await asyncio.sleep(_SYNC_HEARTBEAT_INTERVAL_SECONDS)
        try:
            if not await _write_sync_heartbeat(sessions, run_id):
                return
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Failed to update provider sync heartbeat for run %s', run_id)


async def _write_sync_heartbeat(sessions, run_id: str) -> bool:
    async with sessions() as heartbeat_session:
        result = await heartbeat_session.execute(
            update(ProviderSyncRun)
            .where(
                ProviderSyncRun.id == run_id,
                ProviderSyncRun.status == 'running',
            )
            .values(heartbeat_at=_now_ms())
        )
        await heartbeat_session.commit()
        return bool(result.rowcount or 0)


async def _stop_heartbeat(task: asyncio.Task[None] | None) -> None:
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


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


async def _skipped_resources() -> tuple:
    return ()


def _call_or_skip(resource: str, call, client, resources: tuple):
    """资源未勾选或对应客户端缺失时以空结果跳过，否则发起 provider 调用。"""
    if client is None or resource not in resources:
        return _skipped_resources()
    return _provider_call(resource, call)


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
    if not prices:
        return 0

    # 按 (endpoint_id, unit, currency, unit_price) 去重，避免 FAL API 返回重复价格
    # 导致 UniqueConstraint 违约（与 _record_billing_events/_record_requests 的去重模式一致）。
    unique_prices = {(p.endpoint_id, p.unit, p.currency.upper(), _decimal(p.unit_price)): p for p in prices}

    # 预处理每条价格的匹配键和字段值
    price_entries: list[tuple[object, str, str, str, str]] = []
    for price in unique_prices.values():
        unit_price = _decimal(price.unit_price)
        currency = price.currency.upper()
        price_entries.append((price, unit_price, currency, price.endpoint_id, price.unit))

    # 批量查出涉及端点的已存在价格快照，避免逐条 SELECT（N+1 → 1 查询）
    endpoint_ids = {entry[3] for entry in price_entries}
    existing_rows = (
        await session.scalars(
            select(ProviderPriceSnapshot).where(
                ProviderPriceSnapshot.provider == _PROVIDER,
                ProviderPriceSnapshot.provider_model_id.in_(endpoint_ids),
            )
        )
    ).all()
    existing_map = {(row.provider_model_id, row.unit, row.currency, row.unit_price): row for row in existing_rows}

    count = 0
    for price, unit_price, currency, endpoint_id, unit in price_entries:
        key = (endpoint_id, unit, currency, unit_price)
        row = existing_map.get(key)
        if row is None:
            session.add(
                ProviderPriceSnapshot(
                    id=uuid4().hex,
                    provider=_PROVIDER,
                    provider_model_id=endpoint_id,
                    unit_price=unit_price,
                    unit=unit,
                    currency=currency,
                    first_seen_at=synced_at,
                    last_seen_at=synced_at,
                )
            )
        else:
            row.last_seen_at = synced_at
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


def _billing_event_values(event: FalBillingEvent, synced_at: int) -> dict[str, object]:
    return {
        'provider_model_id': event.endpoint_id,
        'event_timestamp': event.timestamp,
        'event_at': _epoch_ms(event.timestamp),
        'api_key_id': event.auth_method_structured.api_key_id if event.auth_method_structured else None,
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


def _upsert_billing_event(
    session: AsyncSession,
    existing: dict[str, ProviderBillingEvent],
    request_id: str,
    event: FalBillingEvent,
    synced_at: int,
) -> tuple[object, str, int]:
    values = _billing_event_values(event, synced_at)
    row = existing.get(request_id)
    if row is None:
        session.add(
            ProviderBillingEvent(
                id=uuid4().hex,
                provider=_PROVIDER,
                provider_request_id=request_id,
                **values,
            )
        )
    else:
        for field, value in values.items():
            setattr(row, field, value)
    condition = ProviderInvocation.provider_request_id == request_id
    return condition, _decimal(event.cost_total), _epoch_ms(event.timestamp)


async def _record_billing_batch(
    session: AsyncSession,
    batch: tuple[tuple[str, FalBillingEvent], ...],
    synced_at: int,
) -> int:
    request_ids = tuple(request_id for request_id, _event in batch)
    rows = (
        await session.scalars(
            select(ProviderBillingEvent).where(
                ProviderBillingEvent.provider == _PROVIDER,
                ProviderBillingEvent.provider_request_id.in_(request_ids),
            )
        )
    ).all()
    existing = {row.provider_request_id: row for row in rows}
    updates = [_upsert_billing_event(session, existing, item[0], item[1], synced_at) for item in batch]
    result = await session.execute(
        update(ProviderInvocation)
        .where(
            ProviderInvocation.provider == _PROVIDER,
            ProviderInvocation.provider_request_id.in_(request_ids),
        )
        .values(
            actual_cost_total=case(
                *[(cond, cost) for cond, cost, _at in updates], else_=ProviderInvocation.actual_cost_total
            ),
            actual_cost_currency='USD',
            cost_accuracy='exact',
            billing_event_at=case(
                *[(cond, at) for cond, _cost, at in updates], else_=ProviderInvocation.billing_event_at
            ),
            updated_at=synced_at,
        )
    )
    return result.rowcount or 0


async def _record_billing_events(
    session: AsyncSession,
    events: tuple[FalBillingEvent, ...],
    synced_at: int,
) -> tuple[int, int]:
    unique_events = {event.request_id: event for event in events}
    matched = sum(
        [await _record_billing_batch(session, batch, synced_at) for batch in _batches(tuple(unique_events.items()))]
    )
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
    unique_records = {record.request_id: record for record in records}
    matched = sum(
        [await _record_request_batch(session, batch, synced_at) for batch in _batches(tuple(unique_records.items()))]
    )
    return len(unique_records), matched


@dataclass(frozen=True)
class _RequestInvocationUpdate:
    condition: object
    sent_at: int
    started_at: int
    ended_at: int | None
    status_code: int | None
    duration_ms: int | None
    status: str | None


def _upsert_request_record(
    session: AsyncSession,
    existing: dict[str, ProviderRequestRecord],
    request_id: str,
    record: FalRequestRecord,
    synced_at: int,
) -> _RequestInvocationUpdate:
    sent_at = _epoch_ms(record.sent_at)
    started_at = _epoch_ms(record.started_at)
    ended_at = _epoch_ms(record.ended_at) if record.ended_at is not None else None
    duration_ms = int(record.duration * 1000) if record.duration is not None else None
    values = {
        'provider_model_id': record.endpoint_id,
        'sent_at': sent_at,
        'started_at': started_at,
        'ended_at': ended_at,
        'status_code': record.status_code,
        'duration_ms': duration_ms,
        'synced_at': synced_at,
    }
    row = existing.get(request_id)
    if row is None:
        session.add(
            ProviderRequestRecord(
                id=uuid4().hex,
                provider=_PROVIDER,
                provider_request_id=request_id,
                **values,
            )
        )
    else:
        for field, value in values.items():
            setattr(row, field, value)
    return _RequestInvocationUpdate(
        ProviderInvocation.provider_request_id == request_id,
        sent_at,
        started_at,
        ended_at,
        record.status_code,
        duration_ms,
        _status_from_http(record.status_code),
    )


def _request_invocation_values(updates: list[_RequestInvocationUpdate], synced_at: int) -> dict[str, object]:
    values: dict[str, object] = {
        'submitted_at': case(*[(u.condition, u.sent_at) for u in updates], else_=ProviderInvocation.submitted_at),
        'provider_started_at': case(
            *[(u.condition, u.started_at) for u in updates], else_=ProviderInvocation.provider_started_at
        ),
        'provider_completed_at': case(
            *[(u.condition, u.ended_at) for u in updates], else_=ProviderInvocation.provider_completed_at
        ),
        'status_code': case(*[(u.condition, u.status_code) for u in updates], else_=ProviderInvocation.status_code),
        'execution_duration_ms': case(
            *[(u.condition, u.duration_ms) for u in updates], else_=ProviderInvocation.execution_duration_ms
        ),
        'updated_at': synced_at,
    }
    terminal = [(u.condition, u.status) for u in updates if u.status is not None]
    completed = [(u.condition, u.ended_at) for u in updates if u.status is not None and u.ended_at is not None]
    if terminal:
        values['status'] = case(*terminal, else_=ProviderInvocation.status)
    if completed:
        values['completed_at'] = case(*completed, else_=ProviderInvocation.completed_at)
    return values


async def _record_request_batch(
    session: AsyncSession,
    batch: tuple[tuple[str, FalRequestRecord], ...],
    synced_at: int,
) -> int:
    request_ids = tuple(request_id for request_id, _record in batch)
    rows = (
        await session.scalars(
            select(ProviderRequestRecord).where(
                ProviderRequestRecord.provider == _PROVIDER,
                ProviderRequestRecord.provider_request_id.in_(request_ids),
            )
        )
    ).all()
    existing = {row.provider_request_id: row for row in rows}
    updates = [_upsert_request_record(session, existing, item[0], item[1], synced_at) for item in batch]
    result = await session.execute(
        update(ProviderInvocation)
        .where(
            ProviderInvocation.provider == _PROVIDER,
            ProviderInvocation.provider_request_id.in_(request_ids),
        )
        .values(**_request_invocation_values(updates, synced_at))
    )
    return result.rowcount or 0


@dataclass(frozen=True)
class _FetchedPlatformData:
    endpoint_ids: tuple[str, ...]
    prices: tuple
    requests: tuple
    billing_events: tuple
    usage: tuple
    analytics: tuple


async def _clear_stale_sync_runs(session: AsyncSession) -> None:
    stale_cutoff = _now_ms() - _SYNC_STALE_MS
    await session.execute(
        update(ProviderSyncRun)
        .where(
            ProviderSyncRun.provider == _PROVIDER,
            ProviderSyncRun.status == 'running',
            func.coalesce(ProviderSyncRun.heartbeat_at, ProviderSyncRun.started_at) < stale_cutoff,
        )
        .values(
            status='failed',
            error_code='provider_sync_stale',
            completed_at=_now_ms(),
        )
    )
    await session.commit()


async def _start_sync_run(
    session: AsyncSession,
    resources: tuple[str, ...],
    *,
    window_start_at: int,
    now: int,
) -> ProviderSyncRun:
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
        heartbeat_at=now,
        completed_at=None,
    )
    session.add(run)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        running = await session.scalar(
            select(ProviderSyncRun)
            .where(
                ProviderSyncRun.provider == _PROVIDER,
                ProviderSyncRun.status == 'running',
            )
            .order_by(ProviderSyncRun.started_at.desc())
            .limit(1)
        )
        detail = 'Provider sync already in progress'
        if running is not None:
            detail += f' (run {running.id}, started at {running.started_at})'
        raise HTTPException(status_code=409, detail=detail) from error
    await session.refresh(run)
    return run


async def _fetch_platform_data(
    session: AsyncSession,
    form: ProviderSyncForm,
    resources: tuple[str, ...],
    *,
    window_start_at: int,
    now: int,
) -> _FetchedPlatformData:
    keys = await Config.get_many('image_generation.fal.api_key', 'provider_ops.fal.admin_api_key')
    api_key = str(keys.get('image_generation.fal.api_key') or '')
    admin_api_key = str(keys.get('provider_ops.fal.admin_api_key') or '')
    api_client = FalPlatformClient(api_key) if {'pricing', 'requests', 'analytics'} & set(resources) else None
    admin_client = FalPlatformClient(admin_api_key) if {'billing_events', 'usage'} & set(resources) else None
    local_ids = (
        await session.scalars(
            select(ProviderInvocation.provider_model_id).where(ProviderInvocation.provider == _PROVIDER).distinct()
        )
    ).all()
    start, end = _iso(window_start_at), _iso(now)
    billing_events, usage = await asyncio.gather(
        _call_or_skip(
            'billing_events', lambda: admin_client.billing_events(start=start, end=end), admin_client, resources
        ),
        _call_or_skip(
            'usage', lambda: admin_client.usage(start=start, end=end, timeframe=form.timeframe), admin_client, resources
        ),
    )
    endpoint_ids = _relevant_endpoint_ids(tuple(local_ids), billing_events, usage)
    prices, requests, analytics = await asyncio.gather(
        _call_or_skip('pricing', lambda: api_client.prices(endpoint_ids), api_client, resources),
        _call_or_skip(
            'requests', lambda: api_client.requests(endpoint_ids, start=start, end=end), api_client, resources
        ),
        _call_or_skip(
            'analytics',
            lambda: api_client.analytics(endpoint_ids, start=start, end=end, timeframe=form.timeframe),
            api_client,
            resources,
        ),
    )
    return _FetchedPlatformData(endpoint_ids, prices, requests, billing_events, usage, analytics)


async def _replace_usage_buckets(
    session: AsyncSession,
    rows: tuple[FalUsageBucket, ...],
    *,
    timeframe: str,
    window_start_at: int,
    now: int,
    synced_at: int,
) -> int:
    await session.execute(
        delete(ProviderUsageBucket).where(
            ProviderUsageBucket.provider == _PROVIDER,
            ProviderUsageBucket.timeframe == timeframe,
            ProviderUsageBucket.bucket_start_at >= window_start_at,
            ProviderUsageBucket.bucket_start_at < now,
        )
    )
    values = tuple(_usage_rows(rows, timeframe, synced_at))
    session.add_all(values)
    return len(values)


async def _replace_analytics_buckets(
    session: AsyncSession,
    rows: tuple[FalAnalyticsBucket, ...],
    *,
    timeframe: str,
    window_start_at: int,
    now: int,
    synced_at: int,
) -> int:
    await session.execute(
        delete(ProviderAnalyticsBucket).where(
            ProviderAnalyticsBucket.provider == _PROVIDER,
            ProviderAnalyticsBucket.timeframe == timeframe,
            ProviderAnalyticsBucket.bucket_start_at >= window_start_at,
            ProviderAnalyticsBucket.bucket_start_at < now,
        )
    )
    values = tuple(_analytics_rows(rows, timeframe, synced_at))
    session.add_all(values)
    return len(values)


async def _record_platform_data(
    session: AsyncSession,
    form: ProviderSyncForm,
    resources: tuple[str, ...],
    data: _FetchedPlatformData,
    *,
    window_start_at: int,
    now: int,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    synced_at = _now_ms()
    if 'pricing' in resources:
        counts['pricing'] = await _record_prices(session, data.prices, synced_at)
        counts['pricing_unavailable'] = max(0, len(data.endpoint_ids) - len(data.prices))
    if 'requests' in resources:
        counts['requests'], counts['requests_matched'] = await _record_requests(session, data.requests, synced_at)
    if 'billing_events' in resources:
        counts['billing_events'], counts['billing_events_matched'] = await _record_billing_events(
            session, data.billing_events, synced_at
        )
    if 'usage' in resources:
        counts['usage'] = await _replace_usage_buckets(
            session,
            data.usage,
            timeframe=form.timeframe,
            window_start_at=window_start_at,
            now=now,
            synced_at=synced_at,
        )
    if 'analytics' in resources:
        counts['analytics'] = await _replace_analytics_buckets(
            session,
            data.analytics,
            timeframe=form.timeframe,
            window_start_at=window_start_at,
            now=now,
            synced_at=synced_at,
        )
    return counts


async def _fail_sync_run(session: AsyncSession, run_id: str, error: Exception) -> ProviderSyncResult:
    await session.rollback()
    persisted = await session.get(ProviderSyncRun, run_id)
    if persisted is None:
        raise error
    persisted.status = 'failed'
    persisted.error_code = error.code[:64] if isinstance(error, FalPlatformError) else 'provider_platform_sync_failed'
    persisted.completed_at = _now_ms()
    result = _sync_result(persisted)
    await session.commit()
    return result


async def sync_fal_platform(session: AsyncSession, form: ProviderSyncForm) -> ProviderSyncResult:
    await _clear_stale_sync_runs(session)
    resources = tuple(dict.fromkeys(form.resources))
    now = _now_ms()
    window_start_at = now - form.window_hours * 60 * 60 * 1000
    run = await _start_sync_run(session, resources, window_start_at=window_start_at, now=now)
    heartbeat_task = (
        asyncio.create_task(_heartbeat_sync_run(session.bind, run.id)) if session.bind is not None else None
    )

    try:
        data = await _fetch_platform_data(session, form, resources, window_start_at=window_start_at, now=now)
        counts = await _record_platform_data(session, form, resources, data, window_start_at=window_start_at, now=now)
        run.status = 'succeeded'
        run.counts_json = counts
        run.completed_at = _now_ms()
        result = _sync_result(run)
        await session.commit()
        return result
    except Exception as error:
        return await _fail_sync_run(session, run.id, error)
    finally:
        await _stop_heartbeat(heartbeat_task)


__all__ = ['sync_fal_platform']
