from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import aiofiles
from fastapi import Request
from open_webui.env import AIOHTTP_CLIENT_SESSION_SSL, AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition, VideoAssetInput
from open_webui.extensions.provider_ops.service import (
    DatabaseProviderInvocationObserver,
    try_resume_provider_invocation,
    try_start_provider_invocation,
)
from open_webui.extensions.videos.pexels_mock import probe_video_duration
from open_webui.extensions.videos.schemas import VideoAssetReference, VideoTaskResponse
from open_webui.models.config import Config
from open_webui.models.files import Files
from open_webui.storage.provider import Storage
from open_webui.extensions.fal_images.client import FalImageError, resume_fal_queue, run_fal_queue

log = logging.getLogger(__name__)

_DEFAULT_QUEUE_BASE_URL = 'https://queue.fal.run'
_DEFAULT_STORAGE_BASE_URL = 'https://rest.fal.ai'
_DEFAULT_TIMEOUT_SECONDS = 15 * 60
_DEFAULT_RESULT_MAX_BYTES = 500 * 1024 * 1024
_DEFAULT_UPLOAD_LIFETIME_SECONDS = 24 * 60 * 60
_DEFAULT_DELIVERY_MAX_ATTEMPTS = 3
_DEFAULT_RETRY_BASE_DELAY_SECONDS = 1
_DEFAULT_TEMP_MAX_AGE_SECONDS = 24 * 60 * 60
_TEMP_FILE_PREFIX = 'open-webui-fal-video-'
# 复盘 P1：大文件传输（视频上传/下载）的超时配置——大文件正常传输也可能
# 超过 5 分钟，不能用共享池的 total=300s 总超时（会把正常传输砍断成
# download_failed）；改用连接建立超时 + 读空闲超时（复用共享流会话的同一
# 环境变量旋钮）检测挂死，体积上限由 max_bytes 约束。
_TRANSFER_CONNECT_TIMEOUT_SECONDS = 10
_TRANSFER_READ_IDLE_TIMEOUT_SECONDS = int(AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT or 60)
_TRANSFER_CHUNK_SIZE_BYTES = 1024 * 1024


def _retryable_http_status(status_code: int | None) -> bool:
    """408 超时 / 429 限流 / 5xx 服务端错误视为可重试；无状态码不可重试。"""
    return status_code is not None and (status_code in {408, 429} or status_code >= 500)
# 运营中心管理端持久化配置键（Config 表）
_VIDEO_FAL_MOCK_ENABLED_KEY = 'video_generation.fal.mock_enabled'
_VIDEO_FAL_API_KEY_KEY = 'video_generation.fal.api_key'
_IMAGE_FAL_API_KEY_KEY = 'image_generation.fal.api_key'
_MOCK_SCENARIOS = frozenset(
    {
        'success',
        'slow',
        'provider_timeout',
        'provider_failure',
        'rate_limit',
        'malformed_result',
        'oversized_result',
        'delivery_failure',
    }
)


class VideoExecutionError(Exception):
    def __init__(
        self,
        code: str,
        message: str | None = None,
        *,
        provider_submitted: bool = False,
        provider_completed: bool = False,
        retryable: bool = False,
    ):
        super().__init__(message or code)
        self.code = code[:64]
        # Once FAL reports success, delivery failures must not be treated like
        # provider failures: the upstream cost may already be final.
        self.provider_submitted = provider_submitted or provider_completed
        self.provider_completed = provider_completed
        self.retryable = retryable


@dataclass(frozen=True)
class VideoExecutionOutput:
    video_path: Path
    content_type: str
    duration_seconds: int | None = None


ProviderSubmittedCallback = Callable[[dict[str, object]], Awaitable[None]]
ProviderResultCallback = Callable[[str], Awaitable[None]]


