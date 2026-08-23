from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_initialization_runs_migrations_before_creating_one_recovery_task(monkeypatch) -> None:
    from open_webui.extensions.credits import registration

    calls: list[str] = []
    worker_started = asyncio.Event()

    def migrate() -> None:
        calls.append('migrated')

    def validate() -> None:
        calls.append('validated')

    async def run_sync(function):
        calls.append('migration' if function is migrate else 'validation')
        function()

    async def worker() -> None:
        calls.append('worker')
        worker_started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', run_sync)
    monkeypatch.setattr(registration, 'run_credit_migrations', migrate)
    monkeypatch.setattr(registration, '_validate_credit_schema', validate)
    monkeypatch.setattr(registration, '_credit_recovery_worker', worker)
    app = SimpleNamespace(state=SimpleNamespace())

    await registration.initialize_credit_extension(app)
    await worker_started.wait()
    original_task = app.state.credit_recovery_task
    await registration.initialize_credit_extension(app)

    assert calls == ['migration', 'migrated', 'validation', 'validated', 'worker']
    assert app.state.credit_recovery_task is original_task
    task = app.state.credit_recovery_task
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_migration_failure_propagates_without_starting_recovery(monkeypatch) -> None:
    from open_webui.extensions.credits import registration

    async def fail_migration(_function):
        raise RuntimeError('migration failed')

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', fail_migration)
    app = SimpleNamespace(state=SimpleNamespace(startup_complete=False))

    with pytest.raises(RuntimeError, match='migration failed'):
        await registration.initialize_credit_extension(app)

    assert app.state.startup_complete is False
    assert not hasattr(app.state, 'credit_recovery_task')


@pytest.mark.asyncio
async def test_validation_failure_propagates_without_starting_recovery(monkeypatch) -> None:
    from open_webui.extensions.credits import registration

    calls: list[object] = []

    async def run_sync(function):
        calls.append(function)
        if function is registration._validate_credit_schema:
            raise RuntimeError('schema validation failed')

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', run_sync)
    app = SimpleNamespace(state=SimpleNamespace(startup_complete=False))

    with pytest.raises(RuntimeError, match='schema validation failed'):
        await registration.initialize_credit_extension(app)

    assert calls == [registration.run_credit_migrations, registration._validate_credit_schema]
    assert app.state.startup_complete is False
    assert not hasattr(app.state, 'credit_recovery_task')


@pytest.mark.asyncio
async def test_shutdown_cancels_and_awaits_recovery_task(monkeypatch) -> None:
    from open_webui.extensions.credits import registration

    cancelled = asyncio.Event()

    async def worker() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', lambda _function: asyncio.sleep(0))
    monkeypatch.setattr(registration, '_validate_credit_schema', lambda: None)
    monkeypatch.setattr(registration, '_credit_recovery_worker', worker)
    app = SimpleNamespace(state=SimpleNamespace())

    await registration.initialize_credit_extension(app)
    await asyncio.sleep(0)
    task = app.state.credit_recovery_task
    await registration.shutdown_credit_extension(app)

    assert task.cancelled()
    assert cancelled.is_set()
    assert not hasattr(app.state, 'credit_recovery_task')


@pytest.mark.asyncio
async def test_shutdown_preserves_non_cancellation_task_failures() -> None:
    from open_webui.extensions.credits import registration

    async def failed_worker() -> None:
        raise RuntimeError('recovery task failed')

    task = asyncio.create_task(failed_worker())
    await asyncio.sleep(0)
    app = SimpleNamespace(state=SimpleNamespace(credit_recovery_task=task))

    with pytest.raises(RuntimeError, match='recovery task failed'):
        await registration.shutdown_credit_extension(app)


@pytest.mark.asyncio
async def test_recovery_pass_marks_only_stale_unfinished_usage_and_records_metric(monkeypatch) -> None:
    from open_webui.extensions.credits import registration

    cutoffs: list[int] = []
    metrics: list[int] = []

    async def mark_unknown(cutoff: int) -> int:
        cutoffs.append(cutoff)
        return 2

    monkeypatch.setattr(registration, 'mark_stale_usage_unknown', mark_unknown)
    monkeypatch.setattr(registration, '_record_recovered_usages', metrics.append)
    monkeypatch.setattr(registration, '_now', lambda: 10_000)

    assert await registration._recover_stale_usages() == 2
    assert cutoffs == [10_000 - registration.CREDIT_USAGE_STALE_SECONDS]
    assert metrics == [2]
