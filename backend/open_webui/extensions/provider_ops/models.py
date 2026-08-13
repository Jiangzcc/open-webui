from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, Column, Index, Integer, String, UniqueConstraint

from .db import JSONField, ProviderOpsBase


class ProviderInvocation(ProviderOpsBase):
    """One provider call made for a local generation task.

    A task may own multiple rows when it retries or falls back to another
    provider. Provider-specific payloads stay out of the task tables.
    """

    __tablename__ = 'ext_provider_invocation'
    __table_args__ = (
        UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_invocation_request'),
        CheckConstraint("media_kind IN ('image', 'video')", name='ck_ext_provider_invocation_media_kind'),
        CheckConstraint(
            "status IN ('created', 'submitted', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown')",
            name='ck_ext_provider_invocation_status',
        ),
        CheckConstraint('attempt_no >= 1', name='ck_ext_provider_invocation_attempt'),
        CheckConstraint(
            'queue_position IS NULL OR queue_position >= 0',
            name='ck_ext_provider_invocation_queue_position',
        ),
        CheckConstraint(
            'execution_duration_ms IS NULL OR execution_duration_ms >= 0',
            name='ck_ext_provider_invocation_execution_duration',
        ),
        Index('ix_ext_provider_invocation_task', 'task_id', 'created_at', 'id'),
        Index('ix_ext_provider_invocation_provider_created', 'provider', 'created_at', 'id'),
        Index('ix_ext_provider_invocation_model_created', 'provider_model_id', 'created_at', 'id'),
        Index('ix_ext_provider_invocation_status_updated', 'status', 'updated_at', 'id'),
    )

    id = Column(String(128), primary_key=True)
    task_id = Column(String(128), nullable=True)
    user_id = Column(String(128), nullable=False)
    media_kind = Column(String(16), nullable=False)
    provider = Column(String(64), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    attempt_no = Column(Integer, nullable=False, server_default='1')
    provider_request_id = Column(String(128), nullable=True)
    provider_gateway_request_id = Column(String(128), nullable=True)
    status = Column(String(16), nullable=False)
    status_code = Column(Integer, nullable=True)
    queue_position = Column(Integer, nullable=True)
    input_sha256 = Column(String(64), nullable=False)
    provider_metrics_json = Column(JSONField, nullable=True)
    error_code = Column(String(64), nullable=True)
    error_snapshot_json = Column(JSONField, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    submitted_at = Column(BigInteger, nullable=True)
    provider_started_at = Column(BigInteger, nullable=True)
    provider_completed_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)
    execution_duration_ms = Column(BigInteger, nullable=True)
    actual_cost_total = Column(String(64), nullable=True)
    actual_cost_currency = Column(String(3), nullable=True)
    cost_accuracy = Column(String(16), nullable=True)
    billing_event_at = Column(BigInteger, nullable=True)
    updated_at = Column(BigInteger, nullable=False)


class ProviderPriceSnapshot(ProviderOpsBase):
    __tablename__ = 'ext_provider_price_snapshot'
    __table_args__ = (
        UniqueConstraint(
            'provider',
            'provider_model_id',
            'unit',
            'currency',
            'unit_price',
            name='uq_ext_provider_price_value',
        ),
        Index(
            'ix_ext_provider_price_model_seen',
            'provider',
            'provider_model_id',
            'last_seen_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    unit_price = Column(String(64), nullable=False)
    unit = Column(String(64), nullable=False)
    currency = Column(String(3), nullable=False)
    first_seen_at = Column(BigInteger, nullable=False)
    last_seen_at = Column(BigInteger, nullable=False)


class ProviderUsageBucket(ProviderOpsBase):
    __tablename__ = 'ext_provider_usage_bucket'
    __table_args__ = (
        Index('ix_ext_provider_usage_bucket_time', 'provider', 'bucket_start_at', 'id'),
        Index(
            'ix_ext_provider_usage_model_time',
            'provider',
            'provider_model_id',
            'bucket_start_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    timeframe = Column(String(16), nullable=False)
    bucket_start = Column(String(64), nullable=False)
    bucket_start_at = Column(BigInteger, nullable=False)
    api_key_id = Column(String(128), nullable=True)
    unit = Column(String(64), nullable=False)
    quantity = Column(String(64), nullable=False)
    unit_price = Column(String(64), nullable=False)
    percent_discount = Column(String(64), nullable=True)
    cost_subtotal = Column(String(64), nullable=False)
    cost_discount = Column(String(64), nullable=False)
    cost_total = Column(String(64), nullable=False)
    currency = Column(String(3), nullable=False)
    synced_at = Column(BigInteger, nullable=False)


class ProviderBillingEvent(ProviderOpsBase):
    __tablename__ = 'ext_provider_billing_event'
    __table_args__ = (
        UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_billing_event_request'),
        Index('ix_ext_provider_billing_event_time', 'provider', 'event_at', 'id'),
        Index(
            'ix_ext_provider_billing_event_model_time',
            'provider',
            'provider_model_id',
            'event_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    provider_request_id = Column(String(128), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    event_timestamp = Column(String(64), nullable=False)
    event_at = Column(BigInteger, nullable=False)
    api_key_id = Column(String(128), nullable=True)
    output_units = Column(String(64), nullable=True)
    unit_price = Column(String(64), nullable=True)
    percent_discount = Column(String(64), nullable=True)
    cost_subtotal = Column(String(64), nullable=False)
    cost_discount = Column(String(64), nullable=False)
    cost_total = Column(String(64), nullable=False)
    cost_nano_usd = Column(String(64), nullable=False)
    currency = Column(String(3), nullable=False)
    synced_at = Column(BigInteger, nullable=False)


class ProviderRequestRecord(ProviderOpsBase):
    __tablename__ = 'ext_provider_request_record'
    __table_args__ = (
        UniqueConstraint('provider', 'provider_request_id', name='uq_ext_provider_request_record_request'),
        Index('ix_ext_provider_request_record_ended', 'provider', 'ended_at', 'id'),
        Index(
            'ix_ext_provider_request_record_model_ended',
            'provider',
            'provider_model_id',
            'ended_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    provider_request_id = Column(String(128), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    sent_at = Column(BigInteger, nullable=False)
    started_at = Column(BigInteger, nullable=False)
    ended_at = Column(BigInteger, nullable=True)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(BigInteger, nullable=True)
    synced_at = Column(BigInteger, nullable=False)


class ProviderAnalyticsBucket(ProviderOpsBase):
    __tablename__ = 'ext_provider_analytics_bucket'
    __table_args__ = (
        UniqueConstraint(
            'provider',
            'provider_model_id',
            'timeframe',
            'bucket_start',
            name='uq_ext_provider_analytics_bucket',
        ),
        Index('ix_ext_provider_analytics_bucket_time', 'provider', 'bucket_start_at', 'id'),
        Index(
            'ix_ext_provider_analytics_model_time',
            'provider',
            'provider_model_id',
            'bucket_start_at',
            'id',
        ),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    provider_model_id = Column(String(256), nullable=False)
    timeframe = Column(String(16), nullable=False)
    bucket_start = Column(String(64), nullable=False)
    bucket_start_at = Column(BigInteger, nullable=False)
    metrics_json = Column(JSONField, nullable=False)
    synced_at = Column(BigInteger, nullable=False)


class ProviderSyncRun(ProviderOpsBase):
    __tablename__ = 'ext_provider_sync_run'
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'failed')",
            name='ck_ext_provider_sync_run_status',
        ),
        Index('ix_ext_provider_sync_run_provider_started', 'provider', 'started_at', 'id'),
        Index('ix_ext_provider_sync_run_status_started', 'status', 'started_at', 'id'),
    )

    id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False)
    resources_json = Column(JSONField, nullable=False)
    counts_json = Column(JSONField, nullable=True)
    error_code = Column(String(64), nullable=True)
    window_start_at = Column(BigInteger, nullable=False)
    window_end_at = Column(BigInteger, nullable=False)
    started_at = Column(BigInteger, nullable=False)
    completed_at = Column(BigInteger, nullable=True)


__all__ = [
    'ProviderAnalyticsBucket',
    'ProviderBillingEvent',
    'ProviderInvocation',
    'ProviderPriceSnapshot',
    'ProviderRequestRecord',
    'ProviderSyncRun',
    'ProviderUsageBucket',
]
