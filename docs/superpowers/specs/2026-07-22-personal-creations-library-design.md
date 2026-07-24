# 个人作品库（Personal Creations Library）设计

- 状态：修订草案（待用户评审）
- 日期：2026-07-22
- 范围：Spec A —— 个人作品库。社区广场作为独立 Spec B，不在本期实现或建模。
- 受众：熟悉本项目 Open WebUI 二开前后端的开发者。

## 1. 背景、目标与非目标

当前 `/images` 页只把本次页面会话生成的图片保存在 `Images.svelte` 的局部数组中；刷新后页面记录消失。与此同时，后端已经把生产路径生成的图片写入上游 file 存储，但缺少一个按用户组织、可备注和可软删除的作品索引。

本期目标：

1. 所有通过当前统一图片服务成功产生并新落盘的图片，自动进入所属用户的个人作品库；覆盖 `/images` 直调、聊天图片生成/编辑和内置图片工具。
2. 图生图额外保存实际送入 provider 的有序参考图不可变快照，并在作品详情中呈现“参考图 → 提示词/参数 → 结果图”的创作上下文。
3. 普通用户在现有 `/images` 路由内通过「新建｜作品库」双视图浏览自己的作品；管理员在同一作品库视图内可切换「我的作品｜全部作品」，查看所有账号的作品及完整详情。
4. 支持稳定的游标分页、预览、下载、修改备注与从作品库移除。
5. 结果图和参考图字节都复用上游 file/Storage，不写入扩展表、不修改上游表结构，将上游代码改动限制为薄桥接点。

明确不在本期范围内：

- 社区广场、公开发布、点赞、评论、浏览量和 feed 排序；这些属于后续 Spec B。
- 视频、音频的采集与展示。本期数据模型虽然保留 `kind`，数据库约束仍只允许 `image`。
- 上线前历史图片的自动回填。需求已确认作品库从本功能启用后开始记录；旧 file 记录没有稳定、统一的生成来源标记，无法无误区分生成图片与普通上传。空态或说明文案必须明确这一时间边界。
- 跳转回原对话、按模型或 prompt 搜索/筛选、批量管理、相册分组。
- 软删除只从作品库移除索引，不删除上游 file；一期不提供回收站、恢复或永久清理入口。UI 操作文案使用“从作品库移除”，避免让用户误以为聊天中的图片或磁盘文件会被销毁。
- 新的作品条数配额。图片字节仍服从上游 file 存储和部署侧容量策略。

## 2. 设计原则与已核实事实

### 2.1 二开边界

1. 新能力位于 `backend/open_webui/extensions/creations/`，与 `extensions/credits` 并列；不向任何上游表增加字段。
2. 不新增侧栏项目，也不改变 `pinnedMenuItems` 的注册、排序或迁移机制；继续复用既有 `/images` 项，但将它的可见条件改为所有 verified user 可见。管理员的全局作品能力位于该页面的作品库视图内，不新增独立后台路由。
3. `Images.svelte` 只增加视图切换和作品库容器；现有模型选择、积分报价、图片生成、响应式排版和 composer 行为保持不变，但 `/images` 页不再用图片功能开关或 `features.image_generation` 权限阻止 verified user 进入和提交。聊天自动生图与 builtin 图片工具保留现有开关和权限策略。
4. 新表统一使用 `ext_creation_` 前缀。

### 2.2 当前源码事实

1. **生产路径的生成结果已写入上游 file。** `upload_image` 把供应商返回的 base64/URL 转为字节，调用 `upload_file_handler(..., process=False)`，获得 `file_item` 后返回 `/api/v1/files/{id}/content`。file 记录包含 owner、MIME、大小和创建时间，字节由现有 Storage 实现管理。
2. **HTTP 路由不是唯一入口。** `/generations` 与 `/edit` 分别调用 `image_generations` / `image_edits`；聊天 middleware 和内置图片工具也直接调用这两个内部函数。因此把记录逻辑只放在 HTTP wrapper 会漏收聊天和工具产物。
3. **真正的新产物汇聚点是 `upload_image`。** 除本地 FAL mock 外，各生产引擎每产生一张新图片都在这里取得明确的 `file_item.id`。应直接使用该 ID，不从返回 URL 反向解析。
4. **积分层已有幂等重放。** `bill_image_call` 对成功请求会保存结果 URL；相同幂等键重试时直接返回旧 URL，不再次调用 provider 和 `upload_image`，因此不会重复入库。
5. **file 内容端点已有鉴权。** `/api/v1/files/{id}/content` 允许 file owner、管理员或被授予读取权限的用户访问。作品 API 必须另外实施角色和对象边界：普通用户只能查询自己的台账行；管理员可以读取所有用户的可见作品和详情，但修改备注与移除仍仅允许作品 owner。
6. **`ImagePreview.svelte` 只负责预览、缩放、关闭和下载。** caption 编辑与软删除应由作品库自己的 UI 承担。
7. **credits 是扩展工程样板。** 它使用独立 declarative base、独立 Alembic 版本表、上游 head 前置校验、多 worker 迁移锁，以及 `main.py` lifespan 初始化。
8. **当前 `/images` 权限与目标不一致。** `Sidebar.svelte`、`UserMenu.svelte` 和 `Images.svelte` 当前都会检查图片功能开关或 `features.image_generation` 权限；HTTP wrapper 与积分 `_authorize_image_call` 也执行相同闸口。需求已确认：所有 verified user（角色为 `user` 或 `admin`，不含 `pending`）均可进入 `/images` 的作品库，并可通过 `POST /api/v1/images/generations`、`POST /api/v1/images/edit` 直接端点生成/编辑，不受图片功能开关和用户生成功能权限控制。服务端无法安全区分页面请求和同一身份发起的直接 API 请求，因此上述端点本身就是授权边界。聊天自动生图与 builtin 图片工具继续遵循现有策略；后端授权必须依据服务端生成的可信调用渠道区分，不能接受客户端伪造 channel。

