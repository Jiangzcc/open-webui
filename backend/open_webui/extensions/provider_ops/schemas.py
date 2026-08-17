from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderInvocationStatus = Literal[
    'created', 'submitted', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown'
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class ProviderInvocationItem(StrictModel):
    id: str
    task_id: str | None
    user_id: str
    media_kind: Literal['image', 'video']
    provider: str
    provider_model_id: str
    attempt_no: int = Field(ge=1)
    provider_request_id: str | None
    provider_gateway_request_id: str | None
    status: ProviderInvocationStatus
    status_code: int | None
    queue_position: int | None
    provider_metrics: dict[str, object] | None
    error_code: str | None
    created_at: int
    submitted_at: int | None
    provider_started_at: int | None
    provider_completed_at: int | None
    completed_at: int | None
    execution_duration_ms: int | None
    actual_cost_total: str | None
    actual_cost_currency: str | None
    cost_accuracy: Literal['exact', 'estimated', 'allocated'] | None
    billing_event_at: int | None
    updated_at: int


class ProviderInvocationList(StrictModel):
    items: tuple[ProviderInvocationItem, ...]


class ProviderModelSummary(StrictModel):
    provider: str
    provider_model_id: str
    media_kind: Literal['image', 'video']
    request_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    cancelled_count: int = Field(ge=0)
    unknown_count: int = Field(ge=0)
    active_count: int = Field(ge=0)
    average_execution_duration_ms: float | None = Field(default=None, ge=0)
    last_invocation_at: int


class ProviderModelSummaryList(StrictModel):
    items: tuple[ProviderModelSummary, ...]


ProviderSyncResource = Literal['pricing', 'requests', 'billing_events', 'usage', 'analytics']
ProviderSyncTimeframe = Literal['minute', 'hour', 'day', 'week', 'month']


class ProviderSyncForm(StrictModel):
    resources: tuple[ProviderSyncResource, ...] = Field(
        default=('pricing', 'requests', 'billing_events', 'usage', 'analytics'), min_length=1
    )
    window_hours: int = Field(default=24, ge=1, le=24 * 90)
    timeframe: ProviderSyncTimeframe = 'hour'


class ProviderSyncResult(StrictModel):
    id: str
    provider: str
    status: Literal['running', 'succeeded', 'failed']
    resources: tuple[ProviderSyncResource, ...]
    counts: dict[str, int] | None
    error_code: str | None
    window_start_at: int
    window_end_at: int
    started_at: int
    completed_at: int | None


class ProviderPriceItem(StrictModel):
    provider: str
    provider_model_id: str
    unit_price: str
    unit: str
    currency: str
    first_seen_at: int
    last_seen_at: int


class ProviderPriceList(StrictModel):
    items: tuple[ProviderPriceItem, ...]


class ProviderUsageItem(StrictModel):
    provider: str
    provider_model_id: str
    timeframe: str
    bucket_start: str
    api_key_id: str | None
    unit: str
    quantity: str
    unit_price: str
    percent_discount: str | None
    cost_subtotal: str
    cost_discount: str
    cost_total: str
    currency: str
    synced_at: int


class ProviderUsageList(StrictModel):
    items: tuple[ProviderUsageItem, ...]


class ProviderBillingEventItem(StrictModel):
    provider: str
    provider_request_id: str
    provider_model_id: str
    event_timestamp: str
    api_key_id: str | None
    output_units: str | None
    unit_price: str | None
    percent_discount: str | None
    cost_subtotal: str
    cost_discount: str
    cost_total: str
    cost_nano_usd: str
    currency: str
    matched_invocation: bool
    synced_at: int


class ProviderBillingEventList(StrictModel):
    items: tuple[ProviderBillingEventItem, ...]


class ProviderRequestRecordItem(StrictModel):
    provider: str
    provider_request_id: str
    provider_model_id: str
    sent_at: int
    started_at: int
    ended_at: int | None
    status_code: int | None
    duration_ms: int | None
    matched_invocation: bool
    synced_at: int


class ProviderRequestRecordList(StrictModel):
    items: tuple[ProviderRequestRecordItem, ...]


class ProviderAnalyticsItem(StrictModel):
    provider: str
    provider_model_id: str
    timeframe: str
    bucket_start: str
    metrics: dict[str, int | float]
    synced_at: int


class ProviderAnalyticsList(StrictModel):
    items: tuple[ProviderAnalyticsItem, ...]


class ProviderOverview(StrictModel):
    provider: str
    window_start_at: int
    window_end_at: int
    invocation_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    active_count: int = Field(ge=0)
    average_duration_ms: float | None = Field(default=None, ge=0)
    provider_request_count: int = Field(ge=0)
    matched_provider_request_count: int = Field(ge=0)
    billing_event_count: int = Field(ge=0)
    matched_billing_event_count: int = Field(ge=0)
    unbilled_success_count: int = Field(ge=0)
    exact_costs: dict[str, str]
    matched_exact_costs: dict[str, str]
    last_sync_status: Literal['running', 'succeeded', 'failed'] | None
    last_synced_at: int | None


class VideoRuntimeStatus(StrictModel):
    engine: Literal['mock', 'fal', 'invalid']
    fal_api_key_configured: bool
    allowed_models: tuple[str, ...]
    max_credits_per_request: int | None = Field(default=None, ge=1)
    delivery_max_attempts: int = Field(ge=1)
    result_max_bytes: int = Field(ge=1)
    active_task_count: int = Field(ge=0)
    configuration_error: str | None


__all__ = [
    'ProviderInvocationItem',
    'ProviderInvocationList',
    'ProviderInvocationStatus',
    'ProviderAnalyticsItem',
    'ProviderAnalyticsList',
    'ProviderBillingEventItem',
    'ProviderBillingEventList',
    'ProviderModelSummary',
    'ProviderModelSummaryList',
    'ProviderOverview',
    'ProviderPriceItem',
    'ProviderPriceList',
    'ProviderRequestRecordItem',
    'ProviderRequestRecordList',
    'ProviderSyncForm',
    'ProviderSyncResource',
    'ProviderSyncResult',
    'ProviderSyncTimeframe',
    'ProviderUsageItem',
    'ProviderUsageList',
    'VideoRuntimeStatus',
]
