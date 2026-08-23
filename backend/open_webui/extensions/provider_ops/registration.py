from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

import anyio
from fastapi import FastAPI
from open_webui.env import UVICORN_WORKERS
from open_webui.extensions.migration_kit import SchemaGuard, validate_schema
from open_webui.utils.redis import get_redis_client

from .db import provider_ops_session
from .migrations.runner import SPEC, run_provider_ops_migrations

log = logging.getLogger(__name__)

# 厂商计费同步自动化：provider_ops 现在只能通过 POST /admin/providers/fal/sync
# 手动触发。补一个每日定时后台 worker，参考 credits/registration.py 的 recovery
# worker 模式（CancelledError 重抛 + Exception 捕获 + shutdown cancel/await）。
#
# 默认每 24 小时跑一次全量同步（pricing/requests/billing_events/usage/analytics），
# 查询窗口 48h。Redis 可用时用 SET NX 租约在多 worker/实例间选主；多 worker
# 且无 Redis 时禁用自动任务，管理员仍可通过原有端点手动同步。

_PROVIDER_SYNC_INTERVAL_SECONDS = 24 * 60 * 60
_PROVIDER_SYNC_INITIAL_DELAY_SECONDS = 60
_PROVIDER_SYNC_TASK_NAME = 'provider-ops-sync'
# fal 账单通常次日才出，窗口拉到 48h 覆盖昨日数据。
_PROVIDER_SYNC_WINDOW_HOURS = 48
_PROVIDER_SYNC_LEASE_KEY = 'webui:provider-ops:fal-sync:daily'
_provider_sync_redis = get_redis_client(async_mode=True)
_provider_sync_lease_token: str | None = None
_RELEASE_LEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def _claim_periodic_sync_lease() -> bool:
    """每个同步周期只允许一个 worker/实例执行。租约保留到下个周期。"""
    global _provider_sync_lease_token
    if _provider_sync_redis is None:
        return UVICORN_WORKERS == 1
    token = uuid4().hex
    try:
        claimed = bool(
            await _provider_sync_redis.set(
                _PROVIDER_SYNC_LEASE_KEY,
                token,
                nx=True,
                ex=_PROVIDER_SYNC_INTERVAL_SECONDS,
            )
        )
        if claimed:
            _provider_sync_lease_token = token
        return claimed
    except Exception:
        log.exception('Could not claim periodic fal sync lease')
        return UVICORN_WORKERS == 1


async def _release_periodic_sync_lease() -> None:
    """仅释放当前进程实际持有的租约，避免误删其他 worker 的新租约。"""
    global _provider_sync_lease_token
    token = _provider_sync_lease_token
    if token is None:
        return
    if _provider_sync_redis is None:
        _provider_sync_lease_token = None
        return
    try:
        await _provider_sync_redis.eval(
            _RELEASE_LEASE_SCRIPT,
            1,
            _PROVIDER_SYNC_LEASE_KEY,
            token,
        )
    except Exception:
        log.exception('Could not release periodic fal sync lease')
    finally:
        _provider_sync_lease_token = None


async def _run_periodic_fal_sync() -> None:
    """周期性触发 fal 平台同步。

    启动后短暂延迟再跑，避开迁移和其他初始化；后续固定间隔。
    """
    # 不能把首次运行延迟整整 24h：频繁部署会不断重置计时器，使自动同步
    # 永远没有机会执行。短暂等待即可避开启动高峰。
    await asyncio.sleep(_PROVIDER_SYNC_INITIAL_DELAY_SECONDS)
    while True:
        try:
            if not await _claim_periodic_sync_lease():
                await asyncio.sleep(_PROVIDER_SYNC_INTERVAL_SECONDS)
                continue
            from .platform_sync import sync_fal_platform
            from .schemas import ProviderSyncForm

            async with provider_ops_session() as session:
                result = await sync_fal_platform(
                    session,
                    ProviderSyncForm(window_hours=_PROVIDER_SYNC_WINDOW_HOURS),
                )
            if result.status == 'failed':
                log.warning(
                    'Periodic fal platform sync run %s failed: %s',
                    result.id,
                    result.error_code,
                )
                # 同步失败后释放租约，允许其他 worker 在下个周期前重试
                await _release_periodic_sync_lease()
            else:
                log.info('Periodic fal platform sync run %s succeeded', result.id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception('Periodic fal platform sync pass failed')
            # 异常时同样释放租约，避免 24h 内无人接管
            await _release_periodic_sync_lease()
        await asyncio.sleep(_PROVIDER_SYNC_INTERVAL_SECONDS)


async def initialize_provider_ops_extension(app: FastAPI) -> None:
    await anyio.to_thread.run_sync(run_provider_ops_migrations)
    await anyio.to_thread.run_sync(_validate_provider_ops_schema)
    if UVICORN_WORKERS > 1 and _provider_sync_redis is None:
        log.warning(
            'Automatic fal platform sync is disabled with multiple workers and no Redis; '
            'use the admin sync endpoint or configure Redis for leader election'
        )
        return
    # 启动定时同步 worker。幂等：若已有未完成任务则跳过。
    existing = getattr(app.state, 'provider_ops_sync_task', None)
    if existing is None or existing.done():
        app.state.provider_ops_sync_task = asyncio.create_task(
            _run_periodic_fal_sync(),
            name=_PROVIDER_SYNC_TASK_NAME,
        )


_SCHEMA_GUARD = SchemaGuard(
    spec=SPEC,
    required_tables=frozenset(
        {
            'ext_provider_invocation',
            'ext_provider_price_snapshot',
            'ext_provider_billing_event',
            'ext_provider_request_record',
            'ext_provider_usage_bucket',
            'ext_provider_analytics_bucket',
            'ext_provider_sync_run',
        }
    ),
)


def _validate_provider_ops_schema() -> None:
    validate_schema(_SCHEMA_GUARD)


async def shutdown_provider_ops_extension(app: FastAPI) -> None:
    """取消并等待定时同步任务，避免进程退出时 pending task 警告。"""
    task = getattr(app.state, 'provider_ops_sync_task', None)
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        delattr(app.state, 'provider_ops_sync_task')
    await _release_periodic_sync_lease()


__all__ = [
    'initialize_provider_ops_extension',
    'shutdown_provider_ops_extension',
]
