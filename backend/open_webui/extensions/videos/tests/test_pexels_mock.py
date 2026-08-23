"""Tests for the Pexels-backed mock video source.

These tests never hit the network. They cover:
* the key/config gating (``pexels_api_key`` / ``fetch_pexels_mock_clip``),
* the candidate selection (smallest usable mp4, poster URL resolution),
* the poster-from-frame fallback (``extract_poster_from_video``),
and the generator-side dispatch in ``service._finalize_mock_video``:
  * Pexels clip path → ``_finalize_clip_mock_video``,
  * ``None`` clip → static ``welcome`` asset fallback.
"""

from __future__ import annotations

import sys
import types

import pytest
from open_webui.extensions.videos import delivery, pexels_mock, service
from open_webui.extensions.videos.pexels_mock import PexelsMockClip
from open_webui.extensions.videos.schemas import VideoTaskResponse


# --------------------------------------------------------------------------- #
# candidate selection helpers (pure functions, no network)
# --------------------------------------------------------------------------- #
def test_probe_video_duration_uses_container_duration(monkeypatch, tmp_path) -> None:
    closed = False

    class Container:
        duration = 5_000_000

        def close(self):
            nonlocal closed
            closed = True

    fake_av = types.SimpleNamespace(open=lambda _path: Container(), time_base=1_000_000)
    monkeypatch.setitem(sys.modules, 'av', fake_av)

    assert pexels_mock.probe_video_duration(tmp_path / 'video.mp4') == 5
    assert closed is True


def test_pick_smallest_mp4_prefers_lowest_resolution() -> None:
    video = {
        'video_files': [
            {'file_type': 'video/mp4', 'link': 'https://x/a.mp4', 'width': 1280, 'height': 720},
            {'file_type': 'video/mp4', 'link': 'https://x/b.mp4', 'width': 640, 'height': 360},
            {'file_type': 'video/mp4', 'link': 'https://x/c.mp4', 'width': 240, 'height': 426},
            {'file_type': 'text/csv', 'link': 'https://x/d.csv'},
            {'file_type': 'video/mp4', 'link': 'http://insecure.mp4'},
        ]
    }
    chosen = pexels_mock._pick_smallest_mp4(video)
    assert chosen is not None
    assert chosen['link'] == 'https://x/c.mp4'


def test_pick_smallest_mp4_returns_none_without_mp4() -> None:
    assert pexels_mock._pick_smallest_mp4({'video_files': []}) is None
    assert pexels_mock._pick_smallest_mp4({}) is None
    assert pexels_mock._pick_smallest_mp4({'video_files': [{'file_type': 'video/mov'}]}) is None


def test_poster_url_prefers_image_field() -> None:
    video = {
        'image': 'https://images.pexels.com/preview.jpeg',
        'video_pictures': [{'picture': 'https://images.pexels.com/pic-0.jpeg'}],
    }
    url, content_type = pexels_mock._poster_url(video)
    assert url == 'https://images.pexels.com/preview.jpeg'
    assert content_type == 'image/jpeg'


def test_poster_url_falls_back_to_video_pictures() -> None:
    video = {'video_pictures': [{'picture': 'https://images.pexels.com/pic-0.jpeg'}]}
    url, content_type = pexels_mock._poster_url(video)
    assert url == 'https://images.pexels.com/pic-0.jpeg'
    assert content_type == 'image/jpeg'


def test_poster_url_returns_none_when_absent() -> None:
    url, content_type = pexels_mock._poster_url({})
    assert url is None
    assert content_type == 'image/jpeg'


# --------------------------------------------------------------------------- #
# config gating
# --------------------------------------------------------------------------- #
def test_pexels_api_key_reads_env(monkeypatch) -> None:
    monkeypatch.setenv('PEXELS_API_KEY', 'secret-key')
    assert pexels_mock.pexels_api_key() == 'secret-key'


def test_pexels_api_key_returns_none_when_unset(monkeypatch) -> None:
    monkeypatch.delenv('PEXELS_API_KEY', raising=False)
    assert pexels_mock.pexels_api_key() is None


@pytest.mark.asyncio
async def test_fetch_returns_none_when_key_missing(monkeypatch) -> None:
    monkeypatch.delenv('PEXELS_API_KEY', raising=False)
    assert await pexels_mock.fetch_pexels_mock_clip() is None


@pytest.mark.asyncio
async def test_fetch_returns_none_when_list_request_fails(monkeypatch) -> None:
    monkeypatch.setenv('PEXELS_API_KEY', 'secret-key')

    async def fake_request_json(session, url, headers, params):
        return None

    async def fake_get_session():
        return None

    monkeypatch.setattr(pexels_mock, '_request_json', fake_request_json)
    monkeypatch.setattr(pexels_mock, 'get_session', fake_get_session)
    assert await pexels_mock.fetch_pexels_mock_clip() is None


