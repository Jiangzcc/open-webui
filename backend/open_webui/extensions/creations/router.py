from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from open_webui.extensions.creations.db import get_creation_session
from open_webui.extensions.creations.discovery_service import (
    create_discovery_category,
    delete_discovery_category,
    get_discovery_post,
    get_published_content_file,
    get_published_poster_file,
    list_discovery_categories,
    list_discovery_posts,
    list_favorite_posts,
    publish_creation,
    set_reaction,
    update_discovery_category,
    update_discovery_operation,
    withdraw_creation,
)
from open_webui.extensions.creations.generation_tasks import (
    GenerationTaskNotCancellable,
    cancel_generation_task,
    create_generation_task,
    delete_generation_task,
    get_generation_task,
    list_generation_tasks,
    schedule_generation_task,
)
from open_webui.extensions.creations.schemas import (
    AdminCreationDetail,
    AdminCreationListResponse,
    BulkCreationDeleteForm,
    BulkCreationDeleteResponse,
    CaptionUpdateForm,
    CreationDetail,
    CreationKind,
    CreationListResponse,
    CreationListSort,
    CreationPublication,
    CreationPublicationFilter,
    CreationTask,
    DiscoveryCategory,
    DiscoveryCategoryCreateForm,
    DiscoveryCategoryItem,
    DiscoveryCategoryUpdateForm,
    DiscoveryOperationForm,
    DiscoveryPostDetail,
    DiscoveryPostListResponse,
    DiscoverySort,
    ImageGenerationTaskListResponse,
    ImageGenerationTaskResponse,
    ImageGenerationTaskSubmitForm,
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
    soft_delete_many,
    update_caption,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.images.limits import (
    acquire_image_generation_slot,
    enforce_image_generation_rate,
    release_image_generation_slot,
)
from open_webui.storage.provider import Storage
from open_webui.utils.auth import get_admin_user, get_verified_user
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/v1/creations', tags=['creations'])
log = logging.getLogger(__name__)

PersonalScope = Annotated[Literal['mine'], Query(description='Personal creations scope is always mine.')]


def _invalid_cursor_response() -> JSONResponse:
    return JSONResponse(status_code=422, content={'detail': 'invalid cursor'})


@router.post(
    '/generation-tasks',
    response_model=ImageGenerationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_image_generation_task(
    request: Request,
    submission: ImageGenerationTaskSubmitForm,
    idempotency_key: Annotated[str | None, Header(alias='Idempotency-Key')] = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    from open_webui.routers.images import CreateImageForm, EditImageForm

    try:
        form = (
            EditImageForm.model_validate(submission.payload)
            if submission.kind == 'image-to-image'
            else CreateImageForm.model_validate(submission.payload)
        )
    except ValidationError as error:
        return JSONResponse(status_code=422, content=jsonable_encoder(error.errors()))

    key = (idempotency_key or str(uuid4())).strip()
    if not key or len(key) > 128:
        raise HTTPException(status_code=422, detail='invalid idempotency key')
    try:
        enforce_image_generation_rate(user.id)
        await acquire_image_generation_slot(user.id)
    except CreditError as error:
        return JSONResponse(status_code=error.status_code, content=error.to_envelope())
    try:
        task, created = await create_generation_task(
            session,
            user_id=user.id,
            idempotency_key=key,
            kind=submission.kind,
            payload=form.model_dump(exclude_none=True),
        )
    except Exception:
        await release_image_generation_slot(user.id)
        raise
    if created:
        try:
            schedule_generation_task(
                request,
                task_id=task.id,
                user=user,
                form=form,
                kind=submission.kind,
                on_finished=lambda: release_image_generation_slot(user.id),
            )
        except Exception:
            await release_image_generation_slot(user.id)
            raise
    else:
        await release_image_generation_slot(user.id)
    return task


@router.get('/generation-tasks', response_model=ImageGenerationTaskListResponse)
async def list_image_generation_tasks(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_generation_tasks(session, user.id, limit, cursor)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/generation-tasks/{task_id}', response_model=ImageGenerationTaskResponse)
async def get_image_generation_task(
    task_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    task = await get_generation_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='generation task not found')
    return task


@router.delete('/generation-tasks/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_generation_task(
    task_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    task = await get_generation_task(session, user.id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='generation task not found')
    if task.status not in {'succeeded', 'failed'}:
        raise HTTPException(status_code=409, detail='active generation task must be cancelled first')
    removed = await delete_generation_task(session, user.id, task_id)
    if not removed:
        raise HTTPException(status_code=404, detail='generation task not found')


@router.post(
    '/generation-tasks/{task_id}/cancel',
    response_model=ImageGenerationTaskResponse,
)
async def cancel_image_generation_task(
    request: Request,
    task_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        task = await cancel_generation_task(request, session, user.id, task_id)
    except GenerationTaskNotCancellable:
        raise HTTPException(status_code=409, detail='generation task is not cancellable') from None
    if task is None:
        raise HTTPException(status_code=404, detail='generation task not found')
    return task


@router.get('/media', response_model=CreationListResponse)
async def list_media(
    scope: PersonalScope = 'mine',
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    task: CreationTask | None = None,
    publication_status: CreationPublicationFilter | None = None,
    sort: CreationListSort = 'newest',
    kind: CreationKind | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_personal_creations(
            session,
            user.id,
            limit,
            cursor,
            search=search,
            task=task,
            publication_status=publication_status,
            sort=sort,
            kind=kind,
        )
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


@router.post('/media/bulk-delete', response_model=BulkCreationDeleteResponse)
async def bulk_delete_media(
    form: BulkCreationDeleteForm,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return BulkCreationDeleteResponse(removed_ids=await soft_delete_many(session, user.id, form.ids))


@router.post('/media/{creation_id}/publish', response_model=CreationPublication)
async def publish_media(
    creation_id: str,
    form: PublishCreationForm,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        publication = await publish_creation(session, user.id, creation_id, form)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
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
    category: DiscoveryCategory | None = None,
    media_kind: CreationKind | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_discovery_posts(session, user.id, limit, cursor, sort, category, media_kind)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/discover/favorites', response_model=DiscoveryPostListResponse)
async def list_discover_favorites(
    category: DiscoveryCategory | None = None,
    media_kind: CreationKind | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_favorite_posts(session, user.id, limit, cursor, category, media_kind)
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


@router.get('/discover/posts/{post_id}/poster')
async def get_discover_post_poster(
    post_id: str,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    file = await get_published_poster_file(session, post_id)
    if file is None or not getattr(file, 'path', None):
        raise HTTPException(status_code=404, detail='post poster not found')
    try:
        file_path = Path(await asyncio.to_thread(Storage.get_file, file.path))
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail='post poster not found')
        meta = getattr(file, 'meta', None) or {}
        content_type = meta.get('content_type') if isinstance(meta, dict) else None
        return FileResponse(file_path, media_type=content_type)
    except HTTPException:
        raise
    except Exception as error:
        log.exception('Error getting discovery post poster: %s', error)
        raise HTTPException(status_code=400, detail='error getting post poster') from error


@router.get('/admin/media', response_model=AdminCreationListResponse)
async def list_admin_media(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    kind: CreationKind | None = None,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        return await list_admin_creations(session, limit, cursor, kind)
    except ValueError:
        return _invalid_cursor_response()


@router.get('/discover/categories', response_model=tuple[DiscoveryCategoryItem, ...])
async def list_discover_categories(
    _user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return await list_discovery_categories(session)


@router.patch('/admin/discover/posts/{post_id}', response_model=CreationPublication)
async def update_admin_discovery_post(
    post_id: str,
    form: DiscoveryOperationForm,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        publication = await update_discovery_operation(session, post_id, form)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if publication is None:
        raise HTTPException(status_code=404, detail='post not found')
    return publication


@router.get('/admin/discover/categories', response_model=tuple[DiscoveryCategoryItem, ...])
async def list_admin_discover_categories(
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return await list_discovery_categories(session, include_disabled=True)


@router.post(
    '/admin/discover/categories',
    response_model=DiscoveryCategoryItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_discover_category(
    form: DiscoveryCategoryCreateForm,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return await create_discovery_category(session, form)


@router.patch('/admin/discover/categories/{category_id}', response_model=DiscoveryCategoryItem)
async def update_admin_discover_category(
    category_id: DiscoveryCategory,
    form: DiscoveryCategoryUpdateForm,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    try:
        category = await update_discovery_category(session, category_id, form)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if category is None:
        raise HTTPException(status_code=404, detail='category not found')
    return category


@router.delete('/admin/discover/categories/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_discover_category(
    category_id: DiscoveryCategory,
    _user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    result = await delete_discovery_category(session, category_id)
    if result == 'not_found':
        raise HTTPException(status_code=404, detail='category not found')
    if result == 'protected':
        raise HTTPException(status_code=409, detail='default category cannot be deleted')
    if result == 'in_use':
        raise HTTPException(status_code=409, detail='category is in use')
    return None


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


@router.post('/admin/media/{creation_id}/publish', response_model=CreationPublication)
async def publish_admin_media(
    creation_id: str,
    form: PublishCreationForm,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    detail = await get_admin_detail(session, creation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    try:
        publication = await publish_creation(
            session,
            detail.owner.user_id,
            creation_id,
            form,
            allow_hidden=True,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if publication is None:
        raise HTTPException(status_code=404, detail='creation not found')
    return publication


@router.delete('/admin/media/{creation_id}/publish', status_code=204)
async def withdraw_admin_media(
    creation_id: str,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    detail = await get_admin_detail(session, creation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    withdrawn = await withdraw_creation(session, detail.owner.user_id, creation_id)
    if not withdrawn:
        raise HTTPException(status_code=404, detail='publication not found')
    return None


@router.delete('/admin/media/{creation_id}', status_code=204)
async def delete_admin_media(
    creation_id: str,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    detail = await get_admin_detail(session, creation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='creation not found')
    removed = await soft_delete(session, detail.owner.user_id, creation_id)
    if not removed:
        raise HTTPException(status_code=404, detail='creation not found')
    return None


__all__ = ['router']
