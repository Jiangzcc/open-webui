from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
from open_webui.extensions.provider_ops.db import ProviderOpsBase
from open_webui.extensions.provider_ops.models import ProviderInvocation
from open_webui.extensions.provider_ops.service import (
    list_provider_invocations,
    summarize_provider_models,
    try_resume_provider_invocation,
    try_start_provider_invocation,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_observer_records_provider_lifecycle_without_storing_input(monkeypatch, tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def test_session():
        async with sessions() as session:
            yield session

    import open_webui.extensions.provider_ops.service as service

    monkeypatch.setattr(service, 'provider_ops_session', test_session)
    observer = await try_start_provider_invocation(
        task_id='task-1',
        user_id='user-1',
        media_kind='image',
        provider='fal',
        provider_model_id='fal-ai/example',
        payload={'prompt': 'private prompt', 'num_images': 1},
    )
    assert observer is not None
    await observer.submitted({'request_id': 'request-1', 'gateway_request_id': 'gateway-1', 'queue_position': 3})
    resumed = await try_resume_provider_invocation(task_id='task-1', provider_request_id='request-1')
    assert resumed is not None
    assert resumed.invocation_id == observer.invocation_id
    await observer.status({'status': 'IN_QUEUE', 'queue_position': 2})
    await observer.status({'status': 'IN_PROGRESS'})
    await observer.status({'status': 'COMPLETED', 'metrics': {'inference_time': 1.25, 'secret': 'ignored'}})
    await observer.succeeded()

    async with sessions() as session:
        row = await session.get(ProviderInvocation, observer.invocation_id)
        assert row is not None
        assert row.status == 'succeeded'
        assert row.provider_request_id == 'request-1'
        assert row.provider_gateway_request_id == 'gateway-1'
        assert row.queue_position == 2
        assert row.execution_duration_ms == 1250
        assert row.provider_metrics_json == {'inference_time': 1.25}
        assert row.input_sha256 != 'private prompt'
        assert not hasattr(row, 'input_snapshot_json')

        result = await list_provider_invocations(session, limit=10, provider='fal', status='succeeded')
        assert [item.id for item in result.items] == [observer.invocation_id]
        summary = await summarize_provider_models(session, since_ms=0, provider='fal')
        assert len(summary.items) == 1
        assert summary.items[0].request_count == 1
        assert summary.items[0].success_count == 1
        assert summary.items[0].failed_count == 0
        assert summary.items[0].unknown_count == 0
        assert summary.items[0].average_execution_duration_ms == 1250

    await engine.dispose()


@pytest.mark.asyncio
async def test_observer_preserves_first_running_timestamp(monkeypatch, tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def test_session():
        async with sessions() as session:
            yield session

    import open_webui.extensions.provider_ops.service as service

    monkeypatch.setattr(service, 'provider_ops_session', test_session)
    observer = await try_start_provider_invocation(
        task_id=None,
        user_id='user-1',
        media_kind='image',
        provider='fal',
        provider_model_id='fal-ai/example',
        payload={},
    )
    assert observer is not None
    await observer.status({'status': 'IN_PROGRESS'})
    async with sessions() as session:
        first = (await session.get(ProviderInvocation, observer.invocation_id)).provider_started_at
    await observer.status({'status': 'IN_PROGRESS'})
    async with sessions() as session:
        second = (await session.get(ProviderInvocation, observer.invocation_id)).provider_started_at
    assert first == second
    await engine.dispose()


@pytest.mark.asyncio
async def test_observer_records_failure_without_provider_message(monkeypatch, tmp_path) -> None:
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "provider-ops.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(ProviderOpsBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def test_session():
        async with sessions() as session:
            yield session

    import open_webui.extensions.provider_ops.service as service

    monkeypatch.setattr(service, 'provider_ops_session', test_session)
    observer = await try_start_provider_invocation(
        task_id='task-1',
        user_id='user-1',
        media_kind='image',
        provider='fal',
        provider_model_id='fal-ai/example',
        payload={'prompt': 'private prompt'},
    )
    assert observer is not None

    error = RuntimeError('private prompt and signed URL must not be stored')
    await observer.failed(error)
    async with sessions() as session:
        row = await session.get(ProviderInvocation, observer.invocation_id)
        assert row.status == 'failed'
        assert row.error_snapshot_json == {'type': 'RuntimeError'}

    cancelled_observer = await try_start_provider_invocation(
        task_id='task-2',
        user_id='user-1',
        media_kind='image',
        provider='fal',
        provider_model_id='fal-ai/example',
        payload={},
    )
    assert cancelled_observer is not None
    await cancelled_observer.failed(asyncio.CancelledError())
    async with sessions() as session:
        row = await session.get(ProviderInvocation, cancelled_observer.invocation_id)
        # Cancelling the local waiter does not prove that fal cancelled the
        # remote request; keep it reconcilable instead of claiming cancellation.
        assert row.status == 'unknown'
        assert row.error_code == 'client_cancelled'
    await engine.dispose()
