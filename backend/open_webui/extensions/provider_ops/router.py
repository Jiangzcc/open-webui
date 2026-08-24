from __future__ import annotations

from time import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from open_webui.events import EVENTS, publish_event
from open_webui.extensions.videos.executor import video_runtime_diagnostics
from open_webui.internal.db import get_async_session
from open_webui.models.config import Config
from open_webui.utils.auth import get_admin_user
from sqlalchemy.ext.asyncio import AsyncSession

from .platform_queries import (
    get_provider_overview,
    list_provider_analytics,
    list_provider_billing_events,
    list_provider_prices,
    list_provider_requests,
    list_provider_usage,
)
from .platform_sync import sync_fal_platform
from .schemas import (
    FalRuntimeConfig,
    ProviderAnalyticsList,
    ProviderBillingEventList,
    ProviderInvocationList,
    ProviderModelSummaryList,
    ProviderOverview,
    ProviderPriceList,
    ProviderRequestRecordList,
    ProviderSyncForm,
    ProviderSyncResult,
    ProviderUsageList,
    VideoRuntimeStatus,
)
from .service import list_provider_invocations, summarize_provider_models

router = APIRouter(prefix='/api/v1/provider-ops', tags=['provider-ops'])

_MASKED_FAL_API_KEY = '********'


@router.get('/admin/video-runtime', response_model=VideoRuntimeStatus)
async def get_admin_video_runtime_status(
    request: Request,
    _user=Depends(get_admin_user),
):
    return VideoRuntimeStatus.model_validate(await video_runtime_diagnostics(request))


# 运营中心 FAL 配置：字段名 → (Config 存储键, 缺省值)
_FAL_CONFIG_KEYS: dict[str, tuple[str, object]] = {
    'image_generation_api_base_url': ('image_generation.fal.api_base_url', ''),
    'image_generation_api_key': ('image_generation.fal.api_key', ''),
    'image_edit_api_base_url': ('images.edit.fal.api_base_url', ''),
    'image_edit_api_key': ('images.edit.fal.api_key', ''),
    'video_api_key': ('video_generation.fal.api_key', ''),
    'image_mock_enabled': ('image_generation.fal.mock_enabled', False),
    'video_mock_enabled': ('video_generation.fal.mock_enabled', False),
}


async def _read_fal_runtime_config() -> FalRuntimeConfig:
    values = await Config.get_many(*(storage_key for storage_key, _default in _FAL_CONFIG_KEYS.values()))
    public_values = {
        field: (
            _MASKED_FAL_API_KEY
            if field.endswith('_api_key') and values.get(storage_key)
            else values.get(storage_key, default)
        )
        for field, (storage_key, default) in _FAL_CONFIG_KEYS.items()
    }
    return FalRuntimeConfig(**public_values)


@router.get('/admin/fal-config', response_model=FalRuntimeConfig)
async def get_admin_fal_runtime_config(_user=Depends(get_admin_user)) -> FalRuntimeConfig:
    return await _read_fal_runtime_config()


@router.post('/admin/fal-config/update', response_model=FalRuntimeConfig)
async def update_admin_fal_runtime_config(
    request: Request,
    form: FalRuntimeConfig,
    user=Depends(get_admin_user),
) -> FalRuntimeConfig:
    # API keys arrive in this request body. The shared audit middleware records
    # bodies unless the endpoint explicitly opts out, so redact before any
    # await that could hand control back to middleware/error handling.
    request.scope['audit_redact_bodies'] = {'request'}
    updates = {
        storage_key: value
        for field, (storage_key, _default) in _FAL_CONFIG_KEYS.items()
        if (value := getattr(form, field)) != _MASKED_FAL_API_KEY
    }
    await Config.upsert(updates)
    await publish_event(
        request,
        EVENTS.CONFIG_UPDATED,
        actor=user,
        subject_id='fal-runtime-config',
        data={
            'image_mock_enabled': form.image_mock_enabled,
            'video_mock_enabled': form.video_mock_enabled,
        },
    )
    return await _read_fal_runtime_config()


@router.get('/admin/invocations', response_model=ProviderInvocationList)
async def get_admin_provider_invocations(
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    provider: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    status: Annotated[
        Literal['created', 'submitted', 'queued', 'running', 'succeeded', 'failed', 'cancelled', 'unknown'] | None,
        Query(),
    ] = None,
    task_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    provider_model_id: Annotated[str | None, Query(min_length=1, max_length=256)] = None,
    provider_request_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await list_provider_invocations(
        session,
        limit=limit,
        provider=provider,
        status=status,
        task_id=task_id,
        provider_model_id=provider_model_id,
        provider_request_id=provider_request_id,
    )


@router.get('/admin/model-summary', response_model=ProviderModelSummaryList)
async def get_admin_provider_model_summary(
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    provider: Annotated[str | None, Query(min_length=1, max_length=64)] = None,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    since_ms = int(time() * 1000) - window_hours * 60 * 60 * 1000
    return await summarize_provider_models(session, since_ms=since_ms, provider=provider)


@router.get('/admin/overview', response_model=ProviderOverview)
async def get_admin_provider_overview(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    until_ms = int(time() * 1000)
    since_ms = until_ms - window_hours * 60 * 60 * 1000
    return await get_provider_overview(
        session,
        provider=provider,
        since_ms=since_ms,
        until_ms=until_ms,
    )


@router.post('/admin/providers/fal/sync', response_model=ProviderSyncResult)
async def post_admin_fal_platform_sync(
    form: ProviderSyncForm,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await sync_fal_platform(session, form)


@router.get('/admin/prices', response_model=ProviderPriceList)
async def get_admin_provider_prices(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await list_provider_prices(session, provider=provider, limit=limit)


@router.get('/admin/billing-events', response_model=ProviderBillingEventList)
async def get_admin_provider_billing_events(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    since_ms = int(time() * 1000) - window_hours * 60 * 60 * 1000
    return await list_provider_billing_events(session, provider=provider, since_ms=since_ms, limit=limit)


@router.get('/admin/provider-requests', response_model=ProviderRequestRecordList)
async def get_admin_provider_requests(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    since_ms = int(time() * 1000) - window_hours * 60 * 60 * 1000
    return await list_provider_requests(session, provider=provider, since_ms=since_ms, limit=limit)


@router.get('/admin/usage', response_model=ProviderUsageList)
async def get_admin_provider_usage(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    since_ms = int(time() * 1000) - window_hours * 60 * 60 * 1000
    return await list_provider_usage(session, provider=provider, since_ms=since_ms, limit=limit)


@router.get('/admin/analytics', response_model=ProviderAnalyticsList)
async def get_admin_provider_analytics(
    provider: Annotated[str, Query(min_length=1, max_length=64)] = 'fal',
    window_hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    since_ms = int(time() * 1000) - window_hours * 60 * 60 * 1000
    return await list_provider_analytics(session, provider=provider, since_ms=since_ms, limit=limit)


__all__ = ['router']
