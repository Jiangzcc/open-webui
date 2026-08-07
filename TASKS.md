# 图片/视频生成功能二开 — 开发任务清单（交接用）

> 本文档供**另一个模型**接力执行。它是自包含的：执行者无需阅读此前的对话，只需读本文 + 项目 `CLAUDE.md`。
> 本文随仓库提交（已脱敏，不含明文密码），供另一台电脑 pull 接力。执行者完成任何任务后，**不得自行 commit/push/PR/merge/rebase**，需向用户确认。

---

## 0. 给执行者的背景与硬约束

### 0.1 项目形态
- 前端：SvelteKit 2 / Svelte 5 / Vite / TypeScript，用 `npm`。前端在仓库根 `src/`。
- 后端：FastAPI / SQLAlchemy 异步 / Alembic。后端在 `backend/open_webui/`。
- 主工作目录：`D:\code\github\open-webui-main`；后端目录：`D:\code\github\open-webui-main\backend`。
- 平台 Windows 11，主 shell PowerShell，另有 Bash(POSIX)。**禁止使用 Git worktree**。
- 本地开发：前端 `npm run dev` + 后端单独运行（勿臆造后端启动命令，先读 `backend/start_windows.bat` / `backend/dev.sh`）。

### 0.2 分支与扩展约定（来自项目 CLAUDE.md）
- `main` 分支 = Open WebUI 上游原样保留，**只读**，不得在上面开发二开。
- `test` 分支 = 承载本项目二次开发改动。当前在 `test` 分支。
- 二开后端能力**优先放入** `backend/open_webui/extensions/`。
- 新增表/索引/迁移对象用 `ext_` 命名空间 + **独立迁移链**；**不得修改上游已有表结构或迁移历史**（除非用户明确确认）。
- 优先复用现有公开接口/组件 → 独立扩展模块 → 最小薄桥接点接入上游调用链。**不得为局部需求复制/替换/大规模重写上游核心模块**。
- 对接上游 handler 用**模块级惰性可替换名字**（可测试 import seam），别顶部直 import，否则 pytest 易卡死/hang。

### 0.3 硬约束清单（必须逐条遵守）
1. **沟通用中文**。
2. **未经用户明确要求，不得 commit / push / 创建 PR / merge / rebase**；不得覆盖、还原或删除无法确认归属的工作区改动。
3. **不得把真实密码 / API key / Authorization token / Cookie / 其他秘密**写入代码、测试、日志、文档。
4. **UI 必须响应式**：桌面端 + 移动端窄屏都要可用；不得只针对固定宽度设计；关键操作**不得仅依赖 hover**，必须支持触屏 + 键盘操作/焦点/语义化标签/必要 ARIA。还要检查深浅色主题、i18n 文案长度、横向溢出。
5. **用户可见文案走现有 i18n 机制并补齐简体中文翻译**（`src/lib/i18n/locales/zh-CN/translation.json`）。
6. **只改当前需求所必需的文件和行为**，不顺便格式化/重命名/重构无关代码。新增/升级依赖前必须说明必要性。
7. **不得在没有新鲜验证证据时声称任务完成**：代码改后跑与改动直接相关的测试/类型/编译检查，如实报告命令与结果；全量检查受既有错误阻塞时，补目标范围定向验证。
8. 测试账号（仅用于手动登录测试，**绝不硬编码进任何文件**）：见项目 `CLAUDE.md` 的「开发环境信息」一节，本文不重复明文。

### 0.4 验证命令速查
- 后端图片 catalog 测试（当前有 4 个失败，见 C1）：
  `cd backend && python -m pytest open_webui/extensions/fal_catalog/tests/test_loader.py open_webui/extensions/fal_catalog/tests/test_compat.py -q`
- 后端图片 util 测试：
  `cd backend && python -m pytest open_webui/utils/images/test_fal.py open_webui/utils/images/test_fal_models.py -q`
- 后端视频 catalog 测试（未跟踪）：
  `cd backend && python -m pytest open_webui/extensions/fal_catalog/tests/test_video_loader.py -q`
- 前端图片工具单测：
  `cd D:/code/github/open-webui-main && npx vitest run src/lib/utils/image-generation.test.ts`
