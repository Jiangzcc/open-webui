# Personal Creations Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Repository rules override the generic skill: do not use worktrees, and do not delegate Code Review to a subagent.

**Goal:** Build a persistent personal image creations library inside `/images`, capture text-to-image and image-to-image results from every production entry point, preserve immutable reference-image snapshots, and give administrators a read-only view of every user’s visible creations.

**Architecture:** Add an independent `backend/open_webui/extensions/creations/` extension with its own model, Alembic chain, service, router, and startup validation. Keep upstream changes to thin bridges in image billing, image routing, middleware/tool call sites, `main.py`, and the existing `/images` shell. Persist only metadata and upstream file IDs; result and reference bytes remain in the existing File/Storage subsystem.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy async, Alembic, SQLite/PostgreSQL, SvelteKit 2, Svelte 5, TypeScript, Vitest, Tailwind CSS, existing Open WebUI File/Storage and i18n APIs.

## Global Constraints

- Work on the current `test` branch; `main` remains the untouched upstream-tracking branch.
- Do not use Git worktrees in the main session or any auxiliary process.
- Do not delegate Code Review to a subagent; the current main agent performs the final review directly.
- Do not commit, push, open a PR, merge, or rebase unless the user explicitly authorizes that outward-facing action. Each task ends at a verified working-tree checkpoint.
- Prefer the independent extension and thin bridge described here; do not alter upstream tables or migration history.
- All extension tables, indexes, constraints, and migration objects use the `ext_creation_` namespace and an independent Alembic version table named `ext_creation_schema_version`.
- Do not add or upgrade dependencies; use the packages already in `package.json` and `pyproject.toml`.
- All verified users (`user` and `admin`, never `pending`) may open `/images` and call the two direct image HTTP endpoints regardless of image feature switches; chat and builtin tool calls retain the existing feature/permission gates.
- Authorization scope is a required server-side `Literal['direct', 'chat', 'tool']`; clients cannot provide or override it. Valid scope/channel pairs are `direct → web|api`, `chat → chat`, and `tool → tool`.
- A successful provider call returns to the client only after creation rows and `ext_credit_usage.status='succeeded'` commit in one transaction. Terminal-finalization failure leaves usage `invoking` for existing recovery to mark `unknown`; do not refund automatically.
- Store one `ext_creation_media_item` row per generated result. Do not backfill pre-release files, add a batch table, generate thumbnails, add quotas, or implement a recycle bin.
- Store immutable image-to-image reference snapshots as upstream files and an ordered `reference_file_ids_json` array; never persist or return reference data URLs, external URLs, hashes, or internal file IDs in user DTOs.
- Personal read/write routes are owner-scoped. Administrator global routes are separate and read-only; administrators cannot PATCH or DELETE another user’s creation.
- Soft deletion removes only the library row from visible queries; never delete result files or reference snapshot files.
- List pages default to 20, allow 1–100, sort by `created_at DESC, id DESC`, and use a versioned opaque cursor.
- User-facing UI and copy use the existing i18n mechanism with Simplified Chinese translations.
- Local development must respect the intentional Vite proxy default `http://localhost:9000`; do not restore it to 8080/8000. When using `backend/dev.sh`, set `PORT=9000` for the smoke run.
- UI changes must work at desktop and narrow mobile widths, support touch, avoid hover-only actions, preserve visible focus, provide semantic tabs/ARIA, and avoid horizontal overflow.
- Preserve the existing local FAL mock exactly as a server-generated `ReusedImageResult` development exception; do not enable, remove, or broaden it.

---

## File Structure

### New backend files

- `backend/open_webui/extensions/creations/__init__.py` — extension exports only.
- `backend/open_webui/extensions/creations/db.py` — independent declarative base and async session dependency/context manager.
- `backend/open_webui/extensions/creations/models.py` — `CreationMediaItem` ORM model and named constraints/indexes.
- `backend/open_webui/extensions/creations/schemas.py` — capture dataclasses, cursor types, request forms, and response DTOs.
- `backend/open_webui/extensions/creations/capture.py` — request snapshot normalization, normalized-reference decoding/hash verification, reference snapshot upload, and batch finalization.
- `backend/open_webui/extensions/creations/service.py` — cursor encoding, owner/admin reads, caption update, and soft deletion.
- `backend/open_webui/extensions/creations/router.py` — personal and administrator HTTP routes.
- `backend/open_webui/extensions/creations/metrics.py` — bounded low-cardinality counters.
- `backend/open_webui/extensions/creations/registration.py` — migration startup and schema validation; no background worker or shutdown hook.
- `backend/open_webui/extensions/creations/migrations/{__init__.py,alembic.ini,config.py,env.py,runner.py,script.py.mako}` — independent Alembic chain copied structurally from credits with creation-specific names.
- `backend/open_webui/extensions/creations/migrations/versions/{__init__.py,0001_create_creation_media_item.py}` — first extension revision.
- `backend/open_webui/extensions/creations/tests/{__init__.py,conftest.py,test_schemas.py,test_migrations.py,test_capture.py,test_service.py,test_router.py,test_image_entrypoints.py,test_registration.py}` — focused backend suite.

### Modified backend files

- `backend/open_webui/extensions/credits/service.py` — add an in-session succeeded transition used by the shared terminal transaction.
- `backend/open_webui/extensions/credits/image_billing.py` — required authorization scope, opaque internal batch result, mandatory finalizer, and shared terminal transaction.
- `backend/open_webui/extensions/credits/tests/test_image_billing.py` — RED/GREEN coverage for scope and finalizer semantics.
- `backend/open_webui/routers/images.py` — direct-scope authorization, captured result values, reference snapshot bridge, and mandatory finalizer closure.
- `backend/open_webui/tools/builtin.py` — pass `authorization_scope='tool'` at both builtin image call sites.
- `backend/open_webui/utils/middleware.py` — pass `authorization_scope='chat'` at both chat image call sites.
- `backend/open_webui/models/users.py` — one narrow batched owner lookup used by the administrator list, only if still absent when implementing.
- `backend/open_webui/main.py` — initialize the extension and include its router.

### New frontend files

- `src/lib/apis/creations/index.ts` — personal/admin list/detail, PATCH, and DELETE wrappers and DTO types.
- `src/lib/apis/creations/index.test.ts` — fetch contract and error tests.
- `src/lib/utils/creations-library.ts` — scope state, stable page merge, stale-response gate, and optimistic removal helpers.
- `src/lib/utils/creations-library.test.ts` — pure state tests.
- `src/lib/components/images/CreationsLibrary.svelte` — owner/admin grids, scope state, lazy pagination, preview, and error/empty states.
- `src/lib/components/images/CreationsLibrary.test.ts` — source-level accessibility/lazy-loading contract tests following the existing component-test style.
- `src/lib/components/images/CreationDetailsModal.svelte` — lazy detail, ordered references, caption edit, and owner-only removal.
- `src/lib/components/images/CreationDetailsModal.test.ts` — source-level modal/read-only contract tests.

### Modified frontend files

- `src/lib/components/images/Images.svelte` — accessible `新建｜作品库` tabs, persistent view state, direct-page gate removal, composer hiding, and `libraryRevision`.
- `src/lib/components/images/Images.test.ts` — tab, persistence, and revision contracts.
- `src/lib/components/layout/Sidebar.svelte` — make the existing images item visible to verified users.
- `src/lib/components/layout/Sidebar/UserMenu.svelte` — make the existing images menu/pin action visible to verified users.
- `src/lib/i18n/locales/zh-CN/translation.json` — complete Simplified Chinese creation-library copy.

---

### Task 1: Define immutable capture types, API DTOs, and cursor validation

**Files:**
- Create: `backend/open_webui/extensions/creations/__init__.py`
- Create: `backend/open_webui/extensions/creations/schemas.py`
- Create: `backend/open_webui/extensions/creations/tests/__init__.py`
- Create: `backend/open_webui/extensions/creations/tests/test_schemas.py`

**Interfaces:**
- Produces: `AuthorizationScope`, `PreparedReference`, `CapturedImageResult`, `ReusedImageResult`, `CapturedReferenceResult`, `CapturedImageBatch`, `CreationCaptureContext`, `CreationSummary`, `CreationDetail`, `AdminCreationSummary`, `AdminCreationDetail`, `CreationListResponse`, `AdminCreationListResponse`, `CaptionUpdateForm`, `encode_creation_cursor()`, and `decode_creation_cursor()`.
- Consumes: existing Pydantic v2 and Python dataclasses only.