class _VideoProviderObserver:
    def __init__(self, base: object | None, on_submitted: ProviderSubmittedCallback | None):
        self._base = base
        self._on_submitted = on_submitted

    async def _base_call(self, method: str, *args: object) -> None:
        if self._base is not None:
            await getattr(self._base, method)(*args)

    async def submitted(self, payload: dict[str, object]) -> None:
        # Persist Provider Ops first so request_id still has an authoritative
        # diagnostic record if the task-specific recovery write fails.
        # 注意：run_fal_queue 对 observer 回调按 best-effort 吞异常
        # （extensions/fal_images/client.py _notify_provider），提交状态写入
        # 失败不会中断生成。恢复路径的兜底是 video_recovery_state_missing 时
        # 按"供应商受理未确认"退款（service.recover_video_task）。
        await self._base_call('submitted', payload)
        if self._on_submitted is not None:
            await self._on_submitted(payload)

    async def status(self, payload: dict[str, object]) -> None:
        await self._base_call('status', payload)

    async def succeeded(self) -> None:
        await self._base_call('succeeded')

    async def failed(self, error: BaseException) -> None:
        await self._base_call('failed', error)


@dataclass(frozen=True)
class MockVideoExecutor:
    mode: str = 'mock'


@dataclass(frozen=True)
class FalVideoExecutor:
    api_key: str
    queue_base_url: str
    storage_base_url: str
    timeout_seconds: float
    result_max_bytes: int
    upload_lifetime_seconds: int
    mode: str = 'fal'

    async def invoke(  # noqa: C901 - provider and local-delivery phases share one cost boundary
        self,
        request: Request,
        user: object,
        task: VideoTaskResponse,
        definition: FalVideoModelDefinition,
        provider_payload: dict[str, object],
        *,
        on_submitted: ProviderSubmittedCallback | None = None,
        on_result_url: ProviderResultCallback | None = None,
    ) -> VideoExecutionOutput:
        del request
        payload = dict(provider_payload)
        await inject_fal_asset_urls(
            payload,
            task,
            definition,
            user_id=str(getattr(user, 'id', '')),
            api_key=self.api_key,
            storage_base_url=self.storage_base_url,
            upload_lifetime_seconds=self.upload_lifetime_seconds,
        )
        provider_observer = await try_start_provider_invocation(
            task_id=task.id,
            user_id=str(getattr(user, 'id', '')),
            media_kind='video',
            provider='fal',
            provider_model_id=definition.id,
            payload=payload,
        )
        observer = (
            provider_observer
            if on_submitted is None
            else _VideoProviderObserver(provider_observer, on_submitted)
        )
        try:
            result = await run_fal_queue(
                definition.id,
                payload,
                self.api_key,
                self.queue_base_url,
                observer=observer,
                timeout_seconds=self.timeout_seconds,
            )
        except asyncio.CancelledError:
            raise
        except FalImageError as error:
            code = 'video_provider_timeout' if 'timed out' in str(error).lower() else 'video_provider_failed'
            raise VideoExecutionError(
                code,
                str(error),
                provider_submitted=bool(getattr(error, 'provider_submitted', False)),
                provider_completed=bool(getattr(error, 'provider_completed', False)),
                retryable=code == 'video_provider_timeout' or _retryable_http_status(error.status_code),
            ) from error
        except Exception as error:
            provider_submitted = bool(getattr(error, 'provider_submitted', False))
            raise VideoExecutionError(
                'video_provider_failed',
                str(error),
                provider_submitted=provider_submitted,
                provider_completed=bool(getattr(error, 'provider_completed', False)),
                retryable=provider_submitted,
            ) from error

        video_path: Path | None = None
        try:
            video_url = extract_fal_video_url(result, definition.output_field)
            if video_url is None:
                raise VideoExecutionError('video_result_missing')
            if on_result_url is not None:
                await on_result_url(video_url)
            video_path, content_type = await download_fal_video_with_retry(
                video_url,
                max_bytes=self.result_max_bytes,
            )
            if content_type in {'application/octet-stream', 'video/mp4'}:
                if not await asyncio.to_thread(_looks_like_mp4_file, video_path):
                    raise VideoExecutionError('video_result_invalid_type')
                content_type = 'video/mp4'
            if content_type not in definition.output_mime_types:
                raise VideoExecutionError('video_result_invalid_type')
            actual_duration = await asyncio.to_thread(probe_video_duration, video_path)
            return VideoExecutionOutput(
                video_path=video_path,
                content_type=content_type,
                duration_seconds=actual_duration or _task_duration_seconds(task),
            )
        except asyncio.CancelledError as error:
            # Preserve asyncio cancellation while telling the billing layer that
            # FAL had already completed before local delivery was interrupted.
            setattr(error, 'provider_completed', True)
            if video_path is not None:
                await _remove_file(video_path)
            raise
        except VideoExecutionError as error:
            if video_path is not None:
                await _remove_file(video_path)
            raise VideoExecutionError(
                error.code,
                str(error),
                provider_submitted=error.provider_submitted,
                provider_completed=True,
                retryable=error.retryable,
            ) from error
        except Exception as error:
            if video_path is not None:
                await _remove_file(video_path)
            raise VideoExecutionError(
                'video_delivery_failed',
                str(error),
                provider_completed=True,
            ) from error

    async def resume(  # noqa: C901 - recovery distinguishes provider polling, URL refresh, and delivery
        self,
        task: VideoTaskResponse,
        definition: FalVideoModelDefinition,
        *,
        status_url: str | None,
        response_url: str | None,
        result_url: str | None,
        provider_request_id: str | None = None,
        on_result_url: ProviderResultCallback | None = None,
    ) -> VideoExecutionOutput:
        """Resume polling/delivery for a request that FAL already accepted."""
        video_path: Path | None = None
        observer: DatabaseProviderInvocationObserver | None = None
        observer_terminal_notified = False
        try:
            observer = (
                await try_resume_provider_invocation(
                    task_id=task.id,
                    provider_request_id=provider_request_id,
                )
                if provider_request_id is not None
                else None
            )
            video_url = result_url
            if video_url is None:
                if response_url is None:
                    raise VideoExecutionError('video_recovery_state_missing')
                try:
                    result = await resume_fal_queue(
                        status_url=status_url,
                        response_url=response_url,
                        api_key=self.api_key,
                        observer=observer,
                        timeout_seconds=self.timeout_seconds,
                    )
                finally:
                    # client 层对成功、失败与取消都会通知 observer 终态。
                    observer_terminal_notified = True
                video_url = extract_fal_video_url(result, definition.output_field)
                if video_url is None:
                    raise VideoExecutionError('video_result_missing')
                if on_result_url is not None:
                    await on_result_url(video_url)
            elif observer is not None:
                await observer.succeeded()
                observer_terminal_notified = True
            try:
                video_path, content_type = await download_fal_video_with_retry(
                    video_url,
                    max_bytes=self.result_max_bytes,
                )
            except VideoExecutionError as error:
                # A persisted signed media URL may expire while the service is
                # offline. Re-fetch the existing response object for a fresh URL;
                # this is still a GET-only recovery path, never a generation POST.
                if result_url is None or response_url is None or error.code != 'video_result_download_failed':
                    raise
                result = await resume_fal_queue(
                    status_url=None,
                    response_url=response_url,
                    api_key=self.api_key,
                    observer=observer,
                    timeout_seconds=self.timeout_seconds,
                )
                video_url = extract_fal_video_url(result, definition.output_field)
                if video_url is None:
                    raise VideoExecutionError('video_result_missing') from error
                if on_result_url is not None:
                    await on_result_url(video_url)
                video_path, content_type = await download_fal_video_with_retry(
                    video_url,
                    max_bytes=self.result_max_bytes,
                )
            if content_type in {'application/octet-stream', 'video/mp4'}:
                if not await asyncio.to_thread(_looks_like_mp4_file, video_path):
                    raise VideoExecutionError('video_result_invalid_type')
                content_type = 'video/mp4'
            if content_type not in definition.output_mime_types:
                raise VideoExecutionError('video_result_invalid_type')
            actual_duration = await asyncio.to_thread(probe_video_duration, video_path)
            return VideoExecutionOutput(
                video_path=video_path,
                content_type=content_type,
                duration_seconds=actual_duration or _task_duration_seconds(task),
            )
        except asyncio.CancelledError as error:
            await _mark_observer_failed_if_pending(
                observer, error, terminal_notified=observer_terminal_notified
            )
            setattr(error, 'provider_submitted', True)
            if video_path is not None:
                await _remove_file(video_path)
            raise
        except VideoExecutionError as error:
            await _mark_observer_failed_if_pending(
                observer, error, terminal_notified=observer_terminal_notified
            )
            if video_path is not None:
                await _remove_file(video_path)
            raise VideoExecutionError(
                error.code,
                str(error),
                provider_submitted=True,
                provider_completed=bool(result_url) or error.provider_completed,
                retryable=error.retryable,
            ) from error
        except FalImageError as error:
            await _mark_observer_failed_if_pending(
                observer, error, terminal_notified=observer_terminal_notified
            )
            if video_path is not None:
                await _remove_file(video_path)
            code = 'video_provider_timeout' if 'timed out' in str(error).lower() else 'video_provider_failed'
            raise VideoExecutionError(
                code,
                str(error),
                provider_submitted=True,
                provider_completed=bool(getattr(error, 'provider_completed', False)),
                retryable=code == 'video_provider_timeout' or _retryable_http_status(error.status_code),
            ) from error
        except Exception as error:
            await _mark_observer_failed_if_pending(
                observer, error, terminal_notified=observer_terminal_notified
            )
            if video_path is not None:
                await _remove_file(video_path)
            raise VideoExecutionError(
                'video_delivery_failed',
                str(error),
                provider_submitted=True,
                provider_completed=bool(result_url),
            ) from error


