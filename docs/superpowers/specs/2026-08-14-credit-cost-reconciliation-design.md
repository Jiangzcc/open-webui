# 设计：积分扣减 ↔ 厂商真实成本对账链路

> 状态：**本轮只给方案 + TDD 骨架，不写实现**。待评审通过后单独立项实施。
> 与 `docs/extensions/credits-operations.md`、`docs/extensions/extensions-operations.md` 配对。

## 问题

credits 扩展（`ext_credit_usage.charged_credits`，内部积分）与 provider_ops 扩展（`ext_provider_billing_event.actual_cost_total`，厂商 USD）**零代码关联**。两个扩展各自独立 `declarative_base` 和 session。无法回答：

- 这个月扣了用户多少积分，对应厂商多少 USD？
- 毛利率多少？有没有少收/多收？
- 哪些 usage 在厂商侧有计费事件但 credits 侧没记录（或反之）？

## 设计原则（对齐 CLAUDE.md 约束）

- **不修改 credits / provider_ops / creations 已有表结构或迁移历史**。
- 新增对象用独立 `ext_reconciliation_*` 命名空间和独立迁移链。
- 跨扩展只读查询，通过薄桥接调用各扩展已暴露的 repository 函数，不直接 JOIN 异构 metadata。
- 差异检测是只读视图，不产生写副作用（对账失败不影响计费主链路）。

## 关联键（实测数据流，非推测）

两条生成路径的关联键结构**不同**，必须分别处理。

### 视频路径（关联完整，双向）

```
VideoGenerationTask.id  ──(usage_id 列)──→  CreditUsage.id
VideoGenerationTask.id  ←──('video:'+task.id)──  CreditUsage.idempotency_key
VideoGenerationTask.id  ──(ProviderInvocation.task_id)──→  ProviderInvocation  ──(provider_request_id)──→  ProviderBillingEvent
```

- `VideoGenerationTask.usage_id` 列（models.py:238）存了 `CreditUsage.id`（service.py `_set_task_usage_id`）。
- `CreditUsage.idempotency_key = f'video:{task.id}'`（billing.py:144）。
- **缺口**：当前 `run_video_task` 走 mock，**从不调用 `try_start_provider_invocation`**，所以视频侧 `ProviderInvocation` 行不存在。对账链路在视频侧目前断在 `task → invocation` 这一跳。这是 #4（视频执行体落地）要一起补的。

### 图片路径（关联间接，依赖 header 或 URL 反查）

```
ImageGenerationTask.id ──(idempotency_key 列, 仅当客户端发 Idempotency-Key header)── CreditUsage.idempotency_key
ImageGenerationTask.id ──(CreationMediaItem.batch_id)── CreationMediaItem ──(file_id)──→ CreditUsage.result_snapshot.urls
ImageGenerationTask.id ──(ProviderInvocation.task_id = metadata['generation_task_id'])──→ ProviderInvocation ──(provider_request_id)──→ ProviderBillingEvent
```

- `ImageGenerationTask` **没有 `usage_id` 列**（models.py:194-208）。无法从 task 直接拿到 usage。
- 关键耦合点：creations router 用 `key = (header or uuid4())` 作为 task 的 `idempotency_key` 列；`bill_image_call` 读**同一个 request 对象**的 `Idempotency-Key` header 作为 usage 的 idempotency_key（`_header_idempotency_key`）。
  - **客户端发了 header** → 两者相等，可直接 JOIN `ImageGenerationTask.idempotency_key = CreditUsage.idempotency_key`。
  - **客户端没发 header** → task 用一个 uuid4，usage 用**另一个** uuid4，**彻底断开**。此时只能靠 `CreationMediaItem.batch_id = task.id` + `file_id ∈ result_snapshot.urls` 反查 usage。
- `ProviderInvocation.task_id` 由 `try_start_provider_invocation(task_id=metadata.get('generation_task_id'))` 写入（images.py:953/1445），所以图片侧 task → invocation 这跳是通的。

### 结论