## 3. 架构与模块边界

```text
展示层  src/lib/components/images/CreationsLibrary.svelte
        作品网格、加载/空态/失败态、游标加载、预览与详情入口

详情层  src/lib/components/images/CreationDetailsModal.svelte
        按需加载单项详情、caption 编辑、折叠 prompt/参数、从作品库移除

编织层  src/lib/components/images/Images.svelte
        持有 generate/library 视图状态；保留现有生成状态；按视图显示正文和 composer

API 层  src/lib/apis/creations/index.ts
        listCreations / getCreation / updateCreation / deleteCreation
        listAdminCreations / getAdminCreation（管理员只读）

扩展层  backend/open_webui/extensions/creations/
        db.py            CreationBase 与 creation_session
        models.py        CreationMediaItem
        schemas.py       API DTO 与游标结构
        service.py       幂等记录、列表、更新、软删除
        router.py        /api/v1/creations/media
        registration.py  迁移与 schema 校验
        migrations/      独立 Alembic 链

薄桥接  backend/open_webui/routers/images.py
        保留 upload_image 返回的 file_item；共享批次 finalizer 在公开返回前落库

计费编排  backend/open_webui/extensions/credits/image_billing.py
        真实调用强制接收 finalize 回调；报价不经过该函数；同一事务提交作品和 usage 成功终态

挂载点  backend/open_webui/main.py
        初始化扩展并 include_router；扩展无后台任务，无需 shutdown hook
```

依赖方向保持单向：`Images.svelte → CreationsLibrary → API`，后端图片路由只依赖 creations 的窄服务接口；creations 扩展可借用上游 DB/session 和 file 查询能力，但 file 模块不反向依赖 creations。

## 4. 数据模型

### 4.1 单表决策与 `ext_creation_media_item`

需求已确认一期保持单表：每张图片一行，并在多图批次中重复保存 prompt、模型与参数快照。这样个人列表和详情无需 JOIN，迁移与服务更直接；代价是批量图片会重复大文本。`batch_id` 仍用于标识共享请求，未来只有在真实数据量证明重复存储成为问题时，才迁移拆分 `ext_creation_batch`，一期不预先增加第二张表。

字段如下：

| 字段 | 类型 | 约束 / 默认 | 说明 |
|---|---|---|---|
| `id` | `String(128)` | PK | 作品 ID，UUID 字符串 |
| `user_id` | `String(128)` | NOT NULL | 所属用户；普通用户查询边界，也是管理员全局列表的 owner 标识 |
| `kind` | `String(16)` | NOT NULL，CHECK `IN ('image')` | 本期恒为 `image`；不承诺未来新增媒介无需迁移 |
| `file_id` | `String(128)` | NOT NULL，UNIQUE | 上游 file 的应用层引用，也是幂等键；不建立跨域物理 FK |
| `caption` | `String(1000)` | NULLABLE | 用户备注；trim 后空串归一为 NULL |
| `prompt` | `Text` | NOT NULL | 经现有 100,000 UTF-8 bytes 上限验证并 trim 后的提示词；仅作品 owner 和管理员全局详情可见 |
| `negative_prompt` | `Text` | NULLABLE | 原始反向提示词 |
| `model_id` | `String(256)` | NULLABLE | 稳定公开模型 ID；长度对齐现有模型输入上限，不得保存/返回隐藏的 FAL 内部路由 ID |
| `model_name_snapshot` | `String(256)` | NULLABLE | 生成时显示名快照；无法可靠解析时为 NULL |
| `task` | `String(32)` | NOT NULL，CHECK | `text-to-image` 或 `image-to-image` |
| `params_json` | `JSONField` | NULLABLE | 规范化参数快照；见 §4.2 |
| `reference_file_ids_json` | `JSONField` | NULLABLE | 图生图实际输入的有序参考图快照 file ID 列表；文生图为 NULL，见 §4.3 |
| `source` | `String(16)` | NOT NULL，CHECK | `web`、`api`、`chat` 或 `tool` |
| `batch_id` | `String(128)` | NOT NULL | 一次 provider 调用内多图共享；一期不折叠展示 |
| `soft_deleted` | `Boolean` | NOT NULL，server default false | 从个人作品库移除，不影响上游 file |
| `created_at` | `BigInteger` | NOT NULL | 上游 `file_item.created_at` 的秒级 epoch；仅缺失时回退当前时间 |
| `updated_at` | `BigInteger` | NOT NULL | 秒级 epoch |

约束与索引：

- `UniqueConstraint('file_id', name='uq_ext_creation_media_file')`：同一上游结果文件最多一条作品记录。冲突时只有现有行的 `user_id`、`batch_id`、`task`、有序 `reference_file_ids_json` 等不可变身份与本次 context 全部一致，才按幂等成功处理；任一不一致都必须回滚并记录高优先级错误，不能静默 `DO NOTHING`。
- `Index('ix_ext_creation_media_user_visible_created', 'user_id', 'soft_deleted', 'created_at', 'id')`：个人列表与管理员按 owner 筛选的主查询路径。
- `Index('ix_ext_creation_media_visible_created', 'soft_deleted', 'created_at', 'id')`：管理员全部作品的稳定游标查询路径；没有它时全局列表无法利用以 `user_id` 开头的个人索引。
- `Index('ix_ext_creation_media_batch', 'batch_id')`：调试和未来批次操作。
- `ck_ext_creation_media_kind`、`ck_ext_creation_media_task`、`ck_ext_creation_media_source`：枚举 CHECK。

### 4.2 规范化请求参数快照

`params_json` 只保存当前 Pydantic 表单已经接收、经现有大小边界验证、非敏感且可能影响生成结果的字段。键名统一为公开请求语义，只写非 NULL 值：

