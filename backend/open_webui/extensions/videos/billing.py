from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from open_webui.extensions.credits.image_billing import credit_session
from open_webui.extensions.credits.schemas import UserSnapshot
from open_webui.extensions.credits.service import (
    SafeProviderError,
    begin_image_usage,
    mark_usage_failed,
    mark_usage_invoking,
    mark_usage_succeeded_in_session,
)
from open_webui.extensions.fal_catalog import load_video_catalog
from open_webui.extensions.videos.schemas import VideoTaskResponse


@dataclass(frozen=True)
class VideoBillingContext:
    service_type: str
    resource_id: str
    action: str
    channel: str
    dimensions: Mapping[str, str | int]
    request_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, 'dimensions', MappingProxyType(dict(self.dimensions)))


def _request_hash(task: VideoTaskResponse) -> str:
    payload = {
        'task': task.task,
        'model': task.model_id,
        'prompt': task.prompt,
        'params': task.params,
        'assets': [asset.model_dump() for asset in task.assets],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def video_billing_context(task: VideoTaskResponse) -> VideoBillingContext:
    catalog = load_video_catalog()
    internal_id = catalog.public_to_internal.get(task.model_id)
    if internal_id is None:
        raise ValueError('unknown_video_model')
    duration = task.params.get('duration', 1)
    normalized_duration: str | int = str(duration) if duration in {'auto', '0'} else max(1, round(float(duration)))
    dimensions = {
        'duration': normalized_duration,
        'resolution': str(task.params.get('resolution', 'default')),
        'aspect_ratio': str(task.params.get('aspect_ratio', 'default')),
        'audio_mode': str(task.params.get('audio_mode', 'default')),
        **({'fps': str(task.params['fps'])} if task.params.get('fps') is not None else {}),
        **(
            {'output_quality': str(task.params['output_quality'])}
            if task.params.get('output_quality') is not None
            else {}
        ),
    }
    return VideoBillingContext(
        service_type='video',
        resource_id=internal_id,
        action=task.task,
        channel='web',
        dimensions=dimensions,
        request_hash=_request_hash(task),
    )


async def begin_video_usage(user: object, task: VideoTaskResponse):
    snapshot = UserSnapshot(
        id=getattr(user, 'id'),
        name=getattr(user, 'name', None),
        email=getattr(user, 'email', None),
    )
    async with credit_session() as session:
        return await begin_image_usage(
            session,
            snapshot,
            video_billing_context(task),
            f'video:{task.id}',
        )


async def mark_video_usage_invoking(usage_id: str) -> None:
    if await mark_usage_invoking(usage_id) != 1:
        raise RuntimeError('video usage invoking transition failed')


async def mark_video_usage_failed(usage_id: str, code: str) -> None:
    await mark_usage_failed(
        usage_id,
        SafeProviderError(code=code[:64], summary='Video generation failed'),
    )


__all__ = [
    'begin_video_usage',
    'credit_session',
    'mark_usage_succeeded_in_session',
    'mark_video_usage_failed',
    'mark_video_usage_invoking',
    'video_billing_context',
]