async def _mark_observer_failed_if_pending(
    observer: DatabaseProviderInvocationObserver | None,
    error: BaseException,
    *,
    terminal_notified: bool,
) -> None:
    """复盘 P1：恢复路径此前只在成功时通知 observer（快速路径 succeeded /
    轮询路径由 resume_fal_queue 内部通知），executor 自身的失败——恢复状态
    缺失、结果 URL 提取失败、下载与校验失败——全程不通知 failed，
    provider_invocation 行停留无终态（在线路径 run_fal_queue 两个 except
    都会通知）。供应商调用已成功（terminal_notified）后的平台侧交付失败
    不属于供应商调用失败，不得覆盖 succeeded。"""
    if observer is None or terminal_notified:
        return
    await observer.failed(error)


def _positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        log.warning('Ignoring invalid %s=%r', name, value)
        return default
    if parsed <= 0:
        log.warning('Ignoring non-positive %s=%r', name, value)
        return default
    return parsed


async def get_video_fal_settings() -> tuple[bool, str]:
    """运营中心管理端 FAL 配置：返回 (mock 开关, 视频 API key)。

    视频侧 key 为空时回落到图片生成侧 key，方便单一 key 的部署。
    """
    values = await Config.get_many(
        _VIDEO_FAL_MOCK_ENABLED_KEY,
        _VIDEO_FAL_API_KEY_KEY,
        _IMAGE_FAL_API_KEY_KEY,
    )
    mock_enabled = bool(values.get(_VIDEO_FAL_MOCK_ENABLED_KEY, False))
    video_key = values.get(_VIDEO_FAL_API_KEY_KEY)
    image_key = values.get(_IMAGE_FAL_API_KEY_KEY)
    api_key = video_key.strip() if isinstance(video_key, str) else ''
    if not api_key and isinstance(image_key, str):
        api_key = image_key.strip()
    return mock_enabled, api_key