```json
{
  "size": "1024x1024",
  "resolution": "1K",
  "aspect_ratio": "1:1",
  "quality": "low",
  "image_count": 2,
  "steps": 20,
  "seed": 123,
  "output_format": "png",
  "background": "auto",
  "system_prompt": "...",
  "sync_mode": true,
  "safety_tolerance": "6",
  "limit_generations": false,
  "enable_web_search": false,
  "thinking_level": "minimal",
  "enable_safety_checker": false,
  "enable_prompt_expansion": false,
  "acceleration": "regular",
  "input_fidelity": "high"
}
```

`n` 统一重命名为 `image_count`；这些值表达请求快照，不声称是供应商最终采用或返回的参数。空 `negative_prompt` 在独立列中归一为 NULL，不在 JSON 重复保存。

不把 provider payload 整体复制进作品表，尤其不得保存 API key、Authorization header、参考图原始 `image`、`mask_url` / `mask_image_url`（可能为 data URL）、provider 原始响应或隐藏的内部模型 ID。未知字段默认丢弃，而不是自动透传。

### 4.3 图生图参考图快照

图生图保存实际送入 provider 的参考图字节快照，而不是请求中不稳定的 data URL、外部 URL 或裸 file ID。当前 credits adapter 已在 `_references` 中依次读取每张输入图，完成访问权限、SSRF、MIME、magic bytes、单图/总大小和数量校验，并把它们规范化为 `PreparedImageCall.provider_input.image` 中的有序 data URL，同时将 hash 写入 billing snapshot。真实调用的 finalizer 必须从这组已准备的 provider data URL 在内存中解码 `bytes + mime_type`、与对应 hash 复核后创建快照；不得重新读取原始外部 URL 或请求 file。报价路径虽执行同样的准备与 hash 计算，但没有 finalizer，因而不写 file。

真实 provider 成功后、终态作品事务开始前，将每个受验证参考图字节通过现有 `upload_file_handler(..., process=False)` 保存为当前用户拥有的独立 file，文件 metadata 只带低敏感用途标记（例如 `creation_reference=true`），不得复制 prompt、provider payload 或原始 URL。保存后形成：

```python
CapturedReferenceResult(
    file_id=...,
    file_user_id=...,
    file_created_at=...,
    mime_type=...,
    sha256=...,
    position=...,
)
```

`reference_file_ids_json` 只保存按 `position` 排序的内部 file ID 数组，例如 `['id-1', 'id-2']`；文生图为 NULL。数组必须满足当前 `MAX_IMAGE_REFERENCES` 上限、元素是非空且不重复的 file ID，并在 finalizer 中再次确认每个 file owner 与作品 owner 一致。多结果批次的每一行重复这组小型 ID，与一期单表重复 prompt/参数的取舍一致；它不放入 `params_json`，因为这是媒体血缘而不是请求参数。

同一请求中的多个结果共享同一组参考 file；一次请求只上传一份快照。即使原请求已经引用当前用户拥有的上游 file，也仍创建不可变快照，防止原文件以后被替换、删除或权限改变而重写历史。参考图 file 不创建 ChatFile 关联，也不作为独立作品行展示。

失败语义：provider 失败时不保存参考快照；参考快照任一上传失败时不执行作品/usage 终态事务，请求按 §5.2 的终态基础设施失败处理。此前已上传的同批参考 file 可能成为孤儿，一期不擅自删除；指标和日志用于核查。重放已 succeeded 的同一幂等请求直接返回既有结果，不再次上传参考图。finalizer 幂等比较必须包含有序 `reference_file_ids_json`；不得因重放改写它。

### 4.4 刻意不存的字段

- `file_id`：保留在数据库和后端内部，但不返回给用户 DTO，避免前端依赖内部存储标识。
- `content_url`：它可由 `file_id` 和既有路由确定，持久化会在路由前缀变化后陈旧；由 API 响应层生成。
- `mime_type`：读取时取上游 file 的 `meta.content_type`。
- `width` / `height`：当前上传链路不计算尺寸，一期不为瀑布流额外解码图片。
- 原始参考图标识或位置：data URL、外部 URL 和请求中的裸 file ID 都不持久化；只保留 §4.3 创建的不可变快照 file ID。
- `published_post_id`：社区广场尚未设计，一对一字段会过早限制“一帖多图/一图多次发布”。Spec B 应通过独立关联表连接媒体与帖子。

## 5. 写入流程与一致性

### 5.1 规范化创建上下文

作品记录不能从各家 provider payload 猜测。现有 `image_adapter._prepare` 已经生成包含规范化请求、可信模型解析和计费 channel 的 `PreparedImageCall`，但该适配器同时被积分报价接口复用，因此不得让它依赖 creations 或在报价时构造作品对象。

仅在真实图片调用中，`images.py` 传给 `bill_image_call` 的 finalizer 根据以下输入构造中立的 `CreationCaptureContext`：原始且已验证的表单、`PreparedImageCall`、已授权用户，以及 `begin_image_usage` 创建的 `usage.id`。报价调用不传 finalizer，不接触任何作品逻辑。

```python
CreationCaptureContext(
    user_id=...,
    task='text-to-image' | 'image-to-image',
    source='web' | 'api' | 'chat' | 'tool',
    prompt=...,
    negative_prompt=...,
    public_model_id=...,
    model_name_snapshot=...,
    params=...,  # 白名单后的规范化参数
    references=...,  # 图生图时从 PreparedImageCall 的有序 provider data URL 解码并复核 hash；文生图为空
    batch_id=usage.id,
)
```

`public_model_id` 的来源必须是可信的模型注册表反向映射：FAL 的 `transport_model/resource_id` 先经 `public_fal_image_model_id` 转为公开 ID；其他引擎使用其已公开模型 ID。若某个内部 ID 没有公开映射，则保存 NULL，而不是把内部 ID 回退写入作品表。显示名从已登记的模型目录取快照；无法可靠解析时为 NULL。`source` 使用 `prepared.billing.channel`，`batch_id` 唯一使用本次 `usage.id`。

实现必须满足四条边界：

