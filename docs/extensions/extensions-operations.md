# 二开扩展运维手册（Creations / Videos / Provider Ops / Model Ops）

> 本文档与 `docs/extensions/credits-operations.md` 配对，覆盖除积分以外的四个二开扩展的运行手册。积分系统请直接参考那份独立文档。

## 适用范围

本文覆盖以下四个二开扩展（全部位于 `backend/open_webui/extensions/`）：

| 扩展 | 职责 | 启动注册函数 |
| --- | --- | --- |
| `creations` | 图片/视频生成任务表、创作媒体项、发现页社区 | `initialize_creations_extension` |
| `videos` | 视频生成任务调度与执行（含 Pexels mock） | `initialize_videos_extension` |
| `provider_ops` | 厂商调用追踪、计费同步、对账遥测 | `initialize_provider_ops_extension` |
| `model_ops` | 模型运营态（上下架/可见/推荐/排序/标签/维护） | `initialize_model_ops_extension` |

四个扩展在 `main.py` 的 `lifespan` 中按固定顺序串行注册：`model_ops → provider_ops → credits → creations → videos`。顺序不可随意调整——`creations` 的计费依赖 `credits` 已就绪，`videos` 的任务表复用 `creations` 的 schema。

## 启动与关停生命周期

### 后台 worker

二开扩展注册了三类后台 asyncio 任务：

| 任务 | 位置 | 用途 | shutdown 行为 |
| --- | --- | --- | --- |
| `credit-usage-recovery` | `credits/registration.py` | 把卡在 `invoking` 的滞留 usage 标 `unknown` 进对账队列 | cancel + await |
| `provider-ops-sync` | `provider_ops/registration.py` | 每 24h 自动同步 fal 平台计费数据（pricing/requests/billing_events/usage/analytics，窗口 48h） | cancel + await |
| `creation_generation_tasks` / `video_generation_tasks` | 进程内 dict/set，非独立 worker | 持有进行中的生成 asyncio.Task | shutdown 时 cancel + gather |

### 关停顺序

`main.py` shutdown 按以下顺序取消并等待：`videos → creations → credits → provider_ops`。`model_ops` 无 worker，不需要 shutdown。

**已知技术债（待后续处理）**：上游的 `periodic_usage_pool_cleanup` / `periodic_session_pool_cleanup` / `scheduler_worker_loop` 三个 fire-and-forget 任务在 `main.py:390-395` 创建后未存入 `app.state`，shutdown 时未 cancel/await，进程退出会有 pending task 警告。这是上游行为，二开暂未侵入修复。

## 迁移失败语义

- **二开扩展**：迁移失败 `raise RuntimeError`，启动中止（fail-closed）。
- **上游 `config.run_migrations()`**：迁移失败仅 `log.exception` 后继续（fail-open）。
- **结论**：二开扩展迁移挂了应用不会起来；上游迁移挂了应用可能带伤启动。两者语义不一致是已知差异，二开暂未改上游文件。

## Creations 扩展

### 任务生命周期（图片）

1. `POST /api/v1/creations/generation-tasks` → 幂等落库 `ImageGenerationTask`（状态 `queued`）+ `schedule_generation_task` 创建 asyncio 任务，HTTP 立即 202 返回。
2. `run_generation_task` 复用 `image_generations/image_edits(..., 'direct', ...)`，计费走 `bill_image_call` 的预扣→invoking→终态事务。
3. 终态写入后通过事件总线 `publish_generation_event` 广播 SSE（见下）。
4. 服务重启时 `fail_incomplete_generation_tasks` 把 queued/running 批量改 `failed` + `error_code='server_restarted'`。

### 任务事件总线（SSE）

`creations/events.py` 提供进程内 `GenerationEventBus`：

- **端点**：`GET /api/v1/creations/generation-tasks/events`（SSE，`text/event-stream`）。
- **事件格式**：`data: {"kind":"image|video","task_id":"...","status":"...","user_id":"..."}`。
- **过滤**：按 `user_id` 过滤，只推该用户自己的任务事件。
- **心跳**：每 15s 无事件发 `: keepalive` 注释帧，防代理空闲断连。
- **慢消费者**：订阅者队列有界（128），满时丢弃事件不阻塞生产者；客户端断线重连后会拉一次 list 补齐终态。
- **多 worker 限制**：当前是进程内广播，多 worker 部署下跨进程不互通。生产多实例需接入 Redis pub/sub（`publish_generation_event` 已抽象为可替换后端）。

### 发现页

`discovery_service.py` 提供 4 条 feed：`featured / latest / popular / favorites`，keyset 游标分页。`publish_creation` / `withdraw_creation` 控制发布与撤回，`set_reaction` 处理点赞/收藏。管理员可通过 `update_discovery_operation` 改 category/featured/featured_rank，但不能 hide（hide 只在 CreationDetailsModal 详情里反向操作）。

## Videos 扩展

### 执行体是 mock

`run_video_task` 当前固定 `await asyncio.sleep(1.2)` 后走 `_finalize_mock_video`（Pexels 随机片段或 `static/assets/welcome.mp4`）。**没有真实 fal video 调用**。生产环境若误开 `PEXELS_API_KEY` 或 welcome.mp4 存在，用户提交付费视频任务会得到 mock 内容并扣 credit。

