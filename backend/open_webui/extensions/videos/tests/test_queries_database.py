from pathlib import Path

import pytest
import pytest_asyncio
from open_webui.extensions.creations.db import CreationBase
from open_webui.extensions.fal_catalog.video_schemas import FalVideoModelDefinition
from open_webui.extensions.videos import queries
from open_webui.extensions.videos.schemas import VideoTaskSubmitForm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def video_database(tmp_path: Path):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path / "videos.sqlite"}')
    async with engine.begin() as connection:
        await connection.run_sync(CreationBase.metadata.create_all)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield sessions
    finally:
        await engine.dispose()


def _submission(prompt: str = 'A paper boat') -> VideoTaskSubmitForm:
    return VideoTaskSubmitForm(
        task='text-to-video',
        model='model-a',
        prompt=prompt,
        assets=(),
        params={'duration': '5'},
    )


@pytest.fixture(autouse=True)
def _catalog(monkeypatch):
    definition = FalVideoModelDefinition(
        id='fal-ai/model-a',
        public_id='model-a',
        name='Model A',
        provider='fal',
        task='text-to-video',
    )
    monkeypatch.setattr(
        queries,
        'build_video_provider_payload',
        lambda submission: (
            definition,
            {'prompt': submission.prompt, 'duration': '5'},
            {'duration': '5'},
        ),
    )


@pytest.mark.asyncio
async def test_video_query_lifecycle_and_idempotent_replay(video_database) -> None:
    async with video_database() as session:
        created, is_new = await queries.create_video_task(
            session,
            user_id='user-1',
            idempotency_key='key-1',
            submission=_submission(),
        )
        assert is_new is True
        replay, replay_new = await queries.create_video_task(
            session,
            user_id='user-1',
            idempotency_key='key-1',
            submission=_submission(),
        )
        assert replay.id == created.id
        assert replay_new is False
        with pytest.raises(queries.VideoIdempotencyConflictError):
            await queries.create_video_task(
                session,
                user_id='user-1',
                idempotency_key='key-1',
                submission=_submission('Different prompt'),
            )

        assert (await queries.get_video_task(session, 'user-1', created.id)).id == created.id
        assert await queries.get_video_task(session, 'other-user', created.id) is None
        assert (
            await queries.get_video_task_by_idempotency_key(session, 'user-1', 'key-1')
        ).id == created.id
        assert await queries.video_task_exists(session, 'user-1', created.id) is True
        assert await queries.video_task_exists(session, 'other-user', created.id) is False


@pytest.mark.asyncio
async def test_video_query_pagination_and_terminal_delete(video_database) -> None:
    async with video_database() as session:
        first, _ = await queries.create_video_task(
            session,
            user_id='user-1',
            idempotency_key='key-1',
            submission=_submission('First'),
        )
        second, _ = await queries.create_video_task(
            session,
            user_id='user-1',
            idempotency_key='key-2',
            submission=_submission('Second'),
        )
        page = await queries.list_video_tasks(session, 'user-1', 1, since=0)
        assert len(page.items) == 1
        assert page.next_cursor is not None
        next_page = await queries.list_video_tasks(session, 'user-1', 10, cursor=page.next_cursor)
        assert len(next_page.items) == 1

        assert await queries.delete_video_task(session, 'user-1', first.id) is False
        row = await session.get(queries.VideoGenerationTask, first.id)
        row.status = 'failed'
        await session.commit()
        assert await queries.delete_video_task(session, 'user-1', first.id) is True
        assert await queries.delete_video_task(session, 'user-1', second.id) is False


def test_response_and_submission_helpers_fail_closed() -> None:
    assert queries._result(None) is None
    assert queries._result({'url': 123}) is None
    response = queries.VideoTaskResponse(
        id='task-1',
        payload_sha256='a' * 64,
        status='running',
        task='text-to-video',
        prompt='Prompt',
        model_id='model-a',
        params={'multi_prompt': [{'prompt': 'one'}]},
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )
    submission = queries._submission_from_task(response)
    assert isinstance(submission.params['multi_prompt'], str)
    assert queries.video_task_matches_submission(response, _submission()) is False
