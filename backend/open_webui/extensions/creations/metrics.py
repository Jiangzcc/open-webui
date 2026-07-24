from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from opentelemetry import metrics

_ALLOWED_ATTRIBUTE_KEYS = frozenset({'task', 'source'})

_VALID_TASKS = frozenset({'text-to-image', 'image-to-image'})
_VALID_SOURCES = frozenset({'web', 'api', 'chat', 'tool'})


class MetricSink(Protocol):
    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None: ...


def normalize_metric_attributes(attributes: Mapping[str, object]) -> dict[str, str]:
    """Keep creation metrics labels bounded to the approved non-sensitive vocabulary."""
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
    """Lazily create OTel counters so tests can replace the complete sink."""

    def __init__(self, meter: object | None = None) -> None:
        self._meter = meter or metrics.get_meter(__name__)
        self._counters: dict[str, object] = {}

    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(name, unit='1')
            self._counters[name] = counter
        counter.add(value, attributes=dict(attributes))


class CreationMetrics:
    """Best-effort creation telemetry that never alters a capture outcome."""

    def __init__(self, sink: MetricSink) -> None:
        self._sink = sink

    def _add(self, name: str, value: float = 1, *, task: str | None, source: str | None) -> None:
        if task is not None and task not in _VALID_TASKS:
            task = None
        if source is not None and source not in _VALID_SOURCES:
            source = None
        try:
            self._sink.add(name, value, normalize_metric_attributes({'task': task, 'source': source}))
        except Exception:
            pass

    def capture_succeeded(self, *, task: str, source: str, count: int) -> None:
        if count > 0:
            self._add('webui.creations.capture.succeeded', count, task=task, source=source)

    def capture_failed(self, *, task: str, source: str) -> None:
        self._add('webui.creations.capture.failed', task=task, source=source)

    def reference_capture_failed(self, *, task: str, source: str) -> None:
        self._add('webui.creations.capture.reference_failed', task=task, source=source)

    def missing_file(self, *, task: str, source: str) -> None:
        self._add('webui.creations.capture.missing_file', task=task, source=source)


creation_metrics = CreationMetrics(OpenTelemetryMetricSink())


__all__ = [
    'CreationMetrics',
    'MetricSink',
    'OpenTelemetryMetricSink',
    'creation_metrics',
    'normalize_metric_attributes',
]
