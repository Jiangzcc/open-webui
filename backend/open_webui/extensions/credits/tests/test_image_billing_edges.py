import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from open_webui.extensions.credits import image_billing
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.tests.async_test_support import AsyncContext


class _Session:
    def begin(self):
        return AsyncContext()


def test_idempotency_sources_reject_malformed_inputs() -> None:
    with pytest.raises(CreditError):
        image_billing._header_idempotency_key(SimpleNamespace(headers=[]))
    with pytest.raises(CreditError):
        image_billing._header_idempotency_key(
            SimpleNamespace(headers={'Idempotency-Key': ''})
        )
    assert image_billing._header_idempotency_key(SimpleNamespace(headers={})) is None

    identity = SimpleNamespace(user_id='user')
    assert image_billing._metadata_idempotency_key(identity, 'text-to-image', None) is None
    for metadata in ([], {}, {'call_instance_id': 'call', 'credit_channel': 'web'}):
        if metadata == {}:
            assert image_billing._metadata_idempotency_key(
                identity,
                'text-to-image',
                metadata,
            ) is None
        else:
            with pytest.raises(CreditError):
                image_billing._metadata_idempotency_key(
                    identity,
                    'text-to-image',
                    metadata,
                )


def test_provider_result_and_replay_validation() -> None:
    assert image_billing._normalize_internal_url(
        'http://localhost/api/v1/files/file/content'
    ) == '/api/v1/files/file/content'
    with pytest.raises(CreditError):
        image_billing._result_urls(SimpleNamespace())
    with pytest.raises(CreditError):
        image_billing._result_urls(SimpleNamespace(images=1))
    with pytest.raises(CreditError):
        image_billing._result_urls(SimpleNamespace(images=[]))
    with pytest.raises(CreditError):
        image_billing._result_urls(SimpleNamespace(images=[SimpleNamespace(url=1)]))

    usage = SimpleNamespace(result_snapshot=None, id='usage')
    with pytest.raises(CreditError):
        image_billing._replay_result(usage)
    usage.result_snapshot = {'urls': []}
    with pytest.raises(CreditError):
        image_billing._replay_result(usage)
    usage.error_snapshot = {'code': 'provider_code'}
    assert image_billing._replay_error(usage).context['provider_code'] == 'provider_code'


def test_old_usage_outcomes_and_safe_provider_errors() -> None:
    usage = SimpleNamespace(id='usage', result_snapshot={'urls': ['/api/v1/files/file/content']})
    assert image_billing._old_outcome(SimpleNamespace(outcome='succeeded', usage=usage))[0]['url'].endswith(
        '/content'
    )
    for outcome in ('failed', 'processing', 'unknown', 'invalid'):
        with pytest.raises(CreditError):
            image_billing._old_outcome(SimpleNamespace(outcome=outcome, usage=usage))

    assert image_billing._safe_provider_error(HTTPException(status_code=429)).code == 'http_429'
    assert image_billing._safe_provider_error(CreditError(code='provider_failed')).code == 'provider_failed'
    assert image_billing._safe_provider_error(RuntimeError()).code == 'provider_failed'


@pytest.mark.asyncio
async def test_failed_invoking_and_precharge_state_errors(monkeypatch) -> None:
    monkeypatch.setattr(image_billing, 'mark_usage_failed', AsyncMock(side_effect=RuntimeError))
    with pytest.raises(CreditError):
        await image_billing._mark_failed_or_unavailable('usage', RuntimeError())
    image_billing.mark_usage_failed = AsyncMock(return_value=0)
    with pytest.raises(CreditError):
        await image_billing._mark_failed_or_unavailable('usage', RuntimeError())

    monkeypatch.setattr(image_billing, 'mark_usage_invoking', AsyncMock(side_effect=RuntimeError))
    with pytest.raises(CreditError):
        await image_billing._mark_invoking_or_unavailable('usage')
    image_billing.mark_usage_invoking = AsyncMock(return_value=0)
    with pytest.raises(CreditError):
        await image_billing._mark_invoking_or_unavailable('usage')

    session = _Session()
    monkeypatch.setattr(image_billing, 'credit_session', lambda: AsyncContext(session))
    monkeypatch.setattr(image_billing, 'begin_image_usage', AsyncMock(side_effect=RuntimeError))
    with pytest.raises(CreditError):
        await image_billing._begin_or_replay_usage(SimpleNamespace(), object(), 'key')


@pytest.mark.asyncio
async def test_provider_invocation_refunds_only_explicit_pre_submission_failures(monkeypatch) -> None:
    marked = AsyncMock()
    monkeypatch.setattr(image_billing, '_mark_failed_or_unavailable', marked)

    pre_submission = RuntimeError('before submit')
    pre_submission.provider_submitted = False
    for error, restore in ((pre_submission, True), (RuntimeError('unknown'), False)):
        invoke = AsyncMock(side_effect=error)
        with pytest.raises(CreditError, match='provider'):
            await image_billing._invoke_image_provider(
                'usage',
                object(),
                object(),
                invoke,
            )
        assert marked.await_args.kwargs['restore_prepaid'] is restore

    invoke = AsyncMock(side_effect=asyncio.CancelledError)
    with pytest.raises(asyncio.CancelledError):
        await image_billing._invoke_image_provider('usage', object(), object(), invoke)


@pytest.mark.asyncio
async def test_terminal_finalize_maps_write_failures(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(image_billing, 'credit_session', lambda: AsyncContext(session))
    monkeypatch.setattr(
        image_billing,
        'mark_usage_succeeded_in_session',
        AsyncMock(return_value=0),
    )
    with pytest.raises(CreditError, match='unavailable'):
        await image_billing._finalize_image_success(
            'usage',
            object(),
            object(),
            ['/api/v1/files/file/content'],
            AsyncMock(),
        )
