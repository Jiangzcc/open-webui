from __future__ import annotations

import asyncio
from types import SimpleNamespace

from fastapi import HTTPException

from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.videos import service
from open_webui.extensions.videos.executor import MockVideoExecutor, VideoExecutionError
from open_webui.extensions.videos.schemas import VideoTaskResponse


def _row_of(task: VideoTaskResponse):
    """run/recover_video_task 直接按行查询（读取 response 之外的原始列，
    如 params_json 原始列），测试需提供行形态而非响应模型。"""
    return SimpleNamespace(
        id=task.id,
        user_id='user-1',
        status=task.status,
        task=task.task,
        prompt=task.prompt,
        model_id=task.model_id,
        params_json=dict(task.params),
        assets_json=[asset.model_dump() for asset in task.assets],
        result_json=None,
        error_code=task.error_code,
        created_at=task.created_at,
        started_at=None,
        completed_at=None,
        updated_at=task.updated_at,
    )


class _RowContext:
    """creation_session 替身：scalar 返回预置任务行。"""

    def __init__(self, row):
        self.row = row

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    def begin(self):
        return self

    async def scalar(self, _statement):
        return self.row


def test_schedule_video_task_holds_slot_until_worker_finishes(monkeypatch) -> None:
    async def scenario() -> None:
        finish = asyncio.Event()
        released = asyncio.Event()

        async def fake_run(*_args, **_kwargs) -> None:
            await finish.wait()

        async def release() -> None:
            released.set()

        monkeypatch.setattr(service, 'run_video_task', fake_run)
        app = SimpleNamespace(state=SimpleNamespace(video_generation_tasks={}))
        request = SimpleNamespace(app=app)

        service.schedule_video_task(request, 'task-1', object(), on_finished=release)
        worker = app.state.video_generation_tasks['task-1']
        await asyncio.sleep(0)
        assert not released.is_set()

        finish.set()
        await worker
        await asyncio.sleep(0)

        assert released.is_set()
        assert app.state.video_generation_tasks == {}

    asyncio.run(scenario())


def test_slot_release_failure_does_not_mask_worker_cancellation(monkeypatch) -> None:
    async def scenario() -> None:
        async def cancelled_worker(*_args, **_kwargs) -> None:
            raise asyncio.CancelledError

        async def failed_release() -> None:
            raise RuntimeError('event loop already closed')

        monkeypatch.setattr(service, 'run_video_task', cancelled_worker)
        app = SimpleNamespace(state=SimpleNamespace(video_generation_tasks={}))
        service.schedule_video_task(
            SimpleNamespace(app=app),
            'task-1',
            object(),
            on_finished=failed_release,
        )
        worker = app.state.video_generation_tasks['task-1']

        try:
            await worker
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('slot cleanup masked the worker cancellation')

        await asyncio.sleep(0)
        assert app.state.video_generation_tasks == {}

    asyncio.run(scenario())


def test_video_event_publish_failure_is_best_effort(monkeypatch) -> None:
    async def scenario() -> None:
        from open_webui.extensions.creations import events

        async def failed_publish(*_args, **_kwargs) -> None:
            raise RuntimeError('event bus unavailable')

        monkeypatch.setattr(events, 'publish_generation_event', failed_publish)
        await service._publish_video_task_event(
            SimpleNamespace(state=SimpleNamespace()),
            'task-1',
            'user-1',
            'succeeded',
        )

    asyncio.run(scenario())


def test_shutdown_cleanup_failure_does_not_mask_cancellation_or_skip_task_state(monkeypatch) -> None:  # noqa: C901
    async def scenario() -> None:  # noqa: C901
        states: list[str] = []
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        async def set_state(_task_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            states.append(status)

        async def begin_usage(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def cancel_during_invoke(*_args, **_kwargs) -> None:
            raise asyncio.CancelledError

        async def fail_usage(*_args, **_kwargs) -> None:
            raise RuntimeError('database unavailable')

        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(_row_of(task)))
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service.asyncio, 'sleep', cancel_during_invoke)
        monkeypatch.setattr(service, 'mark_video_usage_failed', fail_usage)

        async def resolve_executor():
            return MockVideoExecutor()

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)

        try:
            await service.run_video_task(
                'task-1',
                SimpleNamespace(app=object()),
                SimpleNamespace(id='user-1'),
            )
        except asyncio.CancelledError as error:
            assert error.args == ()
        else:
            raise AssertionError('original cancellation was masked')

        assert states[-1] == 'failed'

    asyncio.run(scenario())


