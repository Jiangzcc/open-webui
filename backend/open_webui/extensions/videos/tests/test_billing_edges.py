from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.tests.async_test_support import AsyncContext
from open_webui.extensions.videos import billing
from open_webui.extensions.videos.schemas import VideoTaskSubmitForm

from .task_test_support import video_task


@pytest.mark.asyncio
async def test_quote_video_usage_success_and_fail_closed_boundaries(monkeypatch) -> None:
    import open_webui.extensions.credits.pricing as pricing
    import open_webui.extensions.videos.catalog as catalog

    submission = VideoTaskSubmitForm(
        task='text-to-video',
        model='public',
        prompt='prompt',
        params={'duration': 5},
    )
    monkeypatch.setattr(billing, '_resolve_internal_model_id', lambda _model: 'internal')
    monkeypatch.setattr(catalog, 'build_video_provider_payload', lambda _form: (object(), {}, {'duration': 5}))
    session = SimpleNamespace()
    monkeypatch.setattr(billing, 'credit_session', lambda: AsyncContext(session))
    monkeypatch.setattr(billing, 'get_balance_if_exists', AsyncMock(return_value=5))
    monkeypatch.setattr(billing, 'get_enabled_price', AsyncMock(return_value=None))
    with pytest.raises(CreditError, match='configured'):
        await billing.quote_video_usage(SimpleNamespace(id='user'), submission)

    price = object()
    billing.get_enabled_price.return_value = price
    monkeypatch.setattr(
        pricing,
        'compute_price',
        Mock(return_value=SimpleNamespace(charged_credits=6)),
    )
    with pytest.raises(CreditError, match='credits'):
        await billing.quote_video_usage(SimpleNamespace(id='user'), submission)
    billing.get_balance_if_exists.return_value = 10
    result = await billing.quote_video_usage(SimpleNamespace(id='user'), submission)
    assert result.charged_credits == 6
    assert result.sufficient is True


@pytest.mark.asyncio
async def test_begin_and_invoking_usage_wrappers(monkeypatch) -> None:
    session = object()
    monkeypatch.setattr(billing, 'credit_session', lambda: AsyncContext(session))
    monkeypatch.setattr(billing, 'video_billing_context', lambda *_args, **_kwargs: object())
    begin = AsyncMock(return_value='begin')
    monkeypatch.setattr(billing, 'begin_generation_usage', begin)
    assert await billing.begin_video_usage(
        SimpleNamespace(id='user'),
        video_task(),
        execution_mode='mock',
    ) == 'begin'
    assert begin.await_args.args[0] is session

    monkeypatch.setattr(billing, 'mark_usage_invoking', AsyncMock(return_value=0))
    with pytest.raises(RuntimeError, match='transition'):
        await billing.mark_video_usage_invoking('usage')


@pytest.mark.asyncio
async def test_heartbeat_logs_transient_error_then_stops_when_ownership_is_lost(monkeypatch) -> None:
    monkeypatch.setattr(billing.asyncio, 'sleep', AsyncMock())
    monkeypatch.setattr(
        billing,
        'touch_usage_invoking',
        AsyncMock(side_effect=[RuntimeError('database'), 0]),
    )
    await billing.heartbeat_video_usage('usage')
    assert billing.touch_usage_invoking.await_count == 2


@pytest.mark.asyncio
async def test_usage_failure_retries_exhaustion_and_preserves_cancellation(monkeypatch) -> None:
    monkeypatch.setattr(billing.asyncio, 'sleep', AsyncMock())
    monkeypatch.setattr(
        billing,
        'mark_usage_failed',
        AsyncMock(side_effect=RuntimeError('database')),
    )
    with pytest.raises(RuntimeError, match='database'):
        await billing.mark_video_usage_failed('usage', 'failed')
    assert billing.mark_usage_failed.await_count == billing._USAGE_FAILURE_MAX_ATTEMPTS

    billing.mark_usage_failed = AsyncMock(side_effect=__import__('asyncio').CancelledError)
    with pytest.raises(__import__('asyncio').CancelledError):
        await billing.mark_video_usage_failed('usage', 'failed')
