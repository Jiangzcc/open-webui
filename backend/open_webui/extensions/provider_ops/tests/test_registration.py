from __future__ import annotations

import asyncio
from types import SimpleNamespace

from open_webui.extensions.provider_ops import registration


def test_periodic_sync_lease_is_global_when_redis_is_available(monkeypatch) -> None:
    class _FakeRedis:
        def __init__(self) -> None:
            self.claimed = False

        async def set(self, _key, _value, *, nx, ex):  # type: ignore[no-untyped-def]
            assert nx is True
            assert ex == registration._PROVIDER_SYNC_INTERVAL_SECONDS
            if self.claimed:
                return False
            self.claimed = True
            return True

    async def scenario() -> None:
        redis = _FakeRedis()
        monkeypatch.setattr(registration, '_provider_sync_redis', redis)
        monkeypatch.setattr(registration, '_provider_sync_lease_token', None)
        assert await registration._claim_periodic_sync_lease() is True
        assert await registration._claim_periodic_sync_lease() is False

    asyncio.run(scenario())


def test_periodic_sync_lease_release_is_owner_scoped(monkeypatch) -> None:
    class _FakeRedis:
        value: str | None = None

        async def set(self, _key, value, *, nx, ex):  # type: ignore[no-untyped-def]
            assert nx is True
            assert ex == registration._PROVIDER_SYNC_INTERVAL_SECONDS
            if self.value is not None:
                return False
            self.value = value
            return True

        async def eval(self, _script, _key_count, _key, token):  # type: ignore[no-untyped-def]
            if self.value != token:
                return 0
            self.value = None
            return 1

    async def scenario() -> None:
        redis = _FakeRedis()
        monkeypatch.setattr(registration, '_provider_sync_redis', redis)
        monkeypatch.setattr(registration, '_provider_sync_lease_token', None)

        assert await registration._claim_periodic_sync_lease() is True
        owned_token = redis.value
        await registration._release_periodic_sync_lease()
        assert redis.value is None

        redis.value = 'another-worker-token'
        monkeypatch.setattr(registration, '_provider_sync_lease_token', owned_token)
        await registration._release_periodic_sync_lease()
        assert redis.value == 'another-worker-token'

    asyncio.run(scenario())


def test_periodic_sync_uses_short_initial_delay(monkeypatch) -> None:
    async def scenario() -> None:
        delays: list[int] = []

        async def stop_after_first_sleep(delay: int) -> None:
            delays.append(delay)
            raise asyncio.CancelledError

        monkeypatch.setattr(registration.asyncio, 'sleep', stop_after_first_sleep)
        try:
            await registration._run_periodic_fal_sync()
        except asyncio.CancelledError:
            pass

        assert delays == [registration._PROVIDER_SYNC_INITIAL_DELAY_SECONDS]
        assert delays[0] < registration._PROVIDER_SYNC_INTERVAL_SECONDS

    asyncio.run(scenario())


def test_shutdown_is_idempotent_when_no_task() -> None:
    # 未初始化 worker 时 shutdown 应安全返回，不抛错。
    asyncio.run(
        registration.shutdown_provider_ops_extension(
            SimpleNamespace(state=SimpleNamespace())
        )
    )


def test_shutdown_cancels_and_awaits_running_task() -> None:
    # 启动一个会一直 sleep 的 worker，shutdown 应 cancel 并 await 它。

    async def scenario() -> None:
        app = SimpleNamespace(state=SimpleNamespace())

        async def _stub_loop() -> None:
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                raise

        app.state.provider_ops_sync_task = asyncio.create_task(_stub_loop())
        await asyncio.sleep(0)  # 让任务真正进入睡眠

        await registration.shutdown_provider_ops_extension(app)

        # state 属性应被删除（shutdown delattr）。
        assert not hasattr(app.state, 'provider_ops_sync_task')

    asyncio.run(scenario())


def test_initialize_skips_when_task_already_running(monkeypatch) -> None:
    # 幂等：已有未完成任务时不重复创建。只验证「跳过创建新任务」逻辑，
    # 不真实跑迁移（迁移校验由独立测试覆盖）。

    async def scenario() -> None:
        app = SimpleNamespace(state=SimpleNamespace())

        async def _stub_loop() -> None:
            await asyncio.sleep(100)

        existing = asyncio.create_task(_stub_loop())
        app.state.provider_ops_sync_task = existing

        # 跳过迁移与 schema 校验（这两步与 worker 幂等性无关）。
        monkeypatch.setattr(registration, 'run_provider_ops_migrations', lambda: None)
        # anyio.to_thread.run_sync 会真实调用被 mock 的函数，故同时 mock 它
        # 为直接同步执行，避免线程池开销与 IO。
        import anyio

        async def _fake_to_thread(func, *args, **kwargs):  # type: ignore[no-untyped-def]
            func()

        monkeypatch.setattr(anyio.to_thread, 'run_sync', _fake_to_thread)
        monkeypatch.setattr(registration, '_validate_provider_ops_schema', lambda: None, raising=False)

        await registration.initialize_provider_ops_extension(app)

        # 应复用已存在的任务，未创建新的。
        assert app.state.provider_ops_sync_task is existing

        existing.cancel()
        try:
            await existing
        except asyncio.CancelledError:
            pass

    asyncio.run(scenario())


def test_initialize_creates_task_when_none(monkeypatch) -> None:
    # 无既有任务时应创建新 worker。

    async def scenario() -> None:
        app = SimpleNamespace(state=SimpleNamespace())

        monkeypatch.setattr(registration, 'run_provider_ops_migrations', lambda: None)
        import anyio

        async def _fake_to_thread(func, *args, **kwargs):  # type: ignore[no-untyped-def]
            func()

        monkeypatch.setattr(anyio.to_thread, 'run_sync', _fake_to_thread)
        monkeypatch.setattr(registration, '_validate_provider_ops_schema', lambda: None, raising=False)

        await registration.initialize_provider_ops_extension(app)
        created = getattr(app.state, 'provider_ops_sync_task', None)
        assert created is not None and not created.done()
        created.cancel()
        try:
            await created
        except asyncio.CancelledError:
            pass

    asyncio.run(scenario())