async def resolve_video_executor() -> MockVideoExecutor | FalVideoExecutor:
    """按管理端配置解析视频执行器：mock 开关开启时返回 Mock，否则走真实 FAL。"""
    mock_enabled, api_key = await get_video_fal_settings()
    if mock_enabled:
        scenario = os.getenv('VIDEO_GENERATION_MOCK_SCENARIO', 'success').strip().lower()
        if scenario not in _MOCK_SCENARIOS:
            raise VideoExecutionError('video_mock_scenario_invalid')
        return MockVideoExecutor()
    if not api_key:
        raise VideoExecutionError('video_fal_not_configured')
    return FalVideoExecutor(
        api_key=api_key,
        queue_base_url=os.getenv('VIDEO_GENERATION_FAL_QUEUE_BASE_URL', _DEFAULT_QUEUE_BASE_URL).strip(),
        storage_base_url=os.getenv('VIDEO_GENERATION_FAL_STORAGE_BASE_URL', _DEFAULT_STORAGE_BASE_URL).strip(),
        timeout_seconds=_positive_int_env('VIDEO_GENERATION_FAL_TIMEOUT_SECONDS', _DEFAULT_TIMEOUT_SECONDS),
        result_max_bytes=_positive_int_env('VIDEO_GENERATION_RESULT_MAX_BYTES', _DEFAULT_RESULT_MAX_BYTES),
        upload_lifetime_seconds=_positive_int_env(
            'VIDEO_GENERATION_FAL_UPLOAD_LIFETIME_SECONDS',
            _DEFAULT_UPLOAD_LIFETIME_SECONDS,
        ),
    )


