from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from open_webui.extensions.creations import capture
from open_webui.extensions.creations.capture import (
    build_creation_capture_context,
    capture_reference_snapshots,
    decode_prepared_references,
    finalize_created_images,
)
from open_webui.extensions.creations.db import CreationBase
from open_webui.extensions.creations.models import CreationMediaItem
from open_webui.extensions.creations.schemas import (
    CapturedImageBatch,
    CapturedImageResult,
    CapturedReferenceResult,
    CreationCaptureContext,
    ReusedImageResult,
)

PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
JPEG_MAGIC = b'\xff\xd8\xff\xe0'


def _data_url(payload: bytes, mime: str) -> str:
    return f'data:{mime};base64,{base64.b64encode(payload).decode("ascii")}'


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@pytest_asyncio.fixture
async def creation_session(tmp_path: Path):
    database_path = tmp_path / 'creations.sqlite'
    engine = create_async_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as connection:
        await connection.run_sync(CreationBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def make_context(
    *,
    user_id: str = 'user-1',
    task: str = 'text-to-image',
    source: str = 'web',
    prompt: str = 'a calm river',
    negative_prompt: str | None = None,
    public_model_id: str | None = 'z-image-turbo',
    model_name_snapshot: str | None = 'Z Image Turbo',
    params: dict | None = None,
    batch_id: str = 'usage-1',
) -> CreationCaptureContext:
    return CreationCaptureContext(
        user_id=user_id,
        task=task,
        source=source,
        prompt=prompt,
        negative_prompt=negative_prompt,
        public_model_id=public_model_id,
        model_name_snapshot=model_name_snapshot,
        params=params or {},
        batch_id=batch_id,
    )


def make_batch(
    *,
    result_file_id: str = 'result-1',
    result_user_id: str = 'user-1',
    result_created_at: int = 11,
    reference_ids: tuple[str, ...] = (),
    reuse: bool = False,
) -> CapturedImageBatch:
    if reuse:
        return CapturedImageBatch(images=(ReusedImageResult(url='/api/v1/files/old/content'),))
    references = tuple(
        CapturedReferenceResult(
            file_id=file_id,
            file_user_id=result_user_id,
            file_created_at=result_created_at,
            mime_type='image/png',
            sha256='a' * 64,
            position=pos,
        )
        for pos, file_id in enumerate(reference_ids)
    )
    return CapturedImageBatch(
        images=(
            CapturedImageResult(
                url=f'/api/v1/files/{result_file_id}/content',
                file_id=result_file_id,
                file_user_id=result_user_id,
                file_created_at=result_created_at,
                mime_type='image/png',
            ),
        ),
        references=references,
    )


@pytest.mark.asyncio
async def test_reference_capture_uses_normalized_provider_data_without_refetch(monkeypatch) -> None:
    uploaded: list[tuple[bytes, str]] = []
    png_bytes = PNG_MAGIC + b'png-test'
    jpeg_bytes = JPEG_MAGIC + b'jpeg-test'

    async def upload(_request, file, metadata, process, user):
        payload = file.file.read()
        uploaded.append((payload, file.content_type))
        return SimpleNamespace(id=f'ref-{len(uploaded)}', user_id=user.id, created_at=10 + len(uploaded))

    monkeypatch.setattr(capture, 'upload_file_handler', upload)

    prepared_references = decode_prepared_references(
        SimpleNamespace(
            provider_input=SimpleNamespace(
                image=(_data_url(png_bytes, 'image/png'), _data_url(jpeg_bytes, 'image/jpeg'))
            ),
            billing=SimpleNamespace(reference_hashes=(_sha(png_bytes), _sha(jpeg_bytes))),
        )
    )
    references = await capture_reference_snapshots(
        request=object(),
        references=prepared_references,
        user=SimpleNamespace(id='user-1'),
    )
    assert [item.position for item in references] == [0, 1]
    assert [item.file_id for item in references] == ['ref-1', 'ref-2']
    assert uploaded[0][0].startswith(PNG_MAGIC)
    assert uploaded[1][0].startswith(JPEG_MAGIC)


@pytest.mark.asyncio
async def test_decode_prepared_references_rejects_hash_or_order_mismatch() -> None:
    png_bytes = PNG_MAGIC + b'a'
    png_data_url = _data_url(png_bytes, 'image/png')

    with pytest.raises(ValueError, match='reference hash'):
        decode_prepared_references(
            SimpleNamespace(
                provider_input=SimpleNamespace(image=(png_data_url,)),
                billing=SimpleNamespace(reference_hashes=(_sha(PNG_MAGIC + b'b'),)),
            )
        )

    with pytest.raises(ValueError, match='reference count'):
        decode_prepared_references(
            SimpleNamespace(
                provider_input=SimpleNamespace(image=(png_data_url, png_data_url)),
                billing=SimpleNamespace(reference_hashes=(_sha(png_bytes),)),
            )
        )


@pytest.mark.asyncio
async def test_decode_prepared_references_rejects_riff_payload_without_webp_signature() -> None:
    fake_webp = b'RIFF' + (4).to_bytes(4, 'little') + b'WAVE'
    with pytest.raises(ValueError, match='mime type'):
        decode_prepared_references(
            SimpleNamespace(
                provider_input=SimpleNamespace(image=_data_url(fake_webp, 'image/webp')),
                billing=SimpleNamespace(reference_hashes=(_sha(fake_webp),)),
            )
        )


@pytest.mark.asyncio
async def test_decode_prepared_references_handles_single_string_and_none() -> None:
    png_bytes = PNG_MAGIC + b'solo'
    references = decode_prepared_references(
        SimpleNamespace(
            provider_input=SimpleNamespace(image=_data_url(png_bytes, 'image/png')),
            billing=SimpleNamespace(reference_hashes=(_sha(png_bytes),)),
        )
    )
    assert [item.position for item in references] == [0]
    assert references[0].sha256 == _sha(png_bytes)

    assert (
        decode_prepared_references(
            SimpleNamespace(provider_input=SimpleNamespace(image=None), billing=SimpleNamespace(reference_hashes=()))
        )
        == ()
    )


@pytest.mark.asyncio
async def test_finalize_writes_one_row_per_captured_result_with_ordered_references(creation_session) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(
            session,
            make_context(),
            make_batch(result_file_id='result-1', reference_ids=('ref-1', 'ref-2')),
        )

    async with creation_session() as session:
        rows = (await session.execute(select(CreationMediaItem))).scalars().all()
        assert len(rows) == 1
        row = rows[0]
        assert row.file_id == 'result-1'
        assert row.kind == 'image'
        assert row.task == 'text-to-image'
        assert row.source == 'web'
        assert row.batch_id == 'usage-1'
        assert row.model_name_snapshot == 'Z Image Turbo'
        assert row.reference_file_ids_json == ['ref-1', 'ref-2']
        assert row.soft_deleted is False
        assert row.created_at == 11


@pytest.mark.asyncio
async def test_finalize_replay_preserves_caption_and_soft_delete(creation_session) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(batch_id='usage-1'), make_batch(reference_ids=('ref-1',)))

    async with creation_session() as session, session.begin():
        row = (await session.execute(select(CreationMediaItem))).scalar_one()
        row.caption = 'keep'
        row.soft_deleted = True

    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(batch_id='usage-1'), make_batch(reference_ids=('ref-1',)))

    async with creation_session() as session:
        row = (await session.execute(select(CreationMediaItem))).scalar_one()
        assert row.caption == 'keep'
        assert row.soft_deleted is True


