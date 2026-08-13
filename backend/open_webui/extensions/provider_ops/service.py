from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from time import time
from uuid import uuid4

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .db import provider_ops_session
from .models import ProviderInvocation
from .schemas import ProviderInvocationItem, ProviderInvocationList, ProviderModelSummary, ProviderModelSummaryList

log = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time() * 1000)


def _input_hash(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str, ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def _safe_metrics(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    allowed = {}
    for key in ('inference_time',):
        metric = value.get(key)
        if isinstance(metric, int | float) and not isinstance(metric, bool) and metric >= 0:
            allowed[key] = metric
    return allowed or None


def _item(row: ProviderInvocation) -> ProviderInvocationItem:
    return ProviderInvocationItem(
        id=row.id,
        task_id=row.task_id,
        user_id=row.user_id,
        media_kind=row.media_kind,
        provider=row.provider,
        provider_model_id=row.provider_model_id,
        attempt_no=row.attempt_no,
        provider_request_id=row.provider_request_id,
        provider_gateway_request_id=row.provider_gateway_request_id,
        status=row.status,
        status_code=row.status_code,
        queue_position=row.queue_position,
        provider_metrics=row.provider_metrics_json,
        error_code=row.error_code,
        created_at=row.created_at,
        submitted_at=row.submitted_at,
        provider_started_at=row.provider_started_at,
        provider_completed_at=row.provider_completed_at,
        completed_at=row.completed_at,
        execution_duration_ms=row.execution_duration_ms,
        actual_cost_total=row.actual_cost_total,
        actual_cost_currency=row.actual_cost_currency,
        cost_accuracy=row.cost_accuracy,
        billing_event_at=row.billing_event_at,
        updated_at=row.updated_at,
    )


@dataclass
class DatabaseProviderInvocationObserver:
    invocation_id: str
    _last_provider_status: str | None = None
    _last_queue_position: int | None = None

    async def _write(self, values: dict[str, object]) -> bool:
        values['updated_at'] = _now_ms()
        try:
            async with provider_ops_session() as session:
                await session.execute(
                    update(ProviderInvocation).where(ProviderInvocation.id == self.invocation_id).values(**values)
                )
                await session.commit()
            return True
        except Exception:
            # Telemetry must never turn a successful provider call into a failed
            # user generation. The exception remains visible to operators.
            log.exception('Failed to update provider invocation %s', self.invocation_id)
            return False

    async def submitted(self, payload: dict[str, object]) -> None:
        now = _now_ms()
        queue_position = payload.get('queue_position')
        changed = await self._write(
            {
                'status': 'submitted',
                'provider_request_id': _short_string(payload.get('request_id'), 128),
                'provider_gateway_request_id': _short_string(payload.get('gateway_request_id'), 128),
                'queue_position': queue_position if isinstance(queue_position, int) and queue_position >= 0 else None,
                'submitted_at': now,
            }
        )
        if changed and isinstance(queue_position, int) and queue_position >= 0:
            self._last_queue_position = queue_position

    async def status(self, payload: dict[str, object]) -> None:
        provider_status = payload.get('status')
        status = {'IN_QUEUE': 'queued', 'IN_PROGRESS': 'running', 'COMPLETED': 'running'}.get(provider_status)
        if status is None:
            return
        queue_position = payload.get('queue_position')
        normalized_position = queue_position if isinstance(queue_position, int) and queue_position >= 0 else None
        if provider_status == self._last_provider_status and normalized_position == self._last_queue_position:
            return
        now = _now_ms()
        values: dict[str, object] = {'status': status}
        if normalized_position is not None:
            values['queue_position'] = normalized_position
        if status == 'running':
            values['provider_started_at'] = func.coalesce(ProviderInvocation.provider_started_at, now)
        if provider_status == 'COMPLETED':
            values['provider_completed_at'] = func.coalesce(ProviderInvocation.provider_completed_at, now)
            metrics = _safe_metrics(payload.get('metrics'))
            if metrics is not None:
                values['provider_metrics_json'] = metrics
                inference_time = metrics.get('inference_time')
                if isinstance(inference_time, int | float):
                    values['execution_duration_ms'] = round(inference_time * 1000)
        changed = await self._write(values)
        if changed:
            self._last_provider_status = provider_status
            if normalized_position is not None:
                self._last_queue_position = normalized_position

    async def succeeded(self) -> None:
        await self._write({'status': 'succeeded', 'completed_at': _now_ms(), 'error_code': None})

    async def failed(self, error: BaseException) -> None:
        client_cancelled = isinstance(error, asyncio.CancelledError)
        provider_cancelled = not client_cancelled and 'cancelled' in str(error).lower()
        status = 'unknown' if client_cancelled else ('cancelled' if provider_cancelled else 'failed')
        await self._write(
            {
                'status': status,
                'status_code': getattr(error, 'status_code', None),
                'completed_at': _now_ms(),
                'error_code': (
                    'client_cancelled'
                    if client_cancelled
                    else ('provider_cancelled' if provider_cancelled else _provider_error_code(error))
                ),
                # Provider messages can echo prompts or signed asset URLs. Keep
                # the diagnostic class but never persist the raw message here.
                'error_snapshot_json': {'type': type(error).__name__},
            }
        )


def _short_string(value: object, length: int) -> str | None:
    return value[:length] if isinstance(value, str) and value else None


def _provider_error_code(error: BaseException) -> str:
    code = getattr(error, 'code', None)
    if isinstance(code, str) and code:
        return code[:64]
    return 'provider_failed'


async def try_start_provider_invocation(
    *,
    task_id: str | None,
    user_id: str,
    media_kind: str,
    provider: str,
    provider_model_id: str,
    payload: dict[str, object],
) -> DatabaseProviderInvocationObserver | None:
    now = _now_ms()
    row = ProviderInvocation(
        id=uuid4().hex,
        task_id=task_id,
        user_id=user_id,
        media_kind=media_kind,
        provider=provider,
        provider_model_id=provider_model_id,
        attempt_no=1,
        status='created',
        input_sha256=_input_hash(payload),
        created_at=now,
        updated_at=now,
    )
    try:
        async with provider_ops_session() as session:
            session.add(row)
            await session.commit()
    except Exception:
        log.exception('Failed to create provider invocation for %s', provider_model_id)
        return None
    return DatabaseProviderInvocationObserver(row.id)


async def list_provider_invocations(
    session: AsyncSession,
    *,
    limit: int,
    provider: str | None = None,
    status: str | None = None,
    task_id: str | None = None,
    provider_model_id: str | None = None,
    provider_request_id: str | None = None,
) -> ProviderInvocationList:
    query = select(ProviderInvocation)
    if provider:
        query = query.where(ProviderInvocation.provider == provider)
    if status:
        query = query.where(ProviderInvocation.status == status)
    if task_id:
        query = query.where(ProviderInvocation.task_id == task_id)
    if provider_model_id:
        query = query.where(ProviderInvocation.provider_model_id == provider_model_id)
    if provider_request_id:
        query = query.where(ProviderInvocation.provider_request_id == provider_request_id)
    ordered = query.order_by(ProviderInvocation.created_at.desc(), ProviderInvocation.id.desc()).limit(limit)
    rows = (await session.scalars(ordered)).all()
    return ProviderInvocationList(items=tuple(_item(row) for row in rows))


async def summarize_provider_models(
    session: AsyncSession,
    *,
    since_ms: int,
    provider: str | None = None,
) -> ProviderModelSummaryList:
    query = (
        select(
            ProviderInvocation.provider,
            ProviderInvocation.provider_model_id,
            ProviderInvocation.media_kind,
            func.count().label('request_count'),
            func.sum(case((ProviderInvocation.status == 'succeeded', 1), else_=0)).label('success_count'),
            func.sum(case((ProviderInvocation.status == 'failed', 1), else_=0)).label('failed_count'),
            func.sum(case((ProviderInvocation.status == 'cancelled', 1), else_=0)).label('cancelled_count'),
            func.sum(case((ProviderInvocation.status == 'unknown', 1), else_=0)).label('unknown_count'),
            func.sum(
                case(
                    (ProviderInvocation.status.in_(('created', 'submitted', 'queued', 'running')), 1),
                    else_=0,
                )
            ).label('active_count'),
            func.avg(ProviderInvocation.execution_duration_ms).label('average_execution_duration_ms'),
            func.max(ProviderInvocation.created_at).label('last_invocation_at'),
        )
        .where(ProviderInvocation.created_at >= since_ms)
        .group_by(
            ProviderInvocation.provider,
            ProviderInvocation.provider_model_id,
            ProviderInvocation.media_kind,
        )
        .order_by(func.count().desc(), ProviderInvocation.provider, ProviderInvocation.provider_model_id)
    )
    if provider:
        query = query.where(ProviderInvocation.provider == provider)
    rows = (await session.execute(query)).all()
    return ProviderModelSummaryList(
        items=tuple(
            ProviderModelSummary(
                provider=row.provider,
                provider_model_id=row.provider_model_id,
                media_kind=row.media_kind,
                request_count=row.request_count,
                success_count=row.success_count,
                failed_count=row.failed_count,
                cancelled_count=row.cancelled_count,
                unknown_count=row.unknown_count,
                active_count=row.active_count,
                average_execution_duration_ms=row.average_execution_duration_ms,
                last_invocation_at=row.last_invocation_at,
            )
            for row in rows
        )
    )


__all__ = [
    'DatabaseProviderInvocationObserver',
    'list_provider_invocations',
    'summarize_provider_models',
    'try_start_provider_invocation',
]