def test_late_cancellation_preserves_committed_success(monkeypatch) -> None:  # noqa: C901
    async def scenario() -> None:  # noqa: C901
        states: list[str] = []
        failed_usage = False
        success_publish_count = 0
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        class _Context:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

            def begin(self):
                return self

        async def set_state(_task_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            states.append(status)

        async def publish(_app, _task_id, _user_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            nonlocal success_publish_count
            if status == 'succeeded':
                success_publish_count += 1
                if success_publish_count == 1:
                    raise asyncio.CancelledError

        async def begin_usage(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def finalize(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return {'url': '/api/v1/files/result/content'}

        async def succeed(*_args, **_kwargs) -> int:
            return 1

        async def fail_usage(*_args, **_kwargs) -> None:
            nonlocal failed_usage
            failed_usage = True

        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', publish)

        async def resolve_executor():
            return MockVideoExecutor()

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(_row_of(task)))
        monkeypatch.setattr(service, 'credit_session', lambda: _Context())
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service.asyncio, 'sleep', no_op)
        monkeypatch.setattr(service, '_finalize_mock_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
        monkeypatch.setattr(service, 'mark_video_usage_failed', fail_usage)

        try:
            await service.run_video_task(
                'task-1',
                SimpleNamespace(app=object()),
                SimpleNamespace(id='user-1'),
            )
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('late cancellation was swallowed')

        assert states[-1] == 'succeeded'
        assert 'failed' not in states
        assert failed_usage is False

    asyncio.run(scenario())


def test_cancellation_during_terminal_commit_uses_persisted_usage_status(monkeypatch) -> None:  # noqa: C901
    async def scenario() -> None:  # noqa: C901
        states: list[str] = []
        failed_usage = False
        credit_session_calls = 0
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        class _TerminalContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                raise asyncio.CancelledError

            def begin(self):
                return self

        class _StatusContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

            async def scalar(self, _statement):
                return 'succeeded'

        def make_credit_session():
            nonlocal credit_session_calls
            credit_session_calls += 1
            return _TerminalContext() if credit_session_calls == 1 else _StatusContext()

        async def set_state(_task_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            states.append(status)

        async def begin_usage(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def finalize(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return {'url': '/api/v1/files/result/content'}

        async def succeed(*_args, **_kwargs) -> int:
            return 1

        async def fail_usage(*_args, **_kwargs) -> None:
            nonlocal failed_usage
            failed_usage = True

        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(_row_of(task)))
        monkeypatch.setattr(service, 'credit_session', make_credit_session)

        async def resolve_executor():
            return MockVideoExecutor()

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service.asyncio, 'sleep', no_op)
        monkeypatch.setattr(service, '_finalize_mock_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
        monkeypatch.setattr(service, 'mark_video_usage_failed', fail_usage)

        try:
            await service.run_video_task(
                'task-1',
                SimpleNamespace(app=object()),
                SimpleNamespace(id='user-1'),
            )
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('terminal-commit cancellation was swallowed')

        assert states[-1] == 'succeeded'
        assert 'failed' not in states
        assert failed_usage is False
        assert credit_session_calls == 2

    asyncio.run(scenario())


def test_recovery_resumes_existing_fal_request_without_new_generation(monkeypatch, tmp_path) -> None:  # noqa: C901
    async def scenario() -> None:  # noqa: C901 - recovery collaborators are isolated explicitly
        states: list[str] = []
        resumed: dict[str, object] = {}
        row = SimpleNamespace(
            id='task-1',
            user_id='user-1',
            idempotency_key='key-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params_json={'duration': '5'},
            assets_json=[],
            result_json=None,
            error_code=None,
            usage_id='usage-1',
            execution_mode='fal',
            provider_request_id='request-1',
            provider_status_url='https://queue.fal.run/status/request-1',
            provider_response_url='https://queue.fal.run/response/request-1',
            provider_result_url=None,
            delivery_attempts=0,
            created_at=1,
            started_at=1,
            completed_at=None,
            updated_at=1,
        )

        class _Context:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

            def begin(self):
                return self

            async def scalar(self, _statement):
                return row

        output_path = tmp_path / 'recovered.mp4'
        output_path.write_bytes(b'video')
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

        async def resume(self, _task, _definition, **kwargs):
            resumed.update(kwargs)
            return service.VideoExecutionOutput(output_path, 'video/mp4', 5)

        async def unexpected_invoke(*_args, **_kwargs):
            raise AssertionError('recovery must not invoke a new provider generation')

        async def no_existing(*_args, **_kwargs):
            return None

        async def set_state(_task_id, status, **_kwargs) -> None:
            states.append(status)

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def finalize(*_args, **_kwargs):
            return {'url': '/api/v1/files/result/content'}

        async def succeed(*_args, **_kwargs):
            return 1

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', resume)
        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', unexpected_invoke)
        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'creation_session', lambda: _Context())
        monkeypatch.setattr(service, 'credit_session', lambda: _Context())
        monkeypatch.setattr(service, '_existing_creation_result', no_existing)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(service, '_finalize_real_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission, **_kwargs: (object(), {}, {}))

        await service.recover_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace(url_path_for=lambda *_args, **_kwargs: '/content')),
            SimpleNamespace(id='user-1'),
        )

        assert resumed['response_url'] == row.provider_response_url
        assert states == ['succeeded']
        assert not output_path.exists()

    asyncio.run(scenario())


def test_shutdown_keeps_submitted_fal_task_recoverable(monkeypatch) -> None:  # noqa: C901
    async def scenario() -> None:  # noqa: C901 - shutdown billing collaborators are isolated explicitly
        states: list[tuple[str, str | None]] = []
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        async def invoke(*_args, **_kwargs):
            error = asyncio.CancelledError()
            setattr(error, 'provider_submitted', True)
            raise error

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def unexpected_fail(*_args, **_kwargs) -> None:
            raise AssertionError('submitted FAL usage must remain invoking for recovery')

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)
        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(_row_of(task)))
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service, 'heartbeat_video_usage', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', unexpected_fail)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission, **_kwargs: (object(), {}, {}))

        try:
            await service.run_video_task(
                'task-1',
                SimpleNamespace(app=SimpleNamespace()),
                SimpleNamespace(id='user-1'),
            )
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError('shutdown cancellation was swallowed')

        assert states == [('running', None), ('running', 'video_recovery_pending')]

    asyncio.run(scenario())


def test_uncertain_submitted_fal_failure_resumes_without_refund(monkeypatch) -> None:  # noqa: C901
    async def scenario() -> None:
        states: list[tuple[str, str | None]] = []
        recovered: list[str] = []
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )

        async def invoke(*_args, **_kwargs):
            raise service.VideoExecutionError(
                'video_provider_failed',
                provider_submitted=True,
                retryable=True,
            )

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def recover(task_id, *_args, **_kwargs) -> None:
            recovered.append(task_id)

        async def unexpected_fail(*_args, **_kwargs) -> None:
            raise AssertionError('uncertain submitted usage must remain invoking for recovery')

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)
        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(_row_of(task)))
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service, 'heartbeat_video_usage', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', unexpected_fail)
        monkeypatch.setattr(service, 'recover_video_task', recover)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission, **_kwargs: (object(), {}, {}))

        await service.run_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace()),
            SimpleNamespace(id='user-1'),
        )

        assert states == [('running', None), ('running', 'video_delivery_pending')]
        assert recovered == ['task-1']

    asyncio.run(scenario())