| 关联跳 | 视频 | 图片（有 header） | 图片（无 header） |
| --- | --- | --- | --- |
| task ↔ usage | ✅ usage_id + idempotency_key | ✅ idempotency_key 相等 | ❌ 断，靠 batch_id+url 反查 |
| task ↔ invocation | ❌ mock 不写 invocation | ✅ task_id | ✅ task_id |
| invocation ↔ billing_event | ✅（落地后）provider_request_id | ✅ provider_request_id | ✅ provider_request_id |

## 方案：只读差异视图 + 报表

### 1. 新增 `reconciliation` 子模块（provider_ops 内，不独立扩展）

放在 `backend/open_webui/extensions/provider_ops/reconciliation.py`，复用 provider_ops 的 `declarative_base` 和 session，避免再开一个独立 metadata。

### 2. 关联解析函数（薄桥接，分媒体类型）

```python
async def resolve_usage_to_provider_cost(
    session: AsyncSession,  # provider_ops session
    *,
    media_kind: Literal['image', 'video'],
    task_id: str,
    credit_usage: CreditUsageSummary,  # 只读快照，跨 session 查来的
) -> ProviderCostLink | None:
    """把一条 CreditUsage 关联到对应的 ProviderBillingEvent 成本。

    image：优先 try idempotency_key JOIN；失败回退 batch_id+file_id 反查。
    video：用 task.usage_id / idempotency_key 直查（落地 #4 后 invocation 也存在）。
    返回 None 表示该 usage 在厂商侧无计费事件（→ missing_billing 差异）。
    """
```

### 3. 差异检测函数

```python
async def detect_usage_cost_discrepancies(
    session: AsyncSession,
    *,
    since_ms: int,
    until_ms: int,
) -> list[UsageCostDiscrepancy]:
    """只读：credits usage 的 charged_credits vs provider billing event 的 actual_cost_total。

    返回三类差异行：
    - missing_billing：credits 扣了但厂商侧无 billing_event（账单未同步？或 mock 路径）
    - missing_usage：厂商 billing_event 有但 credits 无对应 usage（最严重，需即时告警）
    - price_drift：双方都有但 charged_credits 与预期成本偏差超阈值
    """
```

### 4. 管理员对账报表端点

```
GET /api/v1/provider-ops/admin/reconciliation
  ?since_ms=&until_ms=&resource_id=&user_id=&media_kind=&page=
```

返回按时间/模型/用户聚合的差异行 + 汇总毛利率。仅 admin。

### 5. CSV 导出

```
GET /api/v1/provider-ops/admin/reconciliation/export
```

流式 CSV，按 usage 维度一行：usage_id / user_id / media_kind / task_id / charged_credits / actual_cost / currency / diff_type。

### 6. 差异告警

复用 OTel metrics：新增 `webui.reconciliation.discrepancy` counter（标签 `type=missing_billing|missing_usage|price_drift`）。`missing_usage` 即时记日志告警；`price_drift` 按百分比阈值。**不自动调价**（调价需人工确认，避免误调导致系统性亏损）。

## 不做什么

- **不改 credits/provider_ops/creations 表结构**。
- **不做自动调价**：定价变更需管理员前台 `POST /credits/admin/prices`。
- **不做实时对账**：fal 账单次日才出，实时无意义。复用 `provider-ops-sync` worker（#5 已实现每日同步），对账在同步后触发。
- **不做跨扩展事务**：credits usage 与 provider billing_event 的写入本就解耦（设计如此），强行事务化会破坏 fail-closed 语义。
- **不做汇率换算**：billing_event 多币种时按 currency 分桶，只标记不合并。

## TDD 骨架

测试文件：`backend/open_webui/extensions/provider_ops/tests/test_reconciliation.py`（本轮只建骨架 + 接口签名，不写实现）。