def enforce_fal_video_policy(*, model_id: str, charged_credits: int) -> None:
    """Apply optional server-side guards before a paid FAL task is queued."""
    raw_allowlist = os.getenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', '').strip()
    if raw_allowlist:
        allowed = {item.strip() for item in raw_allowlist.split(',') if item.strip()}
        if model_id not in allowed:
            raise VideoExecutionError('video_fal_model_not_allowed')

    raw_limit = os.getenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', '').strip()
    if not raw_limit:
        return
    try:
        limit = int(raw_limit)
    except ValueError as error:
        raise VideoExecutionError('video_fal_policy_invalid') from error
    if limit <= 0:
        raise VideoExecutionError('video_fal_policy_invalid')
    if charged_credits > limit:
        raise VideoExecutionError('video_fal_cost_limit_exceeded')


async def video_runtime_diagnostics(request: Request) -> dict[str, object]:
    mock_enabled, api_key = await get_video_fal_settings()
    raw_allowlist = os.getenv('VIDEO_GENERATION_FAL_ALLOWED_MODELS', '').strip()
    allowed_models = sorted({item.strip() for item in raw_allowlist.split(',') if item.strip()})
    raw_limit = os.getenv('VIDEO_GENERATION_FAL_MAX_CREDITS_PER_REQUEST', '').strip()
    max_credits: int | None = None
    configuration_error: str | None = None
    if mock_enabled:
        if os.getenv('VIDEO_GENERATION_MOCK_SCENARIO', 'success').strip().lower() not in _MOCK_SCENARIOS:
            configuration_error = 'video_mock_scenario_invalid'
    elif not api_key:
        configuration_error = 'video_fal_not_configured'
    if raw_limit:
        try:
            max_credits = int(raw_limit)
            if max_credits <= 0:
                raise ValueError
        except ValueError:
            max_credits = None
            configuration_error = configuration_error or 'video_fal_policy_invalid'
    running = getattr(request.app.state, 'video_generation_tasks', {})
    return {
        'mock_enabled': mock_enabled,
        'fal_api_key_configured': bool(api_key),
        'allowed_models': allowed_models,
        'max_credits_per_request': max_credits,
        'delivery_max_attempts': _positive_int_env(
            'VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS',
            _DEFAULT_DELIVERY_MAX_ATTEMPTS,
        ),
        'result_max_bytes': _positive_int_env('VIDEO_GENERATION_RESULT_MAX_BYTES', _DEFAULT_RESULT_MAX_BYTES),
        'active_task_count': len(running) if isinstance(running, dict) else 0,
        'configuration_error': configuration_error,
    }


def extract_fal_video_url(result: object, output_field: str = 'video') -> str | None:
    if isinstance(result, dict) and isinstance(result.get('data'), dict):
        result = result['data']
    if not isinstance(result, dict):
        return None
    candidate = result.get(output_field)
    if isinstance(candidate, str) and candidate:
        return candidate
    if isinstance(candidate, dict) and isinstance(candidate.get('url'), str):
        return candidate['url']
    fallback = result.get('url')
    return fallback if isinstance(fallback, str) and fallback else None


