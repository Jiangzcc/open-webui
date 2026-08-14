"""积分↔厂商成本对账链路 TDD 骨架。

本轮只落测试桩与接口签名；实现待评审通过后单独立项（见
``docs/superpowers/specs/2026-08-14-credit-cost-reconciliation-design.md``）。

图片/视频关联键结构不同，故按媒体类型分别覆盖：
- 视频：``VideoGenerationTask.usage_id`` / ``idempotency_key`` 直查；
  但当前 mock 路径不写 ``ProviderInvocation``，task↔invocation 跳断，
  故视频对账依赖 #4（视频执行体）落地后才完整。
- 图片：有 ``Idempotency-Key`` header 时 task 与 usage 共享 key 可直查；
  无 header 时 idempotency_key 断开，回退 ``batch_id + file_id`` 反查。
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason='reconciliation design only; implementation is not part of this change')


# ---------------------------------------------------------------------------
# 关联解析
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_video_usage_links_to_billing_via_usage_id() -> None:
    """视频：``CreditUsage.id == VideoGenerationTask.usage_id``，可直查到 ProviderBillingEvent。

    落地 #4 后 ``run_video_task`` 会写 ``ProviderInvocation(task_id=task.id)``，
    ``provider_request_id`` 再关联 ``ProviderBillingEvent``，整链路闭合。
    """
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_image_usage_with_header_links_via_idempotency_key() -> None:
    """图片（客户端发了 ``Idempotency-Key``）：task.idempotency_key == usage.idempotency_key，直接 JOIN。

    creations router 与 ``bill_image_call`` 读同一个 request 的 header，
    故两者相等，无需反查。
    """
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_image_usage_without_header_falls_back_to_batch_id_and_file_id() -> None:
    """图片（无 header）：idempotency_key 断开，回退 batch_id+file_id 反查 usage。

    ``CreationMediaItem.batch_id == task.id`` 且 ``file_id ∈ usage.result_snapshot.urls``，
    两者交集定位唯一 usage。
    """
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_usage_without_provider_invocation_returns_missing_billing() -> None:
    """视频 mock 路径不写 invocation → resolve 返回 None → missing_billing 差异。

    落地 #4 前的预期行为；落地后此用例应改为"真实调用产生 invocation 即可关联"。
    """
    raise NotImplementedError('reconciliation module not implemented this round')


# ---------------------------------------------------------------------------
# 差异检测
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_discrepancy_when_usage_and_billing_match() -> None:
    """usage 与 billing_event 一一对应且金额匹配时，差异列表为空。"""
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_flags_usage_without_billing_event() -> None:
    """credits 扣了但厂商侧无 billing_event → missing_billing 差异行。"""
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_flags_billing_event_without_usage() -> None:
    """厂商有计费但 credits 无 usage → missing_usage 差异行（最严重，需即时告警）。"""
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_flags_price_drift_when_charged_vs_cost_exceeds_threshold() -> None:
    """charged_credits 与预期成本偏差超阈值 → price_drift。

    阈值内不算差异，避免定价正常波动产生噪音。
    """
    raise NotImplementedError('reconciliation module not implemented this round')


# ---------------------------------------------------------------------------
# 聚合 & 报表
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aggregates_margin_by_model() -> None:
    """报表按 model 聚合毛利率 = (charged_credits 总和 - actual_cost 总和) / charged_credits 总和。"""
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_csv_export_streams_one_row_per_usage() -> None:
    """CSV 按 usage 维度，含 charged/actual/currency/diff_type。"""
    raise NotImplementedError('reconciliation module not implemented this round')


# ---------------------------------------------------------------------------
# 不变量
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reconciliation_is_read_only_does_not_write() -> None:
    """对账函数不应产生任何写副作用（不插账本、不改 usage 状态、不删行）。"""
    raise NotImplementedError('reconciliation module not implemented this round')


@pytest.mark.asyncio
async def test_handles_currency_mismatch_without_conversion() -> None:
    """billing_event 多币种时按 currency 分桶，不做汇率换算（只标记不合并）。"""
    raise NotImplementedError('reconciliation module not implemented this round')