- 前端类型检查：`npx svelte-check`（**注：全量有 8762 个预存错误，不可作为门禁**；只看你改动文件的相关行）。
- 目录加载核对（应输出 187 个图片模型 / 23 个视频模型）：
  `cd backend && python -c "import json,os; b='open_webui/extensions/fal_catalog/catalog/image'; print(sum(len(json.load(open(os.path.join(b,f),encoding='utf-8'))) for f in os.listdir(b) if f.endswith('.json') and f!='manifest.json'))"`

### 0.5 关键事实速查（已核实，执行者可直接用，不必重新推导）
- **图片 catalog**：`backend/open_webui/extensions/fal_catalog/catalog/image/` 下 20 个厂商 JSON，共 **187 个图片模型**（121 个 t2i + 66 个 i2i）。
- **docs 厂商目录**：`docs/fal/` 下 36 个厂商目录。图片 catalog 已收 20 家，**图片端点缺失但 docs 有**的厂商已核实：`baai`(emu-3.5-image / omnigen-v1 / omnigen-v2)、`deepseek`(janus)、`patina`(patina + edit)、`phota`(phota + edit)。`decart`(lucy-*) 等需对照文档确认是否纯生成端点。
- **视频 catalog（未跟踪）**：`backend/open_webui/extensions/fal_catalog/catalog/video/` 下 `alibaba.json`(6 模型) / `bytedance.json`(4) / `kling.json`(8) / `ltx.json`(5) + `manifest.json`，共 **23 个视频模型**（9 t2v + 9 i2v + 5 v2v）。`video_schemas.py`、`tests/test_video_loader.py` 未跟踪；`loader.py` / `__init__.py` 有**未提交改动**在加视频 catalog 支持。
- **视频厂商缺口（docs 有视频、catalog 没接，共 7 家）**：`vidu`（文档最全：i2v/reference-to-video/start-end-to-video/template-to-video/q1-q3）、`minimax`(hailuo-2/2.3)、`google`(veo/nano-banana)、`pika`(v2/v2.1/v2.2)、`pixverse`、`luma`(ray-2/ray-3.2)、`runway`。
- **视频字段缺口**：9 个模型缺 `aspect_ratios`（所有 i2v：`wan-2.7-video/image`、`wan-2.5-preview/image`、`kling-video-v3-pro/image`、`kling-video-v3-standard/image`、`kling-video-v3-turbo-pro/image`；3 个 v2v：`happy-horse/edit`、`kling-video-o3-pro/edit`、`kling-video-o3-standard/edit`、`ltx-2.3/retake`）。4 个 v2v 缺 `duration`：`happy-horse/edit`、`kling-video-o3-pro/edit`、`kling-video-o3-standard/edit`、`ltx-2.3/retake`。23 个视频模型 `custom_size` 全为空。
- **custom_size 机制（图片侧已建成，视频侧待迁移）**：
  - schema：`backend/open_webui/extensions/fal_catalog/schemas.py` 的 `CustomSizeConstraints` 模型 + `FalImageModelDefinition.custom_size`/`custom_size_field`（`custom_size` 必须搭配 `custom_size_field`）。
  - 白名单：`backend/open_webui/utils/images/fal_models.py` 的 `_FAL_PUBLIC_MODEL_FIELDS` 含 `custom_size`。
  - 后端校验：`backend/open_webui/utils/images/fal.py` 的 `_parse_pixel_size` / `_validate_custom_size` / `_set_custom_image_size`（非白名单自定义尺寸按 `custom_size` 校验，不合法抛 `FalImageError`；`auto` 透传；其余统一发 `{width,height}` 对象）。
  - 前端校验：`src/lib/utils/image-generation.ts` 的 `validateCustomSize` + `CustomSizeConstraints` 类型 + `ImageModelCapability.customSize`/`presetSizes` + `normalizeCustomSizeConstraints`/`normalizePresetSizes`。
  - 前端 UI：`src/lib/components/images/Images.svelte`（`customWidth`/`customHeight`/`useCustomSize`/`customSizeValue` 响应式 + WxH 输入区；选分辨率自动带入宽高）。