- [ ] **Step 1: Write failing schema and cursor tests**

Create tests that lock the public/internal boundary before production code exists:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from open_webui.extensions.creations.schemas import (
    CaptionUpdateForm,
    CapturedImageBatch,
    CapturedImageResult,
    CapturedReferenceResult,
    CreationReference,
    CreationSummary,
    ReusedImageResult,
    decode_creation_cursor,
    encode_creation_cursor,
)


def test_cursor_round_trip_is_versioned_and_opaque() -> None:
    encoded = encode_creation_cursor(1_784_680_000, 'creation-9')
    assert '=' not in encoded
    assert decode_creation_cursor(encoded) == (1_784_680_000, 'creation-9')


@pytest.mark.parametrize('cursor', ['', 'not-base64', 'e30', 'eyJ2IjoyfQ'])
def test_invalid_cursor_is_rejected(cursor: str) -> None:
    with pytest.raises(ValueError, match='invalid creation cursor'):
        decode_creation_cursor(cursor)


def test_caption_trims_blank_and_limits_unicode_code_points() -> None:
    assert CaptionUpdateForm(caption='   ').caption is None
    assert CaptionUpdateForm(caption='  备注  ').caption == '备注'
    with pytest.raises(ValidationError):
        CaptionUpdateForm(caption='图' * 1001)


def test_internal_capture_values_are_immutable_and_ordered() -> None:
    reference = CapturedReferenceResult(
        file_id='reference-1',
        file_user_id='user-1',
        file_created_at=10,
        mime_type='image/png',
        sha256='a' * 64,
        position=0,
    )
    batch = CapturedImageBatch(
        images=(
            CapturedImageResult(
                url='/api/v1/files/result-1/content',
                file_id='result-1',
                file_user_id='user-1',
                file_created_at=11,
                mime_type='image/png',
            ),
        ),
        references=(reference,),
    )
    assert batch.references == (reference,)
    with pytest.raises(AttributeError):
        batch.references = ()


def test_reused_result_is_a_distinct_server_only_type() -> None:
    batch = CapturedImageBatch(images=(ReusedImageResult(url='/api/v1/files/old/content'),))
    assert isinstance(batch.images[0], ReusedImageResult)


def test_user_summary_never_accepts_internal_file_identity() -> None:
    payload = {
        'id': 'creation-1',
        'kind': 'image',
        'content_url': '/api/v1/files/result-1/content',
        'availability': 'available',
        'mime_type': 'image/png',
        'caption': None,
        'model_name': 'Model',
        'task': 'text-to-image',
        'created_at': 10,
        'updated_at': 10,
        'file_id': 'must-not-survive',
    }
    with pytest.raises(ValidationError):
        CreationSummary.model_validate(payload)


def test_reference_dto_contains_url_state_but_no_internal_id() -> None:
    reference = CreationReference(position=0, content_url=None, availability='missing', mime_type=None)
    assert reference.model_dump() == {
        'position': 0,
        'content_url': None,
        'availability': 'missing',
        'mime_type': None,
    }
```

- [ ] **Step 2: Run the schema test and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests/test_schemas.py" -q
```

Expected: collection fails because `open_webui.extensions.creations.schemas` does not exist.

- [ ] **Step 3: Implement the exact internal and public types**

Use frozen dataclasses for internal values and `ConfigDict(extra='forbid')` for request and response DTOs so unexpected/internal fields fail validation rather than being silently retained or dropped. The central definitions must use these signatures:

```python
AuthorizationScope = Literal['direct', 'chat', 'tool']
CreationTask = Literal['text-to-image', 'image-to-image']
CreationSource = Literal['web', 'api', 'chat', 'tool']
CreationAvailability = Literal['available', 'missing']


@dataclass(frozen=True)
class PreparedReference:
    payload: bytes
    mime_type: str
    sha256: str
    position: int


@dataclass(frozen=True)
class CapturedImageResult:
    url: str
    file_id: str
    file_user_id: str
    file_created_at: int
    mime_type: str


@dataclass(frozen=True)
class ReusedImageResult:
    url: str


@dataclass(frozen=True)
class CapturedReferenceResult:
    file_id: str
    file_user_id: str
    file_created_at: int
    mime_type: str
    sha256: str
    position: int


@dataclass(frozen=True)
class CapturedImageBatch:
    images: tuple[CapturedImageResult | ReusedImageResult, ...]
    references: tuple[CapturedReferenceResult, ...] = ()


@dataclass(frozen=True)
class CreationCaptureContext:
    user_id: str
    task: CreationTask
    source: CreationSource
    prompt: str
    negative_prompt: str | None
    public_model_id: str | None
    model_name_snapshot: str | None
    params: Mapping[str, object]
    batch_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, 'params', MappingProxyType(dict(self.params)))
```

Implement cursor JSON as `{'v': 1, 'created_at': int, 'id': str}`, no padding, maximum encoded length 512, nonnegative signed-64-bit timestamp, and ID length 1–128. `CaptionUpdateForm` must use `ConfigDict(extra='forbid')`, trim the value, convert blank to `None`, and reject more than 1000 Unicode code points.

- [ ] **Step 4: Run the schema test and verify GREEN**

Run the Step 2 command again. Expected: all tests in `test_schemas.py` pass.

- [ ] **Step 5: Checkpoint without committing**

Run `git diff --check -- backend/open_webui/extensions/creations`. Do not commit unless the user separately authorizes it.

---

### Task 2: Add the independent creation table and migration chain

**Files:**
- Create: `backend/open_webui/extensions/creations/db.py`
- Create: `backend/open_webui/extensions/creations/models.py`
- Create: `backend/open_webui/extensions/creations/migrations/__init__.py`
- Create: `backend/open_webui/extensions/creations/migrations/alembic.ini`
- Create: `backend/open_webui/extensions/creations/migrations/config.py`
- Create: `backend/open_webui/extensions/creations/migrations/env.py`
- Create: `backend/open_webui/extensions/creations/migrations/runner.py`
- Create: `backend/open_webui/extensions/creations/migrations/script.py.mako`
- Create: `backend/open_webui/extensions/creations/migrations/versions/__init__.py`
- Create: `backend/open_webui/extensions/creations/migrations/versions/0001_create_creation_media_item.py`
- Create: `backend/open_webui/extensions/creations/tests/conftest.py`
- Create: `backend/open_webui/extensions/creations/tests/test_migrations.py`

**Interfaces:**
- Produces: `CreationBase`, `creation_session()`, `get_creation_session()`, `CreationMediaItem`, and `run_creation_migrations()`.
- Consumes: `DATABASE_SCHEMA`, `AsyncSessionLocal`, `JSONField`, `engine`, and the upstream Alembic head.

- [ ] **Step 1: Write migration tests first**

Model the tests on `extensions/credits/tests/test_migrations.py`, but assert exactly one extension table plus its version table:

```python
EXPECTED_INDEXES = {
    'ix_ext_creation_media_user_visible_created',
    'ix_ext_creation_media_visible_created',
    'ix_ext_creation_media_batch',
}
EXPECTED_CHECKS = {
    'ck_ext_creation_media_kind',
    'ck_ext_creation_media_task',
    'ck_ext_creation_media_source',
}


def test_upgrade_creates_only_creation_objects_and_preserves_upstream_sentinel(sqlite_database) -> None:
    engine, database_path = sqlite_database
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE user (id VARCHAR(128) PRIMARY KEY)'))
    with engine.connect() as connection:
        run_creation_migrations(connection=connection, verify_upstream=False)
    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {
        'user',
        'ext_creation_media_item',
        'ext_creation_schema_version',
    }
    assert not Path(f'{database_path}.creation-migrations.lock').exists()


def test_revision_has_required_constraints_and_indexes(sqlite_database) -> None:
    engine, _ = sqlite_database
    with engine.connect() as connection:
        run_creation_migrations(connection=connection, verify_upstream=False)
    inspector = inspect(engine)
    assert {item['name'] for item in inspector.get_unique_constraints('ext_creation_media_item')} >= {
        'uq_ext_creation_media_file'
    }
    assert {item['name'] for item in inspector.get_check_constraints('ext_creation_media_item')} >= EXPECTED_CHECKS
    assert {item['name'] for item in inspector.get_indexes('ext_creation_media_item')} >= EXPECTED_INDEXES
    assert inspector.get_foreign_keys('ext_creation_media_item') == []
```