@pytest.mark.asyncio
async def test_fetch_picks_smallest_mp4_and_downloads(monkeypatch) -> None:
    monkeypatch.setenv('PEXELS_API_KEY', 'secret-key')

    payload = {
        'videos': [
            {
                'id': 1,
                'duration': 7,
                'image': 'https://images.pexels.com/poster.jpeg',
                'video_files': [
                    {'file_type': 'video/mp4', 'link': 'https://x/big.mp4', 'width': 1280, 'height': 720},
                    {'file_type': 'video/mp4', 'link': 'https://x/small.mp4', 'width': 240, 'height': 426},
                ],
            },
            # no duration -> skipped
            {'id': 2, 'duration': 0, 'video_files': []},
        ]
    }
    downloaded: dict[str, bytes] = {
        'https://x/small.mp4': b'mp4-bytes',
        'https://images.pexels.com/poster.jpeg': b'jpeg-bytes',
    }

    async def fake_request_json(session, url, headers, params):
        return payload

    async def fake_download(session, url, *, max_bytes=None):
        return downloaded.get(url)

    async def fake_get_session():
        return None

    monkeypatch.setattr(pexels_mock, '_request_json', fake_request_json)
    monkeypatch.setattr(pexels_mock, '_download_bytes', fake_download)
    monkeypatch.setattr(pexels_mock, 'get_session', fake_get_session)

    clip = await pexels_mock.fetch_pexels_mock_clip()
    assert isinstance(clip, PexelsMockClip)
    assert clip.video_bytes == b'mp4-bytes'
    assert clip.poster_bytes == b'jpeg-bytes'
    assert clip.poster_content_type == 'image/jpeg'
    assert clip.duration_seconds == 7


@pytest.mark.asyncio
async def test_fetch_returns_clip_with_empty_poster_when_download_fails(monkeypatch) -> None:
    """When the poster download fails, the clip still returns so the caller
    can synthesize a frame from the video — the whole clip must not be lost."""
    monkeypatch.setenv('PEXELS_API_KEY', 'secret-key')

    payload = {
        'videos': [
            {
                'id': 1,
                'duration': 9,
                'image': 'https://images.pexels.com/poster.jpeg',
                'video_files': [
                    {'file_type': 'video/mp4', 'link': 'https://x/small.mp4', 'width': 240, 'height': 426},
                ],
            }
        ]
    }

    async def fake_request_json(session, url, headers, params):
        return payload

    async def fake_download(session, url, *, max_bytes=None):
        return b'mp4-bytes' if url.endswith('small.mp4') else None

    async def fake_get_session():
        return None

    monkeypatch.setattr(pexels_mock, '_request_json', fake_request_json)
    monkeypatch.setattr(pexels_mock, '_download_bytes', fake_download)
    monkeypatch.setattr(pexels_mock, 'get_session', fake_get_session)

    clip = await pexels_mock.fetch_pexels_mock_clip()
    assert clip is not None
    assert clip.video_bytes == b'mp4-bytes'
    assert clip.poster_bytes == b''
    assert clip.duration_seconds == 9


# --------------------------------------------------------------------------- #
# poster-from-frame fallback
# --------------------------------------------------------------------------- #
def test_extract_poster_returns_none_for_garbage() -> None:
    assert pexels_mock.extract_poster_from_video(b'not a video') is None


def test_extract_poster_synthesizes_webp_from_real_mp4() -> None:
    from pathlib import Path

    welcome = Path(__file__).resolve().parents[5] / 'static' / 'assets' / 'welcome.mp4'
    if not welcome.is_file():
        pytest.skip('static welcome.mp4 asset unavailable')
    result = pexels_mock.extract_poster_from_video(welcome.read_bytes())
    assert result is not None
    webp_bytes, content_type = result
    assert content_type == 'image/webp'
    assert webp_bytes[:4] == b'RIFF'  # WEBP magic
    assert len(webp_bytes) > 100


# --------------------------------------------------------------------------- #
# service._finalize_mock_video dispatch (Pexels clip path vs static fallback)
# --------------------------------------------------------------------------- #
class _FakeFile:
    def __init__(self, payload: bytes, filename: str, content_type: str) -> None:
        self.id = f'file:{filename}'
        self.created_at = 1700000000
        self._payload = payload
        self.filename = filename

    async def read(self) -> bytes:
        return self._payload


class _FakeRequest:
    class _App:
        @staticmethod
        def url_path_for(name: str, *, id: str) -> str:
            return f'/api/v1/files/{id}/content'

    app = _App()


def _task() -> VideoTaskResponse:
    return VideoTaskResponse(
        id='task-1',
        status='running',
        task='text-to-video',
        prompt='A paper boat',
        model_id='kling-video-v3-pro',
        params={'duration': '5'},
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )


class _RecordingSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass


