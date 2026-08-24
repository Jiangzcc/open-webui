"""Isolated FAL image admission, provider execution, and result capture.

The upstream image router supplies its existing download/upload callbacks; this
module owns every second-development policy and keeps that router integration
limited to thin calls.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request
from open_webui.extensions.creations.file_cleanup import cleanup_uploaded_files
from open_webui.extensions.creations.generation_tasks import set_image_task_execution_mode
from open_webui.extensions.creations.schemas import CapturedImageBatch, CapturedImageResult
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.provider_ops.service import try_start_provider_invocation
from open_webui.utils.images.fal import (
    FalImageSizeError,
    extract_fal_image_urls,
    get_mock_fal_image_result,
    run_fal_queue,
    validate_fal_image_size,
)

log = logging.getLogger(__name__)

DownloadImage = Callable[[str], Awaitable[tuple[bytes, str]]]
UploadImage = Callable[[Request, bytes, str, dict[str, object], object], Awaitable[tuple[object, object]]]


async def ensure_fal_image_admission(candidate: str, form_data: object) -> None:
    """Validate size and operations state before any paid provider request."""
    from open_webui.extensions.model_ops.db import model_ops_session
    from open_webui.extensions.model_ops.service import ensure_model_enabled

    try:
        validate_fal_image_size(candidate, form_data)
    except FalImageSizeError as error:
        raise CreditError(
            code='invalid_image_size',
            context={'reason': 'custom_size_constraints'},
        ) from error
    try:
        async with model_ops_session() as session:
            await ensure_model_enabled(session, candidate)
    except HTTPException as error:
        detail = getattr(error, 'detail', None)
        message = detail.get('message') if isinstance(detail, dict) else None
        raise CreditError(
            code='provider_failed',
            context={'reason': 'model_disabled', 'message': message or 'Image model is unavailable'},
        ) from error


async def capture_fal_image_result(
    request: Request,
    result: object,
    payload: dict[str, object],
    metadata: dict[str, object],
    user: object,
    *,
    download_image: DownloadImage,
    upload_image: UploadImage,
) -> CapturedImageBatch:
    """Persist a completed provider result, compensating every partial upload."""
    images: list[CapturedImageResult] = []
    uploaded_files: list[object] = []
    try:
        for image_url in extract_fal_image_urls(result):
            image_data, content_type = await download_image(image_url)
            file_item, url = await upload_image(
                request,
                image_data,
                content_type,
                {**payload, **metadata},
                user,
            )
            uploaded_files.append(file_item)
            images.append(
                CapturedImageResult(
                    url=str(url),
                    file_id=file_item.id,
                    file_user_id=file_item.user_id,
                    file_created_at=file_item.created_at,
                    mime_type=content_type,
                )
            )
    except BaseException:
        await cleanup_uploaded_files(uploaded_files)
        raise
    return CapturedImageBatch(images=tuple(images))


async def run_fal_image_pipeline(
    request: Request,
    form_data: object,
    metadata: dict[str, object],
    user: object,
    *,
    fal_model: str,
    payload: dict[str, object],
    api_key: str,
    api_base_url: str,
    mock_enabled: bool,
    download_image: DownloadImage,
    upload_image: UploadImage,
) -> CapturedImageBatch:
    """Execute mock/real FAL once, then persist its result through router APIs."""
    task_id = metadata.get('generation_task_id')
    await set_image_task_execution_mode(
        task_id if isinstance(task_id, str) else None,
        'mock' if mock_enabled else 'fal',
    )
    if mock_enabled:
        log.info('Using mocked fal.ai image result for %s', fal_model)
        result = get_mock_fal_image_result(fal_model, form_data)
    else:
        observer = await try_start_provider_invocation(
            task_id=task_id,
            user_id=str(getattr(user, 'id', '')),
            media_kind='image',
            provider='fal',
            provider_model_id=fal_model,
            payload=payload,
        )
        result = await run_fal_queue(fal_model, payload, api_key, api_base_url, observer=observer)
    return await capture_fal_image_result(
        request,
        result,
        payload,
        metadata,
        user,
        download_image=download_image,
        upload_image=upload_image,
    )


__all__ = ['capture_fal_image_result', 'ensure_fal_image_admission', 'run_fal_image_pipeline']