@pytest.mark.asyncio
async def test_finalize_rejects_file_owner_mismatch(creation_session) -> None:
    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='creation file ownership mismatch'):
            await finalize_created_images(
                session,
                make_context(user_id='user-1'),
                make_batch(result_user_id='user-2'),
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'references',
    [
        (
            CapturedReferenceResult(
                file_id='ref-1',
                file_user_id='user-1',
                file_created_at=10,
                mime_type='image/png',
                sha256='a' * 64,
                position=1,
            ),
        ),
        (
            CapturedReferenceResult(
                file_id='ref-1',
                file_user_id='user-1',
                file_created_at=10,
                mime_type='image/png',
                sha256='a' * 64,
                position=0,
            ),
            CapturedReferenceResult(
                file_id='ref-1',
                file_user_id='user-1',
                file_created_at=10,
                mime_type='image/png',
                sha256='b' * 64,
                position=1,
            ),
        ),
    ],
)
async def test_finalize_rejects_invalid_reference_identity(creation_session, references) -> None:
    base = make_batch()
    batch = CapturedImageBatch(images=base.images, references=references)
    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='invalid creation reference identity'):
            await finalize_created_images(session, make_context(), batch)


@pytest.mark.asyncio
async def test_finalize_reuse_only_batch_is_noop(creation_session) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(), make_batch(reuse=True))

    async with creation_session() as session:
        assert (await session.execute(select(CreationMediaItem))).scalars().all() == []