def test_submission_from_task_reserializes_json_params() -> None:
    """回归（对抗性审查）：params_json 里 JSON 字段（kling multi_prompt）以
    解析后的 dict/list 落库；run/recover_video_task 重建提交表单时表单的
    params 只接受标量，必须先把非标量值序列化回 JSON 字符串，否则
    pydantic 校验失败、任务必然在运行时进入 failed。"""
    task = VideoTaskResponse(
        id='task-1',
        status='running',
        task='text-to-video',
        prompt='orbit',
        model_id='kling-video-v3-pro',
        params={'duration': '5', 'multi_prompt': [{'prompt': 'golden hour orbit', 'duration': 3}]},
        assets=(),
        result=None,
        error_code=None,
        created_at=1,
        updated_at=1,
    )

    submission = service._submission_from_task(task)

    assert isinstance(submission.params['multi_prompt'], str)
    _definition, provider_payload, _safe_params = service.build_video_provider_payload(submission)
    assert provider_payload['multi_prompt'] == [{'prompt': 'golden hour orbit', 'duration': 3}]


def test_create_video_task_stores_plain_prompt(monkeypatch) -> None:
    """落库契约：prompt/params 即用户输入的纯文本原样落库（标签点击时
    已在输入框插入 insert_text），无任何目录快照或 token 展开。"""

    async def scenario() -> None:
        from open_webui.extensions.videos import queries
        from open_webui.extensions.videos.schemas import VideoTaskSubmitForm

        added: list[object] = []

        class _Session:
            async def scalar(self, _statement):
                return None

            def add(self, task):
                added.append(task)

            async def commit(self):
                return None

        async def no_validate(*_args, **_kwargs):
            return None

        monkeypatch.setattr(queries, 'validate_video_assets', no_validate)

        submission = VideoTaskSubmitForm(
            task='text-to-video',
            model='kling-video-v3-pro',
            prompt='golden hour light rises',
            assets=(),
            params={'duration': '5'},
        )

        task, created = await queries.create_video_task(
            _Session(),
            user_id='user-1',
            idempotency_key='key-1',
            submission=submission,
        )

        assert created is True
        row = added[0]
        assert row.prompt == 'golden hour light rises'
        assert row.params_json['duration'] == '5'
        assert task.prompt == 'golden hour light rises'

    asyncio.run(scenario())


