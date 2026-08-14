from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.image_billing import credit_session
from open_webui.extensions.credits.repository import get_balance_if_exists, get_enabled_price
from open_webui.extensions.credits.schemas import UserSnapshot
from open_webui.extensions.credits.service import (
    SafeProviderError,
    begin_image_usage,
    mark_usage_failed,
    mark_usage_invoking,
    mark_usage_succeeded_in_session,
)
from open_webui.extensions.fal_catalog import load_video_catalog
from open_webui.extensions.videos.schemas import VideoTaskResponse, VideoTaskSubmitForm


@dataclass(frozen=True)
class VideoQuoteResult:
    """报价预检结果（不扣费、不占位）。

    用于 submit_video_task 调度前的配额前置校验：余额不足或未配置定价时
    直接拒绝，避免任务进 run_video_task 才发现余额不足。
    """

    configured: bool
    sufficient: bool
    balance: int
    charged_credits: int | None
    error: str | None


def video_quote_dimensions(task: VideoTaskSubmitForm | VideoTaskResponse) -> dict[str, str | int]:
    """从提交表单或任务响应归一化计费维度（复用 quote_video 的维度逻辑）。"""
    params = task.params
    duration = params.get('duration', 1)
    normalized_duration: str | int = str(duration) if duration in {'auto', '0'} else max(1, round(float(duration)))
    dimensions: dict[str, str | int] = {
        'duration': normalized_duration,
        'resolution': str(params.get('resolution', 'default')),
        'aspect_ratio': str(params.get('aspect_ratio', 'default')),
        'audio_mode': str(params.get('audio_mode', 'default')),
    }
    if params.get('fps') is not None:
        dimensions['fps'] = str(params['fps'])
    if params.get('output_quality') is not None:
        dimensions['output_quality'] = str(params['output_quality'])
    return dimensions


def _resolve_internal_model_id(public_model_id: str) -> str:
    catalog = load_video_catalog()
    internal_id = catalog.public_to_internal.get(public_model_id)
    if internal_id is None:
        raise CreditError(code='price_rule_incomplete', context={'reason': 'invalid_video_model'})
    return internal_id


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
    internal_id = _resolve_internal_model_id(task.model_id)
    return VideoBillingContext(
        service_type='video',
        resource_id=internal_id,
        action=task.task,
        channel='web',
        dimensions=MappingProxyType(video_quote_dimensions(task)),
        request_hash=_request_hash(task),
    )


async def quote_video_usage(user: object, submission: VideoTaskSubmitForm) -> VideoQuoteResult:
    """提交前只读报价预检：校验定价已配置 + 余额充足。

    不扣费、不占幂等位。余额不足或未配置时抛 CreditError，由 router 转 402。
    """
    from open_webui.extensions.credits.pricing import compute_price
    from open_webui.extensions.videos.catalog import build_video_provider_payload

    snapshot = UserSnapshot(
        id=getattr(user, 'id'),
        name=getattr(user, 'name', None),
        email=getattr(user, 'email', None),
    )
    internal_id = _resolve_internal_model_id(submission.model)
    _definition, _provider_payload, safe_params = build_video_provider_payload(submission)
    normalized_submission = submission.model_copy(update={'params': safe_params})
    dimensions = video_quote_dimensions(normalized_submission)
    async with credit_session() as session:
        balance = await get_balance_if_exists(session, snapshot.id)
        price = await get_enabled_price(session, 'video', internal_id, submission.task)
        if price is None:
            raise CreditError(code='price_not_configured')
        quote = compute_price(price, dimensions)
        if balance < quote.charged_credits:
            raise CreditError(code='insufficient_credits', context={'required': quote.charged_credits})
        return VideoQuoteResult(
            configured=True,
            sufficient=True,
            balance=balance,
            charged_credits=quote.charged_credits,
            error=None,
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
    # 视频任务失败默认退预扣积分，对齐图片 cancel 路径的 restore_prepaid=True
    # （image_billing.py:377-378）。否则失败后积分会卡在 invoking，只能等
    # 后台 recovery worker 标 unknown 再对账，用户拿不到即时退款。
    await mark_usage_failed(
        usage_id,
        SafeProviderError(code=code[:64], summary='Video generation failed'),
        restore_prepaid=True,
    )


__all__ = [
    'VideoQuoteResult',
    'begin_video_usage',
    'credit_session',
    'mark_usage_succeeded_in_session',
    'mark_video_usage_failed',
    'mark_video_usage_invoking',
    'quote_video_usage',
    'video_billing_context',
    'video_quote_dimensions',
]