- **图片侧测试失败现状（真实回归，需修）**：`test_loader.py` 3 个失败（`test_loads_packaged_image_catalog_with_stable_legacy_snapshot` / `test_packaged_catalog_has_curated_primary_model_order` / `test_packaged_catalog_keeps_edit_siblings_next_to_generation_models`）；`test_compat.py` 1 个失败（`test_legacy_facade_preserves_public_catalog_snapshot`，断言 `==44` 实际 `187`）。共 4 个。`test_fal_models.py` 的 `EXPECTED_NEW_MODELS`/`ALIBABA_I2I_PAIRS` 硬编码阿里条目集合（新增阿里 i2i 模型须同步改表）。`test_fal.py` 2 个 payload 测试预存失败（执行时复核）。
- **积分 credits 已打通**：`backend/open_webui/routers/images.py` 的 `/generations` 与 `/edit` 走 `bill_image_call`（`backend/open_webui/extensions/credits/image_billing.py`），预扣 + 幂等键 + 终端事务提交。前端报价 `ImageCreditQuoteBadge`（`/api/v1/credits/quotes/image`，2s 节流），余额 `CreditMenuEntry` + `CreditLedgerModal`。
- **异步任务 creations**：前端不直连 images API，而是 `POST /api/v1/creations/generation-tasks`（`backend/open_webui/extensions/creations/router.py`），202 返回，`asyncio.create_task` 后台跑，前端每 2s 轮询非终态。启动时 `fail_incomplete_generation_tasks` 把 queued/running 标 failed。**无取消接口，删记录不中断后台 task**。
- **安全/健壮缺口（已挖出，见 D 域）**：无服务端 NSFW 审核（委托 provider 的 `enable_safety_checker`/`safety_tolerance`）；非 fal 引擎（OpenAI/Gemini/ComfyUI/Automatic1111）无显式超时、无重试；生成接口本身无速率限制/并发上限；无 per-model admin 上下线开关（只能改 catalog JSON）；作品库 `CreationsLibrary` 与生成流 `ImageGenerationTask` 两套数据源，删 task ≠ 删 creation。
- **`backend/start_windows.bat` 有未提交改动**（注释掉 `--reload --reload-dir`，本地开发用）。**与功能无关，不要动它**。

---

## 1. 任务总览

| 域 | 主题 | 任务 |
|----|------|------|
| 前置 | 决策 | P0-A |
| A | 视频厂商接入补齐 | A1–A5 |
| B | 视频字段与能力对齐 | B1, B2 |
| C | 技术债清理（前置） | C1, C2 |
| D | 图片体验与健壮性 | D1–D8 |
| E | 图片厂商扩展 | E1 |
| F | 回溯审查与直接修复（全部二开） | F1–F10 |

**建议执行顺序**：C1 → P0-A → A1 → A2 → B2 → D1 → （其余按优先级滚动）→ 各功能域批次完成后触发 F 域审查。

---

## 2. 前置决策

### P0-A · 确认未跟踪视频工作的归属 ｜ 优先级 P0 ｜ 无依赖
**背景**：视频 catalog（`catalog/video/`、`video_schemas.py`、`test_video_loader.py`）为未跟踪文件，`loader.py`/`__init__.py` 有未提交改动在加视频支持。按约束 0.3-2「不得覆盖/删除无法确认归属的工作区改动」，**执行者必须先确认归属**。
**动作**：
1. 用 `git log --all --source -- <path>`、`git stash list`、`git diff` 核查这些未跟踪/未提交改动是否属于此前会话的在建设计。
2. 向用户确认：这是在建设工作吗？要继续推进（作为 A1–A5 的基座）还是先隔离（stash/分支）？
**约束注意**：在用户答复前，**不得修改、删除或覆盖**这些视频文件；但可以只读分析。A 域所有任务依赖本项结论。

---

## 3. 域 A · 视频厂商接入补齐

> 前置：P0-A 确认视频 catalog 在建工作可继续推进后，A1–A5 在此基座上新增厂商 JSON。若 P0-A 结论是隔离重建，则按 `video_schemas.py` 的 `FalVideoModelDefinition` 形态从零落目录。
> 每个厂商任务产出：`catalog/video/<brand>.json` + 在 `manifest.json` 登记；对照 `docs/fal/<brand>/**` 的端点参数（duration / aspect_ratio / resolution / asset_inputs / option_fields / boolean_fields / integer_fields / number_fields / text_fields / fixed_fields / output_field / output_mime_types）。

### A1 · 接入 vidu ｜ P0 ｜ 依赖 P0-A
- **范围**：`docs/fal/vidu/**` 有 image-to-video / reference-to-video / start-end-to-video / template-to-video / q1-q3，文档最全。产出 `catalog/video/vidu.json` + manifest。
- **验收**：`test_video_loader.py` 通过；视频页前端能列出 vidu 模型；按 docs 核对每个端点的必填/可选参数。

