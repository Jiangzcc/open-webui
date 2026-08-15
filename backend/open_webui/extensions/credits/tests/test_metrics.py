from __future__ import annotations

from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import pytest


@dataclass
class CapturingSink:
    events: list[tuple[str, str, float, dict[str, str]]] = field(default_factory=list)

    def add(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        self.events.append(('counter', name, value, dict(attributes)))

    def record(self, name: str, value: float, attributes: Mapping[str, str]) -> None:
        self.events.append(('histogram', name, value, dict(attributes)))


class FailingSink:
    def add(self, _name: str, _value: float, _attributes: Mapping[str, str]) -> None:
        raise RuntimeError('exporter unavailable')

    def record(self, _name: str, _value: float, _attributes: Mapping[str, str]) -> None:
        raise RuntimeError('exporter unavailable')


def test_credit_metrics_emits_required_credit_lifecycle_events() -> None:
    from open_webui.extensions.credits.metrics import CreditMetrics

    sink = CapturingSink()
    metrics = CreditMetrics(sink)

    metrics.quote_succeeded(model='model-a', action='text-to-image', charged_credits=7)
    metrics.quote_rejected(model='model-a', action='text-to-image', error_code='price_not_configured')
    metrics.quote_rejected(model='model-a', action='text-to-image', error_code='price_rule_incomplete')
    metrics.debit_failed(
        model='model-a',
        action='text-to-image',
        channel='web',
        error_code='credit_service_unavailable',
    )
    metrics.debit_failed(
        model='model-a',
        action='text-to-image',
        channel='web',
        error_code='insufficient_credits',
    )
    metrics.debit_succeeded(model='model-a', action='text-to-image', channel='web', charged_credits=7)
    metrics.debit_insufficient(model='model-a', action='text-to-image', channel='web')
    metrics.idempotency_hit(model='model-a', action='text-to-image', channel='web')
    metrics.idempotency_conflict(model='model-a', action='text-to-image', channel='web')
    for status in ('debited', 'invoking', 'succeeded', 'failed', 'unknown'):
        metrics.usage_status(model='model-a', action='text-to-image', channel='web', status=status)
    metrics.long_pending(count=2)
    metrics.admin_adjustment(amount=-9)
    metrics.consistency_anomaly()

    assert sink.events == [
        ('counter', 'webui.credits.quote.success', 1, {'model': 'model-a', 'action': 'text-to-image'}),
        ('histogram', 'webui.credits.quote.charged_credits', 7, {'model': 'model-a', 'action': 'text-to-image'}),
        (
            'counter',
            'webui.credits.quote.price_not_configured',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'error_code': 'price_not_configured'},
        ),
        (
            'counter',
            'webui.credits.quote.price_rule_incomplete',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'error_code': 'price_rule_incomplete'},
        ),
        (
            'counter',
            'webui.credits.debit.rejected',
            1,
            {
                'model': 'model-a',
                'action': 'text-to-image',
                'channel': 'web',
                'error_code': 'credit_service_unavailable',
            },
        ),
        (
            'counter',
            'webui.credits.debit.insufficient',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.debit.success',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'histogram',
            'webui.credits.debit.charged_credits',
            7,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.debit.insufficient',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.idempotency.hit',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.idempotency.conflict',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.usage.debited',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.usage.invoking',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        (
            'counter',
            'webui.credits.usage.succeeded',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        ('counter', 'webui.credits.usage.failed', 1, {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'}),
        (
            'counter',
            'webui.credits.usage.unknown',
            1,
            {'model': 'model-a', 'action': 'text-to-image', 'channel': 'web'},
        ),
        ('counter', 'webui.credits.usage.long_pending', 2, {}),
        ('counter', 'webui.credits.admin_adjustment.decrease', 1, {}),
        ('histogram', 'webui.credits.admin_adjustment.amount', 9, {}),
        ('counter', 'webui.credits.consistency.anomaly', 1, {}),
    ]


def test_credit_metrics_strips_sensitive_or_unbounded_labels() -> None:
    from open_webui.extensions.credits.metrics import normalize_metric_attributes

    attributes = normalize_metric_attributes(
        {
            'model': 'model-a',
            'action': 'text-to-image',
            'channel': 'web',
            'error_code': 'price_not_configured',
            'prompt': 'private prompt',
            'user_id': 'user-123',
            'ip': '192.0.2.7',
            'request_id': 'request-123',
            'authorization': 'Bearer secret',
            'base64': 'YWJj',
            'model_untrusted': 'not-a-whitelisted-label',
        }
    )

    assert attributes == {
        'model': 'model-a',
        'action': 'text-to-image',
        'channel': 'web',
        'error_code': 'price_not_configured',
    }


def test_credit_metrics_never_raise_when_the_observability_sink_fails() -> None:
    from open_webui.extensions.credits.metrics import CreditMetrics

    metrics = CreditMetrics(FailingSink())

    metrics.debit_succeeded(model='model-a', action='text-to-image', channel='web', charged_credits=7)
    metrics.usage_status(model='model-a', action='text-to-image', channel='web', status='succeeded')
    metrics.usage_status(status='unsupported')
    metrics.long_pending(count=0)


@pytest.mark.asyncio
async def test_service_metrics_do_not_change_usage_status_transitions(monkeypatch) -> None:
    import open_webui.extensions.credits.service as service

    class RecordingMetrics:
        def __init__(self) -> None:
            self.statuses: list[str] = []

        def usage_status(self, *, status: str, **_kwargs) -> None:
            self.statuses.append(status)

    async def update(_usage_id, _allowed, _values):
        return 1

    async def succeeded_in_session(_session, _usage_id, _urls):
        return 1

    # mark_usage_succeeded 和 mark_usage_failed 都通过 credit_session() 打开数据库
    # 会话。monkeypatch 为内存假会话，使测试不依赖真实数据库。
    class _FakeUsage:
        """模拟一条处于 invoking 状态的 CreditUsage 行。"""

        def __init__(self) -> None:
            self.status = 'invoking'
            self.exempt = False
            self.charged_credits = 0
            self.ledger_id = None

    class _FakeSession:
        """模拟 AsyncSession：支持 begin()、scalar()、flush()。"""

        def begin(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def scalar(self, _statement):
            return _FakeUsage()

        async def flush(self):
            pass

    @asynccontextmanager
    async def fake_credit_session():
        yield _FakeSession()

    sink = RecordingMetrics()
    monkeypatch.setattr(service, '_update_usage_status', update)
    monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeeded_in_session)
    monkeypatch.setattr(service, 'credit_session', fake_credit_session)
    monkeypatch.setattr(service, 'credit_metrics', sink)

    assert await service.mark_usage_invoking('usage-1') == 1
    assert await service.mark_usage_succeeded('usage-1', ['/api/v1/files/test/content']) == 1
    assert await service.mark_usage_failed('usage-1', service.SafeProviderError('provider_failed', 'safe')) == 1
    assert sink.statuses == ['invoking', 'succeeded', 'failed']


def test_opentelemetry_sink_creates_and_reuses_counter_and_histogram_instruments() -> None:
    from open_webui.extensions.credits.metrics import OpenTelemetryMetricSink

    @dataclass
    class Instrument:
        values: list[tuple[float, dict[str, str]]] = field(default_factory=list)

        def add(self, value: float, attributes: Mapping[str, str]) -> None:
            self.values.append((value, dict(attributes)))

        def record(self, value: float, attributes: Mapping[str, str]) -> None:
            self.values.append((value, dict(attributes)))

    @dataclass
    class Meter:
        counter_calls: list[str] = field(default_factory=list)
        histogram_calls: list[str] = field(default_factory=list)
        counters: dict[str, Instrument] = field(default_factory=dict)
        histograms: dict[str, Instrument] = field(default_factory=dict)

        def create_counter(self, name: str, **_kwargs) -> Instrument:
            self.counter_calls.append(name)
            return self.counters.setdefault(name, Instrument())

        def create_histogram(self, name: str, **_kwargs) -> Instrument:
            self.histogram_calls.append(name)
            return self.histograms.setdefault(name, Instrument())

    meter = Meter()
    sink = OpenTelemetryMetricSink(meter=meter)

    sink.add('webui.credits.quote.success', 1, {'model': 'model-a'})
    sink.add('webui.credits.quote.success', 1, {'model': 'model-a'})
    sink.record('webui.credits.quote.charged_credits', 7, {'model': 'model-a'})

    assert meter.counter_calls == ['webui.credits.quote.success']
    assert meter.histogram_calls == ['webui.credits.quote.charged_credits']
    assert meter.counters['webui.credits.quote.success'].values == [
        (1, {'model': 'model-a'}),
        (1, {'model': 'model-a'}),
    ]
    assert meter.histograms['webui.credits.quote.charged_credits'].values == [(7, {'model': 'model-a'})]
