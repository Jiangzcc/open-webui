import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.creations import registration as creations
from open_webui.extensions.credits import registration as credits
from open_webui.extensions.model_ops import registration as model_ops
from open_webui.extensions.prompt_tags import registration as prompt_tags
from open_webui.extensions.videos import registration as videos


async def _pending(started: asyncio.Event):
    started.set()
    await asyncio.Event().wait()


@pytest.mark.asyncio
async def test_creation_and_video_extension_lifecycles(monkeypatch) -> None:
    extension_cases = (
        (
            creations,
            creations.initialize_creations_extension,
            creations.shutdown_creations_extension,
            '_image_recovery_worker',
            'image_recovery_task',
            'recover_incomplete_generation_tasks',
        ),
        (
            videos,
            videos.initialize_videos_extension,
            videos.shutdown_videos_extension,
            '_video_recovery_worker',
            'video_recovery_task',
            'recover_incomplete_video_tasks',
        ),
    )
    for module, initializer, shutdown, worker_name, task_attr, recovery_name in (
        extension_cases
    ):
        started = asyncio.Event()
        monkeypatch.setattr(module, worker_name, lambda _request, started=started: _pending(started))
        monkeypatch.setattr(module, recovery_name, AsyncMock(return_value=1))
        monkeypatch.setattr(module, 'recovery_request', lambda app: SimpleNamespace(app=app))
        if module is creations:
            monkeypatch.setattr(module.anyio.to_thread, 'run_sync', AsyncMock())
            monkeypatch.setattr(module, 'init_generation_event_bus', Mock())
            monkeypatch.setattr(module, 'shutdown_generation_tasks', AsyncMock())
        else:
            monkeypatch.setattr(module, 'cleanup_stale_fal_video_temp_files', AsyncMock(return_value=1))
            monkeypatch.setattr(module, 'shutdown_video_tasks', AsyncMock())
        app = SimpleNamespace(state=SimpleNamespace())
        await initializer(app)
        await started.wait()
        assert hasattr(app.state, task_attr)
        await shutdown(app)
        assert not hasattr(app.state, task_attr)


@pytest.mark.asyncio
async def test_credit_extension_lifecycle_and_recovery_counter(monkeypatch) -> None:
    started = asyncio.Event()
    monkeypatch.setattr(credits.anyio.to_thread, 'run_sync', AsyncMock())
    monkeypatch.setattr(credits, '_credit_recovery_worker', lambda: _pending(started))
    app = SimpleNamespace(state=SimpleNamespace())
    await credits.initialize_credit_extension(app)
    await started.wait()
    original = app.state.credit_recovery_task
    await credits.initialize_credit_extension(app)
    assert app.state.credit_recovery_task is original
    await credits.shutdown_credit_extension(app)
    assert not hasattr(app.state, 'credit_recovery_task')
    await credits.shutdown_credit_extension(app)

    counter = Mock()
    monkeypatch.setattr(credits, '_recovery_counter', counter)
    credits._record_recovered_usages(0)
    credits._record_recovered_usages(2)
    counter.add.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_schema_only_extensions_run_migration_then_validation(monkeypatch) -> None:
    for module, initializer in (
        (model_ops, model_ops.initialize_model_ops_extension),
        (prompt_tags, prompt_tags.initialize_prompt_tag_extension),
    ):
        run_sync = AsyncMock()
        monkeypatch.setattr(module.anyio.to_thread, 'run_sync', run_sync)
        await initializer(SimpleNamespace())
        assert run_sync.await_count == 2
