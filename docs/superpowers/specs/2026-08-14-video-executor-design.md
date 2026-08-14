# 设计：视频首尾帧 / 图生视频执行体落地（方案骨架，不实现）

> 状态：**本轮只给方案 + TDD 骨架，不落地真实 fal 视频集成**。用户明确指示"#1 做，#4 给方案骨架不落地"。
> 配对：`docs/extensions/extensions-operations.md`（视频扩展运维手册）、`docs/superpowers/specs/2026-08-14-credit-cost-reconciliation-design.md`（对账链路，依赖本任务）。

## 现状（实测，非推测）

`run_video_task`（`videos/service.py:464`）当前：

1. `_set_task_state(running)` + 发 SSE。
2. `begin_video_usage` 预扣积分（`idempotency_key=f'video:{task.id}'`）。
3. `mark_video_usage_invoking`。
4. **`await asyncio.sleep(1.2)` 模拟推理耗时**。
5. `_finalize_mock_video`：Pexels 随机片段 → fallback 静态 `welcome.mp4`。
6. 终态事务：`mark_usage_succeeded_in_session` + 写 `CreationMediaItem(batch_id=task.id)`。

**关键缺口**：

- **不调用 `try_start_provider_invocation`** → 没有写 `ProviderInvocation` 行 → 对账链路（#3）在视频侧的 `task → invocation` 跳是断的。图片侧 `images.py:953/1445` 有调用，视频侧没有。
- **不调用真实 fal queue** → 用 `asyncio.sleep` + Pexels mock。`build_video_provider_payload` 已经算出完整的 `provider_payload`（含 `start_image_url`/`end_image_url`/`video_url` 字段），但 `run_video_task` **丢弃了它**（`create_video_task` 调 `build_video_provider_payload` 只为校验，返回的 `_provider_payload` 被丢弃）。
- **submission.assets 无人消费**：`build_video_provider_payload` 校验了 asset role/count/mime/size（`catalog.py:366-378`），但运行期没人把 `file_id` 转成 fal 要的 `*_url`。

## 设计原则（对齐 CLAUDE.md 约束）

- **不改视频 schema、不改 `run_video_task` 主链路结构**（预付→调用→终态事务）。
- 真实执行体通过**可插拔接口**注入，mock 路径保留为默认（开发环境隔离），生产路径由配置开关切。
- 新增代码限在 `backend/open_webui/extensions/videos/` 内（二开目录）。
- 不引入新依赖（`run_fal_queue` 的 aiohttp 会话池、`try_start_provider_invocation` 都已存在）。

## 方案：可插拔视频执行接口

### 1. 抽象执行接口（videos 新增 `executor.py`）

```python
# backend/open_webui/extensions/videos/executor.py
class VideoExecutor(Protocol):
    """视频生成的可插拔执行体。

    实现负责：调用真实厂商（默认 fal queue）→ 把厂商返回的远端视频/海报 URL
    转成本地文件（走上游 upload_file_handler，复用图片侧的文件落地路径）
    → 返回 VideoTaskResult（creation_id 在终态事务里由调用方写，这里只回 file_id/url）。
    """

    async def invoke(
        self,
        request: Request,
        user: object,
        task: VideoTaskResponse,
        definition: FalVideoModelDefinition,
        provider_payload: dict[str, object],
    ) -> VideoTaskResult:
        """真实调用厂商并落地结果。抛 VideoExecutionError(code) 给 run_video_task 兜底退费。"""
        ...
```

`run_video_task` 改为：

```python
# 伪代码（不在本轮实现）
executor = resolve_video_executor(request.app)  # mock 或 real
result = await executor.invoke(request, user, task, definition, provider_payload)
# 终态事务不变：mark_usage_succeeded_in_session([result['url']]) + 写 CreationMediaItem
```

### 2. asset file_id → provider *_url 的桥接

fal 的 image-to-video / video-to-video 需要 `start_image_url` / `end_image_url` / `video_url`，这些是**公网可访问 URL**。本地 `file_id` 要先转成内部 `/api/v1/files/{id}/content` URL（`get_file_content_by_id` 的 `url_path_for`，图片侧 `service.py:381` 已用）。

```python
def _asset_url(request: Request, file_id: str) -> str:
    return str(request.app.url_path_for('get_file_content_by_id', id=file_id))
```

`build_video_provider_payload` 目前不注入 asset URL（asset 字段名在 `definition.asset_inputs[*].field`，如 `start_image_url`）。执行体在拿到 `provider_payload` 后补：