### A2 · 接入 minimax ｜ P0 ｜ 依赖 P0-A
- **范围**：`docs/fal/minimax/` hailuo-2 / hailuo-2.3。产出 `catalog/video/minimax.json` + manifest。
- **验收**：同 A1。

### A3 · 接入 google 视频 ｜ P1 ｜ 依赖 P0-A
- **范围**：`docs/fal/google/` veo / nano-banana 系列。产出 `catalog/video/google.json` + manifest。

### A4 · 接入 pika ｜ P1 ｜ 依赖 P0-A
- **范围**：`docs/fal/pika/` v2 / v2.1 / v2.2。产出 `catalog/video/pika.json` + manifest。

### A5 · 接入 pixverse / luma / runway ｜ P2 ｜ 依赖 P0-A
- **范围**：三家合一条任务，各取 `docs/fal/<brand>/**` 视频端点。产出对应 `catalog/video/*.json` + manifest。
- **验收**：每家至少一个 t2v 或 i2v 模型可加载。

---

## 4. 域 B · 视频字段与能力对齐

### B1 · 补齐现有 4 家视频厂商字段缺口 ｜ P2 ｜ 无依赖
- **范围**：对照 `docs/fal/{alibaba,bytedance,kling,ltx}/**`，给以下模型补字段：
  - 缺 `aspect_ratios` 的 9 个（见 0.5 视频字段缺口清单）。
  - 缺 `duration` 的 4 个 v2v（`happy-horse/edit`、`kling-video-o3-pro/edit`、`kling-video-o3-standard/edit`、`ltx-2.3/retake`）。
- **验收**：`test_video_loader.py` 通过；前端 `Videos.svelte` 对这些模型能显示宽高比/时长选项。

### B2 · 视频自定义宽高（custom_size 复用迁移） ｜ P1 ｜ 依赖 B1
- **范围**：把图片侧已建成的 `custom_size` 机制迁移到视频侧，与图片体验对齐。
  - schema：`video_schemas.py` 的 `FalVideoModelDefinition` 加 `custom_size`/`custom_size_field`（**复用** `schemas.py` 的 `CustomSizeConstraints`，别另写）。
  - 后端：视频 payload 构建处（`backend/open_webui/extensions/videos/service.py` 或 catalog→payload 路径）加同款校验（复用 `_parse_pixel_size`/`_validate_custom_size`/`_set_custom_image_size` 的逻辑形态）。
  - 前端：`src/lib/components/videos/Videos.svelte` 加 W×H 输入区（复用 `validateCustomSize`）；选分辨率自动带入宽高（参照 `Images.svelte` 的 `selectedResolution`→`customWidth/customHeight` 响应式）。
  - 目录：为支持自由尺寸的视频模型按 docs 填 `custom_size` 约束（A 档按文档精确规则，B 档通用护栏上限 1024×1024 / max_pixels 1048576，参照图片侧分档约定）。
- **验收**：`test_video_loader.py` + 新增 custom_size 用例通过；前端 W×H 输入实时校验、生成按钮在非法时禁用。

---

## 5. 域 C · 技术债清理（前置，解锁 catalog 增改）

### C1 · 修复图片快照测试 4 个失败 ｜ P1 ｜ 无依赖 ｜ 建议最先做
- **范围**：`test_loader.py` 3 个 + `test_compat.py` 1 个，断言锁在「44 模型 / sha256 / primary 顺序」，实际 187。
  - `test_loads_packaged_image_catalog_with_stable_legacy_snapshot`（sha256 + `==44`）
  - `test_packaged_catalog_has_curated_primary_model_order`（硬编码 primary public_id 顺序）
  - `test_packaged_catalog_keeps_edit_siblings_next_to_generation_models`
  - `test_legacy_facade_preserves_public_catalog_snapshot`（`==44`，实际 `187`）
- **改法建议**：把「固定数量 + 精确顺序」改成「不依赖模型总数与精确顺序」的断言（如：校验结构性不变量、校验每 provider 至少含其声明模型、编辑模型紧邻生成模型的关系），或更新基准。**不得删测试绕过**。
- **验收**：`python -m pytest open_webui/extensions/fal_catalog/tests/test_loader.py open_webui/extensions/fal_catalog/tests/test_compat.py -q` 全绿。
- **为何前置**：不修则后续任何 catalog 增删/改字段都会让这 4 个持续红，淹没真实回归。