def test_run_video_task_passes_stored_prompt_to_provider(monkeypatch, tmp_path) -> None:
    """执行期直传：provider payload 的 prompt 就是落库的纯文本（无展开层）。"""

    async def scenario() -> None:
        states: list[str] = []
        invoked_payloads: list[dict] = {}
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='golden hour light rises',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )
        row = _row_of(task)
        result_path = tmp_path / 'result.mp4'
        result_path.write_bytes(b'video')

        async def invoke(self, _request, _user, _task, _definition, provider_payload, **_kwargs):
            invoked_payloads['prompt'] = provider_payload['prompt']
            return service.VideoExecutionOutput(result_path, 'video/mp4', 5)

        async def set_state(_task_id, status, **_kwargs) -> None:
            states.append(status)

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def finalize(*_args, **_kwargs):
            return {'url': '/api/v1/files/result/content'}

        async def succeed(*_args, **_kwargs) -> int:
            return 1

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)
        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _RowContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _RowContext(row))
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service, 'heartbeat_video_usage', no_op)
        monkeypatch.setattr(service, '_finalize_real_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)

        await service.run_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace()),
            SimpleNamespace(id='user-1'),
        )

        # provider 拿到落库原文；任务行与响应一致。
        assert invoked_payloads['prompt'] == 'golden hour light rises'
        assert row.prompt == 'golden hour light rises'
        assert states[-1] == 'succeeded'

    asyncio.run(scenario())


# ── 复盘 #2/#3/#4：交付与恢复可靠性 ─────────────────────────────────


def _recovery_row(**overrides) -> SimpleNamespace:
    """recover_video_task 的最小任务行（可按用例覆盖字段）。"""
    row = SimpleNamespace(
        id='task-1',
        user_id='user-1',
        idempotency_key='key-1',
        status='running',
        task='text-to-video',
        prompt='A paper boat',
        model_id='kling-video-v3-pro',
        params_json={'duration': '5'},
        assets_json=[],
        result_json=None,
        error_code=None,
        usage_id='usage-1',
        execution_mode='fal',
        provider_request_id=None,
        provider_status_url=None,
        provider_response_url=None,
        provider_result_url=None,
        delivery_attempts=0,
        created_at=1,
        started_at=1,
        completed_at=None,
        updated_at=1,
    )
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


class _SessionContext:
    """creation_session/credit_session 替身：scalar 返回预置行。"""

    def __init__(self, row):
        self.row = row

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    def begin(self):
        return self

    async def scalar(self, _statement):
        return self.row


class _ModelOpContext:
    """get_async_db 替身：任意 session 皆可。"""

    async def __aenter__(self):
        return object()

    async def __aexit__(self, *_args) -> None:
        return None


