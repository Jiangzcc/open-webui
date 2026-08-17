from __future__ import annotations

from types import SimpleNamespace

import pytest
from open_webui.extensions.videos import registration


@pytest.mark.asyncio
async def test_video_registration_starts_and_stops_persistent_recovery(monkeypatch) -> None:
    recovered_requests = []
    shutdown_apps = []

    async def cleanup() -> int:
        return 0

    async def recover(request) -> int:
        recovered_requests.append(request)
        return 2

    async def shutdown(app) -> None:
        shutdown_apps.append(app)

    monkeypatch.setattr(registration, 'cleanup_stale_fal_video_temp_files', cleanup)
    monkeypatch.setattr(registration, 'recover_incomplete_video_tasks', recover)
    monkeypatch.setattr(registration, 'shutdown_video_tasks', shutdown)
    app = SimpleNamespace(state=SimpleNamespace())

    await registration.initialize_videos_extension(app)

    assert len(recovered_requests) == 1
    assert recovered_requests[0].app is app
    assert app.state.video_generation_tasks == {}
    assert not app.state.video_recovery_task.done()

    await registration.shutdown_videos_extension(app)

    assert shutdown_apps == [app]
    assert not hasattr(app.state, 'video_recovery_task')
