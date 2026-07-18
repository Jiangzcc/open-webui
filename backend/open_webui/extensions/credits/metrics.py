from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from opentelemetry import metrics

_ALLOWED_ATTRIBUTE_KEYS = frozenset({'model', 'action', 'channel', 'error_code'})
_USAGE_STATUSES = frozenset({'debited', 'invoking', 'succeeded', 'failed', 'unknown'})
_QUOTE_REJECTIONS = frozenset({'price_not_configured', 'price_rule_incomplete'})


class MetricSink(Protocol):
    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None: ...

    def record(self, name: str, value: float, attributes: Mapping[str, str]) -> None: ...


def normalize_metric_attributes(attributes: Mapping[str, object]) -> dict[str, str]:
    """Keep metrics labels bounded to the approved non-sensitive vocabulary."""
    return {
        key: value
        for key, raw_value in attributes.items()
        if key in _ALLOWED_ATTRIBUTE_KEYS
        and isinstance(raw_value, str)
        and raw_value
        and len(raw_value) <= 128
        and not any(ord(character) < 32 or ord(character) == 127 for character in raw_value)
        for value in (raw_value,)
    }


class OpenTelemetryMetricSink:
    """Lazily create OTel instruments so tests can replace the complete sink."""

    def __init__(self, meter: object | None = None) -> None:
        self._meter = meter or metrics.get_meter(__name__)
        self._counters: dict[str, object] = {}
        self._histograms: dict[str, object] = {}

    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(name, unit='1')
            self._counters[name] = counter
        counter.add(value, attributes=dict(attributes))

    def record(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        histogram = self._histograms.get(name)
        if histogram is None:
            histogram = self._meter.create_histogram(name, unit='credits')
            self._histograms[name] = histogram
        histogram.record(value, attributes=dict(attributes))


class CreditMetrics:
    """Best-effort credit telemetry that never alters an accounting outcome."""

    def __init__(self, sink: MetricSink) -> None:
        self._sink = sink

    def _add(self, name: str, value: float = 1, **attributes: object) -> None:
        try:
            self._sink.add(name, value, normalize_metric_attributes(attributes))
        except Exception:
            pass

    def _record(self, name: str, value: float, **attributes: object) -> None:
        try:
            self._sink.record(name, value, normalize_metric_attributes(attributes))
        except Exception:
            pass

    def quote_succeeded(self, *, model: str, action: str, charged_credits: int) -> None:
        self._add('webui.credits.quote.success', model=model, action=action)
        self._record('webui.credits.quote.charged_credits', charged_credits, model=model, action=action)

    def quote_rejected(self, *, model: str, action: str, error_code: str) -> None:
        metric = (
            f'webui.credits.quote.{error_code}' if error_code in _QUOTE_REJECTIONS else 'webui.credits.quote.rejected'
        )
        self._add(metric, model=model, action=action, error_code=error_code)

    def debit_succeeded(self, *, model: str, action: str, channel: str, charged_credits: int) -> None:
        self._add('webui.credits.debit.success', model=model, action=action, channel=channel)
        self._record(
            'webui.credits.debit.charged_credits',
            charged_credits,
            model=model,
            action=action,
            channel=channel,
        )

    def debit_insufficient(self, *, model: str, action: str, channel: str) -> None:
        self._add('webui.credits.debit.insufficient', model=model, action=action, channel=channel)

    def idempotency_hit(self, *, model: str, action: str, channel: str) -> None:
        self._add('webui.credits.idempotency.hit', model=model, action=action, channel=channel)

    def idempotency_conflict(self, *, model: str, action: str, channel: str) -> None:
        self._add('webui.credits.idempotency.conflict', model=model, action=action, channel=channel)

    def usage_status(
        self,
        *,
        status: str,
        model: str | None = None,
        action: str | None = None,
        channel: str | None = None,
        count: int = 1,
    ) -> None:
        if status in _USAGE_STATUSES and count > 0:
            self._add(
                f'webui.credits.usage.{status}',
                count,
                model=model,
                action=action,
                channel=channel,
            )

    def long_pending(self, *, count: int) -> None:
        if count > 0:
            self._add('webui.credits.usage.long_pending', count)

    def admin_adjustment(self, *, amount: int) -> None:
        direction = 'increase' if amount > 0 else 'decrease'
        self._add(f'webui.credits.admin_adjustment.{direction}')
        self._record('webui.credits.admin_adjustment.amount', abs(amount))

    def consistency_anomaly(self) -> None:
        self._add('webui.credits.consistency.anomaly')

    def debit_failed(
        self,
        *,
        model: str,
        action: str,
        channel: str,
        error_code: str,
    ) -> None:
        if error_code == 'insufficient_credits':
            self.debit_insufficient(model=model, action=action, channel=channel)
            return
        self._add(
            'webui.credits.debit.rejected',
            model=model,
            action=action,
            channel=channel,
            error_code=error_code,
        )


credit_metrics = CreditMetrics(OpenTelemetryMetricSink())


__all__ = ['CreditMetrics', 'MetricSink', 'OpenTelemetryMetricSink', 'credit_metrics', 'normalize_metric_attributes']