Also copy and rename the credits tests for repeated upgrade, downgrade preserving an upstream sentinel, upstream-head mismatch, PostgreSQL advisory-lock release, SQLite file-lock release, and connection transaction guards.

- [ ] **Step 2: Run migration tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests/test_migrations.py" -q
```

Expected: import failure for creation DB/model/migration modules.

- [ ] **Step 3: Implement the DB model**

`CreationMediaItem.__table_args__` must contain the named unique/check/index objects below, with no physical FK to user or file tables:

```python
class CreationMediaItem(CreationBase):
    __tablename__ = 'ext_creation_media_item'
    __table_args__ = (
        UniqueConstraint('file_id', name='uq_ext_creation_media_file'),
        CheckConstraint("kind IN ('image')", name='ck_ext_creation_media_kind'),
        CheckConstraint(
            "task IN ('text-to-image', 'image-to-image')",
            name='ck_ext_creation_media_task',
        ),
        CheckConstraint(
            "source IN ('web', 'api', 'chat', 'tool')",
            name='ck_ext_creation_media_source',
        ),
        Index(
            'ix_ext_creation_media_user_visible_created',
            'user_id',
            'soft_deleted',
            'created_at',
            'id',
        ),
        Index(
            'ix_ext_creation_media_visible_created',
            'soft_deleted',
            'created_at',
            'id',
        ),
        Index('ix_ext_creation_media_batch', 'batch_id'),
    )

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False)
    kind = Column(String(16), nullable=False)
    file_id = Column(String(128), nullable=False)
    caption = Column(String(1000), nullable=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    model_id = Column(String(256), nullable=True)
    model_name_snapshot = Column(String(256), nullable=True)
    task = Column(String(32), nullable=False)
    params_json = Column(JSONField, nullable=True)
    reference_file_ids_json = Column(JSONField, nullable=True)
    source = Column(String(16), nullable=False)
    batch_id = Column(String(128), nullable=False)
    soft_deleted = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
```

`db.py` mirrors credits but names the base/session for creations. `get_creation_session()` is an async generator suitable for FastAPI `Depends` and `creation_session()` is an async context manager suitable for services.

- [ ] **Step 4: Implement the independent Alembic chain**

Copy the proven credits migration machinery structurally, then rename every namespace:

```python
_LOCK_NAMESPACE = 'open-webui-creations-migrations'
# SQLite suffix: .creation-migrations.lock
# metadata: CreationBase.metadata
# config attribute: creation_schema
# version table: ext_creation_schema_version
# public runner: run_creation_migrations
```

Revision `0001_create_creation_media_item` must create exactly the columns, constraints, and indexes in Step 3 and drop them in reverse order. Do not import the ORM model from the revision; define the SQL schema explicitly.

- [ ] **Step 5: Run migration tests and verify GREEN**

Run the Step 2 command again. Expected: all migration tests pass on SQLite; PostgreSQL lock tests use mocks and pass without a live PostgreSQL server.

- [ ] **Step 6: Checkpoint without committing**

Run `python -m compileall "backend/open_webui/extensions/creations"` and `git diff --check -- backend/open_webui/extensions/creations`. Do not commit without explicit user authorization.

---

### Task 3: Capture immutable reference snapshots and finalize creation batches idempotently

**Files:**
- Create: `backend/open_webui/extensions/creations/metrics.py`
- Create: `backend/open_webui/extensions/creations/capture.py`
- Create: `backend/open_webui/extensions/creations/tests/test_capture.py`
- Modify: `backend/open_webui/utils/images/fal_models.py`

**Interfaces:**
- Consumes: Task 1 capture dataclasses, Task 2 ORM/session, upstream `File`, `upload_file_handler`, `PreparedImageCall`, and FAL public-ID mapping.
- Produces:
  - `decode_prepared_references(prepared) -> tuple[PreparedReference, ...]`
  - `capture_reference_snapshots(request, references, user) -> tuple[CapturedReferenceResult, ...]`
  - `build_creation_capture_context(raw_form, prepared, user, usage_id) -> CreationCaptureContext`
  - `finalize_created_images(session, context, batch) -> None`

- [ ] **Step 1: Write capture tests before implementation**

Cover ordered snapshot upload, model-ID privacy, parameter allowlisting, owner checks, all-or-nothing identity, duplicate idempotency, and no restoration of soft-deleted rows. The core tests must include:

```python
@pytest.mark.asyncio
async def test_reference_capture_uses_normalized_provider_data_without_refetch(monkeypatch) -> None:
    uploaded: list[tuple[str, bytes, str]] = []
    png_bytes = b'\x89PNG\r\n\x1a\n' + b'png-test'
    jpeg_bytes = b'\xff\xd8\xff' + b'jpeg-test'
    png_data_url = f'data:image/png;base64,{base64.b64encode(png_bytes).decode("ascii")}'
    jpeg_data_url = f'data:image/jpeg;base64,{base64.b64encode(jpeg_bytes).decode("ascii")}'

    async def upload(_request, file, metadata, process, user):
        payload = file.file.read()
        uploaded.append((file.filename, payload, file.content_type))
        return SimpleNamespace(id=f'ref-{len(uploaded)}', user_id=user.id, created_at=10 + len(uploaded))

    monkeypatch.setattr(capture, 'upload_file_handler', upload)
    prepared_references = capture.decode_prepared_references(
        SimpleNamespace(
            provider_input=SimpleNamespace(image=(png_data_url, jpeg_data_url)),
            billing=SimpleNamespace(
                reference_hashes=(sha256(png_bytes).hexdigest(), sha256(jpeg_bytes).hexdigest())
            ),
        )
    )
    references = await capture.capture_reference_snapshots(
        request=object(),
        references=prepared_references,
        user=SimpleNamespace(id='user-1'),
    )
    assert [item.position for item in references] == [0, 1]
    assert [item.file_id for item in references] == ['ref-1', 'ref-2']
    assert uploaded[0][1].startswith(b'\x89PNG\r\n\x1a\n')


@pytest.mark.asyncio
async def test_finalize_replay_preserves_caption_and_soft_delete(creation_session, seeded_files) -> None:
    context = make_context(batch_id='usage-1')
    batch = make_batch(result_file_id='result-1', reference_ids=('ref-1',))
    await finalize_created_images(creation_session, context, batch)
    await creation_session.execute(
        update(CreationMediaItem)
        .where(CreationMediaItem.file_id == 'result-1')
        .values(caption='keep', soft_deleted=True)
    )
    await finalize_created_images(creation_session, context, batch)
    item = (await creation_session.execute(select(CreationMediaItem))).scalar_one()
    assert item.caption == 'keep'
    assert item.soft_deleted is True


@pytest.mark.asyncio
async def test_finalize_rejects_file_owner_mismatch(creation_session, seeded_files) -> None:
    with pytest.raises(RuntimeError, match='creation file ownership mismatch'):
        await finalize_created_images(
            creation_session,
            make_context(user_id='user-1'),
            make_batch(result_user_id='user-2'),
        )
```

Add cases for mixed captured/reused batches, a real batch without a file identity, duplicate reference IDs, mismatched reference hash/order, immutable identity conflict, public FAL model mapping, and unknown fields omitted from `params_json`.

- [ ] **Step 2: Run capture tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests/test_capture.py" -q
```

Expected: import failure for `capture.py` and its public functions.

- [ ] **Step 3: Implement normalized reference decoding and snapshot capture**

`decode_prepared_references(prepared)` accepts only normalized `data:image/png|jpeg|webp;base64,...` values from `PreparedImageCall.provider_input.image`. Decode with `base64.b64decode(..., validate=True)`, verify MIME/magic bytes and existing byte/count limits, compute SHA-256, and compare each digest to the same-position `prepared.billing.reference_hashes`; fail closed on a length, order, or digest mismatch. Return frozen `PreparedReference(payload, mime_type, sha256, position)` values held in memory only. Then `capture_reference_snapshots()` uploads each prepared reference once in input order with metadata exactly as follows:

```python
metadata = {'creation_reference': True}
file = UploadFile(
    file=io.BytesIO(payload),
    filename=f'creation-reference-{reference.position}{extension}',
    headers={'content-type': mime_type},
)
file_item = await upload_file_handler(
    request,
    file=file,
    metadata=metadata,
    process=False,
    user=user,
)
```

Do not pass chat/message metadata, prompt, original URL, hash, or provider payload. If any upload fails, propagate the failure and leave already written files as documented orphan files.

- [ ] **Step 4: Implement context normalization and public model identity**

Use the exact request-parameter whitelist from the spec. Normalize `n` to `image_count`; trim blank negative prompt to `None`. Resolve FAL IDs as:

```python
internal_model = normalize_fal_image_model_id(prepared.billing.resource_id)
public_model_id = (
    public_fal_image_model_id(internal_model)
    if internal_model is not None
    else prepared.billing.resource_id
)
```

Never fall back from a recognized internal FAL ID to the internal string. Derive `source` from `prepared.billing.channel`, `task` from `prepared.billing.action`, and `batch_id` only from `usage_id`.

- [ ] **Step 5: Implement idempotent batch finalization**

For `ReusedImageResult`-only batches, return without writing. Reject mixed reused/captured batches. For every captured result, verify both the captured owner values and actual upstream File rows for result/reference IDs. Load the whole existing row by `file_id` before insert; when two workers race, catch `IntegrityError` around `session.begin_nested()`, then re-read after the savepoint rollback. On a unique collision, compare every immutable identity field, including ordered references; do not alter `caption`, `soft_deleted`, or `updated_at` on an idempotent replay. Because all N rows share the caller’s outer transaction, any mismatch or later failure rolls the entire batch back.

Metrics may expose only `task` and `source` labels:

```python
creation_metrics.capture_succeeded(task=context.task, source=context.source, count=len(batch.images))
creation_metrics.capture_failed(task=context.task, source=context.source)
creation_metrics.reference_capture_failed(task=context.task, source=context.source)
creation_metrics.missing_file(task=item.task, source=item.source)
```

- [ ] **Step 6: Run capture tests and verify GREEN**

Run the Step 2 command again. Expected: all capture tests pass.

- [ ] **Step 7: Checkpoint without committing**

Run `python -m compileall` on `capture.py`, `schemas.py`, and `fal_models.py`, followed by `git diff --check` on those paths. Do not commit without explicit authorization.

---

### Task 4: Implement owner-scoped and administrator read-only creation APIs

**Files:**
- Create: `backend/open_webui/extensions/creations/service.py`
- Create: `backend/open_webui/extensions/creations/router.py`
- Create: `backend/open_webui/extensions/creations/tests/test_service.py`
- Create: `backend/open_webui/extensions/creations/tests/test_router.py`
- Modify: `backend/open_webui/models/users.py` — add the narrow `get_users_by_ids()` helper only if it is still absent at implementation time.

**Interfaces:**
- Consumes: Task 1 DTO/cursor contracts and Task 2 model/session.
- Produces:
  - `GET /api/v1/creations/media`
  - `GET /api/v1/creations/media/{id}`
  - `PATCH /api/v1/creations/media/{id}`
  - `DELETE /api/v1/creations/media/{id}`
  - `GET /api/v1/creations/admin/media`
  - `GET /api/v1/creations/admin/media/{id}`

- [ ] **Step 1: Write service and router authorization tests first**

Use an async SQLite fixture that creates `CreationBase.metadata`, `User.__table__`, and `File.__table__`. Required behavioral tests:

```python
def test_personal_list_never_returns_another_users_creation(client, user_override) -> None:
    user_override(id='user-1', role='user')
    response = client.get('/api/v1/creations/media')
    assert response.status_code == 200
    assert [item['id'] for item in response.json()['items']] == ['creation-user-1']


def test_non_admin_cannot_upgrade_to_global_scope(client, user_override) -> None:
    user_override(id='user-1', role='user')
    assert client.get('/api/v1/creations/admin/media').status_code == 401
    response = client.get('/api/v1/creations/media?scope=all')
    assert response.status_code == 422


def test_admin_global_list_is_read_only_and_includes_deleted_owner(client, admin_override) -> None:
    admin_override(id='admin-1')
    response = client.get('/api/v1/creations/admin/media')
    assert response.status_code == 200
    owners = {item['id']: item['owner'] for item in response.json()['items']}
    assert owners['orphaned-creation']['deleted'] is True
    assert client.patch(
        '/api/v1/creations/media/user-creation',
        json={'caption': 'admin overwrite'},
    ).status_code == 404
    assert client.delete('/api/v1/creations/media/user-creation').status_code == 404


def test_same_second_cursor_has_no_duplicates(client, user_override) -> None:
    user_override(id='user-1', role='user')
    first = client.get('/api/v1/creations/media?limit=2').json()
    second = client.get(
        '/api/v1/creations/media',
        params={'limit': 2, 'cursor': first['next_cursor']},
    ).json()
    ids = [item['id'] for item in first['items'] + second['items']]
    assert len(ids) == len(set(ids))
```

Also test: malformed cursor 422; limit 0/101; list summary excludes prompt/params/references/batch/file IDs; detail includes ordered references; missing and owner-mismatched files produce null URLs; caption normalization; extra PATCH fields rejected; owner DELETE returns 204 repeatedly; another user gets 404; admin global list excludes soft-deleted rows; owner and file lookups are batched once per page.

- [ ] **Step 2: Run API tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests/test_service.py" "backend/open_webui/extensions/creations/tests/test_router.py" -q
```

Expected: import failures for service/router functions.

- [ ] **Step 3: Implement stable owner-scoped queries and DTO assembly**

Personal list SQL must include:

```python
select(CreationMediaItem).where(
    CreationMediaItem.user_id == current_user_id,
    CreationMediaItem.soft_deleted.is_(False),
)
```

Admin list SQL includes only `soft_deleted.is_(False)`. Apply cursor as:

```python
or_(
    CreationMediaItem.created_at < cursor_created_at,
    and_(
        CreationMediaItem.created_at == cursor_created_at,
        CreationMediaItem.id < cursor_id,
    ),
)
```

Fetch `limit + 1`, return at most `limit`, and derive `next_cursor` from the last returned row only when an extra row exists. Batch query all result/reference `File` rows needed for the response and all admin owner `User` rows needed for the current page. Require `file.user_id == creation.user_id` before emitting `/api/v1/files/{id}/content`.

If the current upstream `Users` table API lacks a by-ID batch method, add the following narrow read helper rather than calling `get_user_by_id()` in a loop:

```python
async def get_users_by_ids(
    self,
    ids: list[str],
    db: AsyncSession | None = None,
) -> list[UserModel]:
    if not ids:
        return []
    async with get_async_db_context(db) as session:
        rows = (await session.execute(select(User).where(User.id.in_(ids)))).scalars().all()
        return [UserModel.model_validate(row) for row in rows]
```

Add a focused test in `backend/open_webui/extensions/creations/tests/test_service.py` that counts one user query for an admin page with multiple owners.

- [ ] **Step 4: Implement separate personal/admin routers**

Use explicit dependencies and no client-upgradable scope:

```python
router = APIRouter(prefix='/api/v1/creations', tags=['creations'])

@router.get('/media', response_model=CreationListResponse)
async def list_media(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_verified_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return await list_personal_creations(session, user.id, limit, cursor)

@router.get('/admin/media', response_model=AdminCreationListResponse)
async def list_admin_media(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    user=Depends(get_admin_user),
    session: AsyncSession = Depends(get_creation_session),
):
    return await list_admin_creations(session, limit, cursor)
```

Personal detail/PATCH/DELETE queries always include current `user_id`. Admin has GET routes only. Translate invalid cursors to a 422 response without exposing decoder exception text.

- [ ] **Step 5: Run API tests and verify GREEN**

Run the Step 2 command again. Expected: all service/router tests pass.

- [ ] **Step 6: Checkpoint without committing**

Run compileall and `git diff --check` for `extensions/creations`. Do not commit without explicit authorization.

---

### Task 5: Add mandatory authorization scope and a shared terminal transaction to image billing

**Files:**
- Modify: `backend/open_webui/extensions/credits/service.py`
- Modify: `backend/open_webui/extensions/credits/image_billing.py`
- Modify: `backend/open_webui/extensions/credits/tests/test_usage_service.py`
- Modify: `backend/open_webui/extensions/credits/tests/test_image_billing.py`

**Interfaces:**
- Consumes: Task 1 `AuthorizationScope`; finalizer remains opaque to credits and does not require credits to import creations.
- Produces:

```python
async def mark_usage_succeeded_in_session(
    session: AsyncSession,
    usage_id: str,
    urls: Sequence[str],
) -> int

async def bill_image_call(
    *,
    request: object,
    raw_form_data: object,
    metadata: dict | None,
    raw_user: object | None,
    action: Action,
    authorization_scope: Literal['direct', 'chat', 'tool'],
    invoke: Callable[[PreparedImageCall, object], Awaitable[object]],
    finalize: Callable[[object, PreparedImageCall, object, str], Awaitable[None]],
) -> list[dict[str, str]]
```

- [ ] **Step 1: Update tests first for the new mandatory contract**

Change the signature assertion so `authorization_scope` and `finalize` have no defaults. Add tests for valid/invalid scope-channel pairs, direct bypass, chat/tool gates, transaction call order, rollback, and replay:

```python
@pytest.mark.asyncio
async def test_terminal_finalize_and_success_share_one_transaction(billing_module, monkeypatch) -> None:
    session = TransactionSession()
    monkeypatch.setattr(billing_module, 'credit_session', lambda: fake_credit_session_for(session))
    monkeypatch.setattr(
        billing_module,
        'begin_image_usage',
        AsyncMock(return_value=SimpleNamespace(usage=usage(), outcome='new')),
    )
    finalize = AsyncMock()
    invoke = AsyncMock(
        return_value=SimpleNamespace(images=(SimpleNamespace(url='/api/v1/files/r/content'),))
    )
    result = await bill_image_call(
        request=Request(headers={}),
        raw_form_data=object(),
        metadata=None,
        raw_user=object(),
        action='text-to-image',
        authorization_scope='direct',
        invoke=invoke,
        finalize=finalize,
    )
    assert result == [{'url': '/api/v1/files/r/content'}]
    invoke.assert_awaited_once_with(ANY, ANY)
    finalize.assert_awaited_once_with(session, ANY, ANY, 'usage-1')
    billing_module.mark_usage_succeeded_in_session.assert_awaited_once_with(
        session,
        'usage-1',
        ['/api/v1/files/r/content'],
    )
    assert session.commits == 1


@pytest.mark.asyncio
async def test_finalize_failure_leaves_usage_invoking_and_never_marks_provider_failed(billing_module, monkeypatch) -> None:
    billing_module.mark_usage_failed.reset_mock()
    with pytest.raises(CreditError) as raised:
        await call_bill(finalize=AsyncMock(side_effect=RuntimeError('db failed')))
    assert raised.value.code == 'credit_service_unavailable'
    billing_module.mark_usage_failed.assert_not_awaited()
    billing_module.mark_usage_succeeded_in_session.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('scope', 'channel'),
    [('direct', 'web'), ('direct', 'api'), ('chat', 'chat'), ('tool', 'tool')],
)
async def test_scope_channel_matrix_accepts_only_trusted_pairs(scope, channel) -> None:
    assert validate_authorization_scope(scope, channel) is None
```

- [ ] **Step 2: Run billing tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/credits/tests/test_usage_service.py" "backend/open_webui/extensions/credits/tests/test_image_billing.py" -q
```

Expected: failures because required parameters and the in-session transition do not exist.

- [ ] **Step 3: Split the succeeded transition into in-session and wrapper forms**

Implement `mark_usage_succeeded_in_session()` without opening or committing a transaction. Keep existing `mark_usage_succeeded()` as a compatibility wrapper:

```python
async def mark_usage_succeeded_in_session(
    session: AsyncSession,
    usage_id: str,
    urls: Sequence[str],
) -> int:
    safe_urls = _safe_result_urls(urls)
    result = await session.execute(
        update(CreditUsage)
        .where(CreditUsage.id == usage_id, CreditUsage.status == 'invoking')
        .values(
            status='succeeded',
            result_snapshot={'urls': safe_urls},
            completed_at=_now(),
            updated_at=_now(),
        )
    )
    return result.rowcount


async def mark_usage_succeeded(usage_id: str, urls: Sequence[str]) -> int:
    async with credit_session() as session, session.begin():
        changed = await mark_usage_succeeded_in_session(session, usage_id, urls)
    if changed == 1:
        credit_metrics.usage_status(status='succeeded')
    return changed
```

- [ ] **Step 4: Implement fail-closed scope authorization**

`_authorize_image_call()` always checks user existence and role consistency. For `direct`, skip runtime image switches and user feature permission. For `chat` and `tool`, enforce the existing switch and `features.image_generation`. After `_prepare_image_call`, validate the prepared billing channel against:

```python
_ALLOWED_SCOPE_CHANNELS = {
    'direct': frozenset({'web', 'api'}),
    'chat': frozenset({'chat'}),
    'tool': frozenset({'tool'}),
}
```

Reject any mismatch with sanitized `credit_service_unavailable/invalid_authorization_scope` before precharge or provider invocation.

- [ ] **Step 5: Implement opaque result URL extraction and terminal transaction**

`_result_urls()` must accept either the existing sequence of mappings used by tests/replay compatibility or an object with an `.images` sequence whose items expose `.url`. Do not import creations types. After `_to_provider_form()`, call `result = await invoke(prepared, provider_form)` so the edit bridge sees the immutable prepared references while provider functions still receive their converted Pydantic form. The `images.py` edit bridge decodes/hash-checks and uploads reference snapshots immediately after all result uploads succeed. After provider success and URL validation:

```python
try:
    async with credit_session() as session, session.begin():
        await finalize(session, prepared, result, begin.usage.id)
        changed = await mark_usage_succeeded_in_session(session, begin.usage.id, urls)
        if changed != 1:
            raise _unavailable(begin.usage.id, reason='success_status_not_updated')
except CreditError:
    raise
except Exception:
    raise _unavailable(begin.usage.id, reason='terminal_finalize_failed') from None
credit_metrics.usage_status(status='succeeded')
return [{'url': url} for url in urls]
```

Keep provider exceptions in the existing failed transition. Do not call the failed transition for finalizer/terminal-transaction errors. Replayed succeeded usage returns stored URLs without invoking provider or finalizer.

- [ ] **Step 6: Run billing tests and verify GREEN**

Run the Step 2 command again. Expected: all targeted credits tests pass.

- [ ] **Step 7: Checkpoint without committing**

Run compileall and `git diff --check` on the four modified credits files. Do not commit without explicit authorization.

---

### Task 6: Bridge every image entry point to captured batches and creation finalization

**Files:**
- Modify: `backend/open_webui/routers/images.py`
- Modify: `backend/open_webui/tools/builtin.py`
- Modify: `backend/open_webui/utils/middleware.py`
- Modify: `backend/open_webui/extensions/credits/tests/test_image_billing.py`
- Create: `backend/open_webui/extensions/creations/tests/test_image_entrypoints.py`

**Interfaces:**
- Consumes: Tasks 1, 3, and 5.
- Produces: required `authorization_scope` on `image_generations()` / `image_edits()`, internal `CapturedImageBatch` results, reference snapshots for real edits, and an `images.py` finalizer closure.

- [ ] **Step 1: Write entry-point and captured-result tests first**

Update signature tests to require:

```python
async def image_generations(request, form_data, authorization_scope, metadata=None, user=None)
async def image_edits(request, form_data, authorization_scope, metadata=None, user=None)
```

Add a call matrix test asserting direct wrappers pass `direct`, middleware passes `chat`, builtin tools pass `tool`, and omitting scope is a Python `TypeError`. Add provider-boundary tests that patch `upload_image` and assert real provider branches return `CapturedImageBatch`, while the existing FAL mock returns only `ReusedImageResult` values and never snapshots references.

- [ ] **Step 2: Run entry-point tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/credits/tests/test_image_billing.py" "backend/open_webui/extensions/creations/tests/test_image_entrypoints.py" -q
```

Expected: signature/call assertions fail because scope and captured batches are not wired.

- [ ] **Step 3: Remove only the direct-wrapper image switch gates**

In `generate_images()` and `edit_images()`, remove the global switch and `has_permission` blocks, retain `get_verified_user`, and call the internal function with `authorization_scope='direct'`. Do not remove gating code from chat middleware or builtin tool functions.

- [ ] **Step 4: Return stable captured values from real provider branches**

Keep `upload_image()` returning `(file_item, url)` to minimize upstream churn. At every real result upload, project immediately:

```python
file_item, url = await upload_image(request, image_data, content_type, provider_metadata, user)
images.append(
    CapturedImageResult(
        url=str(url),
        file_id=file_item.id,
        file_user_id=file_item.user_id,
        file_created_at=file_item.created_at,
        mime_type=content_type,
    )
)
```

Return `CapturedImageBatch(images=tuple(images))` from generation provider branches. In the image-edit invoke closure, first await `_invoke_image_edits(...)`; if it is a reused-only FAL mock batch, return it unchanged. Otherwise decode and hash-check `prepared.provider_input.image` against `prepared.billing.reference_hashes`, upload one ordered reference set after all result uploads succeed, and return `CapturedImageBatch(images=internal_result.images, references=references)`. This timing satisfies the spec: reference file failure happens before the terminal DB transaction, so usage remains `invoking`. For the FAL mock, wrap URLs in `ReusedImageResult` and never upload references.

- [ ] **Step 5: Build and pass the mandatory creation finalizer**

Define a narrow closure in `images.py` that captures only the validated raw form, request, and authenticated user:

```python
async def invoke_edit_creations(prepared, provider_form):
    internal_result = await _invoke_image_edits(request, provider_form, metadata, user)
    if all(isinstance(item, ReusedImageResult) for item in internal_result.images):
        return internal_result
    references = await capture_reference_snapshots(
        request,
        decode_prepared_references(prepared),
        user,
    )
    return CapturedImageBatch(images=tuple(internal_result.images), references=references)


async def finalize_image_creations(session, prepared, internal_result, usage_id):
    context = build_creation_capture_context(
        raw_form_data=form_data,
        prepared=prepared,
        user=user,
        usage_id=usage_id,
    )
    await finalize_created_images(session, context, internal_result)
```

Pass `invoke=lambda _prepared, provider_form: _invoke_image_generations(...)` for generation and `invoke=invoke_edit_creations` for edit, plus the mandatory finalizer. Credits remains unaware of creations internals. External return values stay `[{"url": "..."}]` after billing projects the internal batch.

- [ ] **Step 6: Wire trusted scope at all call sites**

Use these exact values:

```python
# HTTP wrappers
authorization_scope='direct'

# backend/open_webui/utils/middleware.py
 authorization_scope='chat'

# backend/open_webui/tools/builtin.py
 authorization_scope='tool'
```

Do not infer scope from `Origin`, `Referer`, body, headers, or `metadata['credit_channel']`. Metadata continues to determine the billing channel only; billing validates it against the server-supplied scope.

- [ ] **Step 7: Run entry-point tests and verify GREEN**

Run the Step 2 command again. Expected: all entry-point and billing integration tests pass.

- [ ] **Step 8: Checkpoint without committing**

Run compileall on all modified Python paths and `git diff --check`. Do not commit without explicit authorization.

---

### Task 7: Register and validate the creations extension at application startup

**Files:**
- Create: `backend/open_webui/extensions/creations/registration.py`
- Create: `backend/open_webui/extensions/creations/tests/test_registration.py`
- Modify: `backend/open_webui/main.py`

**Interfaces:**
- Produces: `initialize_creations_extension(app) -> None`; no shutdown function.
- Consumes: Task 2 migration runner/model and Task 4 router.

- [ ] **Step 1: Write startup tests first**

```python
@pytest.mark.asyncio
async def test_initialization_runs_migration_then_schema_validation(monkeypatch) -> None:
    calls: list[str] = []

    async def run_sync(function):
        calls.append(function.__name__)
        function()

    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', run_sync)
    monkeypatch.setattr(registration, 'run_creation_migrations', lambda: calls.append('migrated'))
    monkeypatch.setattr(registration, '_validate_creation_schema', lambda: calls.append('validated'))
    await registration.initialize_creations_extension(SimpleNamespace(state=SimpleNamespace()))
    assert calls == [
        'run_creation_migrations',
        'migrated',
        '_validate_creation_schema',
        'validated',
    ]


@pytest.mark.asyncio
async def test_initialization_failure_propagates(monkeypatch) -> None:
    async def fail(_function):
        raise RuntimeError('creation migration failed')
    monkeypatch.setattr(registration.anyio.to_thread, 'run_sync', fail)
    with pytest.raises(RuntimeError, match='creation migration failed'):
        await registration.initialize_creations_extension(SimpleNamespace(state=SimpleNamespace()))
```

Add a source-level assertion that `main.py` initializes creations before `startup_complete=True`, includes the router once, and has no creation shutdown hook.

- [ ] **Step 2: Run startup tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests/test_registration.py" -q
```

Expected: missing registration initializer and main wiring.

- [ ] **Step 3: Implement schema validation**

Validate:

- `ext_creation_media_item` exists.
- migration head equals `ext_creation_schema_version` head.
- named unique/check/index objects from Task 2 exist.
- no user/file FK is introduced.

Run migration and validation via `anyio.to_thread.run_sync`. Do not create a background worker or shutdown hook.

- [ ] **Step 4: Add the thin `main.py` wiring**

Import `initialize_creations_extension` and `creations_router`, call the initializer immediately after the credits initializer and before `app.state.startup_complete = True`, and add `app.include_router(creations_router)` next to `credits_router`.

- [ ] **Step 5: Run startup tests and verify GREEN**

Run the Step 2 command again. Expected: all registration tests pass.

- [ ] **Step 6: Checkpoint without committing**

Run compileall on registration/main and `git diff --check`. Do not commit without explicit authorization.

---

### Task 8: Add typed frontend creation APIs and scope-state helpers

**Files:**
- Create: `src/lib/apis/creations/index.ts`
- Create: `src/lib/apis/creations/index.test.ts`
- Create: `src/lib/utils/creations-library.ts`
- Create: `src/lib/utils/creations-library.test.ts`

**Interfaces:**
- Produces: `listCreations`, `getCreation`, `updateCreation`, `deleteCreation`, `listAdminCreations`, `getAdminCreation`, `CreationScope`, `CreationSummary`, `CreationDetail`, and pure page/optimistic helpers.
- Consumes: `WEBUI_API_BASE_URL` and existing bearer-token fetch style.

- [ ] **Step 1: Write API and pure-state tests first**

Mock `global.fetch` and assert exact routes, cursor encoding through `URLSearchParams`, bearer header, PATCH body, DELETE 204 handling, and non-OK JSON errors. Pure helpers must cover duplicate-free merge, independent `mine/all` states, stale request rejection, optimistic removal, and positional rollback:

```typescript
import { describe, expect, test } from 'vitest';
import {
	applyCreationPage,
	beginCreationRequest,
	createCreationScopeState,
	removeCreationOptimistically,
	restoreCreation
} from './creations-library';

describe('creations library state', () => {
	test('keeps mine and all scope cursors independent', () => {
		const mine = createCreationScopeState();
		const all = createCreationScopeState();
		expect(mine).not.toBe(all);
		expect(mine.nextCursor).toBeNull();
		expect(all.nextCursor).toBeNull();
	});

	test('ignores a response from an older request generation', () => {
		const state = createCreationScopeState();
		const first = beginCreationRequest(state);
		const second = beginCreationRequest(state);
		expect(applyCreationPage(state, first, { items: [], next_cursor: null }, true)).toBe(false);
		expect(applyCreationPage(state, second, { items: [], next_cursor: null }, true)).toBe(true);
	});

	test('restores an optimistically removed card at its original index', () => {
		const state = createCreationScopeState([{ id: 'a' }, { id: 'b' }, { id: 'c' }]);
		const removed = removeCreationOptimistically(state, 'b');
		restoreCreation(state, removed);
		expect(state.items.map((item) => item.id)).toEqual(['a', 'b', 'c']);
	});
});
```

- [ ] **Step 2: Run frontend unit tests and verify RED**

Run:

```powershell
npx vitest run "src/lib/apis/creations/index.test.ts" "src/lib/utils/creations-library.test.ts"
```

Expected: module-not-found failures.

- [ ] **Step 3: Implement typed API wrappers**

Use these exported functions:

```typescript
export const listCreations = (token = '', limit = 20, cursor: string | null = null) =>
	requestCreationList('/creations/media', token, limit, cursor);
export const listAdminCreations = (token = '', limit = 20, cursor: string | null = null) =>
	requestCreationList('/creations/admin/media', token, limit, cursor);
export const getCreation = (token: string, id: string) =>
	requestCreationDetail(`/creations/media/${encodeURIComponent(id)}`, token);
export const getAdminCreation = (token: string, id: string) =>
	requestCreationDetail(`/creations/admin/media/${encodeURIComponent(id)}`, token);
export const updateCreation = (token: string, id: string, caption: string | null) =>
	requestJson(`/creations/media/${encodeURIComponent(id)}`, token, {
		method: 'PATCH',
		body: JSON.stringify({ caption })
	});
export const deleteCreation = (token: string, id: string) =>
	requestNoContent(`/creations/media/${encodeURIComponent(id)}`, token, { method: 'DELETE' });
```

Types mirror backend snake_case JSON exactly; do not expose a `file_id` field.

- [ ] **Step 4: Implement pure scope helpers**

`CreationScope = 'mine' | 'all'`. State includes `items`, `nextCursor`, `loaded`, `loading`, `error`, `requestGeneration`, and `stale`. Page merge deduplicates by ID and preserves server order. Optimistic removal returns `{item, index}` for exact rollback.

- [ ] **Step 5: Run frontend unit tests and verify GREEN**

Run the Step 2 command again. Expected: all API/state tests pass.

- [ ] **Step 6: Checkpoint without committing**

Run Prettier check without writing:

```powershell
npx prettier --check "src/lib/apis/creations/**/*.{ts,svelte}" "src/lib/utils/creations-library*.ts"
```

Do not commit without explicit authorization.

---

### Task 9: Make `/images` universally visible and add persistent accessible views

**Files:**
- Modify: `src/lib/components/layout/Sidebar.svelte`
- Modify: `src/lib/components/layout/Sidebar/UserMenu.svelte`
- Modify: `src/lib/components/images/Images.svelte`
- Modify: `src/lib/components/images/Images.test.ts`

**Interfaces:**
- Produces: `view: 'generate' | 'library'`, persistent generated state, a temporary accessible library placeholder panel, hidden composer in library mode, and `libraryRevision`.
- Consumes: existing image-page state only; Task 10 replaces the placeholder with the real library component.

- [ ] **Step 1: Extend source-contract tests first**

Add assertions that:

```typescript
test('uses accessible generate and library tabs without unmounting page state', () => {
	expect(source).toContain("let view: 'generate' | 'library' = 'generate';");
	expect(source).toContain('role="tablist"');
	expect(source).toContain('role="tab"');
	expect(source).toContain('aria-selected={view ===');
	expect(source).toContain('on:keydown={handleTabKeydown}');
	expect(source).toContain('id="images-library-panel"');
	expect(source).toContain('hidden={view !== \'library\'}');
	expect(source).not.toContain('{#if canUseImages}');
});

test('increments library revision after a successful generation', () => {
	const success = source.slice(source.indexOf('generatedImages = ['), source.indexOf('} catch', source.indexOf('generatedImages = [')));
	expect(success).toContain('libraryRevision += 1;');
});
```

Add targeted source tests for Sidebar/UserMenu showing `/images` without `enable_image_generation` or feature-permission conditions.

- [ ] **Step 2: Run Images tests and verify RED**

Run:

```powershell
npx vitest run "src/lib/components/images/Images.test.ts"
```

Expected: new tab/gate/revision assertions fail.

- [ ] **Step 3: Remove navigation and page-level generation gates**

In Sidebar, `case 'images'` returns true for the already verified app user. In UserMenu, remove only the feature-switch wrapper around the existing `/images` item. In `Images.svelte`, remove `canUseImagesPage` import/reactive state and the unavailable-page branch; backend direct endpoints remain the authorization boundary.

- [ ] **Step 4: Add accessible persistent tabs**

Use semantic IDs and keyboard handling:

```typescript
let view: 'generate' | 'library' = 'generate';
let libraryRevision = 0;

const selectView = async (next: 'generate' | 'library') => {
	view = next;
	await tick();
	document.getElementById(`images-${next}-tab`)?.focus();
};

const handleTabKeydown = (event: KeyboardEvent) => {
	if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
		event.preventDefault();
		selectView(view === 'generate' ? 'library' : 'generate');
	}
};
```

Render the generation panel for the `Images.svelte` lifetime and hide it with `hidden`/CSS rather than moving generation state into a child that gets destroyed. Add an accessible `images-library-panel` placeholder in this task; Task 10 replaces only its body with `CreationsLibrary`. Hide the sticky composer whenever `view === 'library'`. Keep the mobile sidebar button and ensure tab targets are at least 44 px high.

- [ ] **Step 5: Wire revision only after nonempty successful results**

Immediately after prepending generated images, increment `libraryRevision`. Do not POST a creation from the frontend. The value remains local until Task 10 passes it to the real library component.

- [ ] **Step 6: Run Images tests and verify GREEN**

Run the Step 2 command again. Expected: all existing and new Images tests pass.

- [ ] **Step 7: Checkpoint without committing**

Run Prettier check on the three Svelte files and `git diff --check`. Do not commit without explicit authorization.

---

### Task 10: Build the responsive library grid and owner/admin detail modal

**Files:**
- Create: `src/lib/components/images/CreationsLibrary.svelte`
- Create: `src/lib/components/images/CreationsLibrary.test.ts`
- Create: `src/lib/components/images/CreationDetailsModal.svelte`
- Create: `src/lib/components/images/CreationDetailsModal.test.ts`
- Modify: `src/lib/components/images/Images.svelte`

**Interfaces:**
- `CreationsLibrary` props: `active: boolean`, `revision: number`, `onCreate: () => void`.
- `CreationDetailsModal` props: `show`, `creationId`, `scope`, `canManage`, `onUpdated`, and `onRemoved`.
- Consumes: Task 8 API/types/state helpers and existing `Loader`, `Modal`, `ImagePreview`, `Spinner`, and toast utilities.

- [ ] **Step 1: Write component source-contract tests first**

Following the existing `Images.test.ts` style, assert lazy images, non-hover details, admin scope, accessibility, missing placeholders, and owner-only controls:

```typescript
const source = readFileSync(fileURLToPath(new URL('./CreationsLibrary.svelte', import.meta.url)), 'utf-8');

test('lazy loads original images and exposes details on touch', () => {
	expect(source).toContain('loading="lazy"');
	expect(source).toContain('decoding="async"');
	expect(source).toContain("$i18n.t('Details')");
	expect(source).toContain('<Loader');
	expect(source).not.toContain('group-hover:opacity-100');
});

test('shows mine/all scope only to admins', () => {
	expect(source).toContain("$user?.role === 'admin'");
	expect(source).toContain("scope === 'mine'");
	expect(source).toContain("scope === 'all'");
	expect(source).toContain("$i18n.t('All creations')");
});
```

Modal tests assert ordered references, lazy loading, folded prompt/parameters, `canManage` around PATCH/DELETE controls, and a confirmation dialog before deletion.

- [ ] **Step 2: Run component tests and verify RED**

Run:

```powershell
npx vitest run "src/lib/components/images/CreationsLibrary.test.ts" "src/lib/components/images/CreationDetailsModal.test.ts"
```

Expected: component files do not exist.

- [ ] **Step 3: Implement independent mine/all scope loading**

Create one state object per scope and load only the active scope. On `revision` change, mark `mine` stale; if admin `all` has loaded, mark it stale too. Reload a stale active scope immediately and defer a hidden scope until activation. Use request generations from Task 8 to ignore late responses. Load next page only when `nextCursor` exists and the active scope is not loading.

- [ ] **Step 4: Implement responsive grid and states**

Use a balanced grid such as `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`, square cards, `object-cover`, and no fixed viewport-wide popup. Include:

- initial spinner;
- personal/admin empty copy;
- first-load retry;
- pagination retry that preserves cards;
- missing-file placeholder;
- always-visible Details button;
- admin owner name/email and deleted-owner fallback;
- result preview through existing `ImagePreview`.

The first request uses 20 items. Do not auto-fetch additional pages without `Loader on:visible` near the bottom.

- [ ] **Step 5: Implement lazy detail and owner-only mutation**

Cache details by `${scope}:${creationId}`. In `CreationDetailsModal`, display result, ordered reference images, owner information for admin scope, caption, folded prompt/negative prompt/parameters/model/source/batch, and missing reference placeholders. Only render caption save and remove controls when `canManage` is true. Before DELETE, show a confirmation whose copy states that chat images remain and restoration is unavailable.

On owner removal: remove optimistically at the original grid position, close the modal, call DELETE, and restore plus toast on failure. Never issue DELETE from admin-all scope.

- [ ] **Step 6: Integrate the real library into the persistent panel**

Replace Task 9’s placeholder body with:

```svelte
<CreationsLibrary
	active={view === 'library'}
	revision={libraryRevision}
	onCreate={() => selectView('generate')}
/>
```

Keep the panel and generation state mounted. Add/adjust `Images.test.ts` assertions for the component props and rerun it together with the component tests.

- [ ] **Step 7: Run component tests and verify GREEN**

Run:

```powershell
npx vitest run "src/lib/components/images/Images.test.ts" "src/lib/components/images/CreationsLibrary.test.ts" "src/lib/components/images/CreationDetailsModal.test.ts"
```

Expected: all parent and child component source-contract tests pass.

- [ ] **Step 8: Run all creation frontend tests**

Run:

```powershell
npx vitest run "src/lib/apis/creations/index.test.ts" "src/lib/utils/creations-library.test.ts" "src/lib/components/images/Images.test.ts" "src/lib/components/images/CreationsLibrary.test.ts" "src/lib/components/images/CreationDetailsModal.test.ts"
```

Expected: all listed test files pass.

- [ ] **Step 9: Checkpoint without committing**

Run Prettier check on all new/modified frontend files and `git diff --check`. Do not commit without explicit authorization.

---

### Task 11: Add localized copy, run full targeted verification, and test real desktop/mobile behavior

**Files:**
- Modify: `src/lib/i18n/locales/zh-CN/translation.json`
- Modify if a check exposes a target-file issue: files already listed in Tasks 1–10 only.

**Interfaces:**
- Consumes: the complete backend and frontend implementation.
- Produces: verified Simplified Chinese, fresh automated evidence, and real desktop/mobile/admin behavior evidence.

- [ ] **Step 1: Add exact Simplified Chinese translations**

Add every new key used by the components, including at least:

```json
{
	"New": "新建",
	"Library": "作品库",
	"My creations": "我的作品",
	"All creations": "全部作品",
	"Details": "详情",
	"Creation details": "作品详情",
	"Reference images": "参考图",
	"Reference image unavailable": "参考图不可用",
	"Source file unavailable": "源文件不可用",
	"Caption": "备注",
	"Save caption": "保存备注",
	"Remove from library": "从作品库移除",
	"Remove this creation from your library?": "要从作品库移除这个作品吗？",
	"This will not delete images in chats, but it cannot be restored to the library in this version.": "这不会删除聊天中的图片，但当前版本无法将它恢复到作品库。",
	"Newly generated images will appear here.": "新生成的图片会自动出现在这里。",
	"Creations recorded before this feature was enabled are not included.": "作品库仅记录此功能启用后生成的作品。",
	"Deleted user": "已删除用户",
	"Owner": "所属用户",
	"Retry": "重试",
	"Load more failed": "加载更多失败"
}
```

Do not run the write-mode i18n parser unless required; it may modify unrelated locales. Validate only referenced keys and JSON syntax.

- [ ] **Step 2: Run the complete targeted backend suite**

Run:

```powershell
$env:PYTHONPATH = 'backend'; $env:WEBUI_SECRET_KEY = 'test-secret-key-for-creations-tests'; python -m pytest "backend/open_webui/extensions/creations/tests" "backend/open_webui/extensions/credits/tests/test_image_billing.py" "backend/open_webui/extensions/credits/tests/test_usage_service.py" -q
```

Expected: all targeted tests pass with zero failures. If an unrelated existing test fails, record the exact test and prove whether the target files are involved before changing code.

- [ ] **Step 3: Run Python compile and formatting checks**

Run:

```powershell
python -m compileall "backend/open_webui/extensions/creations" "backend/open_webui/extensions/credits/image_billing.py" "backend/open_webui/extensions/credits/service.py" "backend/open_webui/routers/images.py" "backend/open_webui/tools/builtin.py" "backend/open_webui/utils/middleware.py" "backend/open_webui/main.py"
python -m ruff format --check "backend/open_webui/extensions/creations" "backend/open_webui/extensions/credits/image_billing.py" "backend/open_webui/extensions/credits/service.py" "backend/open_webui/routers/images.py" "backend/open_webui/tools/builtin.py" "backend/open_webui/utils/middleware.py" "backend/open_webui/main.py"
```

Expected: compileall succeeds and ruff reports no formatting changes required. If ruff is unavailable, report that explicitly and retain compileall plus `git diff --check` evidence.

- [ ] **Step 4: Run the complete targeted frontend suite and format check**

Run:

```powershell
npx vitest run "src/lib/apis/creations/index.test.ts" "src/lib/utils/creations-library.test.ts" "src/lib/components/images/Images.test.ts" "src/lib/components/images/CreationsLibrary.test.ts" "src/lib/components/images/CreationDetailsModal.test.ts" "src/lib/utils/image-generation.test.ts"
npx prettier --check "src/lib/apis/creations/**/*.{ts,svelte}" "src/lib/utils/creations-library*.ts" "src/lib/components/images/*.{ts,svelte}" "src/lib/components/layout/Sidebar.svelte" "src/lib/components/layout/Sidebar/UserMenu.svelte" "src/lib/i18n/locales/zh-CN/translation.json"
```

Expected: all targeted Vitest tests pass and Prettier reports all matched files formatted.

- [ ] **Step 5: Run type checking and distinguish pre-existing diagnostics**

Run:

```powershell
npm run check
```

Expected: no diagnostics in creation/image target files. If the command still fails on known pre-existing files, save the output and run:

```powershell
npx svelte-check --tsconfig ./tsconfig.json --output machine 2>&1 | Select-String -Pattern 'src/lib/apis/creations|src/lib/utils/creations-library|src/lib/components/images|src/lib/components/layout/Sidebar'
```

Expected: no target-file matches. Report the full check as failed due to the exact pre-existing diagnostics; do not call it a pass.

- [ ] **Step 6: Start the actual app using the repository’s verified flow**

Use the existing backend script rather than inventing a command. This checkout’s Vite proxy defaults to `http://localhost:9000`, while `backend/dev.sh` defaults to 8080; align them explicitly without editing either configuration:

```powershell
$env:PORT = '9000'; bash backend/dev.sh
```

Run it in the background. Start the frontend separately:

```powershell
npm run dev
```

Confirm the frontend and backend health endpoints respond before browser interaction. If an authenticated browser session is unavailable, ask the user to log in rather than requesting or embedding credentials.

- [ ] **Step 7: Verify desktop behavior in the browser**

At a desktop viewport around `1440×900`, verify with a normal verified user:

1. `/images` navigation is visible even when image feature switches/permissions are off.
2. `/images` defaults to 新建.
3. Switch to 作品库; the composer disappears and the first page loads once.
4. Switch back; prompt, reference images, model selection, and generated results remain.
5. Generate a real text-to-image result; it appears in the library after success and still exists after refresh.
6. Run image-to-image; detail shows ordered immutable reference snapshots.
7. Edit caption, then remove from library with confirmation; chat/file content remains accessible.
8. Missing result/reference files show placeholders rather than broken URLs.

Use browser network inspection to confirm list summaries omit prompt/params/references/file IDs and detail responses omit internal file IDs, data URLs, and hidden FAL IDs.

- [ ] **Step 8: Verify administrator behavior in the browser**

With an administrator account:

1. 作品库 shows 我的作品｜全部作品 and defaults to 我的作品.
2. 全部作品 shows multiple owners, including deleted-user fallback where seeded.
3. Opening another user’s detail reveals prompt/params/reference snapshots as specified.
4. No caption edit or remove control appears for another user.
5. Direct PATCH/DELETE attempts against another user’s personal route return 404.
6. A normal user request to `/api/v1/creations/admin/media` returns 401.

- [ ] **Step 9: Verify narrow mobile behavior and accessibility**

At a viewport around `390×844`, verify:

- tabs and admin scope controls wrap or scroll safely without horizontal page overflow;
- touch targets are at least about 44 px;
- grid, cards, modal, owner text, references, confirm dialog, and retry actions fit the viewport;
- sticky composer does not obscure content in 新建 and is absent in 作品库;
- Details/remove controls do not rely on hover;
- keyboard Left/Right changes the top-level tab, focus remains visible, ARIA relations are correct;
- light and dark themes remain legible.

- [ ] **Step 10: Perform main-agent review and final diff checks**

The current main agent—not a subagent—reviews the complete diff for correctness, authorization, privacy, upgrade conflicts, responsive UI, and unrelated changes. Then run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors and only files listed by this plan plus the approved spec/plan records. Do not commit or push unless the user explicitly asks after reviewing the verified result.
