from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.creations import image_recovery
from open_webui.extensions.creations.schemas import CapturedImageBatch, CapturedImageResult
from open_webui.extensions.provider_ops.service import ProviderRecoveryState


class _LookupSession:
    def __init__(self, *, task=None, usage=None):
        self.task = task
        self.usage = usage

    async def get(self, _model, _key):
        return self.task

    async def scalar(self, _statement):
        return self.usage

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        return False


def _task(**changes):
    values = {
        'id': 'task-1',
        'user_id': 'user-1',
        'idempotency_key': 'request-1',
        'status': 'running',
        'kind': 'text-to-image',
        'prompt': 'a quiet lake',
        'model_id': 'fal-ai/flux/dev',
        'params_json': {'size': '1024x1024'},
        'execution_mode': 'fal',
        'delivery_attempts': 0,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _usage(**changes):
    values = {
        'id': 'usage-1',
        'user_id': 'user-1',
        'idempotency_key': 'request-1',
        'resource_id': 'fal-ai/flux/dev',
        'action': 'text-to-image',
        'channel': 'web',
        'status': 'invoking',
    }
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_recovery_resumes_existing_fal_request_without_generation_post(monkeypatch) -> None:
    from open_webui.routers import images

    task = _task()
    usage = _usage()

    @asynccontextmanager
    async def creation_context():
        yield _LookupSession(task=task)

    @asynccontextmanager
    async def credit_context():
        yield _LookupSession(usage=usage)

    batch = CapturedImageBatch(
        images=(
            CapturedImageResult(
                url='/api/v1/files/file-1/content',
                file_id='file-1',
                file_user_id='user-1',
                file_created_at=10,
                mime_type='image/png',
            ),
        )
    )
    resume = AsyncMock(return_value={'images': [{'url': 'https://media.example/result.png'}]})
    capture = AsyncMock(return_value=batch)
    set_state = AsyncMock()
    monkeypatch.setattr(image_recovery, 'creation_session', creation_context)
    monkeypatch.setattr(image_recovery, 'credit_session', credit_context)
    monkeypatch.setattr(image_recovery, '_completed_result_from_creations', AsyncMock(return_value=None))
    monkeypatch.setattr(
        image_recovery,
        'load_provider_recovery_state',
        AsyncMock(
            return_value=ProviderRecoveryState(
                provider_request_id='provider-1',
                status_url='https://queue.fal.run/status/provider-1',
                response_url='https://queue.fal.run/response/provider-1',
                result_url=None,
            )
        ),
    )
    monkeypatch.setattr(image_recovery, '_increment_delivery_attempts', AsyncMock(return_value=1))
    monkeypatch.setattr(image_recovery, 'try_resume_provider_invocation', AsyncMock(return_value=None))
    monkeypatch.setattr(image_recovery, 'resume_fal_queue', resume)
    monkeypatch.setattr(image_recovery.Users, 'get_user_by_id', AsyncMock(return_value=SimpleNamespace(id='user-1')))
    monkeypatch.setattr(image_recovery, 'finalize_created_images', AsyncMock())
    monkeypatch.setattr(image_recovery, 'mark_usage_succeeded_in_session', AsyncMock(return_value=1))
    monkeypatch.setattr(image_recovery, '_set_task_state', set_state)
    monkeypatch.setattr(image_recovery, '_publish_image_task_event', AsyncMock())
    monkeypatch.setattr(
        images,
        'get_image_config',
        AsyncMock(return_value=SimpleNamespace(FAL_API_KEY='fake', FAL_API_BASE_URL='https://queue.fal.run')),
    )
    monkeypatch.setattr(images, '_capture_fal_image_result', capture)

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    await image_recovery.recover_generation_task(task.id, request)

    resume.assert_awaited_once()
    assert resume.await_args.kwargs['response_url'].endswith('/provider-1')
    capture.assert_awaited_once()
    assert set_state.await_args.kwargs == {
        'status': 'succeeded',
        'result': [{'url': '/api/v1/files/file-1/content'}],
    }


@pytest.mark.asyncio
async def test_missing_accepted_provider_state_never_restores_prepaid(monkeypatch) -> None:
    task = _task()
    usage = _usage()

    @asynccontextmanager
    async def creation_context():
        yield _LookupSession(task=task)

    @asynccontextmanager
    async def credit_context():
        yield _LookupSession(usage=usage)

    failed = AsyncMock(return_value=1)
    monkeypatch.setattr(image_recovery, 'creation_session', creation_context)
    monkeypatch.setattr(image_recovery, 'credit_session', credit_context)
    monkeypatch.setattr(image_recovery, '_completed_result_from_creations', AsyncMock(return_value=None))
    monkeypatch.setattr(image_recovery, 'load_provider_recovery_state', AsyncMock(return_value=None))
    monkeypatch.setattr(image_recovery, 'mark_usage_failed', failed)
    monkeypatch.setattr(image_recovery, '_set_task_state', AsyncMock())
    monkeypatch.setattr(image_recovery, '_publish_image_task_event', AsyncMock())

    await image_recovery.recover_generation_task(
        task.id,
        SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())),
    )

    assert failed.await_args.kwargs['restore_prepaid'] is False
