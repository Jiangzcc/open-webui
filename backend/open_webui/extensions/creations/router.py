from __future__ import annotations

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.creations.schemas import (
    AdminCreationDetail,
    AdminCreationListResponse,
    CaptionUpdateForm,
    CreationDetail,
    CreationListResponse,
)
from open_webui.extensions.creations.service import (
    get_admin_detail,
    get_personal_detail,
    list_admin_creations,
    list_personal_creations,
    soft_delete,
    update_caption,
)
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
