from __future__ import annotations

import base64
import binascii
import hashlib
import io
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING

from open_webui.extensions.creations.metrics import creation_metrics
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.schemas import (
    CapturedImageBatch,
    CapturedImageResult,
    CapturedReferenceResult,
    CreationCaptureContext,
    PreparedReference,
    ReusedImageResult,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

upload_file_handler = None  # lazily bound on first use; tests monkeypatch this name

_MIME_BY_EXTENSION = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/webp': '.webp',
}
_SUPPORTED_REFERENCE_MIME_TYPES = frozenset(_MIME_BY_EXTENSION)
_MAGIC_PREFIXES = (
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'\xff\xd8\xff', 'image/jpeg'),
)
_PARAM_WHITELIST = (
    'size',
    'resolution',
    'aspect_ratio',
    'quality',
    'image_count',
    'background',
    'steps',
    'guidance_scale',
    'seed',
    'style',
    'output_format',
    'system_prompt',
    'sync_mode',
    'safety_tolerance',
    'limit_generations',
    'enable_web_search',
    'thinking_level',
    'enable_safety_checker',
    'enable_prompt_expansion',
    'acceleration',
    'input_fidelity',
)


def _detect_mime(payload: bytes) -> str | None:
    if len(payload) >= 12 and payload.startswith(b'RIFF') and payload[8:12] == b'WEBP':
        return 'image/webp'
    for prefix, mime in _MAGIC_PREFIXES:
        if payload.startswith(prefix):
            return mime
    return None