```python
# backend/open_webui/extensions/provider_ops/tests/test_reconciliation.py
"""积分↔厂商成本对账链路 TDD 骨架。

本轮只落测试桩与接口签名；实现待评审通过后单独立项。
图片/视频关联键结构不同（见设计文档），故按媒体类型分别覆盖。
"""
from __future__ import annotations

import pytest


# ---- 关联解析 ----

@pytest.mark.asyncio
async def test_video_usage_links_to_billing_via_usage_id() -> None:
    """视频：CreditUsage.id == VideoGenerationTask.usage_id，可直查到 ProviderBillingEvent。"""
    ...


@pytest.mark.asyncio
async def test_image_usage_with_header_links_via_idempotency_key() -> None:
    """图片（客户端发了 Idempotency-Key）：task.idempotency_key == usage.idempotency_key，直接 JOIN。"""
    ...


@pytest.mark.asyncio
async def test_image_usage_without_header_falls_back_to_batch_id_and_file_id() -> None:
    """图片（无 header）：idempotency_key 断开，回退 batch_id+file_id（result_snapshot.urls）反查。"""
    ...


@pytest.mark.asyncio
async def test_usage_without_provider_invocation_returns_missing_billing() -> None:
    """视频 mock 路径不写 invocation → resolve 返回 None → missing_billing 差异（落地 #4 前的预期行为）。"""
    ...


# ---- 差异检测 ----

@pytest.mark.asyncio
async def test_no_discrepancy_when_usage_and_billing_match() -> None:
    """usage 与 billing_event 一一对应且金额匹配时，差异列表为空。"""
    ...


@pytest.mark.asyncio
async def test_flags_usage_without_billing_event() -> None:
    """credits 扣了但厂商侧无 billing_event → missing_billing 差异行。"""
    ...


@pytest.mark.asyncio
async def test_flags_billing_event_without_usage() -> None:
    """厂商有计费但 credits 无 usage → missing_usage 差异行（最严重，需即时告警）。"""
    ...


@pytest.mark.asyncio
async def test_flags_price_drift_when_charged_vs_cost_exceeds_threshold() -> None:
    """charged_credits 与预期成本偏差超阈值 → price_drift（阈值内不算差异，避免噪音）。"""
    ...


# ---- 聚合 & 报表 ----

@pytest.mark.asyncio
async def test_aggregates_margin_by_model() -> None:
    """报表按 model 聚合毛利率 = (charged_credits 总和 - actual_cost 总和) / charged_credits 总和。"""
    ...


@pytest.mark.asyncio
async def test_csv_export_streams_one_row_per_usage() -> None:
    """CSV 按 usage 维度，含 charged/actual/currency/diff_type。"""
    ...


# ---- 不变量 ----

@pytest.mark.asyncio
async def test_reconciliation_is_read_only_does_not_write() -> None:
    """对账函数不应产生任何写副作用（不插账本、不改 usage 状态、不删行）。"""
    ...


@pytest.mark.asyncio
async def test_handles_currency_mismatch_without_conversion() -> None:
    """billing_event 多币种时按 currency 分桶，不做汇率换算（只标记不合并）。"""
    ...
```

## 实施依赖

- **#4（视频执行体）必须先落地或并行**：视频对账的 `task → invocation` 跳依赖 `run_video_task` 真正调用 `try_start_provider_invocation`，当前 mock 路径完全不写 invocation，视频对账无从做起。
- **#5（厂商计费同步自动化）已落地**：对账复用其每日 sync 产出的 `ProviderBillingEvent`，无需自建同步。
- 需确认 `bill_image_call` 终态事务里能拿到 fal 的 `provider_request_id`（fal 返回体里有，`run_fal_queue` 已在 `observer.submitted` 里取 `request_id`，见 service.py:98）。即 invocation 已有 provider_request_id，对账可直接用，**无需改 creations 表结构**——这修正了早期设计中"需给 CreationMediaItem 加 provider_request_id 字段"的判断。

## 待评审问题

1. 图片无 header 路径的 `batch_id + file_id` 反查是否要固化成一张旁挂关联表，避免每次对账都解析 URL？（当前设计倾向先靠反查，量大了再说）
2. 差异告警阈值：`missing_usage` 即时告警无异议；`price_drift` 百分比阈值定多少（±5%？±10%）？
3. CSV 导出权限：仅 admin 无异议，但要不要加审计日志记录谁导出过？
4. 是否需要历史对账快照表（固化每日差异，而非每次实时算）？——倾向先实时算，慢了再加固化。

---

**本轮产出到此为止。实现待评审通过后单独立项。**
