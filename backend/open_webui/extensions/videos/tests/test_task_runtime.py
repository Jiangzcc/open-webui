from __future__ import annotations

import asyncio
from types import SimpleNamespace

from open_webui.extensions.videos import service
from open_webui.extensions.videos.schemas import VideoTaskResponse


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

        class _CreationContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

        async def set_state(_task_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            states.append(status)

        async def get_task(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return task

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
        monkeypatch.setattr(service, 'creation_session', lambda: _CreationContext())
        monkeypatch.setattr(service, 'get_video_task', get_task)
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service.asyncio, 'sleep', cancel_during_invoke)
        monkeypatch.setattr(service, 'mark_video_usage_failed', fail_usage)

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

        async def get_task(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return task

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
        monkeypatch.setattr(service, 'creation_session', lambda: _Context())
        monkeypatch.setattr(service, 'credit_session', lambda: _Context())
        monkeypatch.setattr(service, 'get_video_task', get_task)
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

        class _CreationContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

        class _TerminalContext(_CreationContext):
            def begin(self):
                return self

            async def __aexit__(self, *_args) -> None:
                raise asyncio.CancelledError

        class _StatusContext(_CreationContext):
            async def scalar(self, _statement):
                return 'succeeded'

        def make_credit_session():
            nonlocal credit_session_calls
            credit_session_calls += 1
            return _TerminalContext() if credit_session_calls == 1 else _StatusContext()

        async def set_state(_task_id, status, **_kwargs) -> None:  # type: ignore[no-untyped-def]
            states.append(status)

        async def get_task(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return task

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
        monkeypatch.setattr(service, 'creation_session', lambda: _CreationContext())
        monkeypatch.setattr(service, 'credit_session', make_credit_session)
        monkeypatch.setattr(service, 'get_video_task', get_task)
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
        monkeypatch.setattr(service, 'resolve_video_executor', lambda _request: real)
        monkeypatch.setattr(service, 'creation_session', lambda: _Context())
        monkeypatch.setattr(service, 'credit_session', lambda: _Context())
        monkeypatch.setattr(service, '_existing_creation_result', no_existing)
        monkeypatch.setattr(service, '_increment_delivery_attempts', no_op)
        monkeypatch.setattr(service, '_finalize_real_video', finalize)
        monkeypatch.setattr(service, 'mark_usage_succeeded_in_session', succeed)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission: (object(), {}, {}))

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

        class _Context:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

        async def invoke(*_args, **_kwargs):
            error = asyncio.CancelledError()
            setattr(error, 'provider_submitted', True)
            raise error

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def get_task(*_args, **_kwargs):
            return task

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def unexpected_fail(*_args, **_kwargs) -> None:
            raise AssertionError('submitted FAL usage must remain invoking for recovery')

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)
        monkeypatch.setattr(service, 'resolve_video_executor', lambda _request: real)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _Context())
        monkeypatch.setattr(service, 'get_video_task', get_task)
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service, 'heartbeat_video_usage', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', unexpected_fail)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission: (object(), {}, {}))

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

        class _Context:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args) -> None:
                return None

        async def invoke(*_args, **_kwargs):
            raise service.VideoExecutionError(
                'video_provider_failed',
                provider_submitted=True,
                retryable=True,
            )

        async def set_state(_task_id, status, **kwargs) -> None:
            states.append((status, kwargs.get('error_code')))

        async def get_task(*_args, **_kwargs):
            return task

        async def begin_usage(*_args, **_kwargs):
            return SimpleNamespace(outcome='new', usage=SimpleNamespace(id='usage-1'))

        async def no_op(*_args, **_kwargs) -> None:
            return None

        async def recover(task_id, *_args, **_kwargs) -> None:
            recovered.append(task_id)

        async def unexpected_fail(*_args, **_kwargs) -> None:
            raise AssertionError('uncertain submitted usage must remain invoking for recovery')

        monkeypatch.setattr(service.FalVideoExecutor, 'invoke', invoke)
        monkeypatch.setattr(service, 'resolve_video_executor', lambda _request: real)
        monkeypatch.setattr(service, '_set_task_state', set_state)
        monkeypatch.setattr(service, '_publish_video_task_event', no_op)
        monkeypatch.setattr(service, 'creation_session', lambda: _Context())
        monkeypatch.setattr(service, 'get_video_task', get_task)
        monkeypatch.setattr(service, 'begin_video_usage', begin_usage)
        monkeypatch.setattr(service, '_set_task_usage_id', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_invoking', no_op)
        monkeypatch.setattr(service, 'heartbeat_video_usage', no_op)
        monkeypatch.setattr(service, 'mark_video_usage_failed', unexpected_fail)
        monkeypatch.setattr(service, 'recover_video_task', recover)
        monkeypatch.setattr(service, 'build_video_provider_payload', lambda _submission: (object(), {}, {}))

        await service.run_video_task(
            'task-1',
            SimpleNamespace(app=SimpleNamespace()),
            SimpleNamespace(id='user-1'),
        )

        assert states == [('running', None), ('running', 'video_delivery_pending')]
        assert recovered == ['task-1']

    asyncio.run(scenario())