def test_run_finalize_runs_under_usage_heartbeat(monkeypatch, tmp_path) -> None:
    """复盘 #2：心跳必须覆盖 invoke 与 finalize 两阶段。只在 invoke 期间
    心跳时，大视频两轮上传超过 15 分钟 stale 阈值会让 usage 被回收成
    unknown → 成功转移写 0 行 → 已上传的付费视频被清理且不退款。"""

    async def scenario() -> None:
        states: list[str] = []
        heartbeat_tasks: list[asyncio.Task] = []
        heartbeat_alive_in_finalize: list[bool] = []
        task = VideoTaskResponse(
            id='task-1',
            status='running',
            task='text-to-video',
            prompt='A paper boat',
            model_id='kling-video-v3-pro',
            params={'duration': '5'},
            assets=(),
            result=None,
            error_code=None,
            created_at=1,
            updated_at=1,
        )
        output_path = tmp_path / 'result.mp4'
        output_path.write_bytes(b'video')
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

        async def tracked_heartbeat(_usage_id: str) -> None:
            heartbeat_tasks.append(asyncio.current_task())
            await asyncio.sleep(3600)

        async def invoke(self, *_args, **_kwargs):
            await asyncio.sleep(0)
            assert heartbeat_tasks, 'heartbeat must start during invoke'
            return service.VideoExecutionOutput(output_path, 'video/mp4', 5)

        async def finalize(*_args, **_kwargs):
            heartbeat_alive_in_finalize.append(not heartbeat_tasks[0].done())
            return {'url': '/api/v1/files/result/content'}

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def succeed(*_args, **_kwargs) -> int:
            return 1

        async def set_state(_task_id, status, **_kwargs) -> None:
            states.append(status)

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)

        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'heartbeat_video_usage', tracked_heartbeat)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(_row_of(task)))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(_row_of(task)))
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(
            service, 'build_video_provider_payload', lambda _submission, **_kw: (object(), {}, {})
        )
        monkeypatch.setattr(service, '_finalize_real_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)

        await service.run_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace()),
            SimpleNamespace(id='user-1'),
        )

        assert heartbeat_alive_in_finalize == [True]
        assert heartbeat_tasks[0].done(), 'heartbeat must be cancelled after the task finishes'
        assert states == ['running', 'succeeded']

    asyncio.run(scenario())


def test_recovery_finalize_runs_under_usage_heartbeat(monkeypatch, tmp_path) -> None:
    """恢复路径与 run 路径一致：resume 与 finalize 都在心跳覆盖内。"""

    async def scenario() -> None:
        states: list[str] = []
        heartbeat_tasks: list[asyncio.Task] = []
        heartbeat_alive_in_finalize: list[bool] = []
        row = _recovery_row(
            provider_request_id='request-1',
            provider_response_url='https://queue.fal.run/response/request-1',
        )
        output_path = tmp_path / 'recovered.mp4'
        output_path.write_bytes(b'video')
        real = service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

        async def tracked_heartbeat(_usage_id: str) -> None:
            heartbeat_tasks.append(asyncio.current_task())
            await asyncio.sleep(3600)

        async def resume(self, *_args, **_kwargs):
            await asyncio.sleep(0)
            assert heartbeat_tasks, 'heartbeat must start during resume'
            return service.VideoExecutionOutput(output_path, 'video/mp4', 5)

        async def finalize(*_args, **_kwargs):
            heartbeat_alive_in_finalize.append(not heartbeat_tasks[0].done())
            return {'url': '/api/v1/files/result/content'}

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def succeed(*_args, **_kwargs) -> int:
            return 1

        async def set_state(_task_id, status, **_kwargs) -> None:
            states.append(status)

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', resume)

        async def resolve_executor():
            return real

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'heartbeat_video_usage', tracked_heartbeat)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(
            service, 'build_video_provider_payload', lambda _submission, **_kw: (object(), {}, {})
        )
        monkeypatch.setattr(service, '_finalize_real_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace(url_path_for=lambda *_a, **_kw: '/content')),
            SimpleNamespace(id='user-1'),
        )

        assert heartbeat_alive_in_finalize == [True]
        assert heartbeat_tasks[0].done()
        assert states == ['succeeded']

    asyncio.run(scenario())