### C2 · 修复 test_fal_models.py 阿里表硬编码断言 ｜ P2 ｜ 无依赖
- **范围**：`EXPECTED_NEW_MODELS`（12 条阿里 t2i）、`ALIBABA_I2I_PAIRS`（10 对）、`ALIBABA_I2I_PUBLIC_IDS`（10 条）。`test_no_extra_phantom_alibaba_i2i_registrations_exist` 断言阿里 i2i 集合**恰好**等于 `ALIBABA_I2I_PAIRS`，新增阿里 i2i 模型须同步改表。
- **改法建议**：把「恰好等于固定表」改成「是固定表的超集 + 字段值校验」，降低维护摩擦；或补注释说明维护规则。
- **验收**：`python -m pytest open_webui/utils/images/test_fal_models.py -q` 全绿。

---

## 6. 域 D · 图片体验与健壮性（子代理深挖出的缺口）

### D1 · 生成中取消能力 ｜ P1 ｜ 无依赖
- **现状**：删记录不中断后台 task，credits 已预扣（预扣制，succeeded 才最终确认），task 无取消接口，provider 调用会跑到完成为止。
- **范围**：`creations` 扩展加任务取消接口（中断 in-flight `asyncio.Task`）+ 计费回滚（`mark_usage_failed` 走恢复路径）；前端 `Images.svelte` 生成中显示「取消」按钮。
- **验收**：取消后 task 转 failed/cancelled、credits 不最终扣（预扣回滚）；前端按钮触屏可用。

### D2 · 自定义尺寸错误文案精确化 ｜ P2 ｜ 无依赖
- **现状**：`fal.py` 的 `_validate_custom_size` 抛 `FalImageError`，经 `bill_image_call` 被包成 `provider_failed`，前端文案通用，用户分不清「尺寸不合法」还是「provider 挂了」。
- **范围**：把尺寸校验**前置到计费层之前**（提交前先校验 form 的 size），返回 `invalid_image_size` 专属错误码 + 文案；前端 `imageGenerationErrorMessage` 加该码映射。
- **验收**：填非法尺寸时前端/后端报「尺寸不合法」而非「provider 失败」。

### D3 · 生成页余额常驻显示 ｜ P2 ｜ 无依赖
- **现状**：余额只在用户菜单 / 报价 badge。生成页顶部无常驻余额。
- **范围**：`Images.svelte` 顶部加常驻余额条（复用现有 credits API）；窄屏不溢出。
- **验收**：生成页可见总余额；生成后刷新。

### D4 · per-model 上下线 admin UI ｜ P2 ｜ 无依赖
- **现状**：模型启用/禁用由 catalog JSON + `model_ops` 扩展的 `ensure_model_enabled` 决定，管理员无法在 UI 上临时下线故障模型（只能改 `maintenanceMessage`）。
- **范围**：admin 加 per-model 临时上下线开关（走扩展，不改上游表）。
- **验收**：下线后前端该模型灰禁 + 维护文案。

### D5 · 非 fal 引擎超时与重试 ｜ P2 ｜ 无依赖
- **现状**：OpenAI/Gemini/ComfyUI/Automatic1111 无显式超时、无重试，偶发超时挂死 task 直到 asyncio 被外部取消。仅 fal 有 `FAL_REQUEST_TIMEOUT_SECONDS=180`。
- **范围**：给非 fal 引擎加显式超时 + 有限重试（指数退避，最多 N 次）。
- **验收**：模拟超时场景 task 不再永久 running。

### D6 · 生成接口速率限制/并发上限 ｜ P3 ｜ 无依赖
- **现状**：只有积分余额是配额，富裕用户可瞬间并发跑多个 task 撞 provider 配额。
- **范围**：`/generations` 与 `/creations/generation-tasks` 加 per-user 并发上限/速率限制（复用 `CreditRateLimiter` 形态）。
- **验收**：超并发时返回 `rate_limited` 码 + 文案。

### D7 · 作品库与生成流数据源统一 ｜ P3 ｜ 决策类
- **现状**：`CreationsLibrary` 走 `CreationMediaItem` 表，生成流走 `ImageGenerationTask` 表，删 task ≠ 删 creation（`finalize_created_images` 与 task 表不在同一事务）。
- **范围**：先评估后改——是否同事务化删除，或加级联清理。**属侵入式，需用户确认**再动。
- **约束注意**：按 0.3-2，评估后向用户报告方案，勿擅自改数据模型。