**运维要点**：上线前确认 `PEXELS_API_KEY` 未配置、或确保视频生成入口处于未上线状态。

### 限流与并发槽

`videos/limits.py`（二开新增，镜像 `images/limits.py`）：

- 提交速率：每用户 4 次/60s（Redis 滚窗 + 内存兜底），超限 429。
- 并发槽：每用户 1 个进行中任务（`VIDEO_GENERATION_MAX_CONCURRENT_PER_USER`），超限 429。
- **多 worker 限制**：并发槽是进程内 dict，多 worker 部署下每进程独立计数，实际并发上限 = 配置值 × worker 数。生产多实例需 Redis 化（见下「已知限制」）。

### 配额前置校验

`submit_video_task` 在调度前调用 `quote_video_usage` 只读预检余额：余额不足或未配置定价直接 402，不入库不调度。`run_video_task` 内仍会 `begin_video_usage` 正式扣费（前置校验与正式扣费之间有 TOCTOU 窗口，但扣费本身有乐观并发防护兜底）。

### 取消

视频任务不提供用户取消接口。仅在服务关停时取消进程内 worker；`run_video_task` 的 `except CancelledError` 分支兜底写 `failed` + 退预扣积分（`mark_video_usage_failed` 已传 `restore_prepaid=True`）。

### 失败退费

视频失败默认退预扣（对齐图片 cancel 路径）。`mark_video_usage_failed` 在 `videos/billing.py` 调用 `mark_usage_failed(..., restore_prepaid=True)`。

## Provider Ops 扩展

### 厂商计费同步自动化

`provider_ops/registration.py` 注册 `provider-ops-sync` 后台 worker：

- **周期**：每 24h 一次，首次延迟一个间隔（避开启动高峰）。
- **窗口**：48h（fal 账单通常次日才出）。
- **失败**：`sync_fal_platform` 已持久化到 `ProviderSyncRun`（status='failed' + error_code），worker 只记日志，不重试队列（避免引入复杂调度依赖）。
- **手动触发**：`POST /api/v1/provider-ops/admin/providers/fal/sync` 仍可随时手动跑。

### 只读 + 同步

provider_ops 全部 GET + 一个 POST sync，无 PATCH/DELETE。无法手动修正/删除错误账单事件或请求记录，数据只增不减（清理需直连 DB）。

### 仅 fal 一家

`platform_sync.py` 的 `_PROVIDER='fal'`、前端 `ProviderOperations.svelte` 的 `<option value="fal">` 硬编码。接入第二厂商需改后端常量 + 前端写死选项。

## Model Ops 扩展

### 管理范围

`model_ops` 只管 6 个运营字段：`visible / enabled / recommended / sort_order / tags / maintenance_message`。

- **不管定价**：定价完全在 credits 扩展，管理员要在两个后台切换。
- **不管默认模型**：默认模型仍由 `IMAGE_GENERATION_MODEL` 等环境/配置项决定。
- **无审计历史表**：只有 `updated_by_id`/`updated_by_name_snapshot` 快照（覆盖前次操作者），无变更历史表。
- **无 DELETE**：catalog 移除模型后残留 `ImageModelOperation` 行无法 API 清理（需直连 DB）。

## 已知限制与技术债

1. **SSE 跨进程不互通**：`GenerationEventBus` 是进程内广播，多 worker 部署下客户端连到不同 worker 收不到彼此的事件。生产多实例需接 Redis pub/sub。
2. **并发槽非全局**：`videos/limits.py` 和 `images/limits.py` 的 `_active_by_user` 是进程内 dict，多 worker 下每进程独立计数。
3. **报价缓存跨进程**：已改用 Redis（`credits/quote_cache.py`），Redis 不可用时降级进程内 dict——降级期间多 worker 不共享。
4. **视频 mock 与生产路径混淆风险**：见上文「执行体是 mock」。
5. **provider_ops 无 DELETE/PATCH**：账单/请求记录无法清理。
6. **三个上游后台任务 shutdown 未 cancel**：见上文「启动与关停生命周期」。

## 故障排查速查

| 症状 | 排查方向 |
| --- | --- |
| 视频生成总是返回固定片段 | 确认是否走了 mock 路径；检查 `PEXELS_API_KEY` 与 `welcome.mp4` |
| 视频任务失败但未退积分 | 检查 `mark_video_usage_failed` 是否传 `restore_prepaid=True`；查 `ext_credit_usage` 状态 |
| 生成任务状态不更新 | 检查 SSE 是否连上 `/generation-tasks/events`；降级为轮询兜底 |
| 厂商计费数据不刷新 | 检查 `provider-ops-sync` worker 是否在跑；手动 `POST /admin/providers/fal/sync` |
| 扩展迁移失败启动中止 | 看日志 `RuntimeError: ... migration validation failed`；确认 `ext_*_schema_version` 表 |
| 运营页慢 | operations 页已懒加载，首屏只加载 discovery；其余 tab 按需 `import()` |

## 相关文档

- 积分系统运维：`docs/extensions/credits-operations.md`
- 上游补丁清单：`docs/extensions/credits-upstream-patch-manifest.md`
- 设计与计划文档：`docs/superpowers/specs/` 与 `docs/superpowers/plans/`
