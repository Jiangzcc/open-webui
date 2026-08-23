from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL
from open_webui.utils.session_pool import get_session
from pydantic import BaseModel, ConfigDict, Field, ValidationError

FAL_PLATFORM_BASE_URL = 'https://api.fal.ai/v1'
_MAX_ENDPOINTS_PER_REQUEST = 50
_MAX_PAGES = 100
_ANALYTICS_METRICS = (
    'request_count',
    'success_count',
    'user_error_count',
    'error_count',
    'p50_prepare_duration',
    'p75_prepare_duration',
    'p90_prepare_duration',
    'p95_prepare_duration',
    'p99_prepare_duration',
    'p25_duration',
    'p50_duration',
    'p75_duration',
    'p90_duration',
    'p95_duration',
    'p99_duration',
    'startup_error_count',
    'connection_error_count',
    'timeout_error_count',
    'runtime_error_count',
    'cold_boot_count',
    # p50/p75/p90_cold_boot_duration 已移除：FAL 平台对部分 endpoint
    # （如 fal-ai/kling-video/v3/pro/text-to-video）请求这三个分位数时
    # 服务端返回 500 server_error（2026-08-23 实测），导致整个 analytics
    # 同步失败回滚。cold_boot_count 保留冷启动监控；待 FAL 修复后可加回。
    'total_billable_duration',
)


class _ExternalModel(BaseModel):
    model_config = ConfigDict(extra='ignore', frozen=True)


class FalPrice(_ExternalModel):
    endpoint_id: str = Field(min_length=1, max_length=256)
    unit_price: Decimal = Field(ge=0, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=3, max_length=3)


class FalAuthMethod(_ExternalModel):
    detail: str
    api_key_id: str | None = None


class FalUsageItem(_ExternalModel):
    endpoint_id: str = Field(min_length=1, max_length=256)
    unit: str = Field(min_length=1, max_length=64)
    quantity: Decimal = Field(ge=0, allow_inf_nan=False)
    unit_price: Decimal = Field(ge=0, allow_inf_nan=False)
    percent_discount: Decimal | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    cost_subtotal: Decimal = Field(ge=0, allow_inf_nan=False)
    cost_discount: Decimal = Field(ge=0, allow_inf_nan=False)
    cost_total: Decimal = Field(ge=0, allow_inf_nan=False)
    currency: str = Field(min_length=3, max_length=3)
    auth_method_structured: FalAuthMethod | None = None


class FalAnalyticsItem(_ExternalModel):
    endpoint_id: str = Field(min_length=1, max_length=256)
    request_count: int | None = Field(default=None, ge=0)
    success_count: int | None = Field(default=None, ge=0)
    user_error_count: int | None = Field(default=None, ge=0)
    error_count: int | None = Field(default=None, ge=0)
    p50_prepare_duration: float | None = Field(default=None, ge=0)
    p75_prepare_duration: float | None = Field(default=None, ge=0)
    p90_prepare_duration: float | None = Field(default=None, ge=0)
    p95_prepare_duration: float | None = Field(default=None, ge=0)
    p99_prepare_duration: float | None = Field(default=None, ge=0)
    p25_duration: float | None = Field(default=None, ge=0)
    p50_duration: float | None = Field(default=None, ge=0)
    p75_duration: float | None = Field(default=None, ge=0)
    p90_duration: float | None = Field(default=None, ge=0)
    p95_duration: float | None = Field(default=None, ge=0)
    p99_duration: float | None = Field(default=None, ge=0)
    startup_error_count: int | None = Field(default=None, ge=0)
    connection_error_count: int | None = Field(default=None, ge=0)
    timeout_error_count: int | None = Field(default=None, ge=0)
    runtime_error_count: int | None = Field(default=None, ge=0)
    cold_boot_count: int | None = Field(default=None, ge=0)
    p50_cold_boot_duration: float | None = Field(default=None, ge=0)
    p75_cold_boot_duration: float | None = Field(default=None, ge=0)
    p90_cold_boot_duration: float | None = Field(default=None, ge=0)
    total_billable_duration: float | None = Field(default=None, ge=0)


class FalBillingEvent(_ExternalModel):
    request_id: str = Field(min_length=1, max_length=128)
    endpoint_id: str = Field(min_length=1, max_length=256)
    timestamp: str = Field(min_length=1, max_length=64)
    output_units: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    unit_price: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    percent_discount: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    cost_subtotal: Decimal = Field(ge=0, allow_inf_nan=False)
    cost_discount: Decimal = Field(ge=0, allow_inf_nan=False)
    cost_total: Decimal = Field(ge=0, allow_inf_nan=False)
    cost_estimate_nano_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    auth_method_structured: FalAuthMethod | None = None


