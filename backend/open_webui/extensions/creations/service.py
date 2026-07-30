from __future__ import annotations

import time
from collections.abc import Iterable

from open_webui.extensions.creations.models import CreationMediaItem, CreationPost, CreationPostMedia
from open_webui.extensions.creations.schemas import (
    AdminCreationDetail,
    AdminCreationListResponse,
    AdminCreationSummary,
    AdminOwner,
    CreationAvailability,
    CreationDetail,
    CreationListResponse,
    CreationReference,
    CreationSummary,
    decode_creation_cursor,
    encode_creation_cursor,
)
from sqlalchemy import and_, asc, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

_CONTENT_URL_TEMPLATE = '/api/v1/files/{}/content'

# Mirror of schemas._PROMPT_PREVIEW_CHARS; kept here so the projection layer
# never has to reach into the schema module for a presentation constant.
_PROMPT_PREVIEW_CHARS = 200

Files = None  # lazily bound on first use; tests monkeypatch this name
Users = None  # lazily bound on first use; tests monkeypatch this name


def _bind_files() -> object:
    global Files
    if Files is None:
        from open_webui.models.files import Files as _files

        Files = _files
    return Files


def _bind_users() -> object:
    global Users
    if Users is None:
        from open_webui.models.users import Users as _users

        Users = _users
    return Users


def _now() -> int:
    return int(time.time())


def _model_display_name(item: CreationMediaItem) -> str | None:
    return item.model_name_snapshot or item.model_id


def _prompt_preview(item: CreationMediaItem) -> str | None:
    """Trim the stored prompt to a glance-length snippet for list cards.

    The waterfall card floats this under the thumbnail; the full prompt still
    ships with the detail endpoint, so clipping here trades precision for bulk
    on a listing that already omits most heavy fields. Whitespace is collapsed
    so a multi-line prompt does not smuggle tall vertical breaks into a two-row
    chip overlay.
    """
    raw = item.prompt
    if not isinstance(raw, str):
        return None
    flattened = ' '.join(raw.split())
    if not flattened:
        return None
    if len(flattened) <= _PROMPT_PREVIEW_CHARS:
        return flattened
    return flattened[: _PROMPT_PREVIEW_CHARS - 1].rstrip() + '…'


def _file_content_url_and_mime(
    file: object | None, owner_id: str
) -> tuple[str | None, str | None, CreationAvailability]:
    if file is None:
        return None, None, 'missing'
    if getattr(file, 'user_id', None) != owner_id:
        return None, None, 'missing'
    file_id = getattr(file, 'id', None)
    if not isinstance(file_id, str):
        return None, None, 'missing'
    meta = getattr(file, 'meta', None) or {}
    content_type = None
    if isinstance(meta, dict):
        raw = meta.get('content_type')
        if isinstance(raw, str):
            content_type = raw
    return _CONTENT_URL_TEMPLATE.format(file_id), content_type, 'available'


def _index_files_by_id(files: Iterable[object]) -> dict[str, object]:
    return {getattr(file, 'id'): file for file in files if getattr(file, 'id', None) is not None}