@pytest.mark.asyncio
async def test_finalize_rejects_mixed_reused_and_captured_batch(creation_session) -> None:
    batch = CapturedImageBatch(
        images=(
            CapturedImageResult(
                url='/api/v1/files/r1/content',
                file_id='r1',
                file_user_id='user-1',
                file_created_at=11,
                mime_type='image/png',
            ),
            ReusedImageResult(url='/api/v1/files/old/content'),
        )
    )
    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='mixes reused and captured'):
            await finalize_created_images(session, make_context(), batch)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'changed_context',
    [
        {'prompt': 'a different prompt'},
        {'negative_prompt': 'different negative prompt'},
        {'model_name_snapshot': 'Different model name'},
        {'params': {'quality': 'high'}},
    ],
)
async def test_finalize_rejects_replay_when_generation_snapshot_changes(creation_session, changed_context) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(), make_batch())

    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='immutable identity conflict'):
            await finalize_created_images(session, make_context(**changed_context), make_batch())


@pytest.mark.asyncio
async def test_finalize_rejects_replay_when_result_timestamp_changes(creation_session) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(), make_batch(result_created_at=11))

    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='immutable identity conflict'):
            await finalize_created_images(session, make_context(), make_batch(result_created_at=12))


@pytest.mark.asyncio
async def test_finalize_rejects_immutable_identity_conflict(creation_session) -> None:
    async with creation_session() as session, session.begin():
        await finalize_created_images(
            session,
            make_context(user_id='user-1', batch_id='usage-1'),
            make_batch(result_file_id='shared-file', reference_ids=('ref-1',)),
        )

    async with creation_session() as session, session.begin():
        with pytest.raises(RuntimeError, match='immutable identity conflict'):
            await finalize_created_images(
                session,
                make_context(user_id='user-1', batch_id='different-batch'),
                make_batch(result_file_id='shared-file', reference_ids=('ref-1',)),
            )


@pytest.mark.asyncio
async def test_build_context_maps_fal_public_id_and_allowlists_params(monkeypatch) -> None:
    from open_webui.extensions.fal_images import models as fal_models

    internal_id = None
    for model in fal_models.FAL_IMAGE_MODELS:
        if fal_models.public_fal_image_model_id(model['id']) is not None:
            internal_id = model['id']
            break
    assert internal_id is not None, 'registry must expose at least one publicly aliased FAL model'
    public_id = fal_models.public_fal_image_model_id(internal_id)

    prepared = SimpleNamespace(
        billing=SimpleNamespace(
            resource_id=internal_id,
            action='image-to-image',
            channel='chat',
            reference_hashes=(),
        ),
        provider_input=SimpleNamespace(
            model=internal_id,
            prompt='paint it black',
            image=None,
            size=None,
            resolution=None,
            aspect_ratio='16:9',
            quality='hd',
            image_count=2,
            extra={
                'noise': 'drop-me',
                'negative_prompt': '  blurry  ',
                'background': 'transparent',
                'output_format': 'png',
                'system_prompt': 'follow the composition',
                'sync_mode': True,
                'safety_tolerance': '4',
                'limit_generations': False,
                'enable_web_search': False,
                'thinking_level': 'minimal',
                'enable_safety_checker': True,
                'enable_prompt_expansion': False,
                'acceleration': 'regular',
                'input_fidelity': 'high',
                'strength': 0.65,
            },
        ),
    )
    ctx = build_creation_capture_context(
        raw_form=SimpleNamespace(model=internal_id, prompt='paint it black', negative_prompt='blurry'),
        prepared=prepared,
        user=SimpleNamespace(id='user-9', name='Alice', email='alice@example.com'),
        usage_id='usage-9',
    )
    assert ctx.user_id == 'user-9'
    assert ctx.task == 'image-to-image'
    assert ctx.source == 'chat'
    assert ctx.batch_id == 'usage-9'
    assert ctx.negative_prompt == 'blurry'
    assert ctx.public_model_id == public_id
    assert ctx.model_name_snapshot == next(
        model['name'] for model in fal_models.FAL_IMAGE_MODELS if model['id'] == internal_id
    )
    assert 'noise' not in ctx.params
    assert ctx.params == {
        'aspect_ratio': '16:9',
        'quality': 'hd',
        'image_count': 2,
        'background': 'transparent',
        'output_format': 'png',
        'system_prompt': 'follow the composition',
        'sync_mode': True,
        'safety_tolerance': '4',
        'limit_generations': False,
        'enable_web_search': False,
        'thinking_level': 'minimal',
        'enable_safety_checker': True,
        'enable_prompt_expansion': False,
        'acceleration': 'regular',
        'input_fidelity': 'high',
        'strength': 0.65,
    }


