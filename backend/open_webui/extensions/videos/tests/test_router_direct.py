from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos import router
from open_webui.extensions.videos.executor import FalVideoExecutor, MockVideoExecutor, VideoExecutionError

USER = SimpleNamespace(id='user-1')
SUBMISSION = SimpleNamespace(model='model-a')
SESSION = object()


@pytest.mark.asyncio
async def test_video_admission_maps_all_failure_classes(monkeypatch) -> None:
    monkeypatch.setattr(router, 'ensure_model_enabled', AsyncMock())
    monkeypatch.setattr(router, 'enforce_video_generation_rate', AsyncMock())
    monkeypatch.setattr(router, 'quote_video_usage', AsyncMock(return_value=SimpleNamespace(charged_credits=3)))
    resolve = AsyncMock(return_value=MockVideoExecutor())
    monkeypatch.setattr(router, 'resolve_video_executor', resolve)
    assert await router._video_admission(USER, SUBMISSION, SESSION) is None

    for error, status_code in (
        (router.VideoInputError('invalid input'), 422),
        (VideoExecutionError('unavailable'), 503),
        (CreditError(code='insufficient_credits'), 402),
    ):
        resolve.side_effect = error
        response = await router._video_admission(USER, SUBMISSION, SESSION)
        assert response.status_code == status_code

    resolve.side_effect = None
    resolve.return_value = FalVideoExecutor('fake', 'https://queue.test', 'https://storage.test', 1, 1, 1)
    policy = Mock(side_effect=VideoExecutionError('video_fal_cost_limit_exceeded'))
    monkeypatch.setattr(router, 'enforce_fal_video_policy', policy)
    assert (await router._video_admission(USER, SUBMISSION, SESSION)).status_code == 403
    policy.side_effect = VideoExecutionError('video_fal_policy_invalid')
    assert (await router._video_admission(USER, SUBMISSION, SESSION)).status_code == 503


@pytest.mark.asyncio
async def test_create_and_schedule_releases_slot_on_every_non_worker_path(monkeypatch) -> None:
    acquire = AsyncMock()
    release = AsyncMock()
    monkeypatch.setattr(router, 'acquire_video_generation_slot', acquire)
    monkeypatch.setattr(router, 'release_video_generation_slot', release)
    monkeypatch.setattr(router, 'fail_video_task_scheduling', AsyncMock())
    request = SimpleNamespace(app=object())

    acquire.side_effect = CreditError(code='rate_limited')
    assert isinstance(
        await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key'),
        JSONResponse,
    )
    acquire.side_effect = None

    create = AsyncMock(side_effect=router.VideoIdempotencyConflictError())
    monkeypatch.setattr(router, 'create_video_task', create)
    assert (await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key')).status_code == 409
    create.side_effect = ValueError('bad asset')
    assert (await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key')).status_code == 422
    create.side_effect = RuntimeError('db')
    with pytest.raises(RuntimeError):
        await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key')

    task = SimpleNamespace(id='task-1')
    create.side_effect = None
    create.return_value = (task, False)
    assert await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key') is task

    create.return_value = (task, True)
    schedule = Mock()
    monkeypatch.setattr(router, 'schedule_video_task', schedule)
    assert await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key') is task
    await schedule.call_args.kwargs['on_finished']()

    schedule.side_effect = RuntimeError('scheduler')
    with pytest.raises(RuntimeError):
        await router._create_and_schedule_video_task(request, SESSION, USER, SUBMISSION, 'key')
    router.fail_video_task_scheduling.assert_awaited_once_with(request.app, task.id, USER.id)


@pytest.mark.asyncio
async def test_video_list_get_and_delete_routes_cover_races(monkeypatch) -> None:
    marker = object()
    monkeypatch.setattr(router, 'public_video_catalog_for_user', AsyncMock(return_value=marker))
    assert await router.get_video_models(model_session=SESSION) is marker

    monkeypatch.setattr(router, 'list_video_tasks', AsyncMock(return_value=marker))
    assert await router.get_video_tasks(user=USER, session=SESSION) is marker
    router.list_video_tasks.side_effect = ValueError
    assert (await router.get_video_tasks(user=USER, session=SESSION)).status_code == 422

    monkeypatch.setattr(router, 'get_video_task', AsyncMock(return_value=None))
    with pytest.raises(HTTPException):
        await router.get_one_video_task('task', user=USER, session=SESSION)
    terminal = SimpleNamespace(status='failed')
    router.get_video_task.return_value = terminal
    assert await router.get_one_video_task('task', user=USER, session=SESSION) is terminal

    router.get_video_task.return_value = SimpleNamespace(status='running')
    with pytest.raises(HTTPException) as active:
        await router.remove_video_task('task', user=USER, session=SESSION)
    assert active.value.status_code == 409

    router.get_video_task.return_value = terminal
    monkeypatch.setattr(router, 'delete_video_task', AsyncMock(return_value=False))
    monkeypatch.setattr(router, 'video_task_exists', AsyncMock(return_value=True))
    with pytest.raises(HTTPException) as raced:
        await router.remove_video_task('task', user=USER, session=SESSION)
    assert raced.value.status_code == 409
    router.video_task_exists.return_value = False
    with pytest.raises(HTTPException) as gone:
        await router.remove_video_task('task', user=USER, session=SESSION)
    assert gone.value.status_code == 404
    router.delete_video_task.return_value = True
    assert await router.remove_video_task('task', user=USER, session=SESSION) is None
