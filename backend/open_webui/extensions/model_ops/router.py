from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_admin_user
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import ModelOperationItem, ModelOperationList, ModelOperationUpdate
from .service import list_model_operations, update_model_operation

router = APIRouter(prefix='/api/v1/image-model-ops', tags=['image-model-ops'])


@router.get('/admin/models', response_model=ModelOperationList)
async def get_admin_image_model_operations(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await list_model_operations(session)


@router.patch('/admin/models/{model_id:path}', response_model=ModelOperationItem)
async def patch_admin_image_model_operation(
    model_id: Annotated[str, Field(min_length=1, max_length=256)],
    form: ModelOperationUpdate,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
):
    item = await update_model_operation(session, model_id, form, user)
    if item is None:
        raise HTTPException(status_code=404, detail='image model not found')
    return item


__all__ = ['router']