def test_recovery_stops_after_max_delivery_attempts(monkeypatch) -> None:
    """复盘 #3：投递尝试达到上限后转终态，不让 60 秒恢复循环无限重试、
    预扣积分永久占用。已受理的供应商请求保留预扣，交由对账修复流程。"""

    async def scenario() -> None:
        states: list[tuple[str, str | None]] = []
        failed_usage: dict[str, object] = {}
        row = _recovery_row(delivery_attempts=5)

        async def unexpected_resume(*_args, **_kwargs):
            raise AssertionError('exceeded delivery attempts must not poll the provider again')

        async def mark_failed(usage_id, code, *, restore_prepaid):
            failed_usage.update(usage_id=usage_id, code=code, restore_prepaid=restore_prepaid)

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', unexpected_resume)
        monkeypatch.setattr(
            service, '_increment_delivery_attempts', lambda *_a, **_kw: (_ for _ in ()).throw(
                AssertionError('attempts must not be incremented past the cap')
            )
        )
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task('task-1', SimpleNamespace(app=SimpleNamespace()), SimpleNamespace(id='user-1'))

        assert states == [('failed', 'video_delivery_attempts_exceeded')]
        assert failed_usage == {
            'usage_id': 'usage-1',
            'code': 'video_delivery_attempts_exceeded',
            'restore_prepaid': False,
        }

    asyncio.run(scenario())


def test_recovery_state_missing_without_submission_refunds(monkeypatch) -> None:
    """复盘 #4：恢复状态缺失且从未持久化提交状态 ⇒ 无法确认 FAL 是否
    受理过请求，与在线路径一致按未受理退款，而不是永久保留预扣。"""

    async def scenario() -> None:
        states: list[tuple[str, str | None]] = []
        failed_usage: dict[str, object] = {}
        row = _recovery_row()

        async def resume_raises(*_args, **_kwargs):
            raise service.VideoExecutionError('video_recovery_state_missing')

        async def mark_failed(usage_id, code, *, restore_prepaid):
            failed_usage.update(usage_id=usage_id, code=code, restore_prepaid=restore_prepaid)

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', resume_raises)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(
            service, 'build_video_provider_payload', lambda _submission, **_kw: (object(), {}, {})
        )

        async def resolve_executor():
            return service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task('task-1', SimpleNamespace(app=SimpleNamespace()), SimpleNamespace(id='user-1'))

        assert states == [('failed', 'video_recovery_state_missing')]
        assert failed_usage['restore_prepaid'] is True

    asyncio.run(scenario())


def test_recovery_state_missing_with_submission_keeps_charge(monkeypatch) -> None:
    """已持久化提交状态（FAL 已受理）时恢复状态缺失：保留预扣等待对账，
    避免厂商已收费而平台自动退款。"""

    async def scenario() -> None:
        failed_usage: dict[str, object] = {}
        row = _recovery_row(
            provider_request_id='request-1',
            provider_response_url='https://queue.fal.run/response/request-1',
        )

        async def resume_raises(*_args, **_kwargs):
            raise service.VideoExecutionError('video_recovery_state_missing')

        async def mark_failed(usage_id, code, *, restore_prepaid):
            failed_usage.update(usage_id=usage_id, code=code, restore_prepaid=restore_prepaid)

        async def no_op(*_args, **_kwargs) -> None:
            return None

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', resume_raises)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(
            service, 'build_video_provider_payload', lambda _submission, **_kw: (object(), {}, {})
        )

        async def resolve_executor():
            return service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600)

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
        monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed)
        monkeypatch.setattr(service, '_set_task_state', no_op)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task('task-1', SimpleNamespace(app=SimpleNamespace()), SimpleNamespace(id='user-1'))

        assert failed_usage['restore_prepaid'] is False

    asyncio.run(scenario())