1. context 来自已校验、已规范化的请求，不来自供应商响应；图生图 reference 必须从 `PreparedImageCall.provider_input.image` 的有序规范化 data URL 解码，并与 billing snapshot 中相同顺序的 `reference_hashes` 复核，不能再次读取外部 URL 或原始 file。
2. context 只在真实生成调用的内存 finalizer 中构造和传递；报价路径可以完成现有参考图校验和 hash 计算，但不得构造作品 context、上传参考 file 或接触 creations service。
3. context 不得塞进会持久化到上游 `file.meta.data` 的通用 `metadata`，避免重复存储 prompt、参数和参考图。
4. `CreationCaptureContext` 位于 creations 的 schema 模块；`images.py` 可以同时编织 credits 与 creations，但两扩展服务不得相互反向导入。
5. reference bytes 只在真实调用的进程内短暂存在；参考快照上传完成后不得保留在 usage snapshot、日志或作品 JSON 中。

### 5.2 批次终态事务与提交顺序

provider 的单次调用可能返回多张图片。每张图片仍由 `upload_image` 写 file；`upload_image` 已返回 `(file_item, url)`。各 `_invoke_*` 分支在内部将它投影为不携带 ORM session 的稳定值对象：

```python
CapturedImageResult(
    url=...,
    file_id=...,
    file_user_id=...,
    file_created_at=...,
    mime_type=...,
)
```

真实 provider 结果的 `file_id` / `file_user_id` 必须存在。只有服务端 FAL mock 使用独立的 `ReusedImageResult(url=...)`，不能混用空 file ID 表示。共享调用链收到整批内部结果后，在公开返回前完成终态事务；HTTP/聊天/工具对外仍保持原来的 `[{url}]` DTO：

```text
provider 返回 N 张结果图片
  → 对每张结果调用 upload_image，收集 N 个 file_item + url
  → 图生图：把同一份受验证 reference bytes 各上传一次，收集有序 reference file items
  → 打开一个 credit_session 事务
       ├─ finalize_created_images(session, context, result_file_items, reference_file_items)
       │    插入 N 行；每行保存同一有序 reference file ID 列表；冲突时校验不可变身份
       └─ mark_usage_succeeded(session, usage_id, urls)
  → 两部分一起 commit
  → 返回 [{url}, ...] 给现有调用链
```

这里采用用户确认的“同事务提交”，而不是 fire-and-forget 或 outbox。结果 file 与参考快照 file 都必须在该事务之前由上游 file/Storage 成功落盘；`finalize_created_images` 接收调用方提供的 `AsyncSession`，只执行 `flush`，不得自行 begin/commit；`mark_usage_succeeded` 同样提供接受现有 session 的事务内版本。这样不会出现“积分 usage 已成功但作品缺失”，也避免一批多图只写入部分作品或只关联部分参考图。

`bill_image_call` 增加无默认值、真实调用必填的窄 `finalize(session, prepared, internal_result, usage_id)` 回调，由图片路由传入；积分报价不调用 `bill_image_call`，因此不需要该回调。credits 模块只负责在自己的终态事务内调用它，不导入 creations 服务。`_result_urls` 从内部结果提取 URL，外部返回前再投影为原有 `[{url}]`，不把 `file_item` 暴露给 API。顺序必须是 provider 成功 → 校验结果 URL → 同事务写作品并把 usage 标记 succeeded → 返回结果。

失败语义：

- provider 或任一结果 file 上传失败：不创建该批作品记录，也不保存参考快照，沿用当前 provider 失败路径。此前已落盘的结果 file 可能成为孤儿，但不会作为半批作品展示；一期不擅自删除它们。
- provider 成功后，任一参考快照 file 上传失败：不进入作品/usage 终态提交并返回 `credit_service_unavailable`；已落盘的结果 file 和部分参考 file 可能成为孤儿。usage 保持 `invoking`，不调用 `mark_usage_failed`、不自动退款。
- 结果与参考 file 全部创建后，终态事务失败：作品 INSERT 与 usage succeeded 一起回滚，上游 file 全部保留；本次请求返回 `credit_service_unavailable`，而不是伪装成 provider failed。
- 上述终态事务失败时 usage 仍为 `invoking` 且积分保持已扣状态；现有 recovery 会将长期未完成项转为 `unknown`。本期不自动退款，因为供应商实际已经成功并产生了成本；管理员可依据 usage/file 日志人工核对。后续若要自动恢复，应围绕 `unknown` usage 设计独立 reconciliation，而不能直接把它标为 failed 或退款。
- 客户端只有在对同一提交复用同一个 `Idempotency-Key` 时才能获得请求级幂等。当前前端每次 `submitHandler` 调用都会生成新 key；自动网络重试必须复用该 key，用户再次点击属于新的提交，可能再次调用 provider。这一行为沿用现有积分契约，不由作品库另造幂等体系。
- `finalize_created_images` 被重复调用：只有 `file_id` 对应行的 `user_id`、`kind`、`batch_id`、`task`、prompt、模型、参数快照和有序 `reference_file_ids_json` 等不可变生成身份完全一致才按幂等成功。幂等命中不得改写用户可变字段 `caption`、`soft_deleted` 或 `updated_at`，尤其不能把用户已经移除的作品自动恢复；不可变身份不一致则整批失败。

本期不增加“从 succeeded usage URL 回填作品”的补偿路径；如果未来要覆盖旧 usage 或崩溃窗口，应设计独立、可审计的 reconciliation 任务，而不是在普通读请求里解析 URL。

### 5.3 覆盖范围与入口授权

作品捕获发生在共享图片内部调用链和 `upload_image` 桥接点，因此覆盖：

- `/api/v1/images/generations`
- `/api/v1/images/edit`
- 聊天 middleware 自动生成/编辑
- builtin `generate_image` / `edit_image`

入口授权按服务端可信 channel 区分：