def _summary_from_item(
    item: CreationMediaItem, file: object | None, publication_status: str | None = None
) -> CreationSummary:
    content_url, mime_type, availability = _file_content_url_and_mime(file, item.user_id)
    return CreationSummary(
        id=item.id,
        kind=item.kind,
        content_url=content_url,
        availability=availability,
        mime_type=mime_type,
        caption=item.caption,
        prompt_preview=_prompt_preview(item),
        model_name=_model_display_name(item),
        task=item.task,
        publication_status=publication_status,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _references_for_item(item: CreationMediaItem, files_by_id: dict[str, object]) -> tuple[CreationReference, ...]:
    raw_ids = item.reference_file_ids_json
    if not raw_ids:
        return ()
    references: list[CreationReference] = []
    for position, file_id in enumerate(raw_ids):
        file = files_by_id.get(file_id) if isinstance(file_id, str) else None
        content_url, mime_type, availability = _file_content_url_and_mime(file, item.user_id)
        references.append(
            CreationReference(
                position=position,
                content_url=content_url,
                availability=availability,
                mime_type=mime_type,
            )
        )
    return tuple(references)


def _detail_from_item(item: CreationMediaItem, files_by_id: dict[str, object]) -> CreationDetail:
    result_file = files_by_id.get(item.file_id)
    content_url, mime_type, availability = _file_content_url_and_mime(result_file, item.user_id)
    return CreationDetail(
        id=item.id,
        kind=item.kind,
        content_url=content_url,
        availability=availability,
        mime_type=mime_type,
        caption=item.caption,
        model_id=item.model_id,
        model_name=_model_display_name(item),
        task=item.task,
        prompt=item.prompt,
        negative_prompt=item.negative_prompt,
        params=item.params_json,
        source=item.source,
        batch_id=item.batch_id,
        references=_references_for_item(item, files_by_id),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _collect_file_ids(items: list[CreationMediaItem]) -> list[str]:
    file_ids: list[str] = []
    for item in items:
        file_ids.append(item.file_id)
        raw_refs = item.reference_file_ids_json or []
        if isinstance(raw_refs, list):
            for ref_id in raw_refs:
                if isinstance(ref_id, str):
                    file_ids.append(ref_id)
    return file_ids


async def _bulk_load_files(file_ids: list[str]) -> dict[str, object]:
    if not file_ids:
        return {}
    unique_ids = list(dict.fromkeys(file_ids))
    files = await _bind_files().get_files_by_ids(unique_ids)
    return _index_files_by_id(files)


async def _owners_for_items(items: list[CreationMediaItem]) -> dict[str, AdminOwner]:
    user_ids = list(dict.fromkeys(item.user_id for item in items))
    if not user_ids:
        return {}
    users = await _bind_users().get_users_by_ids(user_ids)
    found = {user.id: user for user in users}
    owners: dict[str, AdminOwner] = {}
    for uid in user_ids:
        user = found.get(uid)
        if user is None:
            owners[uid] = AdminOwner(user_id=uid, deleted=True)
        else:
            owners[uid] = AdminOwner(
                user_id=user.id,
                name=user.name,
                email=user.email,
                profile_image_url=user.profile_image_url,
                deleted=False,
            )
    return owners


def _apply_cursor(stmt, cursor: str | None, sort: str = 'newest'):
    if not cursor:
        return stmt
    cursor_created_at, cursor_id = decode_creation_cursor(cursor)
    comparator = (
        or_(
            CreationMediaItem.created_at > cursor_created_at,
            and_(CreationMediaItem.created_at == cursor_created_at, CreationMediaItem.id > cursor_id),
        )
        if sort == 'oldest'
        else or_(
            CreationMediaItem.created_at < cursor_created_at,
            and_(CreationMediaItem.created_at == cursor_created_at, CreationMediaItem.id < cursor_id),
        )
    )
    return stmt.where(comparator)


async def list_personal_creations(
    session: AsyncSession,
    user_id: str,
    limit: int,
    cursor: str | None,
    search: str | None = None,
    task: str | None = None,
    publication_status: str | None = None,
    sort: str = 'newest',
) -> CreationListResponse:
    stmt = (
        select(CreationMediaItem, CreationPost.status)
        .outerjoin(CreationPostMedia, CreationPostMedia.creation_id == CreationMediaItem.id)
        .outerjoin(CreationPost, CreationPost.id == CreationPostMedia.post_id)
        .where(
            CreationMediaItem.user_id == user_id,
            CreationMediaItem.soft_deleted.is_(False),
        )
    )
    normalized_search = (search or '').strip()
    if normalized_search:
        pattern = f'%{normalized_search}%'
        stmt = stmt.where(
            or_(
                CreationMediaItem.prompt.ilike(pattern),
                CreationMediaItem.caption.ilike(pattern),
                CreationMediaItem.model_name_snapshot.ilike(pattern),
                CreationMediaItem.model_id.ilike(pattern),
            )
        )
    if task:
        stmt = stmt.where(CreationMediaItem.task == task)
    if publication_status == 'published':
        stmt = stmt.where(CreationPost.status == 'published')
    elif publication_status == 'unpublished':
        stmt = stmt.where(or_(CreationPost.status.is_(None), CreationPost.status != 'published'))
    ordering = (
        (asc(CreationMediaItem.created_at), asc(CreationMediaItem.id))
        if sort == 'oldest'
        else (desc(CreationMediaItem.created_at), desc(CreationMediaItem.id))
    )
    stmt = stmt.order_by(*ordering).limit(limit + 1)
    stmt = _apply_cursor(stmt, cursor, sort)
    rows = (await session.execute(stmt)).all()
    items = list(rows)
    next_cursor = None
    if len(items) > limit:
        page = items[:limit]
        boundary = page[-1][0]
        next_cursor = encode_creation_cursor(boundary.created_at, boundary.id)
    else:
        page = items
    media_items = [item for item, _status in page]
    files_by_id = await _bulk_load_files(_collect_file_ids(media_items))
    summaries = tuple(
        _summary_from_item(item, files_by_id.get(item.file_id), status) for item, status in page
    )
    return CreationListResponse(items=summaries, next_cursor=next_cursor)


async def list_admin_creations(
    session: AsyncSession,
    limit: int,
    cursor: str | None,
) -> AdminCreationListResponse:
    stmt = (
        select(CreationMediaItem, CreationPost.status)
        .outerjoin(CreationPostMedia, CreationPostMedia.creation_id == CreationMediaItem.id)
        .outerjoin(CreationPost, CreationPost.id == CreationPostMedia.post_id)
        .where(CreationMediaItem.soft_deleted.is_(False))
        .order_by(desc(CreationMediaItem.created_at), desc(CreationMediaItem.id))
        .limit(limit + 1)
    )
    stmt = _apply_cursor(stmt, cursor)
    rows = (await session.execute(stmt)).all()
    items = list(rows)
    next_cursor = None
    if len(items) > limit:
        page = items[:limit]
        boundary = page[-1][0]
        next_cursor = encode_creation_cursor(boundary.created_at, boundary.id)
    else:
        page = items
    media_items = [item for item, _status in page]
    files_by_id = await _bulk_load_files(_collect_file_ids(media_items))
    owners = await _owners_for_items(media_items)
    summaries: list[AdminCreationSummary] = []
    for item, publication_status in page:
        content_url, mime_type, availability = _file_content_url_and_mime(files_by_id.get(item.file_id), item.user_id)
        summaries.append(
            AdminCreationSummary(
                id=item.id,
                kind=item.kind,
                content_url=content_url,
                availability=availability,
                mime_type=mime_type,
                caption=item.caption,
                prompt_preview=_prompt_preview(item),
                model_name=_model_display_name(item),
                task=item.task,
                publication_status=publication_status,
                created_at=item.created_at,
                updated_at=item.updated_at,
                owner=owners[item.user_id],
            )
        )
    return AdminCreationListResponse(items=tuple(summaries), next_cursor=next_cursor)


async def _load_owned_item(session: AsyncSession, user_id: str | None, creation_id: str) -> CreationMediaItem | None:
    stmt = select(CreationMediaItem).where(
        CreationMediaItem.id == creation_id,
        CreationMediaItem.soft_deleted.is_(False),
    )
    if user_id is not None:
        stmt = stmt.where(CreationMediaItem.user_id == user_id)
    return (await session.execute(stmt.limit(1))).scalar_one_or_none()


async def get_personal_detail(session: AsyncSession, user_id: str, creation_id: str) -> CreationDetail | None:
    item = await _load_owned_item(session, user_id, creation_id)
    if item is None:
        return None
    files_by_id = await _bulk_load_files([item.file_id, *_flatten_reference_ids(item)])
    detail = _detail_from_item(item, files_by_id)
    from open_webui.extensions.creations.discovery_service import get_creation_publication

    return detail.model_copy(update={'publication': await get_creation_publication(session, user_id, creation_id)})


async def get_admin_detail(session: AsyncSession, creation_id: str) -> AdminCreationDetail | None:
    item = await _load_owned_item(session, None, creation_id)
    if item is None:
        return None
    files_by_id = await _bulk_load_files([item.file_id, *_flatten_reference_ids(item)])
    owners = await _owners_for_items([item])
    detail = _detail_from_item(item, files_by_id)
    from open_webui.extensions.creations.discovery_service import get_creation_publication

    detail = detail.model_copy(
        update={'publication': await get_creation_publication(session, item.user_id, creation_id)}
    )
    return AdminCreationDetail(**detail.model_dump(), owner=owners[item.user_id])


async def update_caption(
    session: AsyncSession,
    user_id: str,
    creation_id: str,
    caption: str | None,
) -> CreationDetail | None:
    item = await _load_owned_item(session, user_id, creation_id)
    if item is None:
        return None
    normalized_caption: str | None = caption
    if isinstance(normalized_caption, str):
        normalized_caption = normalized_caption.strip() or None
    await session.execute(
        update(CreationMediaItem)
        .where(
            CreationMediaItem.id == creation_id,
            CreationMediaItem.user_id == user_id,
        )
        .values(caption=normalized_caption, updated_at=_now())
    )
    await session.commit()
    refreshed = await _load_owned_item(session, user_id, creation_id)
    assert refreshed is not None
    files_by_id = await _bulk_load_files([refreshed.file_id, *_flatten_reference_ids(refreshed)])
    detail = _detail_from_item(refreshed, files_by_id)
    from open_webui.extensions.creations.discovery_service import get_creation_publication

    return detail.model_copy(update={'publication': await get_creation_publication(session, user_id, creation_id)})


async def soft_delete(
    session: AsyncSession,
    user_id: str,
    creation_id: str,
) -> bool:
    ownership_stmt = select(CreationMediaItem.id).where(
        CreationMediaItem.id == creation_id,
        CreationMediaItem.user_id == user_id,
    )
    owned = (await session.execute(ownership_stmt.limit(1))).scalar_one_or_none()
    if owned is None:
        return False
    await session.execute(
        update(CreationMediaItem)
        .where(
            CreationMediaItem.id == creation_id,
            CreationMediaItem.user_id == user_id,
        )
        .values(soft_deleted=True, updated_at=_now())
    )
    post_ids = select(CreationPostMedia.post_id).where(CreationPostMedia.creation_id == creation_id)
    await session.execute(
        update(CreationPost)
        .where(CreationPost.id.in_(post_ids), CreationPost.status != 'hidden')
        .values(status='withdrawn', updated_at=_now())
    )
    await session.commit()
    return True


async def soft_delete_many(
    session: AsyncSession, user_id: str, creation_ids: tuple[str, ...]
) -> tuple[str, ...]:
    owned = tuple(
        (
            await session.execute(
                select(CreationMediaItem.id).where(
                    CreationMediaItem.id.in_(creation_ids),
                    CreationMediaItem.user_id == user_id,
                    CreationMediaItem.soft_deleted.is_(False),
                )
            )
        )
        .scalars()
        .all()
    )
    if not owned:
        return ()
    now = _now()
    await session.execute(
        update(CreationMediaItem)
        .where(CreationMediaItem.id.in_(owned), CreationMediaItem.user_id == user_id)
        .values(soft_deleted=True, updated_at=now)
    )
    post_ids = select(CreationPostMedia.post_id).where(CreationPostMedia.creation_id.in_(owned))
    await session.execute(
        update(CreationPost)
        .where(CreationPost.id.in_(post_ids), CreationPost.status != 'hidden')
        .values(status='withdrawn', updated_at=now)
    )
    await session.commit()
    return owned


def _flatten_reference_ids(item: CreationMediaItem) -> list[str]:
    raw = item.reference_file_ids_json or []
    if not isinstance(raw, list):
        return []
    return [rid for rid in raw if isinstance(rid, str)]


__all__ = [
    'get_admin_detail',
    'get_personal_detail',
    'list_admin_creations',
    'list_personal_creations',
    'soft_delete',
    'soft_delete_many',
    'update_caption',
]
