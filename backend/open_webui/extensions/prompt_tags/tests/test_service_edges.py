from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from open_webui.extensions.prompt_tags import service
from open_webui.extensions.prompt_tags.schemas import PromptTagModelRef
from sqlalchemy.exc import IntegrityError


def _row(**changes):
    values = {
        'media_kinds_json': ['image', 'video', 'invalid'],
        'model_refs_json': [
            {'media_kind': 'image', 'model_id': 'fal-ai/z-image/turbo'},
            {'invalid': True},
        ],
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_tag_scope_helpers_fail_closed_for_corrupt_rows(monkeypatch) -> None:
    assert service._media_kinds(_row()) == ('image', 'video')
    assert service._media_kinds(_row(media_kinds_json=None)) == ()
    assert len(service._model_refs(_row())) == 1
    assert service._model_refs(_row(model_refs_json=None)) == ()

    assert service._tag_applies(_row(model_refs_json=[]), None, None) is True
    assert service._tag_applies(_row(), 'video', 'model') is True
    assert service._tag_applies(_row(), 'image', None) is False
    assert service._tag_applies(_row(media_kinds_json=['video']), 'image', 'model') is False

    monkeypatch.setattr(
        service,
        'load_video_catalog_cached',
        lambda: SimpleNamespace(
            internal_to_public={'fal-ai/video': 'video'},
            public_to_internal={'video': 'fal-ai/video'},
        ),
    )
    assert service.canonical_model_id('video', '/video/') == 'fal-ai/video'
    assert service.canonical_model_id('video', 'fal-ai/video') == 'fal-ai/video'
    refs = service._canonical_refs(
        (
            PromptTagModelRef(media_kind='video', model_id='video'),
            PromptTagModelRef(media_kind='video', model_id='fal-ai/video'),
        )
    )
    assert refs == [{'media_kind': 'video', 'model_id': 'fal-ai/video'}]


@pytest.mark.asyncio
async def test_catalog_import_finisher_commits_rolls_back_and_maps_conflicts() -> None:
    session = SimpleNamespace(flush=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock())
    await service._finish_catalog_import(session, dry_run=False)
    session.commit.assert_awaited_once()

    session.commit.reset_mock()
    await service._finish_catalog_import(session, dry_run=True)
    session.rollback.assert_awaited()

    # flush_only：只 flush 保持事务打开，既不提交也不回滚（导入中途先落库分类用）。
    session.rollback.reset_mock()
    await service._finish_catalog_import(session, dry_run=False, flush_only=True)
    session.flush.assert_awaited()
    session.commit.assert_not_awaited()
    session.rollback.assert_not_awaited()

    session.flush.side_effect = IntegrityError('statement', {}, RuntimeError('constraint'))
    with pytest.raises(service.PromptTagConflictError):
        await service._finish_catalog_import(session, dry_run=False)
    session.flush.side_effect = RuntimeError('db')
    with pytest.raises(RuntimeError):
        await service._finish_catalog_import(session, dry_run=False)


@pytest.mark.asyncio
async def test_delete_paths_reject_missing_and_nonempty_categories() -> None:
    session = SimpleNamespace(
        get=AsyncMock(return_value=None),
        scalar=AsyncMock(),
        execute=AsyncMock(),
        delete=AsyncMock(),
        commit=AsyncMock(),
    )
    with pytest.raises(service.PromptTagNotFoundError):
        await service.delete_category(session, 'missing', cascade=False)
    with pytest.raises(service.PromptTagNotFoundError):
        await service.delete_tag(session, 'missing')

    row = object()
    session.get.return_value = row
    session.scalar.return_value = 'tag'
    with pytest.raises(service.PromptTagCategoryNotEmptyError):
        await service.delete_category(session, 'category', cascade=False)
    await service.delete_category(session, 'category', cascade=True)
    session.execute.assert_awaited_once()
    session.delete.assert_awaited_once_with(row)
