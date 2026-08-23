from __future__ import annotations

import base64
import json
import time
from collections.abc import Iterable
from typing import Literal
from uuid import uuid4

from open_webui.extensions.creations.models import (
    CreationMediaItem,
    CreationPost,
    CreationPostMedia,
    CreationPostReaction,
    DiscoveryCategorySetting,
)
from open_webui.extensions.creations.schemas import (
    CreationPublication,
    DiscoveryCategory,
    DiscoveryCategoryCreateForm,
    DiscoveryCategoryItem,
    DiscoveryCategoryUpdateForm,
    DiscoveryOperationForm,
    DiscoveryPostDetail,
    DiscoveryPostListResponse,
    DiscoveryPostSummary,
    DiscoverySort,
    PublicOwner,
    PublishCreationForm,
    ReactionKind,
    ReactionState,
)
from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

Files = None
Users = None

_PROMPT_PREVIEW_CHARS = 200
_DISCOVERY_CONTENT_URL = '/api/v1/creations/discover/posts/{}/content'
_DISCOVERY_POSTER_URL = '/api/v1/creations/discover/posts/{}/poster'


def _bind_files() -> object:
    global Files
    if Files is None:
        from open_webui.models.files import Files as upstream_files

        Files = upstream_files
    return Files


def _bind_users() -> object:
    global Users
    if Users is None:
        from open_webui.models.users import Users as upstream_users

        Users = upstream_users
    return Users


def _now() -> int:
    return int(time.time())


def _publication(post: CreationPost) -> CreationPublication:
    return CreationPublication(
        post_id=post.id,
        status=post.status,
        title=post.title,
        description=post.description,
        show_prompt=post.show_prompt,
        category=post.category or 'other',
        featured=post.featured_at is not None,
        featured_rank=post.featured_rank if post.featured_rank is not None else 1000,
        published_at=post.published_at,
    )


async def _category_exists(
    session: AsyncSession,
    category_id: DiscoveryCategory,
    *,
    include_disabled: bool,
) -> bool:
    stmt = select(DiscoveryCategorySetting.id).where(DiscoveryCategorySetting.id == category_id)
    if not include_disabled:
        stmt = stmt.where(DiscoveryCategorySetting.enabled.is_(True))
    return (await session.scalar(stmt.limit(1))) is not None


async def get_creation_publication(session: AsyncSession, user_id: str, creation_id: str) -> CreationPublication | None:
    stmt = (
        select(CreationPost)
        .join(CreationPostMedia, CreationPostMedia.post_id == CreationPost.id)
        .join(CreationMediaItem, CreationMediaItem.id == CreationPostMedia.creation_id)
        .where(
            CreationPostMedia.creation_id == creation_id,
            CreationMediaItem.user_id == user_id,
            CreationMediaItem.soft_deleted.is_(False),
        )
        .limit(1)
    )
    post = (await session.execute(stmt)).scalar_one_or_none()
    return _publication(post) if post else None


async def _load_files(file_ids: Iterable[str]) -> dict[str, object]:
    ids = list(dict.fromkeys(file_ids))
    if not ids:
        return {}
    files = await _bind_files().get_files_by_ids(ids)
    return {file.id: file for file in files}


async def _public_owners(user_ids: Iterable[str]) -> dict[str, PublicOwner]:
    ids = list(dict.fromkeys(user_ids))
    if not ids:
        return {}
    users = await _bind_users().get_users_by_ids(ids)
    found = {user.id: user for user in users}
    return {
        user_id: PublicOwner(
            user_id=user_id,
            name=getattr(found.get(user_id), 'name', None),
            profile_image_url=getattr(found.get(user_id), 'profile_image_url', None),
            deleted=found.get(user_id) is None,
        )
        for user_id in ids
    }