- `image_generations` / `image_edits` 和 `bill_image_call` 的内部 `authorization_scope` 是无默认值的必填 `Literal['direct','chat','tool']`：HTTP wrapper 显式传 `direct`，聊天 middleware 传 `chat`，builtin 传 `tool`。它不从 request、header、body 或 metadata 推断，也不进入公开 Pydantic DTO；新增调用点若未选择 scope，应在类型检查/测试中失败。
- scope 与计费 channel 必须 fail-closed 校验：只允许 `direct → web|api`、`chat → chat`、`tool → tool`；任何不匹配都拒绝调用，不能一边使用宽松授权、一边记录成另一来源。
- `direct` scope 跳过图片功能开关和 `features.image_generation` 权限，但仍执行用户存在性、verified role、积分余额、价格配置、模型和参数校验。
- `chat` / `tool` scope 继续执行现有图片开关和用户生成功能权限检查。
- API key 能否调用直接端点仍先受现有 API-key endpoint restrictions 约束；一旦通过并得到 verified user 身份，其图片授权与其他直接 HTTP 调用相同。
- 不使用 `Origin`、`Referer`、客户端自定义 header 或 metadata 中的 `credit_channel` 来证明请求来自 `/images` 页面。
- 管理后台保留现有图片功能开关的标签与说明文案，不在本期重命名；尽管 direct `/images` 端点不受开关影响，chat/tool 仍按开关执行。该文案差异是需求方明确接受的取舍。

本地 FAL mock 直接返回预置旧 URL、没有新 `file_item`，属于开发调试例外。该分支由服务端代码产生内部 `reused_result=true` 标记，finalizer 校验标记后 no-op，再按现有逻辑完成 usage；该标记不能来自请求 DTO、metadata 或 provider 响应。除这个显式开发分支外，真实调用缺少 file items 必须失败，不能静默跳过作品捕获。

## 6. API 契约与鉴权

Router 前缀：`/api/v1/creations`。个人读写端点使用 `get_verified_user`；管理员全局读取端点使用 `get_admin_user`。普通用户路由永远不能通过 query 参数切换到全局 scope，管理员权限由独立依赖和独立路由建立。

读取权限与写权限刻意分离：管理员可以查看所有未软删作品、完整 prompt/参数和参考图，但除非管理员本身就是作品 owner，否则不能通过本期个人 API 修改 caption 或移除作品。这样满足运营查看需求，同时避免“可查看”被隐式扩大为代替用户编辑或删除。

### 6.1 列表

```http
GET /api/v1/creations/media?limit=20&cursor=<opaque>
```

- `limit` 默认 20，范围 1–100。较小首屏用于控制直接加载原图的带宽；一期不生成缩略图。
- 固定排序：`created_at DESC, id DESC`。
- cursor 使用无填充 base64url 编码版本化 JSON：`{"v":1,"created_at":<int>,"id":"<string>"}`。服务端严格校验解码长度、JSON 结构、版本、整数范围和 ID 长度，格式错误返回 422。
- cursor 不签名，因为服务端根据端点固定查询 scope：个人路由始终附加当前 `user_id`，管理员路由始终经过 `get_admin_user`。篡改 cursor 只能改变调用者已获授权集合中的起始位置。
- 查询必须同时包含 `user_id == current_user.id` 与 `soft_deleted == false`，不能先按 item ID 查询后再做 Python 比较。
- 列表响应是轻量卡片摘要，不返回 `file_id`、prompt、negative prompt、params、references 或 batch ID；个人响应也不额外返回 owner 信息。

响应：

```json
{
  "items": [
    {
      "id": "...",
      "kind": "image",
      "content_url": "/api/v1/files/.../content",
      "availability": "available",
      "mime_type": "image/png",
      "caption": null,
      "model_name": "Google / Nano Banana 2",
      "task": "text-to-image",
      "created_at": 1784680000,
      "updated_at": 1784680000
    }
  ],
  "next_cursor": "..."
}
```

列表服务批量读取本页 file 记录，避免 N+1：

- 个人列表要求 `file.user_id == current_user.id`；管理员列表要求 `file.user_id == creation.user_id`。满足时返回 `availability='available'`、内容 URL和 MIME。
- file 不存在或 owner 与作品 owner 不匹配：`availability='missing'`、`content_url=null`，记录告警；即使管理员可读取所有 file，也不能用管理员身份掩盖台账与 file owner 不一致的数据损坏。

### 6.2 管理员全部作品列表

```http
GET /api/v1/creations/admin/media?limit=20&cursor=<opaque>
```

- 端点必须使用 `get_admin_user`，普通 verified user 调用返回 401；不接受 `scope=all`、`include_all=true` 等可把个人路由升级为全局查询的参数。
- 只查询 `soft_deleted == false`，按相同的 `created_at DESC, id DESC` 排序和 cursor 契约分页；一期不展示用户已从作品库移除的记录。
- 一期不新增服务端搜索或用户筛选，管理员看到所有账号混合的时间倒序流；后续如数据量要求筛选，可新增显式 `owner_user_id` 参数并继续走管理员端点与 owner 索引。
- 管理员摘要在普通卡片字段之外增加最小 owner DTO：`owner: {id, name, email, profile_image_url, deleted}`。名称、邮箱和头像在读取时从现有 Users 批量查询，不复制进作品表；账号已删除时返回 `owner: {id, name: null, email: null, profile_image_url: null, deleted: true}`。
- 批量 owner 查询和批量 file 查询都只针对当前页，避免 N+1；管理员摘要仍不返回 prompt、params、references、batch ID 或内部 file ID。

### 6.3 单项详情

个人详情：

```http
GET /api/v1/creations/media/{id}
```

管理员详情：

```http
GET /api/v1/creations/admin/media/{id}
```

