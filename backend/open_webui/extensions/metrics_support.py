from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from opentelemetry import metrics

_MAX_ATTRIBUTE_VALUE_LENGTH = 128


class MetricSink(Protocol):
    """计数与直方图遥测的落点协议；实现必须自行吞掉异常。"""

    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None: ...

    def record(self, name: str, value: float, attributes: Mapping[str, str]) -> None: ...


def build_attribute_normalizer(allowed_keys: frozenset[str]):
    """复盘 P2：creations/credits 两份 metrics 基础设施逐字重复——收敛共享。

    allowed_keys 由各模块注入，标签词汇表仍各自治理。"""

    def normalize_metric_attributes(attributes: Mapping[str, object]) -> dict[str, str]:
        """Keep metrics labels bounded to the module-approved non-sensitive vocabulary."""
        return {
            key: value
            for key, raw_value in attributes.items()
            if key in allowed_keys
            and isinstance(raw_value, str)
            and raw_value
            and len(raw_value) <= _MAX_ATTRIBUTE_VALUE_LENGTH
            and not any(ord(character) < 32 or ord(character) == 127 for character in raw_value)
            for value in (raw_value,)
        }

    return normalize_metric_attributes


class OpenTelemetryMetricSink:
    """Lazily create OTel instruments so tests can replace the complete sink."""

    def __init__(
        self,
        meter: object | None = None,
        *,
        meter_name: str | None = None,
        histogram_unit: str = '1',
    ) -> None:
        # meter_name 保持调用方模块的 instrumentation scope 与合并前一致。
        self._meter = meter or metrics.get_meter(meter_name or __name__)
        self._counters: dict[str, object] = {}
        self._histograms: dict[str, object] = {}
        self._histogram_unit = histogram_unit

    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(name, unit='1')
            self._counters[name] = counter
        counter.add(value, attributes=dict(attributes))

    def record(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        histogram = self._histograms.get(name)
        if histogram is None:
            histogram = self._meter.create_histogram(name, unit=self._histogram_unit)
            self._histograms[name] = histogram
        histogram.record(value, attributes=dict(attributes))


__all__ = ['MetricSink', 'OpenTelemetryMetricSink', 'build_attribute_normalizer']
