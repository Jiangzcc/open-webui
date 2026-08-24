import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.videos import delivery
from open_webui.extensions.videos.execution_types import VideoExecutionError, VideoExecutionOutput
from open_webui.extensions.videos.pexels_mock import PexelsMockClip

from .task_test_support import video_task


class _Request:
    app = SimpleNamespace(
        url_path_for=lambda _name, *, id: f'/files/{id}',
    )


def test_delivery_config_and_duration_helpers(monkeypatch) -> None:
    monkeypatch.delenv('TEST_DELAY', raising=False)
    assert delivery._positive_float_env('TEST_DELAY', 1.5) == 1.5
    monkeypatch.setenv('TEST_DELAY', 'invalid')
    assert delivery._positive_float_env('TEST_DELAY', 1.5) == 1.5
    monkeypatch.setenv('TEST_DELAY', '-1')
    assert delivery._positive_float_env('TEST_DELAY', 1.5) == 1.5
    monkeypatch.setenv('TEST_DELAY', '2.25')
    assert delivery._positive_float_env('TEST_DELAY', 1.5) == 2.25
    assert delivery._duration_seconds({'duration': None}) == 5
    assert delivery._duration_seconds({'duration': 0.1}) == 1


@pytest.mark.asyncio
async def test_mock_scenario_dispatch_is_deterministic(monkeypatch) -> None:
    sleep = AsyncMock()
    monkeypatch.setattr(delivery.asyncio, 'sleep', sleep)
    monkeypatch.setenv('VIDEO_GENERATION_MOCK_SCENARIO', 'slow')
    monkeypatch.setenv('VIDEO_GENERATION_MOCK_SLOW_SECONDS', '0')
    await delivery._run_mock_scenario()
    sleep.assert_awaited_once_with(0)

    for scenario, code in (
        ('provider_timeout', 'video_provider_timeout'),
        ('invalid', 'video_mock_scenario_invalid'),
    ):
        monkeypatch.setenv('VIDEO_GENERATION_MOCK_SCENARIO', scenario)
        with pytest.raises(VideoExecutionError) as captured:
            await delivery._run_mock_scenario()
        assert captured.value.code == code
        assert captured.value.provider_completed is False


@pytest.mark.asyncio
async def test_upload_file_supports_bytes_and_paths_and_closes_stream(monkeypatch, tmp_path) -> None:
    sources = []

    async def upload(_request, *, file, metadata, process, user):
        sources.append((file.file, file.file.read(), metadata, process, user))
        return SimpleNamespace(id='file')

    monkeypatch.setattr(delivery, 'upload_file_handler', upload)
    path = tmp_path / 'video.mp4'
    path.write_bytes(b'path')
    await delivery._upload_video_file(
        _Request(),
        SimpleNamespace(id='user'),
        b'bytes',
        'bytes.mp4',
        'video/mp4',
        metadata={'kind': 'bytes'},
    )
    await delivery._upload_video_file(
        _Request(),
        SimpleNamespace(id='user'),
        path,
        'path.mp4',
        'video/mp4',
        metadata={'kind': 'path'},
    )
    assert [item[1] for item in sources] == [b'bytes', b'path']
    assert all(item[0].closed for item in sources)


@pytest.mark.asyncio
async def test_persist_mock_creation_cleans_both_files_on_flush_failure(monkeypatch) -> None:
    cleanup = AsyncMock()
    monkeypatch.setattr(delivery, '_cleanup_generated_files', cleanup)
    session = SimpleNamespace(
        add=Mock(),
        flush=AsyncMock(side_effect=RuntimeError('database failure')),
    )
    video_file = SimpleNamespace(id='video', created_at=None)
    poster_file = SimpleNamespace(id='poster')
    with pytest.raises(RuntimeError):
        await delivery._persist_mock_creation(
            _Request(),
            SimpleNamespace(id='user'),
            video_task(),
            session,
            video_file,
            poster_file,
            5,
        )
    cleanup.assert_awaited_once_with([video_file, poster_file])