### D8 · 服务端内容审核兜底 ｜ P3 ｜ 决策类
- **现状**：NSFW 完全委托 provider（`enable_safety_checker`，z-image turbo 默认 false）；自建 ComfyUI/Automatic1111 后端无任何审核。合规风险。
- **范围**：评估是否在结果回调做服务端 NSFW 拦截（接现有审核能力或 provider flag 读取）。
- **约束注意**：决策类，先评估报用户。

---

## 7. 域 E · 图片厂商扩展

### E1 · 补齐图片目录缺失厂商 ｜ P3 ｜ 依赖 C1
- **范围**：已核实图片端点缺失但 docs 有的厂商：`baai`(emu-3.5-image / omnigen-v1 / omnigen-v2)、`deepseek`(janus)、`patina`(patina + edit)、`phota`(phota + edit)；`decart`(lucy-*) 等对照 `docs/fal/**` 确认是否纯生成端点后补。产出 `catalog/image/<brand>.json`。
- **验收**：`test_loader.py`/`test_compat.py` 绿（C1 已修后）；图片页列出新增模型。
- **约束注意**：每加一个图片模型都会触发 C1 的快照——必须先完成 C1。

---

## 8. 域 F · 回溯审查与直接修复

> **范围**：`test` 分支相对 `main` 的**全部二开改动**（图片 custom_size、catalog 全量、视频 catalog 在建、credits/creations 扩展等）。**审查范围 = 全部二开，不止这一轮。**
> **执行约定**：审查 → 发现问题 → **直接改**。触及 CLAUDE.md 硬约束（0.3）或来源不明改动的，**停下问用户**；其余直接修。审查动作本身不产代码，只产「问题清单→修复」。
> **执行时机**：作为阶段触发——各功能域（A/B/D/E）批次完成后跑一遍 F；不作为孤立单点任务。
> **工具建议**：`git diff main...test` 取二开全量 diff 作为审查面。

**硬约束线（发现即改）**：
- **F1 上游侵入审查**：是否动了上游核心流程/原表/既有迁移历史；本可走扩展/桥接却改了核心的，回退成薄桥接。
- **F2 命名与迁移合规**：新增表/索引是否 `ext_` 前缀 + 独立迁移链；有无混入上游迁移。
- **F3 可测试 import seam**：对接上游 handler 是否用模块级惰性可替换名字（防 pytest 卡死）。
- **F4 秘密泄漏**：代码/测试/日志/文档有无硬编码密码/密钥/token/cookie。
- **F5 i18n + zh-CN**：新增用户可见文案是否走 i18n 并补简中；有无裸中文/裸英文。
- **F6 响应式 + 触屏 + 无障碍**：新增/受影响布局窄屏是否可用；关键操作是否只靠 hover；焦点/ARI/键盘是否齐全。

**质量线（发现即改或记录）**：
- **F7 前后端校验一致性**：`custom_size` 前端 `validateCustomSize` vs 后端 `_validate_custom_size` 规则是否漂移、约束是否同步、错误码是否精确（接 D2）。
- **F8 死代码/重复实现**：残留死代码（如已删的 `presetSizeOptions`/`selectCustomPreset` 是否清干净）；有无复制上游已有能力的重复实现。
- **F9 错误归因**：错误码是否被笼统包成 `provider_failed`（接 D2）。
- **F10 遗留债兜底**：4 个失败快照、阿里表硬编码等（接 C1/C2）是否还卡着。

---

## 9. 建议执行顺序

1. **C1**（清债，解锁后续 catalog 改动）
2. **P0-A**（确认视频归属，解锁 A 域）
3. **A1 / A2**（vidu / minimax 接入，视频最大缺口）
4. **B2**（视频自定义宽高，与图片对齐）
5. **D1**（生成中取消，体验硬缺口）
6. 其余按优先级滚动：A3/A4 → C2 → D2/D3 → B1 → A5 → D4/D5 → E1 → D6/D7/D8
7. 各功能域批次完成后触发 **F 域**审查并直接修复

> 任何任务完成后：跑相关验证命令（见 0.4），如实报告结果；**不自行 commit**，向用户确认后再提交。