def _transfer_session() -> aiohttp.ClientSession:
    """大文件传输专用一次性 session（复盘 P1）。

    共享池 session 带 total=300s 总超时，大视频的正常上传/下载也可能超过
    5 分钟，会被砍断成可重试失败（重试后同样被砍）；长传输还会长时间占用
    共享池 per-host 连接配额，挤占其它 API 流量。这里每次传输用独立
    session：无总超时，靠连接/读空闲超时检测挂死，用完即关。
    """
    timeout = aiohttp.ClientTimeout(
        total=None,
        sock_connect=_TRANSFER_CONNECT_TIMEOUT_SECONDS,
        sock_read=_TRANSFER_READ_IDLE_TIMEOUT_SECONDS,
    )
    return aiohttp.ClientSession(timeout=timeout, trust_env=True)


async def _initiate_fal_storage_upload(
    session: aiohttp.ClientSession,
    *,
    filename: str,
    content_type: str,
    api_key: str,
    storage_base_url: str,
    upload_lifetime_seconds: int,
) -> tuple[str, str]:
    """发起 FAL 存储上传握手，返回（upload_url, file_url）；两个 URL 都经过 HTTPS 安全校验。"""
    lifecycle = json.dumps({'expiration_duration_seconds': upload_lifetime_seconds})
    headers = {
        'Authorization': f'Key {api_key}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Fal-Object-Lifecycle-Preference': lifecycle,
    }
    initiate_url = f'{storage_base_url.rstrip("/")}/storage/upload/initiate?storage_type=gcs'
    async with session.post(
        initiate_url,
        json={'file_name': filename, 'content_type': content_type},
        headers=headers,
        ssl=AIOHTTP_CLIENT_SESSION_SSL,
    ) as response:
        if response.status >= 400:
            detail = await response.text()
            raise VideoExecutionError(
                'video_asset_upload_failed',
                detail,
                retryable=_retryable_http_status(response.status),
            )
        initiated = await response.json(content_type=None)
    upload_url = initiated.get('upload_url') if isinstance(initiated, dict) else None
    file_url = initiated.get('file_url') if isinstance(initiated, dict) else None
    if not isinstance(upload_url, str) or not isinstance(file_url, str):
        raise VideoExecutionError('video_asset_upload_failed', 'fal upload response is incomplete')
    if not _is_safe_https_url(upload_url) or not _is_safe_https_url(file_url):
        raise VideoExecutionError('video_asset_upload_failed', 'fal upload response contains an invalid URL')
    return upload_url, file_url