class FalRequestRecord(_ExternalModel):
    request_id: str = Field(min_length=1, max_length=128)
    endpoint_id: str = Field(min_length=1, max_length=256)
    started_at: str = Field(min_length=1, max_length=64)
    sent_at: str = Field(min_length=1, max_length=64)
    ended_at: str | None = Field(default=None, max_length=64)
    status_code: int | None = Field(default=None, ge=100, le=599)
    duration: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)


class FalUsageBucket(_ExternalModel):
    bucket: str
    results: tuple[FalUsageItem, ...]


class FalAnalyticsBucket(_ExternalModel):
    bucket: str
    results: tuple[FalAnalyticsItem, ...]


class FalPriceResponse(_ExternalModel):
    prices: tuple[FalPrice, ...]


class FalUsageResponse(_ExternalModel):
    time_series: tuple[FalUsageBucket, ...] = ()
    next_cursor: str | None = None


class FalAnalyticsResponse(_ExternalModel):
    time_series: tuple[FalAnalyticsBucket, ...] = ()
    next_cursor: str | None = None


class FalBillingEventResponse(_ExternalModel):
    billing_events: tuple[FalBillingEvent, ...]
    next_cursor: str | None = None


class FalRequestResponse(_ExternalModel):
    items: tuple[FalRequestRecord, ...]
    next_cursor: str | None = None