def _decode_one_data_url(value: object) -> tuple[bytes, str]:
    if not isinstance(value, str) or not value.startswith('data:') or ';base64,' not in value:
        raise ValueError('reference image must be a normalized base64 data url')
    header, _, encoded = value.partition(';base64,')
    declared_mime = header[len('data:') :]
    if declared_mime not in _SUPPORTED_REFERENCE_MIME_TYPES:
        raise ValueError('reference image has an unsupported mime type')
    try:
        payload = base64.b64decode(encoded.encode('ascii'), validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError('reference image payload is not valid base64') from error
    detected = _detect_mime(payload)
    if detected is None or detected != declared_mime:
        raise ValueError('reference image mime type does not match its bytes')
    return payload, declared_mime


def decode_prepared_references(prepared: object) -> tuple[PreparedReference, ...]:
    provider_input = getattr(prepared, 'provider_input', None)
    image = getattr(provider_input, 'image', None) if provider_input is not None else None
    if image is None:
        return ()
    if isinstance(image, str):
        image_sequence: tuple[str, ...] = (image,)
    elif isinstance(image, (tuple, list)):
        image_sequence = tuple(image)
    else:
        raise ValueError('reference image input must be a string or a sequence of strings')

    hashes = getattr(getattr(prepared, 'billing', None), 'reference_hashes', ())
    if not isinstance(hashes, tuple):
        hashes = tuple(hashes)
    if len(image_sequence) != len(hashes):
        raise ValueError('reference count does not match prepared billing hashes')

    prepared_references: list[PreparedReference] = []
    for position, (value, expected_hash) in enumerate(zip(image_sequence, hashes, strict=True)):
        payload, mime_type = _decode_one_data_url(value)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected_hash:
            raise ValueError('reference hash does not match prepared billing hash')
        prepared_references.append(
            PreparedReference(payload=payload, mime_type=mime_type, sha256=digest, position=position)
        )
    return tuple(prepared_references)


async def capture_reference_snapshots(
    request: object,
    references: Sequence[PreparedReference],
    user: object,
) -> tuple[CapturedReferenceResult, ...]:
    global upload_file_handler
    from starlette.datastructures import UploadFile

    if upload_file_handler is None:
        from open_webui.routers.files import upload_file_handler as _handler

        upload_file_handler = _handler

    captured: list[CapturedReferenceResult] = []
    for reference in references:
        extension = _MIME_BY_EXTENSION[reference.mime_type]
        file = UploadFile(
            file=io.BytesIO(reference.payload),
            filename=f'creation-reference-{reference.position}{extension}',
            headers={'content-type': reference.mime_type},
        )
        try:
            file_item = await upload_file_handler(
                request,
                file=file,
                metadata={'creation_reference': True},
                process=False,
                user=user,
            )
        except Exception:
            creation_metrics.reference_capture_failed(task=None, source=None)
            raise
        captured.append(
            CapturedReferenceResult(
                file_id=file_item.id,
                file_user_id=file_item.user_id,
                file_created_at=file_item.created_at,
                mime_type=reference.mime_type,
                sha256=reference.sha256,
                position=reference.position,
            )
        )
    return tuple(captured)


def _allowlisted_params(provider_input: object, raw_negative_prompt: str | None) -> dict[str, object]:
    params: dict[str, object] = {}
    for key in _PARAM_WHITELIST:
        value = getattr(provider_input, key, None) if hasattr(provider_input, key) else None
        if value is None:
            extra = getattr(provider_input, 'extra', None)
            if isinstance(extra, Mapping):
                value = extra.get(key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        params[key] = value
    return params


def _normalize_negative_prompt(raw: object, provider_input: object) -> str | None:
    candidates: Iterable[object] = (raw,)
    extra = getattr(provider_input, 'extra', None)
    if isinstance(extra, Mapping):
        candidates = (raw, extra.get('negative_prompt'))
    for candidate in candidates:
        if isinstance(candidate, str):
            stripped = candidate.strip()
            if stripped:
                return stripped
    return None


def build_creation_capture_context(
    raw_form: object,
    prepared: object,
    user: object,
    usage_id: str,
    generation_task_id: str | None = None,
) -> CreationCaptureContext:
    from open_webui.utils.images.fal_models import normalize_fal_image_model_id, public_fal_image_model_id

    billing = getattr(prepared, 'billing', None)
    provider_input = getattr(prepared, 'provider_input', None)
    resource_id = getattr(billing, 'resource_id', None)
    internal_model = (
        normalize_fal_image_model_id(resource_id) if isinstance(resource_id, str) and '/' in resource_id else None
    )
    public_model_id = public_fal_image_model_id(internal_model) if internal_model is not None else resource_id
    model_name_snapshot = None
    if internal_model is not None:
        from open_webui.utils.images.fal_models import FAL_IMAGE_MODELS

        registered_model = next((model for model in FAL_IMAGE_MODELS if model.get('id') == internal_model), None)
        if registered_model is not None and isinstance(registered_model.get('name'), str):
            model_name_snapshot = registered_model['name']

    raw_negative = getattr(raw_form, 'negative_prompt', None)
    negative_prompt = _normalize_negative_prompt(raw_negative, provider_input)
    prompt = getattr(provider_input, 'prompt', '') or getattr(raw_form, 'prompt', '')

    return CreationCaptureContext(
        user_id=getattr(user, 'id'),
        task=getattr(billing, 'action'),
        source=getattr(billing, 'channel'),
        prompt=prompt,
        negative_prompt=negative_prompt,
        public_model_id=public_model_id,
        model_name_snapshot=model_name_snapshot,
        params=_allowlisted_params(provider_input, raw_negative),
        batch_id=generation_task_id or usage_id,
    )


def _reference_ids_match(existing: object, incoming: list[str]) -> bool:
    existing_value = getattr(existing, 'reference_file_ids_json', None)
    if existing_value is None:
        return not incoming
    if not isinstance(existing_value, list):
        existing_value = list(existing_value)
    return existing_value == incoming


async def _load_existing(session: AsyncSession, file_id: str) -> CreationMediaItem | None:
    result = await session.execute(select(CreationMediaItem).where(CreationMediaItem.file_id == file_id).limit(1))
    return result.scalar_one_or_none()


async def _insert_creation(
    session: AsyncSession,
    context: CreationCaptureContext,
    result: CapturedImageResult,
    reference_ids: list[str],
) -> CreationMediaItem:
    item = CreationMediaItem(
        id=uuid.uuid4().hex,
        user_id=context.user_id,
        kind='image',
        file_id=result.file_id,
        caption=None,
        prompt=context.prompt,
        negative_prompt=context.negative_prompt,
        model_id=context.public_model_id,
        model_name_snapshot=context.model_name_snapshot,
        task=context.task,
        params_json=dict(context.params),
        reference_file_ids_json=list(reference_ids) or None,
        source=context.source,
        batch_id=context.batch_id,
        soft_deleted=False,
        created_at=result.file_created_at,
        updated_at=result.file_created_at,
    )
    session.add(item)
    await session.flush()
    return item


async def _verify_replay(
    existing: CreationMediaItem,
    context: CreationCaptureContext,
    result: CapturedImageResult,
    reference_ids: list[str],
) -> None:
    mismatches = (
        existing.user_id != context.user_id,
        existing.kind != 'image',
        existing.file_id != result.file_id,
        existing.task != context.task,
        existing.source != context.source,
        existing.batch_id != context.batch_id,
        existing.prompt != context.prompt,
        existing.negative_prompt != context.negative_prompt,
        existing.model_id != context.public_model_id,
        existing.model_name_snapshot != context.model_name_snapshot,
        existing.params_json != dict(context.params),
        existing.created_at != result.file_created_at,
        not _reference_ids_match(existing, reference_ids),
    )
    if any(mismatches):
        raise RuntimeError('creation immutable identity conflict')


async def finalize_created_images(
    session: AsyncSession,
    context: CreationCaptureContext,
    batch: CapturedImageBatch,
) -> None:
    images = batch.images
    has_reused = any(isinstance(item, ReusedImageResult) for item in images)
    has_captured = any(isinstance(item, CapturedImageResult) for item in images)
    if has_reused and has_captured:
        creation_metrics.capture_failed(task=context.task, source=context.source)
        raise RuntimeError('creation batch mixes reused and captured results')
    if has_reused and not has_captured:
        return

    for reference in batch.references:
        if reference.file_user_id != context.user_id:
            creation_metrics.capture_failed(task=context.task, source=context.source)
            raise RuntimeError('creation file ownership mismatch')

    reference_ids = [reference.file_id for reference in batch.references]
    if [reference.position for reference in batch.references] != list(range(len(batch.references))) or len(
        reference_ids
    ) != len(set(reference_ids)):
        creation_metrics.capture_failed(task=context.task, source=context.source)
        raise RuntimeError('invalid creation reference identity')

    try:
        for result in images:
            if not isinstance(result, CapturedImageResult):
                continue
            if result.file_user_id != context.user_id:
                raise RuntimeError('creation file ownership mismatch')
            existing = await _load_existing(session, result.file_id)
            if existing is None:
                await _insert_creation(session, context, result, reference_ids)
            else:
                await _verify_replay(existing, context, result, reference_ids)
    except Exception:
        creation_metrics.capture_failed(task=context.task, source=context.source)
        raise

    captured_count = sum(1 for item in images if isinstance(item, CapturedImageResult))
    creation_metrics.capture_succeeded(task=context.task, source=context.source, count=captured_count)


__all__ = [
    'build_creation_capture_context',
    'capture_reference_snapshots',
    'decode_prepared_references',
    'finalize_created_images',
]