- 个人查询同时包含 `id`、当前 `user_id` 和 `soft_deleted=false`；不存在、已删除或属于他人的记录统一返回 404。
- 管理员查询使用 `get_admin_user`，条件包含 `id` 和 `soft_deleted=false`，可读取任意 owner 的未删除作品；普通用户不得调用。管理员详情额外返回与全局摘要相同的 `owner` DTO。
- 返回列表摘要字段，并额外返回 `prompt`、`negative_prompt`、公开 `model_id`、`params`、`references`、`source` 和 `batch_id`；仍不返回结果或参考图的内部 `file_id`。
- `references` 按输入顺序返回；每项仅包含 `position`、`content_url`、`availability` 和 `mime_type`。服务端批量读取本项参考 file，逐项要求 `file.user_id == creation.user_id`；缺失或 owner 不匹配时返回 `availability='missing'`、`content_url=null` 并记录告警，不因单张缺失隐藏其余参考图。管理员身份只允许读取，不能跳过该一致性检查。
- 文生图详情返回空数组 `references: []`，避免前端区分 NULL；图生图也不得返回原始 data URL、外部 URL、hash 或参考 file ID。
- 前端只在用户打开详情时请求，并按 `scope + 作品 ID` 缓存在当前组件生命周期内，防止管理员从“全部作品”切回“我的作品”时误复用不同 scope 的响应；caption 更新成功后同步更新个人摘要与详情缓存。

### 6.4 修改备注

```http
PATCH /api/v1/creations/media/{id}
Content-Type: application/json

{"caption": "新的备注"}
```

- body 只接受 `caption: string | null`，额外字段拒绝；该个人端点没有管理员 override。管理员只有在 `current_user.id == creation.user_id` 时才能成功修改自己的作品。
- 服务层按 Python Unicode code point 执行 `len(caption) <= 1000`，不依赖不同数据库对 `VARCHAR(1000)` 的执行差异；trim 后空串变为 NULL。
- SQL 更新条件包含 `id`、当前 `user_id` 和 `soft_deleted=false`。
- 不存在、已删除或属于他人的记录统一返回 404。

### 6.5 从作品库移除

```http
DELETE /api/v1/creations/media/{id}
```

- 只把台账行设为 `soft_deleted=true` 并更新 `updated_at`；不删除结果 file、参考快照 file 或 Storage 字节，同一批其他作品可能仍引用同一组参考快照。
- 一期不提供回收站、恢复 API、永久清理 API 或参考快照孤儿清理；不能通过普通 UI 重新关联已软删作品。
- SQL 条件始终包含当前 `user_id`，没有管理员 override；管理员在“全部作品”中查看他人作品时不显示移除操作。
- 对当前用户已软删的记录重复调用仍返回 204，以便 optimistic UI 安全重试。
- 他人的记录与不存在记录统一返回 404。
- 未来若增加参考快照清理任务，必须同时证明：没有可见或软删作品的 `reference_file_ids_json` 引用该 file、没有 ChatFile/其他上游引用，并遵守已确认的账号删除后完整保留策略。

## 7. `/images` 界面编织

### 7.1 入口、默认视图与状态所有权

`/images` 导航项对所有 verified user 可见：保留既有 item ID、图标、href、固定与排序机制，只移除 `Sidebar.svelte` / `UserMenu.svelte` 对图片开关和 `features.image_generation` 的可见性判断。`pending` 账号仍被应用现有 verified-user 边界拒绝。

`Images.svelte` 新增 `view: 'generate' | 'library' = 'generate'`，所有 verified user 默认仍进入「新建」。组件不再用 `canUseImagesPage` 把整页替换为“不可用”空态；直接生成/编辑的最终授权由后端端点执行。

进入「作品库」后，普通用户直接显示自己的网格；管理员额外显示第二级 scope 切换「我的作品｜全部作品」，默认仍为「我的作品」，避免管理员日常创作时意外浏览所有人的私人 prompt。scope 控件只对 `$user.role === 'admin'` 渲染，但安全边界完全由独立管理员 API 的 `get_admin_user` 保证。切换到「全部作品」后卡片明确显示 owner 名称和邮箱；已删除账号显示“已删除用户（ID）”。

Tab 使用 `role="tablist"` / `role="tab"` / `role="tabpanel"`、`aria-selected`、`aria-controls` 和对应 ID；支持左右方向键切换，点击区域至少约 44px。切换视图后焦点留在被选中的 Tab，不强制滚动页面顶部。

切换到作品库时不能卸载整个生成视图的 script 状态，否则会丢失 prompt、参考图、模型选择和本次刚生成结果。具体规则：

- `Images.svelte` 始终挂载并持有现有生成状态。
- 通过条件渲染隐藏生成正文和 sticky composer；切回后原状态保留。
- `CreationsLibrary.svelte` 在 `Images.svelte` 生命周期内保持挂载，并按 `scope: 'mine' | 'all'` 分别持有列表、cursor、滚动位置、请求代次和详情缓存；首次进入某个 scope 时才加载。普通用户只能存在 `mine` scope。离开 `/images` 后状态自然销毁。
- 生成成功后无需前端再 POST 入库；`Images.svelte` 递增 `libraryRevision`。如果作品库当前可见，重载“我的作品”第一页；管理员的“全部作品”若已经加载，也标记为 stale，并在当前可见时立即重载、隐藏时下次激活重载。每个 scope 以各自最新请求代次为准，丢弃旧响应。后端自动捕获仍是正确性的唯一来源。

### 7.2 作品库交互

- 均衡响应式网格，中等尺寸卡片；用 CSS `aspect-square` / `object-cover`，不依赖数据库宽高。
- 一期不生成或缓存缩略图，网格直接使用鉴权原图 URL；每个 `<img>` 必须设置 `loading="lazy"`、`decoding="async"`、显式卡片尺寸以避免布局抖动。首批仅 20 张，`Loader` 只在接近列表底部时取下一页，不预取全部历史。
- 卡片只显示图片、caption 摘要、模型显示名和创建时间，并提供始终可见的“详情”入口；管理员“全部作品”卡片额外显示 owner 名称与邮箱。不依赖桌面 hover 才能操作。
- 点击图片打开现有 `ImagePreview`，只复用其缩放与下载。
- 点击“详情”打开新的 `CreationDetailsModal.svelte`，此时按需加载当前 scope 的完整字段；图生图先展示有序“参考图”区域，再展示结果与默认折叠的 prompt/参数/模型信息。owner 查看自己的作品时可编辑 caption 和“从作品库移除”；管理员查看他人作品时为严格只读，不渲染 PATCH/DELETE 操作，不修改 `ImagePreview.svelte`。
- 参考图缩略项同样使用 `loading="lazy"` / `decoding="async"`；点击可复用 `ImagePreview`。`availability='missing'` 时显示对应位置的“参考图不可用”占位，其余参考图和结果仍可操作。
- “从作品库移除”先显示确认对话框，明确“不会删除聊天中的图片，但一期无法从作品库恢复”；确认后采用 optimistic UI：先从列表移除并关闭详情，失败则按原位置回滚并 toast。204 视为成功。移除作品索引不删除结果 file 或参考快照 file。
- 分页复用现有 `Loader on:visible` 模式；仅当 `next_cursor` 非空且当前未加载时请求下一页。

