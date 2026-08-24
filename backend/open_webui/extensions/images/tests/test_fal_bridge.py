from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.images import fal_bridge
from open_webui.extensions.tests.async_test_support import AsyncContext


@pytest.mark.asyncio
async def test_admission_maps_size_and_disabled_model_errors(monkeypatch) -> None:
    monkeypatch.setattr(
        'open_webui.extensions.model_ops.db.model_ops_session',
        lambda: AsyncContext(object()),
    )
    enabled = AsyncMock()
    monkeypatch.setattr('open_webui.extensions.model_ops.service.ensure_model_enabled', enabled)
    monkeypatch.setattr(fal_bridge, 'validate_fal_image_size', lambda *_args: None)
    await fal_bridge.ensure_fal_image_admission('model', object())
    enabled.assert_awaited_once()

    monkeypatch.setattr(
        fal_bridge,
        'validate_fal_image_size',
        lambda *_args: (_ for _ in ()).throw(fal_bridge.FalImageSizeError('bad')),
    )
    with pytest.raises(CreditError) as size:
        await fal_bridge.ensure_fal_image_admission('model', object())
    assert size.value.code == 'invalid_image_size'

    monkeypatch.setattr(fal_bridge, 'validate_fal_image_size', lambda *_args: None)
    enabled.side_effect = HTTPException(status_code=503, detail={'message': 'disabled'})
    with pytest.raises(CreditError) as disabled:
        await fal_bridge.ensure_fal_image_admission('model', object())
    assert disabled.value.context == {'reason': 'model_disabled', 'message': 'disabled'}


@pytest.mark.asyncio
async def test_capture_compensates_partial_upload(monkeypatch) -> None:
    monkeypatch.setattr(fal_bridge, 'extract_fal_image_urls', lambda _result: ('one', 'two'))
    cleanup = AsyncMock()
    monkeypatch.setattr(fal_bridge, 'cleanup_uploaded_files', cleanup)
    file_item = SimpleNamespace(id='file-1', user_id='user-1', created_at=1)

    async def download(url):
        if url == 'two':
            raise RuntimeError('download failed')
        return b'image', 'image/png'

    upload = AsyncMock(return_value=(file_item, '/content'))
    with pytest.raises(RuntimeError):
        await fal_bridge.capture_fal_image_result(
            SimpleNamespace(),
            object(),
            {'prompt': 'safe'},
            {'task': 'id'},
            SimpleNamespace(id='user-1'),
            download_image=download,
            upload_image=upload,
        )
    cleanup.assert_awaited_once_with([file_item])


@pytest.mark.asyncio
async def test_capture_returns_all_persisted_images(monkeypatch) -> None:
    monkeypatch.setattr(fal_bridge, 'extract_fal_image_urls', lambda _result: ('one',))
    file_item = SimpleNamespace(id='file-1', user_id='user-1', created_at=1)
    batch = await fal_bridge.capture_fal_image_result(
        SimpleNamespace(),
        object(),
        {'prompt': 'safe'},
        {'task': 'id'},
        SimpleNamespace(id='user-1'),
        download_image=AsyncMock(return_value=(b'image', 'image/png')),
        upload_image=AsyncMock(return_value=(file_item, '/content')),
    )
    assert batch.images[0].file_id == 'file-1'


@pytest.mark.asyncio
@pytest.mark.parametrize('mock_enabled', [True, False])
async def test_pipeline_selects_mock_or_real_provider_without_network(monkeypatch, mock_enabled) -> None:
    mode = AsyncMock()
    capture = AsyncMock(return_value=object())
    queue = AsyncMock(return_value={'images': []})
    observer = object()
    monkeypatch.setattr(fal_bridge, 'set_image_task_execution_mode', mode)
    monkeypatch.setattr(fal_bridge, 'capture_fal_image_result', capture)
    monkeypatch.setattr(fal_bridge, 'get_mock_fal_image_result', lambda *_args: {'mock': True})
    monkeypatch.setattr(fal_bridge, 'try_start_provider_invocation', AsyncMock(return_value=observer))
    monkeypatch.setattr(fal_bridge, 'run_fal_queue', queue)

    result = await fal_bridge.run_fal_image_pipeline(
        SimpleNamespace(),
        object(),
        {'generation_task_id': 'task-1'},
        SimpleNamespace(id='user-1'),
        fal_model='model',
        payload={'prompt': 'safe'},
        api_key='fake-key',
        api_base_url='https://queue.test',
        mock_enabled=mock_enabled,
        download_image=AsyncMock(),
        upload_image=AsyncMock(),
    )
    assert result is capture.return_value
    mode.assert_awaited_once_with('task-1', 'mock' if mock_enabled else 'fal')
    assert queue.await_count == (0 if mock_enabled else 1)
