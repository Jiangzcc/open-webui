from __future__ import annotations

from open_webui.extensions.metrics_support import (
    MetricSink,
    OpenTelemetryMetricSink,
    build_attribute_normalizer,
)

_ALLOWED_ATTRIBUTE_KEYS = frozenset({'task', 'source'})

_VALID_TASKS = frozenset({'text-to-image', 'image-to-image'})
_VALID_SOURCES = frozenset({'web', 'api', 'chat', 'tool'})

# 复盘 P2：标签过滤/OTel sink 与 credits 逐字重复——收敛至 metrics_support。
normalize_metric_attributes = build_attribute_normalizer(_ALLOWED_ATTRIBUTE_KEYS)


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


creation_metrics = CreationMetrics(OpenTelemetryMetricSink(meter_name=__name__))


__all__ = [
    'CreationMetrics',
    'MetricSink',
    'OpenTelemetryMetricSink',
    'creation_metrics',
    'normalize_metric_attributes',
]