@pytest.mark.asyncio
async def test_build_context_keeps_original_resource_id_for_non_fal_engines() -> None:
    prepared = SimpleNamespace(
        billing=SimpleNamespace(
            resource_id='openai-direct-model',
            action='text-to-image',
            channel='api',
            reference_hashes=(),
        ),
        provider_input=SimpleNamespace(
            model='openai-direct-model',
            prompt='hi',
            image=None,
            size='1024x1024',
            resolution=None,
            aspect_ratio=None,
            quality=None,
            image_count=1,
            extra={},
        ),
    )
    ctx = build_creation_capture_context(
        raw_form=SimpleNamespace(model='openai-direct-model', prompt='hi', negative_prompt=None),
        prepared=prepared,
        user=SimpleNamespace(id='user-1'),
        usage_id='usage-1',
    )
    assert ctx.public_model_id == 'openai-direct-model'
    assert ctx.source == 'api'


@pytest.mark.asyncio
async def test_build_context_prefers_raw_form_prompt() -> None:
    """捕获层落库用户提交原文（raw_form 优先）：provider_input 只是经过
    变换的输入兜底，任务行/作品详情记录的始终是输入框里的内容。"""
    prepared = SimpleNamespace(
        billing=SimpleNamespace(
            resource_id='openai-direct-model',
            action='text-to-image',
            channel='api',
            reference_hashes=(),
        ),
        provider_input=SimpleNamespace(
            model='openai-direct-model',
            prompt='a girl, cinematic lighting',
            image=None,
            size=None,
            resolution=None,
            aspect_ratio=None,
            quality=None,
            image_count=1,
            extra={},
        ),
    )
    ctx = build_creation_capture_context(
        raw_form=SimpleNamespace(
            model='openai-direct-model',
            prompt='a girl, cinematic lighting',
            negative_prompt=None,
        ),
        prepared=prepared,
        user=SimpleNamespace(id='user-1'),
        usage_id='usage-1',
    )
    assert ctx.prompt == 'a girl, cinematic lighting'


@pytest.mark.asyncio
async def test_capture_reference_snapshots_records_mime_sha_position(monkeypatch) -> None:
    png_bytes = PNG_MAGIC + b'alpha'

    async def upload(_request, file, metadata, process, user):
        assert metadata == {'creation_reference': True}
        assert process is False
        payload = file.file.read()
        assert payload == png_bytes
        assert file.filename.endswith('.png')
        return SimpleNamespace(id='snap-1', user_id=user.id, created_at=42)

    monkeypatch.setattr(capture, 'upload_file_handler', upload)
    references = await capture_reference_snapshots(
        request=object(),
        references=decode_prepared_references(
            SimpleNamespace(
                provider_input=SimpleNamespace(image=_data_url(png_bytes, 'image/png')),
                billing=SimpleNamespace(reference_hashes=(_sha(png_bytes),)),
            )
        ),
        user=SimpleNamespace(id='user-1'),
    )
    assert len(references) == 1
    snap = references[0]
    assert snap.file_id == 'snap-1'
    assert snap.file_user_id == 'user-1'
    assert snap.mime_type == 'image/png'
    assert snap.sha256 == _sha(png_bytes)
    assert snap.position == 0
    assert snap.file_created_at == 42


