from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import logging
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
                if not (result.rowcount or 0):
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Failed to update provider sync heartbeat for run %s', run_id)


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


async def _record_billing_events(
    session: AsyncSession,
    events: tuple[FalBillingEvent, ...],
    synced_at: int,
) -> tuple[int, int]:
    unique_events = {event.request_id: event for event in events}
    if not unique_events:
        return 0, 0

    matched = 0
    for batch in _batches(tuple(unique_events.items())):
        request_ids = tuple(request_id for request_id, _event in batch)
        existing_rows = (
            await session.scalars(
                select(ProviderBillingEvent).where(
                    ProviderBillingEvent.provider == _PROVIDER,
                    ProviderBillingEvent.provider_request_id.in_(request_ids),
                )
            )
        ).all()
        existing_map = {row.provider_request_id: row for row in existing_rows}
        cost_whens: list[tuple[object, str]] = []
        event_at_whens: list[tuple[object, int]] = []

        for request_id, event in batch:
            event_at = _epoch_ms(event.timestamp)
            api_key_id = event.auth_method_structured.api_key_id if event.auth_method_structured else None
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
            row = existing_map.get(request_id)
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

            cond = ProviderInvocation.provider_request_id == request_id
            cost_whens.append((cond, _decimal(event.cost_total)))
            event_at_whens.append((cond, event_at))

        result = await session.execute(
            update(ProviderInvocation)
            .where(
                ProviderInvocation.provider == _PROVIDER,
                ProviderInvocation.provider_request_id.in_(request_ids),
            )
            .values(
                actual_cost_total=case(*cost_whens, else_=ProviderInvocation.actual_cost_total),
                actual_cost_currency='USD',
                cost_accuracy='exact',
                billing_event_at=case(*event_at_whens, else_=ProviderInvocation.billing_event_at),
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
    unique_records = {record.request_id: record for record in records}
    if not unique_records:
        return 0, 0

    matched = 0
    for batch in _batches(tuple(unique_records.items())):
        request_ids = tuple(request_id for request_id, _record in batch)
        existing_rows = (
            await session.scalars(
                select(ProviderRequestRecord).where(
                    ProviderRequestRecord.provider == _PROVIDER,
                    ProviderRequestRecord.provider_request_id.in_(request_ids),
                )
            )
        ).all()
        existing_map = {row.provider_request_id: row for row in existing_rows}
        submitted_whens: list[tuple[object, int]] = []
        started_whens: list[tuple[object, int]] = []
        completed_whens: list[tuple[object, int | None]] = []
        status_code_whens: list[tuple[object, int | None]] = []
        duration_whens: list[tuple[object, int | None]] = []
        status_whens: list[tuple[object, str]] = []
        inv_completed_whens: list[tuple[object, int]] = []

        for request_id, record in batch:
            sent_at = _epoch_ms(record.sent_at)
            started_at = _epoch_ms(record.started_at)
            ended_at = _epoch_ms(record.ended_at) if record.ended_at is not None else None
            duration_ms = int(record.duration * 1000) if record.duration is not None else None
            status = _status_from_http(record.status_code)
            values = {
                'provider_model_id': record.endpoint_id,
                'sent_at': sent_at,
                'started_at': started_at,
                'ended_at': ended_at,
                'status_code': record.status_code,
                'duration_ms': duration_ms,
                'synced_at': synced_at,
            }
            row = existing_map.get(request_id)
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

            cond = ProviderInvocation.provider_request_id == request_id
            submitted_whens.append((cond, sent_at))
            started_whens.append((cond, started_at))
            completed_whens.append((cond, ended_at))
            status_code_whens.append((cond, record.status_code))
            duration_whens.append((cond, duration_ms))
            if status is not None:
                status_whens.append((cond, status))
                if ended_at is not None:
                    inv_completed_whens.append((cond, ended_at))

        update_values: dict[str, object] = {
            'submitted_at': case(*submitted_whens, else_=ProviderInvocation.submitted_at),
            'provider_started_at': case(*started_whens, else_=ProviderInvocation.provider_started_at),
            'provider_completed_at': case(*completed_whens, else_=ProviderInvocation.provider_completed_at),
            'status_code': case(*status_code_whens, else_=ProviderInvocation.status_code),
            'execution_duration_ms': case(*duration_whens, else_=ProviderInvocation.execution_duration_ms),
            'updated_at': synced_at,
        }
        if status_whens:
            update_values['status'] = case(*status_whens, else_=ProviderInvocation.status)
        if inv_completed_whens:
            update_values['completed_at'] = case(*inv_completed_whens, else_=ProviderInvocation.completed_at)

        result = await session.execute(
            update(ProviderInvocation)
            .where(
                ProviderInvocation.provider == _PROVIDER,
                ProviderInvocation.provider_request_id.in_(request_ids),
            )
            .values(**update_values)
        )
        matched += result.rowcount or 0
    return len(unique_records), matched


async def sync_fal_platform(session: AsyncSession, form: ProviderSyncForm) -> ProviderSyncResult:
    # 僵尸运行清理：以最近心跳（旧数据回退到 started_at）判断，避免把正常执行超过
    # 两小时的长同步误标为失败，同时允许崩溃后未清理的 running 行自动恢复。
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
        heartbeat_at=now,
        completed_at=None,
    )
    run_id = run.id
    session.add(run)
    try:
        # ux_ext_provider_sync_run_running 在数据库层保证同一 provider 只有一个
        # running 行，消除“先查询、后插入”之间的并发竞态。
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
    heartbeat_task = (
        asyncio.create_task(_heartbeat_sync_run(session.bind, run_id)) if session.bind is not None else None
    )

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

        # 复盘 P2：五个 provider API 是纯网络往返，原先串行 await。
        # 依赖关系分两层：billing/usage 互相独立；endpoint_ids 由二者派生，
        # prices/requests/analytics 再依赖 endpoint_ids 且互相独立——
        # 各层内部 gather 并发，层间保持依赖。
        billing_events, usage = await asyncio.gather(
            _call_or_skip('billing_events', lambda: admin_client.billing_events(start=start, end=end), admin_client, resources),
            _call_or_skip(
                'usage', lambda: admin_client.usage(start=start, end=end, timeframe=form.timeframe), admin_client, resources
            ),
        )
        endpoint_ids = _relevant_endpoint_ids(tuple(local_endpoint_ids), billing_events, usage)
        prices, requests, analytics = await asyncio.gather(
            _call_or_skip('pricing', lambda: api_client.prices(endpoint_ids), api_client, resources),
            _call_or_skip('requests', lambda: api_client.requests(endpoint_ids, start=start, end=end), api_client, resources),
            _call_or_skip(
                'analytics',
                lambda: api_client.analytics(endpoint_ids, start=start, end=end, timeframe=form.timeframe),
                api_client,
                resources,
            ),
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
    finally:
        await _stop_heartbeat(heartbeat_task)


__all__ = ['sync_fal_platform']
