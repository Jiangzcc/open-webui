from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from open_webui.internal.db import get_async_session
from open_webui.utils.auth import get_admin_user, get_verified_user
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    MediaKind,
    PromptTagAdminCatalog,
    PromptTagCategoryCreate,
    PromptTagCategoryItem,
    PromptTagCategoryUpdate,
    PromptTagCreate,
    PromptTagExportDocument,
    PromptTagImportRequest,
    PromptTagImportResult,
    PromptTagItem,
    PromptTagPublicCatalog,
    PromptTagUpdate,
)
from .service import (
    PromptTagCategoryNotEmptyError,
    PromptTagConflictError,
    PromptTagNotFoundError,
    create_category,
    create_tag,
    delete_category,
    delete_tag,
    export_catalog,
    get_admin_catalog,
    get_public_catalog,
    import_catalog,
    update_category,
    update_tag,
)

router = APIRouter(prefix='/api/v1/prompt-tags', tags=['prompt-tags'])


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, PromptTagNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, (PromptTagConflictError, PromptTagCategoryNotEmptyError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    raise error


@router.get('', response_model=PromptTagPublicCatalog)
async def get_prompt_tag_catalog(
    media_kind: MediaKind | None = None,
    model_id: Annotated[str | None, Query(min_length=1, max_length=256)] = None,
    _user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagPublicCatalog:
    return await get_public_catalog(session, media_kind=media_kind, model_id=model_id)


@router.get('/admin/catalog', response_model=PromptTagAdminCatalog)
async def get_admin_prompt_tag_catalog(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagAdminCatalog:
    return await get_admin_catalog(session)


@router.get('/admin/categories', response_model=tuple[PromptTagCategoryItem, ...])
async def get_admin_prompt_tag_categories(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> tuple[PromptTagCategoryItem, ...]:
    return (await get_admin_catalog(session)).categories


@router.post(
    '/admin/categories',
    response_model=PromptTagCategoryItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_prompt_tag_category(
    form: PromptTagCategoryCreate,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagCategoryItem:
    try:
        return await create_category(session, form, user)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
        raise AssertionError('unreachable')


@router.patch('/admin/categories/{category_id}', response_model=PromptTagCategoryItem)
async def update_admin_prompt_tag_category(
    category_id: str,
    form: PromptTagCategoryUpdate,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagCategoryItem:
    try:
        return await update_category(session, category_id, form, user)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
        raise AssertionError('unreachable')


@router.delete('/admin/categories/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_prompt_tag_category(
    category_id: str,
    cascade: bool = False,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    try:
        await delete_category(session, category_id, cascade=cascade)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/admin/tags', response_model=tuple[PromptTagItem, ...])
async def get_admin_prompt_tags(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> tuple[PromptTagItem, ...]:
    return (await get_admin_catalog(session)).tags


@router.post('/admin/tags', response_model=PromptTagItem, status_code=status.HTTP_201_CREATED)
async def create_admin_prompt_tag(
    form: PromptTagCreate,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagItem:
    try:
        return await create_tag(session, form, user)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
        raise AssertionError('unreachable')


@router.patch('/admin/tags/{tag_id}', response_model=PromptTagItem)
async def update_admin_prompt_tag(
    tag_id: str,
    form: PromptTagUpdate,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagItem:
    try:
        return await update_tag(session, tag_id, form, user)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
        raise AssertionError('unreachable')


@router.delete('/admin/tags/{tag_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_prompt_tag(
    tag_id: str,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    try:
        await delete_tag(session, tag_id)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/admin/export', response_model=PromptTagExportDocument)
async def export_admin_prompt_tags(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagExportDocument:
    return await export_catalog(session)


@router.post('/admin/import', response_model=PromptTagImportResult)
async def import_admin_prompt_tags(
    form: PromptTagImportRequest,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> PromptTagImportResult:
    try:
        return await import_catalog(session, form, user)
    except (PromptTagNotFoundError, PromptTagConflictError, PromptTagCategoryNotEmptyError) as error:
        _raise_http_error(error)
        raise AssertionError('unreachable')


__all__ = ['router']