### 7.3 加载与错误状态

- 首次加载：Spinner 加简洁占位。
- 空库：明确说明“新生成的图片会自动出现在这里”，提供切回「新建」按钮。
- 首次请求失败：错误空态 + 重试；不影响切回生成页。
- 后续分页失败：保留已加载项目，在列表尾部显示重试，不清空已有内容。
- `availability='missing'`：显示不可用占位和“源文件不可用”，仍允许改 caption 或从库中移除。

## 8. 后端扩展挂载与迁移

新增：

```text
backend/open_webui/extensions/creations/
├── __init__.py
├── db.py
├── models.py
├── schemas.py
├── service.py
├── router.py
├── registration.py
├── migrations/
│   ├── env.py
│   ├── runner.py
│   ├── script.py.mako
│   └── versions/0001_create_creation_media_item.py
└── tests/
```

迁移链对齐 credits：

- 独立版本表 `ext_creation_schema_version`。
- 迁移前验证上游 `alembic_version` 已到当前 head。
- PostgreSQL advisory lock 与 SQLite 文件锁避免多 worker 同时迁移。
- `CreationBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))`，复用上游 engine/session/`JSONField`。
- migration 显式创建表、索引和约束，不修改上游 schema。

`registration.py` 仅负责：

1. 在线程中运行 `run_creation_migrations`。
2. 校验必需表、版本 head、CHECK/UNIQUE/索引存在。

扩展本期没有常驻后台任务，因此只需要 `initialize_creations_extension(app)`，不设计空的 shutdown hook。

`main.py` 的改动限于：导入 initializer/router、lifespan startup 调 initializer、`app.include_router(creations_router)`。

## 9. 安全、隐私与可观察性

1. **对象级授权：** 个人列表、详情、PATCH、DELETE 都把当前 `user_id` 写进 SQL 条件；他人 ID 不得返回可区分信息。管理员全局列表/详情是使用 `get_admin_user` 的独立只读路由，不通过放宽个人路由条件实现；管理员不能通过本期接口修改或移除他人作品。
2. **文件二次校验：** 组装结果图和每张参考图 DTO 时都要求 `file.user_id == creation.user_id`；内容下载继续由上游 file endpoint 鉴权。管理员可读取其他用户 file，但不能借此掩盖 owner 不一致的损坏记录。
3. **隐私与管理员能力：** 普通用户的 prompt、negative prompt、caption、参数和参考图仅本人可读；管理员因明确的全局作品需求可通过管理员详情读取这些私人字段。UI 必须明确显示作品 owner，API 不把管理员读取能力扩展给普通 verified user。作品表和响应都不记录/返回参考图 base64、原始 URL、hash、内部 file ID 或隐藏供应商 ID。参考快照 file metadata 不包含 prompt、原始 URL 或 provider payload。
4. **发布隔离：** 未来 Spec B 中“发布结果作品”不得隐式公开参考图；参考图可能含私人照片或客户素材，只有独立、明确、可审计的用户授权才能进入社区 DTO。
5. **删除隔离：** 软删作品索引绝不删除结果或参考 file，防止聊天消息或同批其他作品引用失效。
6. **计数器：** 至少记录 `capture_succeeded`、`capture_failed`、`reference_capture_failed`、`missing_file`，标签只使用低基数的 `task/source`，不把 user/file/model ID 放进 metric label。
7. **日志：** 失败日志可包含内部 creation/file ID 便于定位，但不打印 prompt、caption、参考图内容/URL/hash 或 provider 密钥。
8. **账号删除后的保留策略：** 需求已确认采用完整保留。管理员删除或 SCIM 删除用户时，不删除、不匿名化 `ext_creation_media_item` 或其引用的参考快照 file；`user_id`、prompt、negative prompt、caption 和参数快照继续保留。表不对上游 user 建物理 FK，避免用户删除被作品行阻断。删除后普通用户无法访问这些行，但管理员全局作品列表仍可通过保存的 `user_id` 展示“已删除用户”并读取作品详情；owner 名称、邮箱和头像无法从 Users 恢复时为 NULL。本期不提供管理员清理能力。未来若引入隐私清理、法定删除或管理员清理能力，必须另行设计显式的数据保留工具。

## 10. 测试与验收标准

### 10.1 后端