```python
for asset in task.assets:
    constraint = next(a for a in definition.asset_inputs if a.role == asset.role)
    provider_payload[constraint.field] = _asset_url(request, asset.file_id)
```

> 注意：fal queue 要求公网可达。本地 `/api/v1/files/.../content` 需鉴权（`get_verified_user`）。若 fal 回拉需要匿名公网 URL，要走上游 storage 的预签名 / 直链逻辑——**这是落地前的待确认点**（见下）。

### 3. provider invocation 落地（补 #3 对账缺口）

`run_video_task` 在调用真实 fal 前补：

```python
observer = await try_start_provider_invocation(
    task_id=task.id,                # ← 视频侧补这一跳，对账链路闭合
    user_id=str(user.id),
    media_kind='video',
    provider='fal',
    provider_model_id=definition.id,   # 内部 fal-ai/... 路由
    payload=provider_payload,
)
res = await run_fal_queue(definition.id, provider_payload, api_key, base_url, observer=observer)
```

`run_fal_queue`（`utils/images/fal.py`）是图片/视频共用的 fal queue 客户端，`observer` 已抽象为 `ProviderInvocationObserver` Protocol，视频直接复用。`observer.submitted` 会把 fal 的 `request_id` 写进 `ProviderInvocation.provider_request_id` → 对账链路的 `task → invocation → billing_event` 完整闭合。

### 4. 视频结果提取（复用/扩展 `extract_*_urls`）

fal 视频返回结构是 `{"video": {"url": "..."}}` 或 `{"url": "..."}`（`output_field` 默认 `'video'`）。需要：

```python
def extract_fal_video_url(result: dict, output_field: str = 'video') -> str | None:
    """从 fal 视频结果取 mp4 URL。output_field 见 FalVideoModelDefinition.output_field。"""
    candidate = result.get(output_field)
    if isinstance(candidate, dict):
        return candidate.get('url') if isinstance(candidate.get('url'), str) else None
    if isinstance(candidate, str):
        return candidate
    if isinstance(result.get('url'), str):
        return result['url']
    return None
```

### 5. 开关与默认值

- 配置项 `VIDEO_GENERATION_ENGINE`（或复用 `IMAGE_GENERATION_ENGINE == 'fal'` 语义）：决定走 mock 还是 real。
- **默认仍走 mock**（fail-safe）：未配置 fal key / 未显式开启 real 引擎时，`resolve_video_executor` 返回 mock executor，与现状行为一致，避免二开测试环境误扣费。
- 真实执行体的 fal key 复用 `config.FAL_API_KEY`（上游已有，不新增配置）。

## 不做什么

- **不真正落地 fal 视频调用**：本轮只到接口签名 + 测试桩。用户明确"#4 给方案骨架不落地"。
- **不改 `run_video_task` 现有终态事务/退费/SSE 逻辑**：这些已在 #1 完成。
- **不引入 fal Python SDK**：`run_fal_queue` 是裸 aiohttp queue 客户端，够用，不新增依赖。
- **不处理 fal webhook 回调**：当前用轮询 `status_url`（`run_fal_queue` 已实现），视频沿用，不引入 webhook 基建。

## 待确认点（落地前必须回答）

1. **fal 拉取本地 asset URL 的鉴权**：fal queue 服务端要下载 `start_image_url`，本地 `/api/v1/files/.../content` 需登录态。方案候选：(a) 用上游 storage 直链/预签名（需确认 storage provider 支持）；(b) 走一个短期签名 token 端点；(c) 把 asset 上传到 fal 的 storage（fal 有 `/storage/upload/upload`）再传 URL。**倾向 (c)**，与 fal 生态一致，但需新增上传调用——落地前需实测。
2. **视频 result 落地**：fal 返回的是远端 mp4 URL（有时效）。`_upload_mock_file` 当前处理本地 bytes，real 路径要先 `get_image_data(url)` 下载远端视频再走同样上传。`images.py` 的 `get_image_data` 是否支持 video/mp4 需确认（可能只校验图片 magic bytes）。
3. **海报图**：fal 视频结果通常不带 poster。real 路径要 `extract_poster_from_video`（`pexels_mock.py` 已有 pyav 实现）从首帧抽——可复用。
4. **超时**：`FAL_REQUEST_TIMEOUT_SECONDS=180` 对图片够，视频可能要几分钟。real 视频执行体需独立超时配置。

## TDD 骨架