def _install_fake_upload(monkeypatch, captured: list[tuple[str, str, int]]) -> None:
    async def fake_upload_file_handler(request, *, file, metadata, process, user):
        payload = await file.read()
        content_type = (
            file.headers.get('content-type', 'application/octet-stream')
            if hasattr(file, 'headers')
            else 'application/octet-stream'
        )
        captured.append((file.filename, content_type, len(payload)))
        return _FakeFile(payload, file.filename, content_type)

    monkeypatch.setattr(delivery, 'upload_file_handler', fake_upload_file_handler)


@pytest.mark.asyncio
async def test_finalize_dispatches_to_pexels_clip(monkeypatch) -> None:
    captured: list[tuple[str, str, int]] = []
    _install_fake_upload(monkeypatch, captured)

    clip = PexelsMockClip(
        video_bytes=b'mp4-from-pexels',
        poster_bytes=b'jpeg-from-pexels',
        poster_content_type='image/jpeg',
        duration_seconds=42,
    )
    monkeypatch.setattr(
        delivery, 'fetch_pexels_mock_clip', lambda: _async_return(clip))

    session = _RecordingSession()
    result = await service._finalize_mock_video(_FakeRequest(), types.SimpleNamespace(id='u1'), _task(), session)

    assert result['duration_seconds'] == 42  # real Pexels duration wins over task param '5'
    assert result['file_id'] == 'file:generated-video.mp4'
    assert result['poster_file_id'] == 'file:generated-video-poster.jpg'
    filenames = [name for name, _ct, _size in captured]
    assert filenames == ['generated-video.mp4', 'generated-video-poster.jpg']
    assert session.added and session.added[0].kind == 'video'
    assert session.added[0].duration_seconds == 42


@pytest.mark.asyncio
async def test_finalize_synthesizes_poster_when_pexels_has_none(monkeypatch) -> None:
    captured: list[tuple[str, str, int]] = []
    _install_fake_upload(monkeypatch, captured)

    from pathlib import Path

    welcome = Path(__file__).resolve().parents[5] / 'static' / 'assets' / 'welcome.mp4'
    if not welcome.is_file():
        pytest.skip('static welcome.mp4 asset unavailable')

    clip = PexelsMockClip(
        video_bytes=welcome.read_bytes(),
        poster_bytes=b'',  # Pexels had no poster → synthesize from first frame
        poster_content_type='image/jpeg',
        duration_seconds=11,
    )
    monkeypatch.setattr(delivery, 'fetch_pexels_mock_clip', lambda: _async_return(clip))

    session = _RecordingSession()
    result = await service._finalize_mock_video(_FakeRequest(), types.SimpleNamespace(id='u1'), _task(), session)

    assert result['poster_file_id'] == 'file:generated-video-poster.webp'
    poster_upload = [c for c in captured if c[0].endswith('.webp')]
    assert poster_upload, 'a webp poster should have been uploaded'
    assert poster_upload[0][2] > 100  # synthesized webp has real content


@pytest.mark.asyncio
async def test_finalize_falls_back_to_static_assets_when_pexels_unavailable(monkeypatch) -> None:
    captured: list[tuple[str, str, int]] = []
    _install_fake_upload(monkeypatch, captured)

    monkeypatch.setattr(delivery, 'fetch_pexels_mock_clip', lambda: _async_return(None))

    session = _RecordingSession()
    result = await service._finalize_mock_video(_FakeRequest(), types.SimpleNamespace(id='u1'), _task(), session)

    # static fallback uses the task's configured duration ('5'), not a Pexels duration
    assert result['duration_seconds'] == 5
    assert result['file_id'] == 'file:generated-video.mp4'
    assert result['poster_file_id'] == 'file:generated-video-poster.webp'
    assert [name for name, _ct, _size in captured] == [
        'generated-video.mp4',
        'generated-video-poster.webp',
    ]


@pytest.mark.asyncio
async def test_finalize_clip_uses_real_duration_and_pexels_poster(monkeypatch) -> None:
    """Directly exercise _finalize_clip_mock_video with a full Pexels clip."""
    captured: list[tuple[str, str, int]] = []
    _install_fake_upload(monkeypatch, captured)

    clip = PexelsMockClip(
        video_bytes=b'the-video',
        poster_bytes=b'the-poster',
        poster_content_type='image/jpeg',
        duration_seconds=33,
    )
    session = _RecordingSession()
    result = await delivery._finalize_clip_mock_video(
        _FakeRequest(), types.SimpleNamespace(id='u1'), _task(), session, clip
    )
    assert result['duration_seconds'] == 33
    assert result['file_id'] == 'file:generated-video.mp4'
    assert result['poster_file_id'] == 'file:generated-video-poster.jpg'
    assert session.added[0].prompt == 'A paper boat'
    assert session.added[0].batch_id == 'task-1'


# --------------------------------------------------------------------------- #
# small async helper (avoids depending on a specific awaitable constructor)
# --------------------------------------------------------------------------- #
async def _async_return(value):
    return value