@pytest.mark.asyncio
async def test_mock_delivery_rejects_missing_assets_and_uses_static_poster_fallback(
    monkeypatch,
    tmp_path,
) -> None:
    missing = tmp_path / 'missing'
    monkeypatch.setattr(delivery, 'fetch_pexels_mock_clip', AsyncMock(return_value=None))
    monkeypatch.setattr(delivery, '_MOCK_VIDEO_PATH', missing)
    monkeypatch.setattr(delivery, '_MOCK_POSTER_PATH', missing)
    with pytest.raises(RuntimeError, match='mock assets'):
        await delivery._finalize_mock_video(_Request(), SimpleNamespace(id='user'), video_task(), object())

    poster = tmp_path / 'poster.webp'
    poster.write_bytes(b'poster')
    monkeypatch.setattr(delivery, '_MOCK_POSTER_PATH', poster)
    monkeypatch.setattr(delivery, 'extract_poster_from_video', lambda _source: None)
    uploaded = AsyncMock(return_value=(SimpleNamespace(), SimpleNamespace()))
    persisted = AsyncMock(return_value={'ok': True})
    monkeypatch.setattr(delivery, '_upload_mock_pair', uploaded)
    monkeypatch.setattr(delivery, '_persist_mock_creation', persisted)
    clip = PexelsMockClip(b'video', b'', 'application/octet-stream', 0)
    assert await delivery._finalize_clip_mock_video(
        _Request(),
        SimpleNamespace(id='user'),
        video_task(),
        object(),
        clip,
    ) == {'ok': True}
    assert uploaded.await_args.args[3] == b'poster'
    assert uploaded.await_args.args[4] == 'generated-video-poster.webp'


@pytest.mark.asyncio
async def test_real_video_upload_and_result_helpers_cover_poster(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        delivery,
        'extract_poster_from_video',
        lambda _path: (b'poster', 'image/jpeg'),
    )
    uploads = AsyncMock(
        side_effect=[
            SimpleNamespace(id='video', created_at=3),
            SimpleNamespace(id='poster', created_at=3),
        ]
    )
    monkeypatch.setattr(delivery, '_upload_video_file', uploads)
    output = VideoExecutionOutput(tmp_path / 'video.mp4', 'video/mp4', None)
    uploaded_files = []
    video_file, poster_file = await delivery._upload_real_video_files(
        _Request(),
        SimpleNamespace(id='user'),
        video_task(),
        output,
        uploaded_files,
    )
    assert uploaded_files == [video_file, poster_file]
    creation, duration = delivery._real_video_creation(
        SimpleNamespace(id='user'),
        video_task(),
        output,
        video_file,
        poster_file,
    )
    result = delivery._real_video_result(_Request(), creation, duration)
    assert result['poster_url'] == '/files/poster'
    assert result['duration_seconds'] == 5


@pytest.mark.asyncio
async def test_real_video_finalizer_preserves_provider_boundary_and_cleans(monkeypatch, tmp_path) -> None:
    cleanup = AsyncMock()
    monkeypatch.setattr(delivery, '_cleanup_generated_files', cleanup)
    output = VideoExecutionOutput(tmp_path / 'video.mp4', 'video/mp4', 5)

    cancellation = asyncio.CancelledError()
    monkeypatch.setattr(delivery, '_upload_real_video_files', AsyncMock(side_effect=cancellation))
    with pytest.raises(asyncio.CancelledError) as captured:
        await delivery._finalize_real_video(
            _Request(),
            SimpleNamespace(id='user'),
            video_task(),
            object(),
            output,
        )
    assert captured.value.provider_completed is True

    for error, expected in (
        (VideoExecutionError('existing'), 'existing'),
        (RuntimeError('upload'), 'video_delivery_failed'),
    ):
        monkeypatch.setattr(delivery, '_upload_real_video_files', AsyncMock(side_effect=error))
        with pytest.raises(VideoExecutionError) as failure:
            await delivery._finalize_real_video(
                _Request(),
                SimpleNamespace(id='user'),
                video_task(),
                object(),
                output,
            )
        assert failure.value.code == expected


@pytest.mark.asyncio
async def test_cleanup_result_files_ignores_missing_and_non_string_ids(monkeypatch) -> None:
    found = SimpleNamespace(id='found')
    get_file = AsyncMock(side_effect=[found, None])
    cleanup = AsyncMock()
    monkeypatch.setattr(delivery.Files, 'get_file_by_id', get_file)
    monkeypatch.setattr(delivery, '_cleanup_generated_files', cleanup)
    await delivery._cleanup_result_files(None)
    await delivery._cleanup_result_files(
        {'file_id': 'found', 'poster_file_id': 'missing', 'other': 1}
    )
    cleanup.assert_awaited_once_with([found])