def test_recovery_catalog_rejection_terminates_task(monkeypatch) -> None:
    """复盘 #3：模型下架（VideoInputError）必须转终态；原先落入泛型
    handler 被设回 running，60 秒恢复循环无限重试、任务永不终态。"""

    async def scenario() -> None:
        states: list[tuple[str, str | None]] = []
        failed_usage: dict[str, object] = {}
        row = _recovery_row(
            provider_request_id='request-1',
            provider_response_url='https://queue.fal.run/response/request-1',
        )

        async def unexpected_resume(*_args, **_kwargs):
            raise AssertionError('catalog-rejected recovery must not poll the provider')

        def payload_raises(*_args, **_kwargs):
            raise service.VideoInputError('unknown_video_model')

        async def mark_failed(usage_id, code, *, restore_prepaid):
            failed_usage.update(usage_id=usage_id, code=code, restore_prepaid=restore_prepaid)

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', unexpected_resume)
        monkeypatch.setattr(service, 'build_video_provider_payload', payload_raises)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task('task-1', SimpleNamespace(app=SimpleNamespace()), SimpleNamespace(id='user-1'))

        assert states == [('failed', 'video_input_rejected:unknown_video_model')]
        # FAL 已受理（提交状态持久化）→ 保留预扣等待对账。
        assert failed_usage['restore_prepaid'] is False

    asyncio.run(scenario())


def test_recovery_billing_failure_does_not_block_terminal_state(monkeypatch) -> None:
    """复盘 #3：mark_video_usage_failed 抛错不能吞掉任务终态写入
    （原先是全库唯一未包 try/except 的失败路径，DB 抖动会让任务
    永留 running）。"""

    async def scenario() -> None:
        states: list[tuple[str, str | None]] = []
        row = _recovery_row(
            provider_request_id='request-1',
            provider_response_url='https://queue.fal.run/response/request-1',
        )

        async def resume_raises(*_args, **_kwargs):
            raise service.VideoExecutionError('video_result_invalid_type')

        async def mark_failed_raises(*_args, **_kwargs):
            raise RuntimeError('credits db unavailable')

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        monkeypatch.setattr(service.FalVideoExecutor, 'resume', resume_raises)
        monkeypatch.setattr(service, 'creation_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, 'credit_session', lambda: _SessionContext(row))
        monkeypatch.setattr(service, '_existing_creation_result', no_op)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(
            service, 'build_video_provider_payload', lambda _submission, **_kw: (object(), {}, {})
        )
        monkeypatch.setattr(service, 'mark_video_usage_failed', mark_failed_raises)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)

        await service.recover_video_task('task-1', SimpleNamespace(app=SimpleNamespace()), SimpleNamespace(id='user-1'))

        assert states == [('failed', 'video_result_invalid_type')]

    asyncio.run(scenario())


class _ScanContext:
    """recover_incomplete_video_tasks 的 creation_session 替身：返回预置行。"""

    def __init__(self, rows):
        self.rows = rows

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def execute(self, _statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.rows))


def _patch_recovery_scan(
    monkeypatch,
    rows,
    *,
    ensure_model_enabled,
    quote,
    executor=None,
    enforce_policy=None,
) -> dict[str, list]:
    """为 recover_incomplete_video_tasks 测试打齐桩，返回观测容器。"""
    observed: dict[str, list] = {'scheduled': [], 'states': [], 'released': []}

    async def set_state(task_id, status, **kwargs) -> None:
        observed['states'].append((task_id, status, kwargs.get('error_code')))

    async def no_op(*_args, **_kwargs) -> None:
        return None

    async def get_user(_user_id):
        return SimpleNamespace(id='user-1')

    def schedule(_request, task_id, _user) -> bool:
        # 同步桩：真实的 schedule_video_recovery_task 内部 create_task，调用点无 await。
        observed['scheduled'].append(task_id)
        return True

    async def release(user_id) -> None:
        observed['released'].append(user_id)

    monkeypatch.setattr(service, 'creation_session', lambda: _ScanContext(rows))
    monkeypatch.setattr(service, '_set_task_state', set_state)
    monkeypatch.setattr(service, 'acquire_video_generation_slot', no_op)
    monkeypatch.setattr(service, 'release_video_generation_slot', release)
    monkeypatch.setattr(service, 'schedule_video_recovery_task', schedule)
    monkeypatch.setattr(service.Users, 'get_user_by_id', get_user)
    monkeypatch.setattr(service, 'get_async_db', lambda: _ModelOpContext())
    monkeypatch.setattr(service, 'ensure_model_enabled', ensure_model_enabled)
    monkeypatch.setattr(service, 'quote_video_usage', quote)
    if executor is not None:
        async def resolve_executor():
            return executor

        monkeypatch.setattr(service, 'resolve_video_executor', resolve_executor)
    if enforce_policy is not None:
        monkeypatch.setattr(service, 'enforce_fal_video_policy', enforce_policy)
    return observed