async def publish_creation(
    session: AsyncSession,
    user_id: str,
    creation_id: str,
    form: PublishCreationForm,
    *,
    allow_hidden: bool = False,
) -> CreationPublication | None:
    item = (
        await session.execute(
            select(CreationMediaItem)
            .where(
                CreationMediaItem.id == creation_id,
                CreationMediaItem.user_id == user_id,
                CreationMediaItem.soft_deleted.is_(False),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if item is None:
        return None
    file = (await _load_files([item.file_id])).get(item.file_id)
    if file is None or getattr(file, 'user_id', None) != user_id:
        return None

    post = (
        await session.execute(
            select(CreationPost)
            .join(CreationPostMedia, CreationPostMedia.post_id == CreationPost.id)
            .where(CreationPostMedia.creation_id == creation_id)
            .limit(1)
        )
    ).scalar_one_or_none()
    now = _now()
    if post is None:
        category = form.category or 'other'
        if not await _category_exists(session, category, include_disabled=allow_hidden):
            raise ValueError('invalid discovery category')
        post = CreationPost(
            id=str(uuid4()),
            user_id=user_id,
            status='published',
            title=form.title,
            description=form.description,
            show_prompt=form.show_prompt,
            category=category,
            featured_at=None,
            featured_rank=1000,
            like_count=0,
            favorite_count=0,
            published_at=now,
            created_at=now,
            updated_at=now,
        )
        session.add(post)
        session.add(
            CreationPostMedia(
                post_id=post.id,
                creation_id=creation_id,
                position=0,
                created_at=now,
            )
        )
    else:
        if post.user_id != user_id or (post.status == 'hidden' and not allow_hidden):
            return None
        if form.category is not None:
            if not await _category_exists(session, form.category, include_disabled=allow_hidden):
                raise ValueError('invalid discovery category')
            post.category = form.category
        post.status = 'published'
        post.title = form.title
        post.description = form.description
        post.show_prompt = form.show_prompt
        post.published_at = now
        post.updated_at = now
    await session.commit()
    return _publication(post)


async def withdraw_creation(session: AsyncSession, user_id: str, creation_id: str) -> bool:
    post = (
        await session.execute(
            select(CreationPost)
            .join(CreationPostMedia, CreationPostMedia.post_id == CreationPost.id)
            .where(
                CreationPostMedia.creation_id == creation_id,
                CreationPost.user_id == user_id,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if post is None:
        return False
    if post.status != 'hidden':
        post.status = 'withdrawn'
        post.featured_at = None
        post.updated_at = _now()
        await session.commit()
    return True


def _prompt_preview(item: CreationMediaItem, show_prompt: bool) -> str | None:
    if not show_prompt:
        return None
    flattened = ' '.join(item.prompt.split())
    if len(flattened) <= _PROMPT_PREVIEW_CHARS:
        return flattened or None
    return flattened[: _PROMPT_PREVIEW_CHARS - 1].rstrip() + '…'


def _encode_cursor(primary: int, published_at: int, post_id: str) -> str:
    payload = json.dumps({'p': primary, 't': published_at, 'id': post_id}, separators=(',', ':'))
    return base64.urlsafe_b64encode(payload.encode()).rstrip(b'=').decode()


def _decode_cursor(cursor: str) -> tuple[int, int, str]:
    try:
        padding = '=' * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
        primary, published_at, post_id = payload['p'], payload['t'], payload['id']
        if not isinstance(primary, int) or not isinstance(published_at, int) or not isinstance(post_id, str):
            raise ValueError
        return primary, published_at, post_id
    except Exception:
        raise ValueError('invalid discovery cursor') from None


async def _reaction_sets(session: AsyncSession, user_id: str, post_ids: list[str]) -> tuple[set[str], set[str]]:
    if not post_ids:
        return set(), set()
    rows = (
        await session.execute(
            select(CreationPostReaction.post_id, CreationPostReaction.kind).where(
                CreationPostReaction.user_id == user_id,
                CreationPostReaction.post_id.in_(post_ids),
            )
        )
    ).all()
    return (
        {post_id for post_id, kind in rows if kind == 'like'},
        {post_id for post_id, kind in rows if kind == 'favorite'},
    )


async def _summaries(
    session: AsyncSession,
    user_id: str,
    rows: list[tuple[CreationPost, CreationMediaItem]],
) -> tuple[DiscoveryPostSummary, ...]:
    files = await _load_files(
        file_id for _, item in rows for file_id in (item.file_id, item.poster_file_id) if isinstance(file_id, str)
    )
    owners = await _public_owners(item.user_id for _, item in rows)
    post_ids = [post.id for post, _ in rows]
    liked, favorited = await _reaction_sets(session, user_id, post_ids)
    summaries: list[DiscoveryPostSummary] = []
    for post, item in rows:
        file = files.get(item.file_id)
        poster_file = files.get(item.poster_file_id) if item.poster_file_id else None
        available = file is not None and getattr(file, 'user_id', None) == item.user_id
        poster_available = poster_file is not None and getattr(poster_file, 'user_id', None) == item.user_id
        meta = getattr(file, 'meta', None) or {}
        summaries.append(
            DiscoveryPostSummary(
                id=post.id,
                title=post.title,
                description=post.description,
                content_url=_DISCOVERY_CONTENT_URL.format(post.id) if available else None,
                poster_url=(_DISCOVERY_POSTER_URL.format(post.id) if poster_available else None),
                kind=item.kind,
                duration_seconds=item.duration_seconds,
                availability='available' if available else 'missing',
                mime_type=meta.get('content_type') if available and isinstance(meta, dict) else None,
                prompt_preview=_prompt_preview(item, post.show_prompt),
                model_name=item.model_name_snapshot or item.model_id,
                category=post.category or 'other',
                featured=post.featured_at is not None,
                featured_rank=post.featured_rank if post.featured_rank is not None else 1000,
                owner=owners[item.user_id],
                like_count=post.like_count,
                favorite_count=post.favorite_count,
                liked=post.id in liked,
                favorited=post.id in favorited,
                published_at=post.published_at,
            )
        )
    return tuple(summaries)


def _visible_posts_stmt():
    return (
        select(CreationPost, CreationMediaItem)
        .join(CreationPostMedia, CreationPostMedia.post_id == CreationPost.id)
        .join(CreationMediaItem, CreationMediaItem.id == CreationPostMedia.creation_id)
        .where(
            CreationPost.status == 'published',
            CreationMediaItem.soft_deleted.is_(False),
        )
    )


async def _disabled_category_ids(session: AsyncSession) -> tuple[str, ...]:
    """Return the ids of disabled discovery categories (public feed excludes them)."""
    rows = (
        await session.execute(select(DiscoveryCategorySetting.id).where(DiscoveryCategorySetting.enabled.is_(False)))
    ).scalars()
    return tuple(rows)


def _apply_feed_filters(stmt, disabled_categories, category, media_kind):
    if disabled_categories:
        stmt = stmt.where(CreationPost.category.notin_(disabled_categories))
    if category is not None:
        stmt = stmt.where(CreationPost.category == category)
    if media_kind is not None:
        stmt = stmt.where(CreationMediaItem.kind == media_kind)
    return stmt


async def list_discovery_posts(
    session: AsyncSession,
    user_id: str,
    limit: int,
    cursor: str | None,
    sort: DiscoverySort,
    category: DiscoveryCategory | None = None,
    media_kind: str | None = None,
) -> DiscoveryPostListResponse:
    stmt = _visible_posts_stmt()
    # 公开动态排除已禁用分类的帖子：分类选择器隐藏已禁用分类，动态亦不应泄露其内容。
    disabled_categories = await _disabled_category_ids(session)
    stmt = _apply_feed_filters(stmt, disabled_categories, category, media_kind)
    if sort == 'featured':
        stmt = stmt.where(CreationPost.featured_at.is_not(None))
    popularity = CreationPost.favorite_count * 2 + CreationPost.like_count
    if cursor:
        primary, published_at, post_id = _decode_cursor(cursor)
        if sort == 'featured':
            stmt = stmt.where(
                or_(
                    CreationPost.featured_rank > primary,
                    and_(
                        CreationPost.featured_rank == primary,
                        CreationPost.featured_at < published_at,
                    ),
                    and_(
                        CreationPost.featured_rank == primary,
                        CreationPost.featured_at == published_at,
                        CreationPost.id < post_id,
                    ),
                )
            )
        elif sort == 'popular':
            stmt = stmt.where(
                or_(
                    popularity < primary,
                    and_(popularity == primary, CreationPost.published_at < published_at),
                    and_(
                        popularity == primary,
                        CreationPost.published_at == published_at,
                        CreationPost.id < post_id,
                    ),
                )
            )
        else:
            stmt = stmt.where(
                or_(
                    CreationPost.published_at < published_at,
                    and_(CreationPost.published_at == published_at, CreationPost.id < post_id),
                )
            )
    if sort == 'featured':
        stmt = stmt.order_by(
            CreationPost.featured_rank.asc(),
            desc(CreationPost.featured_at),
            desc(CreationPost.id),
        )
    elif sort == 'popular':
        stmt = stmt.order_by(desc(popularity), desc(CreationPost.published_at), desc(CreationPost.id))
    else:
        stmt = stmt.order_by(desc(CreationPost.published_at), desc(CreationPost.id))
    rows = list((await session.execute(stmt.limit(limit + 1))).all())
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        post = page[-1][0]
        primary = (
            post.featured_rank
            if sort == 'featured'
            else post.favorite_count * 2 + post.like_count
            if sort == 'popular'
            else post.published_at
        )
        cursor_time = post.featured_at if sort == 'featured' else post.published_at
        next_cursor = _encode_cursor(primary, cursor_time or 0, post.id)
    return DiscoveryPostListResponse(items=await _summaries(session, user_id, page), next_cursor=next_cursor)


async def list_favorite_posts(
    session: AsyncSession,
    user_id: str,
    limit: int,
    cursor: str | None,
    category: DiscoveryCategory | None = None,
    media_kind: str | None = None,
) -> DiscoveryPostListResponse:
    stmt = _visible_posts_stmt().join(
        CreationPostReaction,
        and_(
            CreationPostReaction.post_id == CreationPost.id,
            CreationPostReaction.user_id == user_id,
            CreationPostReaction.kind == 'favorite',
        ),
    )
    disabled_categories = await _disabled_category_ids(session)
    stmt = _apply_feed_filters(stmt, disabled_categories, category, media_kind)
    if cursor:
        _, published_at, post_id = _decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                CreationPost.published_at < published_at,
                and_(CreationPost.published_at == published_at, CreationPost.id < post_id),
            )
        )
    rows = list(
        (
            await session.execute(
                stmt.order_by(desc(CreationPost.published_at), desc(CreationPost.id)).limit(limit + 1)
            )
        ).all()
    )
    page = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        post = page[-1][0]
        next_cursor = _encode_cursor(post.published_at, post.published_at, post.id)
    return DiscoveryPostListResponse(items=await _summaries(session, user_id, page), next_cursor=next_cursor)


async def update_discovery_operation(
    session: AsyncSession,
    post_id: str,
    form: DiscoveryOperationForm,
) -> CreationPublication | None:
    post = await session.get(CreationPost, post_id)
    if post is None:
        return None
    now = _now()
    if form.category is not None:
        if not await _category_exists(session, form.category, include_disabled=True):
            raise ValueError('invalid discovery category')
        post.category = form.category
    if form.featured is True:
        if post.status != 'published':
            raise ValueError('only published creations can be featured')
        post.featured_at = post.featured_at or now
    elif form.featured is False:
        post.featured_at = None
    # 排名变更只在作品已进入精选流（featured_at 已设置）时生效，避免
    # featured_rank 被静默更新但 featured_at=None 的不一致状态。
    if form.featured_rank is not None:
        if post.featured_at is not None:
            post.featured_rank = form.featured_rank
        elif form.featured is not True:
            raise ValueError('featured rank can only be set for featured creations')
    post.updated_at = now
    await session.commit()
    return _publication(post)


async def list_discovery_categories(
    session: AsyncSession,
    *,
    include_disabled: bool = False,
) -> tuple[DiscoveryCategoryItem, ...]:
    stmt = select(DiscoveryCategorySetting)
    if not include_disabled:
        stmt = stmt.where(DiscoveryCategorySetting.enabled.is_(True))
    rows = (
        await session.execute(stmt.order_by(DiscoveryCategorySetting.sort_order, DiscoveryCategorySetting.id))
    ).scalars()
    return tuple(
        DiscoveryCategoryItem(
            id=row.id,
            display_name=row.display_name,
            enabled=row.enabled,
            sort_order=row.sort_order,
        )
        for row in rows
    )


async def update_discovery_category(
    session: AsyncSession,
    category_id: DiscoveryCategory,
    form: DiscoveryCategoryUpdateForm,
) -> DiscoveryCategoryItem | None:
    category = await session.get(DiscoveryCategorySetting, category_id)
    if category is None:
        return None
    if form.display_name is not None:
        category.display_name = form.display_name
    if form.enabled is not None:
        if category.id == 'other' and form.enabled is False:
            raise ValueError('default category cannot be disabled')
        category.enabled = form.enabled
    if form.sort_order is not None:
        category.sort_order = form.sort_order
    category.updated_at = _now()
    await session.commit()
    return DiscoveryCategoryItem(
        id=category.id,
        display_name=category.display_name,
        enabled=category.enabled,
        sort_order=category.sort_order,
    )


async def create_discovery_category(
    session: AsyncSession,
    form: DiscoveryCategoryCreateForm,
) -> DiscoveryCategoryItem:
    category = DiscoveryCategorySetting(
        id=f'category_{uuid4().hex[:12]}',
        display_name=form.display_name,
        enabled=form.enabled,
        sort_order=form.sort_order,
        updated_at=_now(),
    )
    session.add(category)
    await session.commit()
    return DiscoveryCategoryItem(
        id=category.id,
        display_name=category.display_name,
        enabled=category.enabled,
        sort_order=category.sort_order,
    )


async def delete_discovery_category(
    session: AsyncSession,
    category_id: DiscoveryCategory,
) -> Literal['deleted', 'not_found', 'protected', 'in_use']:
    category = await session.get(DiscoveryCategorySetting, category_id)
    if category is None:
        return 'not_found'
    if category.id == 'other':
        return 'protected'
    usage_count = await session.scalar(
        select(func.count()).select_from(CreationPost).where(CreationPost.category == category_id)
    )
    if usage_count:
        return 'in_use'
    await session.delete(category)
    await session.commit()
    return 'deleted'


async def get_discovery_post(session: AsyncSession, user_id: str, post_id: str) -> DiscoveryPostDetail | None:
    row = (await session.execute(_visible_posts_stmt().where(CreationPost.id == post_id).limit(1))).first()
    if row is None:
        return None
    post, item = row
    summary = (await _summaries(session, user_id, [(post, item)]))[0]
    return DiscoveryPostDetail(
        **summary.model_dump(),
        model_id=item.model_id,
        prompt=item.prompt if post.show_prompt else None,
        negative_prompt=item.negative_prompt if post.show_prompt else None,
        params=item.params_json,
        task=item.task,
    )


async def set_reaction(
    session: AsyncSession,
    user_id: str,
    post_id: str,
    kind: ReactionKind,
    active: bool,
) -> ReactionState | None:
    post = (
        await session.execute(
            select(CreationPost)
            .join(CreationPostMedia, CreationPostMedia.post_id == CreationPost.id)
            .join(CreationMediaItem, CreationMediaItem.id == CreationPostMedia.creation_id)
            .where(
                CreationPost.id == post_id,
                CreationPost.status == 'published',
                CreationMediaItem.soft_deleted.is_(False),
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if post is None:
        return None
    existing = (
        await session.execute(
            select(CreationPostReaction).where(
                CreationPostReaction.post_id == post_id,
                CreationPostReaction.user_id == user_id,
                CreationPostReaction.kind == kind,
            )
        )
    ).scalar_one_or_none()
    if active and existing is None:
        session.add(CreationPostReaction(post_id=post_id, user_id=user_id, kind=kind, created_at=_now()))
        try:
            await session.flush()
        except IntegrityError:
            # 复盘 P1：并发重复点赞（双击/双请求）时两个事务都可能读到
            # existing is None 而插入同一主键——幂等按"已生效"处理并重开
            # 事务，不能把主键冲突的 500 暴露给用户。
            await session.rollback()
    elif not active and existing is not None:
        await session.execute(
            delete(CreationPostReaction).where(
                CreationPostReaction.post_id == post_id,
                CreationPostReaction.user_id == user_id,
                CreationPostReaction.kind == kind,
            )
        )
    # 复盘 P1：计数重算为单条原子 UPDATE（子查询在数据库端执行），消除
    # Python 侧"读统计→赋值"间隙下并发反应互相覆盖计数的丢更新窗口。
    await session.execute(
        update(CreationPost)
        .where(CreationPost.id == post_id)
        .values(
            like_count=select(func.count())
            .where(CreationPostReaction.post_id == post_id, CreationPostReaction.kind == 'like')
            .scalar_subquery(),
            favorite_count=select(func.count())
            .where(CreationPostReaction.post_id == post_id, CreationPostReaction.kind == 'favorite')
            .scalar_subquery(),
            updated_at=_now(),
        )
    )
    await session.commit()
    fresh = (
        await session.execute(
            select(CreationPost.like_count, CreationPost.favorite_count).where(CreationPost.id == post_id)
        )
    ).one()
    return ReactionState(
        post_id=post_id,
        kind=kind,
        active=active,
        like_count=int(fresh[0]),
        favorite_count=int(fresh[1]),
    )


async def get_published_content_file(session: AsyncSession, post_id: str) -> object | None:
    row = (await session.execute(_visible_posts_stmt().where(CreationPost.id == post_id).limit(1))).first()
    if row is None:
        return None
    _, item = row
    file = (await _load_files([item.file_id])).get(item.file_id)
    if file is None or getattr(file, 'user_id', None) != item.user_id:
        return None
    return file


async def get_published_poster_file(session: AsyncSession, post_id: str) -> object | None:
    row = (await session.execute(_visible_posts_stmt().where(CreationPost.id == post_id).limit(1))).first()
    if row is None:
        return None
    _, item = row
    if not isinstance(item.poster_file_id, str):
        return None
    file = (await _load_files([item.poster_file_id])).get(item.poster_file_id)
    if file is None or getattr(file, 'user_id', None) != item.user_id:
        return None
    return file


__all__ = [
    'get_creation_publication',
    'get_discovery_post',
    'get_published_content_file',
    'get_published_poster_file',
    'list_discovery_posts',
    'list_favorite_posts',
    'publish_creation',
    'set_reaction',
    'withdraw_creation',
]