@pytest.mark.asyncio
async def test_capture_reference_snapshots_empty_for_no_references(monkeypatch) -> None:
    async def upload(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError('upload must not be called without references')

    monkeypatch.setattr(capture, 'upload_file_handler', upload)
    references = await capture_reference_snapshots(
        request=object(),
        references=(),
        user=SimpleNamespace(id='user-1'),
    )
    assert references == ()


@pytest.mark.asyncio
async def test_capture_reference_snapshots_propagates_upload_failure(monkeypatch) -> None:
    png_bytes = PNG_MAGIC + b'beta'

    async def upload(_request, file, metadata, process, user):
        raise RuntimeError('storage blew up')

    monkeypatch.setattr(capture, 'upload_file_handler', upload)
    with pytest.raises(RuntimeError, match='storage blew up'):
        await capture_reference_snapshots(
            request=object(),
            references=decode_prepared_references(
                SimpleNamespace(
                    provider_input=SimpleNamespace(image=_data_url(png_bytes, 'image/png')),
                    billing=SimpleNamespace(reference_hashes=(_sha(png_bytes),)),
                )
            ),
            user=SimpleNamespace(id='user-1'),
        )


@pytest.mark.asyncio
async def test_finalize_preloads_existing_rows_in_one_batched_query(creation_session, monkeypatch) -> None:
    """复盘 P2：N 图 finalize 原先逐张 SELECT（N+1）；现在批量预载只查一次。"""
    context = make_context()
    images = tuple(
        CapturedImageResult(
            url=f'/api/v1/files/result-{index}/content',
            file_id=f'result-{index}',
            file_user_id='user-1',
            file_created_at=11,
            mime_type='image/png',
        )
        for index in range(3)
    )
    batch = CapturedImageBatch(images=images, references=())

    real_batch = capture._load_existing_batch
    queries = 0

    async def counting_batch(session_, file_ids):
        nonlocal queries
        queries += 1
        assert sorted(file_ids) == ['result-0', 'result-1', 'result-2']
        return await real_batch(session_, file_ids)

    monkeypatch.setattr(capture, '_load_existing_batch', counting_batch)

    async with creation_session() as session, session.begin():
        await finalize_created_images(session, context, batch)

    assert queries == 1
    async with creation_session() as session:
        rows = (await session.execute(select(CreationMediaItem))).scalars().all()
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_finalize_concurrent_duplicate_insert_replays_committed_row(creation_session, monkeypatch) -> None:
    """复盘 P1：同 file_id 并发捕获撞唯一约束时按已提交行回退 replay 校验
    （SAVEPOINT 只回滚本条插入，不动计费 terminal 事务）——一致的幂等重放
    放行，已生成的付费结果不整体失败。"""
    context = make_context()
    batch = make_batch(reference_ids=('ref-1',))

    # 另一事务已提交同一结果的 creation 行（内容与本次一致）。
    async with creation_session() as session, session.begin():
        await finalize_created_images(session, make_context(), make_batch(reference_ids=('ref-1',)))

    real_load_existing = capture._load_existing
    fallback_loads = 0

    async def load_batch_missing(session_, file_ids):
        # 并发窗口：批量预载读不到另一事务已提交的行，误判为首次插入。
        return {}

    async def count_fallback_load(session_, file_id):
        nonlocal fallback_loads
        fallback_loads += 1
        return await real_load_existing(session_, file_id)

    monkeypatch.setattr(capture, '_load_existing_batch', load_batch_missing)
    monkeypatch.setattr(capture, '_load_existing', count_fallback_load)

    async with creation_session() as session, session.begin():
        await finalize_created_images(session, context, batch)

    assert fallback_loads == 1
    async with creation_session() as session:
        rows = (await session.execute(select(CreationMediaItem))).scalars().all()
    assert len(rows) == 1