class FalPlatformError(RuntimeError):
    def __init__(self, code: str, *, status_code: int | None = None):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def _chunks(values: tuple[str, ...], size: int) -> Iterable[tuple[str, ...]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


class FalPlatformClient:
    def __init__(self, api_key: str, base_url: str = FAL_PLATFORM_BASE_URL):
        if not api_key:
            raise FalPlatformError('provider_credentials_missing')
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')

    async def _get(self, path: str, params: list[tuple[str, str]]) -> dict[str, Any]:
        session = await get_session()
        async with session.get(
            f'{self._base_url}{path}',
            params=params,
            headers={'Authorization': f'Key {self._api_key}'},
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        ) as response:
            if response.status >= 400:
                code = f'provider_platform_http_{response.status}'
                try:
                    payload = await response.json(content_type=None)
                    error = payload.get('error') if isinstance(payload, dict) else None
                    candidate = error.get('type') if isinstance(error, dict) else None
                    if isinstance(candidate, str) and candidate:
                        code = candidate[:64]
                except Exception:
                    pass
                raise FalPlatformError(code, status_code=response.status)
            payload = await response.json(content_type=None)
        if not isinstance(payload, dict):
            raise FalPlatformError('provider_platform_invalid_response')
        return payload

    async def prices(self, endpoint_ids: tuple[str, ...]) -> tuple[FalPrice, ...]:
        prices: list[FalPrice] = []

        async def fetch_batch(endpoint_batch: tuple[str, ...]) -> None:
            try:
                payload = await self._get(
                    '/models/pricing',
                    [('endpoint_id', endpoint_id) for endpoint_id in endpoint_batch],
                )
            except FalPlatformError as error:
                # FAL rejects the whole request when one endpoint ID has no
                # pricing record. Split only 404 batches so valid catalog
                # endpoints can still be synchronized without hiding auth,
                # rate-limit, or server failures.
                if error.status_code != 404:
                    raise
                if len(endpoint_batch) == 1:
                    return
                midpoint = len(endpoint_batch) // 2
                await fetch_batch(endpoint_batch[:midpoint])
                await fetch_batch(endpoint_batch[midpoint:])
                return
            prices.extend(FalPriceResponse.model_validate(payload).prices)

        try:
            for endpoint_batch in _chunks(endpoint_ids, _MAX_ENDPOINTS_PER_REQUEST):
                await fetch_batch(endpoint_batch)
        except ValidationError as error:
            raise FalPlatformError('provider_platform_invalid_response') from error
        return tuple(prices)

    async def usage(
        self,
        *,
        start: str,
        end: str,
        timeframe: str,
    ) -> tuple[FalUsageBucket, ...]:
        params = [
            ('start', start),
            ('end', end),
            ('timeframe', timeframe),
            ('bound_to_timeframe', 'false'),
            ('expand', 'time_series'),
            ('expand', 'auth_method_structured'),
            ('limit', '50'),
        ]
        return await self._paginated_usage(params)

    async def billing_events(self, *, start: str, end: str) -> tuple[FalBillingEvent, ...]:
        params = [
            ('start', start),
            ('end', end),
            ('expand', 'auth_method_structured'),
            ('limit', '10000'),
        ]
        events: list[FalBillingEvent] = []
        cursor = None
        seen_cursors: set[str] = set()
        try:
            for _ in range(_MAX_PAGES):
                page_params = [*params, *(([('cursor', cursor)]) if cursor else [])]
                page = FalBillingEventResponse.model_validate(await self._get('/models/billing-events', page_params))
                events.extend(page.billing_events)
                cursor = page.next_cursor
                if not cursor:
                    return tuple(events)
                if cursor in seen_cursors:
                    raise FalPlatformError('provider_platform_cursor_loop')
                seen_cursors.add(cursor)
        except ValidationError as error:
            raise FalPlatformError('provider_platform_invalid_response') from error
        raise FalPlatformError('provider_platform_page_limit')

    async def requests(
        self,
        endpoint_ids: tuple[str, ...],
        *,
        start: str,
        end: str,
    ) -> tuple[FalRequestRecord, ...]:
        records: list[FalRequestRecord] = []
        try:
            for endpoint_batch in _chunks(endpoint_ids, _MAX_ENDPOINTS_PER_REQUEST):
                params = [
                    *[('endpoint_id', endpoint_id) for endpoint_id in endpoint_batch],
                    ('start', start),
                    ('end', end),
                    ('sort_by', 'ended_at'),
                    ('limit', '100'),
                ]
                cursor = None
                seen_cursors: set[str] = set()
                for _ in range(_MAX_PAGES):
                    page_params = [*params, *(([('cursor', cursor)]) if cursor else [])]
                    page = FalRequestResponse.model_validate(
                        await self._get('/models/requests/by-endpoint', page_params)
                    )
                    records.extend(page.items)
                    cursor = page.next_cursor
                    if not cursor:
                        break
                    if cursor in seen_cursors:
                        raise FalPlatformError('provider_platform_cursor_loop')
                    seen_cursors.add(cursor)
                else:
                    raise FalPlatformError('provider_platform_page_limit')
        except ValidationError as error:
            raise FalPlatformError('provider_platform_invalid_response') from error
        return tuple(records)

    async def _paginated_usage(self, params: list[tuple[str, str]]) -> tuple[FalUsageBucket, ...]:
        buckets: list[FalUsageBucket] = []
        cursor = None
        seen_cursors: set[str] = set()
        try:
            for _ in range(_MAX_PAGES):
                page_params = [*params, *(([('cursor', cursor)]) if cursor else [])]
                page = FalUsageResponse.model_validate(await self._get('/models/usage', page_params))
                buckets.extend(page.time_series)
                cursor = page.next_cursor
                if not cursor:
                    return tuple(buckets)
                if cursor in seen_cursors:
                    raise FalPlatformError('provider_platform_cursor_loop')
                seen_cursors.add(cursor)
        except ValidationError as error:
            raise FalPlatformError('provider_platform_invalid_response') from error
        raise FalPlatformError('provider_platform_page_limit')

    async def analytics(
        self,
        endpoint_ids: tuple[str, ...],
        *,
        start: str,
        end: str,
        timeframe: str,
    ) -> tuple[FalAnalyticsBucket, ...]:
        buckets: list[FalAnalyticsBucket] = []
        try:
            for endpoint_batch in _chunks(endpoint_ids, _MAX_ENDPOINTS_PER_REQUEST):
                params = [
                    *[('endpoint_id', endpoint_id) for endpoint_id in endpoint_batch],
                    ('start', start),
                    ('end', end),
                    ('timeframe', timeframe),
                    ('bound_to_timeframe', 'false'),
                    ('expand', 'time_series'),
                    *[('expand', metric) for metric in _ANALYTICS_METRICS],
                    ('limit', '50'),
                ]
                cursor = None
                seen_cursors: set[str] = set()
                for _ in range(_MAX_PAGES):
                    page_params = [*params, *(([('cursor', cursor)]) if cursor else [])]
                    page = FalAnalyticsResponse.model_validate(await self._get('/models/analytics', page_params))
                    buckets.extend(page.time_series)
                    cursor = page.next_cursor
                    if not cursor:
                        break
                    if cursor in seen_cursors:
                        raise FalPlatformError('provider_platform_cursor_loop')
                    seen_cursors.add(cursor)
                else:
                    raise FalPlatformError('provider_platform_page_limit')
        except ValidationError as error:
            raise FalPlatformError('provider_platform_invalid_response') from error
        return tuple(buckets)


__all__ = [
    'FAL_PLATFORM_BASE_URL',
    'FalAnalyticsBucket',
    'FalBillingEvent',
    'FalPlatformClient',
    'FalPlatformError',
    'FalPrice',
    'FalRequestRecord',
    'FalUsageBucket',
]