- 迁移：SQLite 新库升级、重复升级幂等、独立版本表、上游未到 head 时失败、必需约束/索引校验。
- 捕获：生成与编辑各自写入；web/api/chat/tool source；多图共享 batch；真实调用内部结果必须含 file identity，服务端 mock 使用独立结果类型；file_id 冲突不重复且不覆盖 caption/soft_deleted；写入失败不删除 file。
- 参考快照：data URL、远程 URL和现有 file 三种输入都复用 provider 的同一份受验证 bytes/mime/hash，保持输入顺序；报价不上传；provider 失败不上传；多结果只上传一组；现有 file 输入也生成独立快照；不得二次抓远程 URL；参考上传失败不进入终态提交。
- 终态事务：作品整批 INSERT 与 usage succeeded 同事务提交；任一失败两者一起回滚；终态事务失败不调用 `mark_usage_failed`，usage 保持 invoking 并最终由 recovery 转 unknown；已落盘的结果/参考孤儿 file 不自动删除。
- 幂等边界：同一 file 重复 finalize 不重复，有序参考 file ID 列表属于不可变身份且不被重放改写；同一 Idempotency-Key 的自动重试遵循既有 usage 结果；新的 key 被视为新的提交。
- 数据脱敏：只保存参数白名单；普通用户公开模型 ID和管理员请求中的真实 FAL ID最终都映射为公开 `model_id`，绝不回退成 `fal-ai/...`；参考图原始 data URL、外部 URL、hash、请求 file ID 与 mask data URL 不进入作品表或用户 DTO。
- 列表与详情：个人列表只返回当前用户的轻量摘要，个人详情 owner-only；管理员独立只读端点返回所有账号的未软删摘要与完整详情。两种 scope 都覆盖 `created_at/id` 同秒稳定游标、版本化 cursor 非法输入、limit 边界、响应不含内部 `file_id`、无 N+1 file/owner 查询；普通用户不能通过参数升级 scope。
- 管理员授权：非 admin 调用 `/admin/media*` 被拒绝；admin 能看到当前与已删除账号的作品、owner DTO、prompt/params/references；全局列表排除软删；管理员查看他人详情时没有 PATCH/DELETE，直接调用个人写端点仍因 owner SQL 条件返回 404。
- 文件状态：结果和参考 file 都覆盖正常、缺失、owner 不匹配三种情况；批量 file 查询只取当前列表页或单项详情需要的 IDs，并确保 missing/owner mismatch 不生成内容 URL，即使当前调用者是管理员。
- 修改/删除：owner 成功；他人统一 404；管理员对他人没有 override；caption code point 长度与规范化；DELETE 重试幂等且无恢复端点；不调用 file 删除。
- 入口覆盖与授权：HTTP、middleware 和 builtin 调用都必须显式提供 authorization scope 和 finalize；direct scope 对 verified user 开放；chat/tool 保留现有闸口；API key endpoint restrictions 仍生效；客户端 metadata/header 不能伪造 scope；只有服务端 FAL mock 标记可执行无新作品的 no-op finalize。
- 账号删除：管理员和 SCIM 删除后作品行及私人字段完整保留，不存在 user FK 阻断删除，也不新增隐式清理调用；个人端点不再可达，管理员全局端点仍返回带 deleted owner DTO 的作品。

### 10.2 前端

- 入口与授权：verified user 的 `/images` 导航始终可见且默认进入「新建」；direct scope 绕过图片开关/功能权限但保留身份、积分、价格和参数校验；chat/tool scope 仍受现有闸口；pending 被拒绝；客户端伪造 channel/scope 无效。
- 切到作品库会加载一次；管理员首次切换「我的作品｜全部作品」时分别加载并缓存 scope，普通用户没有 all scope；切回新建后 prompt、参考图、模型与已生成结果不丢失。直接生成成功后 mine scope 可见态立即刷新、隐藏态下次激活刷新；已加载的 admin all scope 同样失效并按可见性刷新，各 scope 忽略自己的过期响应。
- 首屏、空态、失败重试、游标加载、分页失败保留已有项；打开详情时才按当前 scope 请求完整字段，并以 `scope + id` 缓存。
- 管理员“全部作品”卡片和详情清楚显示 owner；已删除账号使用保存的 user ID 降级展示；查看他人作品时不渲染 caption 编辑或移除操作。
- 首屏默认 20 项、原图 `loading="lazy"` / `decoding="async"`，且没有自动预取全部历史。
- caption PATCH 成功/失败；“从作品库移除”先确认，再验证 optimistic 成功/回滚；无回收站入口。
- missing file 占位不渲染坏 URL。
- `ImagePreview` 打开正确的结果或参考图 URL；`CreationDetailsModal` 按需加载详情，图生图按原输入顺序展示参考图并默认折叠 prompt/参数；owner 模式承载编辑/移除，管理员查看他人作品时严格只读；两者职责不混淆。
- 参考图详情覆盖 available/missing 混合状态、懒加载和点击预览；列表不得加载或返回参考图；移除作品后不调用结果或参考 file 删除。
- Tab 键盘操作、ARIA 关系和切换焦点正确；窄屏下 Tab、网格和操作菜单不横向溢出。

### 10.3 完成定义

1. 新生成/编辑的生产图片只有在整批作品记录成功提交后才作为请求成功返回；图生图还必须完成有序参考图快照关联；随后可从同一用户作品库读到，刷新页面仍存在。
2. 聊天和 builtin 工具产物同样入库，且相同结果 file 不重复；图生图详情能在原始输入 URL 或 file 后续失效时继续读取快照参考图。
3. 普通用户无法通过个人列表、详情、PATCH、DELETE、结果 file URL 或参考 file URL读取/修改他人作品；只有管理员经独立只读路由和现有管理员 file 权限才能查看所有人的作品，且不能修改/移除他人作品。
4. 管理员全局列表稳定分页并显示 owner；账号删除后作品仍以“已删除用户 + user ID”可见，软删作品不出现在全局列表。
5. 迁移在 SQLite 与 PostgreSQL 并发启动模型下沿用 credits 的锁与校验策略。
6. 相关后端定向测试、前端 Vitest、格式检查与项目可运行的类型检查有新鲜通过证据；若全量检查受既有错误阻塞，报告目标文件定向结果和既有错误清单。

## 11. 后续 Spec B 接入原则

本期不在 media 表预埋 `published_post_id` 或社交统计字段。社区广场设计时新增独立帖子与关联表，例如：

```text
ext_creation_post
ext_creation_post_media(post_id, media_item_id, position)
```

这样自然支持一帖多图、排序和未来同一作品多次发布，不需要让个人作品表承担社区生命周期。`kind` 字段可继续作为 API 判别字段，但加入 video/audio 时仍需显式迁移数据库 CHECK、捕获链路和展示组件。