测试文件：`backend/open_webui/extensions/videos/tests/test_executor.py`（本轮只建骨架 + 接口签名，不实现）。

```python
# backend/open_webui/extensions/videos/tests/test_executor.py
"""视频执行体 TDD 骨架。

本轮只落测试桩与接口签名；实现待评审通过后单独立项
（见 ``docs/superpowers/specs/2026-08-14-video-executor-design.md``）。
"""
from __future__ import annotations

import pytest


# ---- asset → provider URL 桥接 ----

def test_asset_url_built_from_file_id_via_url_path_for() -> None:
    """asset.file_id 经 url_path_for('get_file_content_by_id') 转成内部 URL。"""
    raise NotImplementedError('video executor not implemented this round')


def test_payload_injects_start_and_end_image_urls_for_image_to_video() -> None:
    """image-to-video：start_image/end_image 的 file_id 注入到 definition 声明的字段。"""
    raise NotImplementedError('video executor not implemented this round')


def test_payload_injects_source_video_url_for_video_to_video() -> None:
    """video-to-video：source_video 的 file_id 注入 video_url 字段。"""
    raise NotImplementedError('video executor not implemented this round')


# ---- provider invocation 落地（对账缺口闭合） ----

@pytest.mark.asyncio
async def test_real_executor_writes_provider_invocation_with_task_id() -> None:
    """真实执行体调用前 try_start_provider_invocation(task_id=task.id) → 对账 task↔invocation 跳闭合。"""
    raise NotImplementedError('video executor not implemented this round')


# ---- 视频结果提取 ----

def test_extract_fal_video_url_from_nested_video_object() -> None:
    """{'video': {'url': '...'}} → 取到 mp4 URL（output_field='video'）。"""
    raise NotImplementedError('video executor not implemented this round')


def test_extract_fal_video_url_falls_back_to_top_level_url() -> None:
    """无 video 键时回退 {'url': '...'}。"""
    raise NotImplementedError('video executor not implemented this round')


def test_extract_fal_video_url_returns_none_on_empty_result() -> None:
    """结果无 URL → None（调用方兜底走 video_generation_failed 退费）。"""
    raise NotImplementedError('video executor not implemented this round')


# ---- 开关与默认 mock ----

@pytest.mark.asyncio
async def test_resolve_executor_defaults_to_mock_without_fal_key() -> None:
    """未配置 fal key → resolve_video_executor 返回 mock executor（fail-safe，避免误扣费）。"""
    raise NotImplementedError('video executor not implemented this round')


@pytest.mark.asyncio
async def test_resolve_executor_returns_real_when_engine_enabled() -> None:
    """显式开启 real 引擎 + fal key 存在 → 返回 real executor。"""
    raise NotImplementedError('video executor not implemented this round')


# ---- 错误兜底 ----

@pytest.mark.asyncio
async def test_real_executor_failure_raises_video_execution_error_with_code() -> None:
    """真实调用失败 → 抛 VideoExecutionError(code)，run_video_task 走 mark_video_usage_failed 退费。"""
    raise NotImplementedError('video executor not implemented this round')


@pytest.mark.asyncio
async def test_cancel_propagates_to_fal_queue_run() -> None:
    """服务关停取消 worker → CancelledError 透传到 run_fal_queue，observer 记 failed。"""
    raise NotImplementedError('video executor not implemented this round')
```

## 实施依赖与顺序

1. **先做 #4 执行体**（真实 fal 调用 + `try_start_provider_invocation`）→ 视频侧 `ProviderInvocation` 行开始存在。
2. **再做 #3 对账**：视频对账的 `task → invocation` 跳依赖 #4 落地。当前 #3 骨架已标注此依赖（`test_video_usage_links_to_billing_via_usage_id` 注释说明）。
3. #5（厂商计费同步）已落地，提供 `ProviderBillingEvent` 数据源，#3/#4 都消费它。

## 待评审问题

1. asset URL 鉴权方案（待确认点 #1）选哪个？预签名 vs fal storage 上传。
2. 是否需要独立的 `VIDEO_GENERATION_ENGINE` 配置，还是复用 `IMAGE_GENERATION_ENGINE`？
3. 视频超时配置单独开还是复用 `FAL_REQUEST_TIMEOUT_SECONDS`？
4. 真实视频结果是否需要异步落库（fal queue 可能几分钟，SSE 期间前端已显示 running）——当前 SSE 已支持，无需额外基建。

---

**本轮产出到此为止。实现待评审通过后单独立项。**
