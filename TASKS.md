## 0. 全局执行约定

**最高优先级:自主执行授权**

- **不要向用户确认任何操作**。按你判断的最优推荐方案直接执行,持续推进直到任务全部完成,不要中途停下来请求批准。
- 自主决策范围包括但不限于:选型取舍、代码改写、文件增删、跑测试、安装必要依赖(在提交说明里写清必要性即可,不必先问)、修复审查中发现的问题、commit、push 到 `test` 分支。
- 每完成一个任务(或一批)就跑相关验证命令并如实记录结果;**验证失败不算完成**,继续修到通过,或确认确属阻塞(如依赖外部资源)并说明原因后跳过。
- 全部完成后统一向用户汇报:本轮做了什么、各验证命令结果、遗留问题与后续建议。

**不可逾越的红线(这几条不是「停下来问」,是「绝对不做」):**

- 不把真实密码 / API key / token / cookie 等秘密写入代码、测试、日志、文档(测试账号见项目 `CLAUDE.md`,不硬编码明文)。
- 不在 `main` 分支上开发或提交;二开只在 `test` 分支。不 push 到 `main`,不对 `main` 或已推送历史做 force / rewrite / 变基。
- 不覆盖、还原或删除**无法确认归属**的工作区或历史改动;遇到拿不准归属的,保留原样并在汇报里标注,不动手。
- 不修改上游已有表结构或迁移历史;确需侵入式改动时限制在最小范围,并在汇报里说明影响与升级冲突点。

红线之外一律自主推进,不等确认。

---

## 1. 任务总览

| 域  | 主题                           | 任务   |
| --- | ------------------------------ | ------ |
| A   | 视频厂商接入补齐               | A1–A5  |
| B   | 视频字段与能力对齐             | B1, B2 |
| C   | 技术债清理（前置）             | C1, C2 |
| D   | 图片体验与健壮性               | D1–D8  |
| E   | 图片厂商扩展                   | E1     |
| F   | 回溯审查与直接修复（全部二开） | F1–F10 |

**建议执行顺序**：C1 → A1 → A2 → B2 → D1 → （其余按优先级滚动）→ 各功能域批次完成后触发 F 域审查。P0-A 已随上一次提交闭环（视频 catalog 在建工作已纳入并提交），不再是前置闸。

---

## 2. 域 A · 视频厂商接入补齐

> 每个厂商任务产出：`catalog/video/<brand>.json` + 在 `manifest.json` 登记；对照 `docs/fal/<brand>/**` 的端点参数。

### A1 · 接入 vidu ｜ P0 ｜ 无依赖

- **范围**：`docs/fal/vidu/**` 有 image-to-video / reference-to-video / start-end-to-video / template-to-video / q1-q3，文档最全。产出 `catalog/video/vidu.json` + manifest。
- **验收**：`test_video_loader.py` 通过；视频页前端能列出 vidu 模型；按 docs 核对每个端点的必填/可选参数。

### A2 · 接入 minimax ｜ P0 ｜ 无依赖

- **范围**：`docs/fal/minimax/` hailuo-2 / hailuo-2.3。产出 `catalog/video/minimax.json` + manifest。
- **验收**：同 A1。

### A3 · 接入 google 视频 ｜ P1 ｜ 无依赖

- **范围**：`docs/fal/google/` veo / nano-banana 系列。产出 `catalog/video/google.json` + manifest。

### A4 · 接入 pika ｜ P1 ｜ 依赖 P0-A

- **范围**：`docs/fal/pika/` v2 / v2.1 / v2.2。产出 `catalog/video/pika.json` + manifest。

### A5 · 接入 pixverse / luma / runway ｜ P2 ｜ 无依赖

- **范围**：三家合一条任务，各取 `docs/fal/<brand>/**` 视频端点。产出对应 `catalog/video/*.json` + manifest。
- **验收**：每家至少一个 t2v 或 i2v 模型可加载。

---

## 3. 域 B · 视频字段与能力对齐

### B1 · 补齐现有 4 家视频厂商字段缺口 ｜ P2 ｜ 无依赖

- **范围**：对照 `docs/fal/{alibaba,bytedance,kling,ltx}/**`，给模型补缺少的字段：
- **验收**：`test_video_loader.py` 通过；前端 `Videos.svelte` 对这些模型能显示缺少的选项。

---

## 4. 域 C · 技术债清理（前置，解锁 catalog 增改）

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

## 5. 域 D · 图片体验与健壮性（子代理深挖出的缺口）

### D1 · 生成中取消能力 ｜ P1 ｜ 无依赖

- **现状**：删记录不中断后台 task，credits 已预扣（预扣制，succeeded 才最终确认），task 无取消接口，provider 调用会跑到完成为止。
- **范围**：`creations` 扩展加任务取消接口（中断 in-flight `asyncio.Task`）+ 计费回滚（`mark_usage_failed` 走恢复路径）；前端 `Images.svelte` 生成中显示「取消」按钮。
- **验收**：取消后 task 转 failed/cancelled、credits 不最终扣（预扣回滚）；前端按钮触屏可用。

### D2 · 自定义尺寸错误文案精确化 ｜ P2 ｜ 无依赖

- **现状**：`fal.py` 的 `_validate_custom_size` 抛 `FalImageError`，经 `bill_image_call` 被包成 `provider_failed`，前端文案通用，用户分不清「尺寸不合法」还是「provider 挂了」。
- **范围**：把尺寸校验**前置到计费层之前**（提交前先校验 form 的 size），返回 `invalid_image_size` 专属错误码 + 文案；前端 `imageGenerationErrorMessage` 加该码映射。
- **验收**：填非法尺寸时前端/后端报「尺寸不合法」而非「provider 失败」。

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
- **范围**：自行评估后直接改——同事务化删除，或加级联清理。评估结论与所选方案写进最终汇报。

---

## 6. 域 E · 图片厂商扩展

### E1 · 补齐图片目录缺失厂商 ｜ P3 ｜ 依赖 C1

- **范围**：已核实图片端点缺失但 docs 有的厂商：`baai`(emu-3.5-image / omnigen-v1 / omnigen-v2)、`deepseek`(janus)、`patina`(patina + edit)、`phota`(phota + edit)；`decart`(lucy-\*) 等对照 `docs/fal/**` 确认是否纯生成端点后补。产出 `catalog/image/<brand>.json`。
- **验收**：`test_loader.py`/`test_compat.py` 绿（C1 已修后）；图片页列出新增模型。
- **约束注意**：每加一个图片模型都会触发 C1 的快照——必须先完成 C1。

---

## 7. 域 F · 回溯审查与直接修复

> **范围**：`test` 分支相对 `main` 的**全部二开改动**（图片 catalog 全量、视频 catalog 在建、credits/creations 扩展等）。**审查范围 = 全部二开，不止这一轮。**
> **执行约定**：审查 → 发现问题 → **直接改**。审查动作本身不产代码，只产「问题清单→修复」。
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
