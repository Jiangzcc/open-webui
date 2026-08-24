import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.provider_ops import registration
from open_webui.extensions.tests.async_test_support import AsyncContext, wait_until_cancelled


@pytest.mark.asyncio
async def test_periodic_lease_claim_and_owner_safe_release(monkeypatch) -> None:
    redis = SimpleNamespace(set=AsyncMock(return_value=True), eval=AsyncMock())
    monkeypatch.setattr(registration, '_provider_sync_redis', redis)
    registration._provider_sync_lease_token = None
    assert await registration._claim_periodic_sync_lease() is True
    assert registration._provider_sync_lease_token is not None
    await registration._release_periodic_sync_lease()
    redis.eval.assert_awaited_once()
    assert registration._provider_sync_lease_token is None

    redis.set.side_effect = RuntimeError('redis')
    monkeypatch.setattr(registration, 'UVICORN_WORKERS', 1)
    assert await registration._claim_periodic_sync_lease() is True


@pytest.mark.asyncio
async def test_initialize_is_idempotent_and_shutdown_awaits_worker(monkeypatch) -> None:
    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', AsyncMock())
    monkeypatch.setattr(registration, 'UVICORN_WORKERS', 1)
    monkeypatch.setattr(registration, '_provider_sync_redis', None)
    started = asyncio.Event()

    async def worker():
        await wait_until_cancelled(started)

    monkeypatch.setattr(registration, '_run_periodic_fal_sync', worker)
    app = SimpleNamespace(state=SimpleNamespace())
    await registration.initialize_provider_ops_extension(app)
    await started.wait()
    original = app.state.provider_ops_sync_task
    await registration.initialize_provider_ops_extension(app)
    assert app.state.provider_ops_sync_task is original
    await registration.shutdown_provider_ops_extension(app)
    assert not hasattr(app.state, 'provider_ops_sync_task')


@pytest.mark.asyncio
async def test_initialize_disables_unsafe_multiworker_fallback(monkeypatch) -> None:
    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', AsyncMock())
    monkeypatch.setattr(registration, 'UVICORN_WORKERS', 2)
    monkeypatch.setattr(registration, '_provider_sync_redis', None)
    app = SimpleNamespace(state=SimpleNamespace())
    await registration.initialize_provider_ops_extension(app)
    assert not hasattr(app.state, 'provider_ops_sync_task')


@pytest.mark.asyncio
async def test_lease_fallback_and_release_error_paths(monkeypatch) -> None:
    monkeypatch.setattr(registration, '_provider_sync_redis', None)
    monkeypatch.setattr(registration, 'UVICORN_WORKERS', 2)
    assert await registration._claim_periodic_sync_lease() is False

    registration._provider_sync_lease_token = None
    await registration._release_periodic_sync_lease()
    registration._provider_sync_lease_token = 'token'
    await registration._release_periodic_sync_lease()
    assert registration._provider_sync_lease_token is None

    redis = SimpleNamespace(eval=AsyncMock(side_effect=RuntimeError('redis')))
    monkeypatch.setattr(registration, '_provider_sync_redis', redis)
    registration._provider_sync_lease_token = 'token'
    await registration._release_periodic_sync_lease()
    assert registration._provider_sync_lease_token is None


@pytest.mark.asyncio
async def test_periodic_worker_skips_unclaimed_lease_and_releases_failed_run(monkeypatch) -> None:
    sleeps = 0

    async def sleep(_seconds):
        nonlocal sleeps
        sleeps += 1
        if sleeps >= 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(registration.asyncio, 'sleep', sleep)
    monkeypatch.setattr(registration, '_claim_periodic_sync_lease', AsyncMock(return_value=False))
    with pytest.raises(asyncio.CancelledError):
        await registration._run_periodic_fal_sync()

    sleeps = 0
    monkeypatch.setattr(registration, '_claim_periodic_sync_lease', AsyncMock(return_value=True))
    monkeypatch.setattr(registration, '_release_periodic_sync_lease', AsyncMock())
    from open_webui.extensions.provider_ops import platform_sync

    monkeypatch.setattr(
        platform_sync,
        'sync_fal_platform',
        AsyncMock(return_value=SimpleNamespace(status='failed', id='run', error_code='failed')),
    )

    monkeypatch.setattr(
        registration,
        'provider_ops_session',
        lambda: AsyncContext(object()),
    )
    with pytest.raises(asyncio.CancelledError):
        await registration._run_periodic_fal_sync()
    registration._release_periodic_sync_lease.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_without_worker_still_releases_lease(monkeypatch) -> None:
    release = AsyncMock()
    monkeypatch.setattr(registration, '_release_periodic_sync_lease', release)
    await registration.shutdown_provider_ops_extension(
        SimpleNamespace(state=SimpleNamespace())
    )
    release.assert_awaited_once()