async def _upload_file_to_fal_once(
    *,
    path: Path,
    filename: str,
    content_type: str,
    api_key: str,
    storage_base_url: str,
    upload_lifetime_seconds: int,
) -> str:
    session = _transfer_session()
    try:
        upload_url, file_url = await _initiate_fal_storage_upload(
            session,
            filename=filename,
            content_type=content_type,
            api_key=api_key,
            storage_base_url=storage_base_url,
            upload_lifetime_seconds=upload_lifetime_seconds,
        )
        with path.open('rb') as source:
            async with session.put(
                upload_url,
                data=source,
                headers={'Content-Type': content_type},
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as response:
                if response.status >= 400:
                    detail = await response.text()
                    raise VideoExecutionError(
                        'video_asset_upload_failed',
                        detail,
                        retryable=_retryable_http_status(response.status),
                    )
        return file_url
    except asyncio.CancelledError:
        raise
    except VideoExecutionError:
        raise
    except Exception as error:
        raise VideoExecutionError('video_asset_upload_failed', str(error), retryable=True) from error
    finally:
        await session.close()


async def upload_file_to_fal(
    *,
    path: Path,
    filename: str,
    content_type: str,
    api_key: str,
    storage_base_url: str,
    upload_lifetime_seconds: int,
) -> str:
    attempts = _positive_int_env('VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS', _DEFAULT_DELIVERY_MAX_ATTEMPTS)
    for attempt in range(attempts):
        try:
            return await _upload_file_to_fal_once(
                path=path,
                filename=filename,
                content_type=content_type,
                api_key=api_key,
                storage_base_url=storage_base_url,
                upload_lifetime_seconds=upload_lifetime_seconds,
            )
        except VideoExecutionError as error:
            if not error.retryable or attempt + 1 >= attempts:
                raise
            await asyncio.sleep(_DEFAULT_RETRY_BASE_DELAY_SECONDS * (attempt + 1))
    raise AssertionError('unreachable')


async def _validate_asset_reference(
    reference: VideoAssetReference,
    constraints: dict[str, VideoAssetInput],
    *,
    user_id: str,
) -> tuple[VideoAssetInput, Path, str, str, int]:
    """校验单个资产引用，返回（约束、本地路径、文件名、MIME、体积）。"""
    constraint = constraints.get(reference.role)
    if constraint is None:
        raise VideoExecutionError('video_asset_invalid')
    file = await Files.get_file_by_id_and_user_id(reference.file_id, user_id)
    if file is None or not file.path:
        raise VideoExecutionError('video_asset_not_found')
    metadata = file.meta if isinstance(file.meta, dict) else {}
    content_type = metadata.get('content_type')
    if not isinstance(content_type, str) or content_type not in constraint.mime_types:
        raise VideoExecutionError('video_asset_invalid_type')
    source_path = Path(await asyncio.to_thread(Storage.get_file, file.path))
    size = await asyncio.to_thread(lambda: source_path.stat().st_size)
    if size > constraint.max_bytes:
        raise VideoExecutionError('video_asset_too_large')
    filename = Path(file.filename).name or f'{reference.file_id}.bin'
    return constraint, source_path, filename, content_type, size


async def inject_fal_asset_urls(
    payload: dict[str, object],
    task: VideoTaskResponse,
    definition: FalVideoModelDefinition,
    *,
    user_id: str,
    api_key: str,
    storage_base_url: str,
    upload_lifetime_seconds: int,
) -> None:
    constraints = {item.role: item for item in definition.asset_inputs or ()}
    # 复盘 P2：校验阶段必须串行先于任何上传——grouped_bytes 总量校验若与
    # 上传交错，第二个文件超总量时第一个文件已把字节白白推到 FAL 存储。
    specs: list[tuple[str, Path, str, str]] = []
    grouped_bytes: dict[str, int] = {}
    for reference in task.assets:
        constraint, source_path, filename, content_type, size = await _validate_asset_reference(
            reference, constraints, user_id=user_id
        )
        grouped_bytes[constraint.field] = grouped_bytes.get(constraint.field, 0) + size
        if constraint.max_total_bytes is not None and grouped_bytes[constraint.field] > constraint.max_total_bytes:
            raise VideoExecutionError('video_asset_too_large')
        specs.append((constraint.field, source_path, filename, content_type))
    # 上传是纯网络往返，原先逐个串行 await（复盘 P2）；gather 保持入参
    # 顺序，各资产 URL 在 payload 字段内的顺序与串行实现一致。
    urls = await asyncio.gather(
        *(
            upload_file_to_fal(
                path=spec_path,
                filename=spec_filename,
                content_type=spec_content_type,
                api_key=api_key,
                storage_base_url=storage_base_url,
                upload_lifetime_seconds=upload_lifetime_seconds,
            )
            for _, spec_path, spec_filename, spec_content_type in specs
        )
    )
    grouped: dict[str, list[str]] = {}
    for (field, _spec_path, _spec_filename, _spec_content_type), file_url in zip(specs, urls, strict=True):
        grouped.setdefault(field, []).append(file_url)
    for field, field_urls in grouped.items():
        constraint = next(item for item in definition.asset_inputs or () if item.field == field)
        payload[field] = field_urls if constraint.multiple else field_urls[0]


async def _drain_response_to_file(
    response: aiohttp.ClientResponse,
    target: object,
    *,
    max_bytes: int,
) -> None:
    """流式写盘并执行体积上限校验；空响应视为可重试的下载失败。"""
    size = 0
    async for chunk in response.content.iter_chunked(_TRANSFER_CHUNK_SIZE_BYTES):
        size += len(chunk)
        if size > max_bytes:
            raise VideoExecutionError('video_result_too_large')
        await target.write(chunk)
    if size == 0:
        raise VideoExecutionError(
            'video_result_download_failed',
            'empty video response',
            retryable=True,
        )


async def download_fal_video(url: str, *, max_bytes: int) -> tuple[Path, str]:
    if not _is_safe_https_url(url):
        raise VideoExecutionError('video_result_invalid_url')
    session = _transfer_session()
    fd, temporary_name = tempfile.mkstemp(prefix=_TEMP_FILE_PREFIX, suffix='.mp4')
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        async with session.get(url, ssl=AIOHTTP_CLIENT_SESSION_SSL) as response:
            if response.status >= 400:
                raise VideoExecutionError(
                    'video_result_download_failed',
                    f'HTTP {response.status}',
                    retryable=_retryable_http_status(response.status),
                )
            declared = response.content_length
            if declared is not None and declared > max_bytes:
                raise VideoExecutionError('video_result_too_large')
            content_type = (
                response.headers.get('Content-Type', 'application/octet-stream')
                .split(';', maxsplit=1)[0]
                .strip()
                .lower()
            )
            async with aiofiles.open(temporary_path, 'wb') as target:
                await _drain_response_to_file(response, target, max_bytes=max_bytes)
            return temporary_path, content_type
    except asyncio.CancelledError:
        await _remove_file(temporary_path)
        raise
    except Exception as error:
        await _remove_file(temporary_path)
        if isinstance(error, VideoExecutionError):
            raise
        raise VideoExecutionError('video_result_download_failed', str(error), retryable=True) from error
    finally:
        await session.close()


async def download_fal_video_with_retry(url: str, *, max_bytes: int) -> tuple[Path, str]:
    attempts = _positive_int_env('VIDEO_GENERATION_DELIVERY_MAX_ATTEMPTS', _DEFAULT_DELIVERY_MAX_ATTEMPTS)
    for attempt in range(attempts):
        try:
            return await download_fal_video(url, max_bytes=max_bytes)
        except VideoExecutionError as error:
            if not error.retryable or attempt + 1 >= attempts:
                raise
            await asyncio.sleep(_DEFAULT_RETRY_BASE_DELAY_SECONDS * (attempt + 1))
    raise AssertionError('unreachable')


async def cleanup_stale_fal_video_temp_files(*, max_age_seconds: int = _DEFAULT_TEMP_MAX_AGE_SECONDS) -> int:
    cutoff = time.time() - max_age_seconds

    def cleanup() -> int:
        removed = 0
        for path in Path(tempfile.gettempdir()).glob(f'{_TEMP_FILE_PREFIX}*.mp4'):
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                log.exception('Could not inspect or remove stale FAL video temp file %s', path)
        return removed

    return await asyncio.to_thread(cleanup)


def _task_duration_seconds(task: VideoTaskResponse) -> int | None:
    value = task.params.get('duration')
    try:
        return max(1, round(float(value))) if value is not None else None
    except (TypeError, ValueError):
        return None


def _looks_like_mp4_file(path: Path) -> bool:
    with path.open('rb') as source:
        header = source.read(12)
    return len(header) >= 12 and header[4:8] == b'ftyp'


async def _remove_file(path: Path) -> None:
    try:
        await asyncio.to_thread(path.unlink, missing_ok=True)
    except Exception:
        log.exception('Could not remove temporary FAL video %s', path)


def _is_safe_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == 'https' and bool(parsed.netloc) and parsed.username is None and parsed.password is None


__all__ = [
    'FalVideoExecutor',
    'MockVideoExecutor',
    'VideoExecutionError',
    'VideoExecutionOutput',
    'cleanup_stale_fal_video_temp_files',
    'download_fal_video',
    'download_fal_video_with_retry',
    'enforce_fal_video_policy',
    'extract_fal_video_url',
    'get_video_fal_settings',
    'inject_fal_asset_urls',
    'resolve_video_executor',
    'upload_file_to_fal',
    'video_runtime_diagnostics',
]
