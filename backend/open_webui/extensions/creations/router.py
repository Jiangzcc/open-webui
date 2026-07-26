from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.creations.discovery_service import (
    get_discovery_post,
    get_published_content_file,
    list_discovery_posts,
    list_favorite_posts,
    publish_creation,
    set_reaction,
    withdraw_creation,
)
from open_webui.extensions.creations.schemas import (
    AdminCreationDetail,
    AdminCreationListResponse,
    CaptionUpdateForm,
    CreationDetail,
    CreationListResponse,
    CreationPublication,
    DiscoveryPostDetail,
    DiscoveryPostListResponse,
    DiscoverySort,
    PublishCreationForm,
    ReactionKind,
    ReactionState,
)
from open_webui.extensions.creations.service import (
    get_admin_detail,
    get_personal_detail,
    list_admin_creations,
    list_personal_creations,
    soft_delete,
    update_caption,
)
from open_webui.storage.provider import Storage
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/v1/creations', tags=['creations'])
log = logging.getLogger(__name__)

PersonalScope = Annotated[Literal['mine'], Query(description='Personal creations scope is always mine.')]


def _invalid_cursor_response() -> JSONResponse:
    return JSONResponse(status_code=422, content={'detail': 'invalid creation cursor'})


@router.get('/media', response_model=CreationListResponse)
async def list_media(
    scope: PersonalScope = 'mine',
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_personal_creations(session, user.id, limit, cursor)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/media/{creation_id}', response_model=CreationDetail)
async def get_media(
    creation_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    detail = await get_personal_detail(session, user.id, creation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    return detail


@router.patch('/media/{creation_id}', response_model=CreationDetail)
async def update_media(
    creation_id: str,
    payload: dict,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        form = CaptionUpdateForm.model_validate(payload)
    except ValidationError as error:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(error.errors()),
        )
    detail = await update_caption(session, user.id, creation_id, form.caption)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    return detail


@router.delete('/media/{creation_id}', status_code=204)
async def delete_media(
    creation_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    removed = await soft_delete(session, user.id, creation_id)
    if not removed:
        raise HTTPException(status_code=404, detail='creation not found')
    return None


@router.post('/media/{creation_id}/publish', response_model=CreationPublication)
async def publish_media(
    creation_id: str,
    form: PublishCreationForm,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    publication = await publish_creation(session, user.id, creation_id, form)
    if publication is None:
        raise HTTPException(status_code=404, detail='creation not found')
    return publication


@router.delete('/media/{creation_id}/publish', status_code=204)
async def withdraw_media(
    creation_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    withdrawn = await withdraw_creation(session, user.id, creation_id)
    if not withdrawn:
        raise HTTPException(status_code=404, detail='publication not found')
    return None


@router.get('/discover/posts', response_model=DiscoveryPostListResponse)
async def list_discover_posts(
    sort: DiscoverySort = 'latest',
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_discovery_posts(session, user.id, limit, cursor, sort)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/discover/favorites', response_model=DiscoveryPostListResponse)
async def list_discover_favorites(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_favorite_posts(session, user.id, limit, cursor)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/discover/posts/{post_id}', response_model=DiscoveryPostDetail)
async def get_discover_post(
    post_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    post = await get_discovery_post(session, user.id, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail='post not found')
    return post


@router.put('/discover/posts/{post_id}/reactions/{kind}', response_model=ReactionState)
async def add_discover_reaction(
    post_id: str,
    kind: ReactionKind,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    reaction = await set_reaction(session, user.id, post_id, kind, True)
    if reaction is None:
        raise HTTPException(status_code=404, detail='post not found')
    return reaction


@router.delete('/discover/posts/{post_id}/reactions/{kind}', response_model=ReactionState)
async def remove_discover_reaction(
    post_id: str,
    kind: ReactionKind,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    reaction = await set_reaction(session, user.id, post_id, kind, False)
    if reaction is None:
        raise HTTPException(status_code=404, detail='post not found')
    return reaction


@router.get('/discover/posts/{post_id}/content')
async def get_discover_post_content(
    post_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    file = await get_published_content_file(session, post_id)
    if file is None or not getattr(file, 'path', None):
        raise HTTPException(status_code=404, detail='post content not found')
    try:
        file_path = Path(await asyncio.to_thread(Storage.get_file, file.path))
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail='post content not found')
        meta = getattr(file, 'meta', None) or {}
        content_type = meta.get('content_type') if isinstance(meta, dict) else None
        return FileResponse(file_path, media_type=content_type)
    except HTTPException:
        raise
    except Exception as error:
        log.exception('Error getting discovery post content: %s', error)
        raise HTTPException(status_code=400, detail='error getting post content') from error


@router.get('/admin/media', response_model=AdminCreationListResponse)
async def list_admin_media(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_admin_creations(session, limit, cursor)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/admin/media/{creation_id}', response_model=AdminCreationDetail)
async def get_admin_media(
    creation_id: str,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    detail = await get_admin_detail(session, creation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    return detail


__all__ = ['router']