def test_recovery_scan_rejects_queued_task_when_model_disabled(monkeypatch) -> None:
    """复盘 #9：排队任务恢复前按当前配置重新准入——模型已被管理员停用
    时转终态，而不是照常调度扣费。"""

    async def scenario() -> None:
        row = _recovery_row(status='queued')

        async def ensure_disabled(*_args, **_kwargs):
            raise HTTPException(
                status_code=503,
                detail={'code': 'video_model_unavailable', 'message': 'maintenance'},
            )

        async def quote(*_args, **_kwargs):
            raise AssertionError('model admission must fail before quoting')

        observed = _patch_recovery_scan(monkeypatch, [row], ensure_model_enabled=ensure_disabled, quote=quote)

        scheduled = await service.recover_incomplete_video_tasks(SimpleNamespace(app=SimpleNamespace()))

        assert scheduled == 0
        assert observed['scheduled'] == []
        assert observed['states'] == [('task-1', 'failed', 'video_model_unavailable')]

    asyncio.run(scenario())


def test_recovery_scan_leaves_transient_failures_to_run_path(monkeypatch) -> None:
    """余额不足/价格未配置等暂时性原因不做准入拦截：照常调度，由
    run_video_task 的 begin_video_usage 抛 CreditError 走既有终态失败路径
    （排队任务不能无限滞留，且语义与在线提交一致）。"""

    async def scenario() -> None:
        row = _recovery_row(status='queued')

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def quote(*_args, **_kwargs):
            raise CreditError(code='insufficient_credits')

        observed = _patch_recovery_scan(
            monkeypatch, [row], ensure_model_enabled=ensure_enabled, quote=quote
        )

        scheduled = await service.recover_incomplete_video_tasks(SimpleNamespace(app=SimpleNamespace()))

        assert scheduled == 1
        assert observed['scheduled'] == ['task-1']
        assert observed['states'] == []

    asyncio.run(scenario())


def test_recovery_scan_rejects_queued_task_over_price_limit(monkeypatch) -> None:
    """复盘 #9：价格上调后超过 FAL 每请求限价的排队任务转终态，
    而不是按新价照常扣费。"""

    async def scenario() -> None:
        row = _recovery_row(status='queued')

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def quote(*_args, **_kwargs):
            return SimpleNamespace(charged_credits=5000)

        def enforce_raises(*, model_id, charged_credits):
            raise VideoExecutionError('video_fal_cost_limit_exceeded')

        observed = _patch_recovery_scan(
            monkeypatch,
            [row],
            ensure_model_enabled=ensure_enabled,
            quote=quote,
            executor=service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600),
            enforce_policy=enforce_raises,
        )

        scheduled = await service.recover_incomplete_video_tasks(SimpleNamespace(app=SimpleNamespace()))

        assert scheduled == 0
        assert observed['scheduled'] == []
        assert observed['states'] == [('task-1', 'failed', 'video_fal_cost_limit_exceeded')]

    asyncio.run(scenario())


def test_recovery_scan_schedules_qualified_queued_task(monkeypatch) -> None:
    """准入全部通过的排队任务照常调度（回归保护）。"""

    async def scenario() -> None:
        row = _recovery_row(status='queued')

        async def ensure_enabled(*_args, **_kwargs) -> None:
            return None

        async def quote(*_args, **_kwargs):
            return SimpleNamespace(charged_credits=100)

        def enforce_ok(*, model_id, charged_credits) -> None:
            return None

        observed = _patch_recovery_scan(
            monkeypatch,
            [row],
            ensure_model_enabled=ensure_enabled,
            quote=quote,
            executor=service.FalVideoExecutor('key', 'queue', 'storage', 900, 1024, 3600),
            enforce_policy=enforce_ok,
        )

        scheduled = await service.recover_incomplete_video_tasks(SimpleNamespace(app=SimpleNamespace()))

        assert scheduled == 1
        assert observed['scheduled'] == ['task-1']
        assert observed['states'] == []

    asyncio.run(scenario())
