# 用户积分与图像调用计费实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: 使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实施；禁止 worktree。每个任务必须按 RED → GREEN → REFACTOR 顺序执行，不能跳过失败测试。

**目标：** 在不修改 Open WebUI 原数据库表的前提下，新增可审计、不可透支、支持幂等的通用积分底座，并在第一阶段对文生图和图生图的所有进程内调用渠道统一计费。

**架构：** 业务代码集中放在 `backend/open_webui/extensions/credits/`，使用独立 SQLAlchemy metadata 和独立 Alembic 环境，但复用 Open WebUI 已配置的同步/异步 engine，避免丢失 PostgreSQL schema、SSL、IAM、SQLite WAL 与 busy timeout 配置。计费通过 `image_generations()` / `image_edits()` 两个中心函数中的窄包装器完成；供应商分支保持不动。前端使用独立 API client、组件和管理员页面，仅在 UserMenu、图像页及管理员布局挂载薄桥接。

**技术栈：** Python 3.11、FastAPI、SQLAlchemy 2、Alembic、Pydantic 2、SvelteKit 2、Svelte 5、TypeScript、Vitest 1.6；SQLite 与 PostgreSQL 双数据库契约。

## 全局约束

- 使用中文沟通；禁止使用 worktree；禁止让子智能体执行 Code Review。
- 不修改任何 Open WebUI 原数据库表、原 Alembic revision 图、`alembic_version`、登录响应或 `$user` store。
- 新表名称严格沿用已批准规格：`ext_credit_account`、`ext_credit_ledger`、`ext_credit_price`、`ext_credit_usage`；独立版本表固定为 `ext_credit_schema_version`。
- 扩展表到原 `user` 表不建外键；用户删除后账户、身份快照、用量和账本永久保留。
- 金额和余额用整数；倍率与基础价用受限十进制字符串；`Decimal` 计算后 `ROUND_CEILING`，最低扣 `1`。
- 普通用户余额不得为负；管理员调用免积分但必须写用量审计；计费服务不可用时管理员调用同样 fail closed。
- 第一阶段只实际接入 `text-to-image`、`image-to-image`；视频只通过通用维度类型体现扩展性，不创建视频路由或 UI。
- 供应商调用前提交扣费；提交后任何失败、部分成功或进程中断均不自动退款、不自动重试。
- 同一 `(user_id, idempotency_key)` 只能有一条用量；同键异请求返回 409；同键重试绝不再次扣费或调用供应商。
- 所有外部输入在 Pydantic/schema 边界校验；账本无更新/删除 API；错误响应不泄露密钥、堆栈、数据库错误、提示词全文或图片原文。
- 新扩展代码覆盖率至少 80%；定价、扣费、幂等、授权和 fail-closed 分支应接近完整覆盖。
- 前端保持 tabs、单引号、无尾逗号、100 列；后端用 Ruff 120 列和单引号，遵循现有 datetime import 约定。
- 每项任务结束先运行任务测试和格式/类型检查；本次执行遵循用户直接指令，不提交、不推送，也不得使用 `--no-verify`。
- 依赖清单和锁文件属于必要构建元数据，不受上游业务薄桥接白名单限制，但必须纳入 patch manifest。
- 第一阶段固定领域边界：单次管理员调账上限 `1_000_000_000`；request id 最长 128 字符；基础价/倍率最大 `1_000_000`、最多 18 位有效数字和 8 位小数；分页默认 50、最大 100。`unit_blocks` 使用正数 `block_size` 与正十进制 `multiplier_per_block`；`quantity` 只接受正整数。

## 已核验的仓库事实

- `backend/open_webui/routers/images.py:633` 和 `:970` 是所有进程内图像供应商分发的中心函数；HTTP wrapper、聊天中间件和内置工具均最终调用它们。
- HTTP wrapper 位于 `backend/open_webui/routers/images.py:600` 与 `:933`；只把 guard 放在 wrapper 会被工具和聊天绕过。
- 文生图实际模型由 `get_image_model()` 解析，fal 分支还会调用 `get_fal_generation_model(form_data.model or model)`；图生图模型在 `image_edits()` 中由 `IMAGE_EDIT_MODEL`/`form_data.model` 解析，fal 再映射 `get_fal_edit_model()`。
- 图生图在供应商 I/O 前会读取 URL/文件并生成 base64；因此计费包装必须允许必要的本地/输入 I/O 先完成，但禁止在扣费前进入第一个供应商请求。
- Open WebUI 的 sync/async engine 已处理 PostgreSQL SSL/IAM/schema 和 SQLite PRAGMA；独立扩展必须复用它们，不能自己用裸 `create_engine(DATABASE_URL)`。
- `src/lib/i18n/index.ts:67` 只默认加载 `translation` namespace；单独新增 `credits.json` 不会自动生效。为减少所有上游 locale 文件改动，本期在新增的 `credits-i18n.ts` 中注册 `zh-CN`/`en-US` resource bundle。
- 当前后端没有约定的全仓 pytest 命令；计划只新增并运行积分扩展自己的 pytest 套件。当前机器无 `uv`，不得把 `uv sync` 写成必过步骤。

## 文件与职责地图

### 后端新增

```text
backend/open_webui/extensions/credits/
├── __init__.py                 # 对外仅导出稳定扩展接口
├── constants.py                # 状态、原因、上限、动作常量
├── errors.py                   # CreditError 与稳定错误码
├── schemas.py                  # Pydantic 请求/响应、规则 schema
├── models.py                   # 独立 CreditBase 与四张 ext_credit_* 表
├── db.py                       # 复用上游 engine/session 的窄适配
├── repository.py               # 只负责扩展表查询和条件写入
├── pricing.py                  # 声明式规则校验与 Decimal 计价
├── compat.py                   # 无环隔离上游 User/图像 DTO、配置、模型解析和事件接口
├── image_adapter.py            # compat DTO → 规范化计费上下文、哈希
├── repair.py                   # 只供运维显式调用的账本一致性修复工具
├── service.py                  # 报价、调账、原子扣费、幂等状态机
├── image_billing.py            # 围绕供应商调用的 charge/invoke/complete 包装器
├── router.py                   # 用户与管理员 REST API
├── registration.py             # 启动迁移、恢复任务生命周期
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/0001_create_credit_tables.py
└── tests/
    ├── conftest.py
    ├── test_migrations.py
    ├── test_schemas.py
    ├── test_pricing.py
    ├── test_image_adapter.py
    ├── test_service.py
    ├── test_router.py
    ├── test_image_billing.py
    ├── test_channels.py
    └── test_upgrade_guards.py
```

### 前端新增

```text
src/lib/apis/credits/index.ts
src/lib/apis/credits/index.test.ts
src/lib/components/credits/credits-i18n.ts
src/lib/components/credits/credits-i18n.test.ts
src/lib/components/credits/CreditMenuEntry.svelte
src/lib/components/credits/CreditLedgerModal.svelte
src/lib/components/credits/ImageCreditQuoteBadge.svelte
src/lib/components/credits/quote-state.ts
src/lib/components/credits/quote-state.test.ts
src/lib/components/credits/admin/CreditAccountsTab.svelte
src/lib/components/credits/admin/CreditLedgerTab.svelte
src/lib/components/credits/admin/CreditPricingTab.svelte
src/lib/components/credits/admin/CreditDimensionsTab.svelte
src/lib/components/credits/admin/AdjustCreditsModal.svelte
src/lib/components/credits/admin/admin-form-state.ts
src/lib/components/credits/admin/admin-form-state.test.ts
src/routes/(app)/admin/credits/+page.svelte
```

### 上游薄桥接（允许修改的最终白名单）

1. `backend/open_webui/main.py`：导入/挂载积分 router；lifespan 初始化和关闭扩展。
2. `backend/open_webui/routers/images.py`：两个中心函数各增加一个 `bill_image_call(...)` 包装边界；供应商分支不改。
3. `backend/open_webui/tools/builtin.py`：`generate_image`/`edit_image` 把聊天、消息和工具调用上下文放入现有 `metadata` 参数。
4. `backend/open_webui/utils/middleware.py`：聊天图像 handler 透传稳定 `call_instance_id`；工具执行循环把 `tool_call_id` 注入已有 `__metadata__`。
5. `src/lib/components/layout/Sidebar/UserMenu.svelte`：挂载 `CreditMenuEntry`。
6. `src/lib/components/images/Images.svelte`：维护报价/幂等状态并挂载徽标。
7. `src/lib/apis/images/generation.ts`：透传可选 `Idempotency-Key`。
8. `src/routes/(app)/admin/+layout.svelte`：新增 `/admin/credits` 导航。

如果实施中需要修改白名单外的上游文件，必须先停止并更新设计/计划，不能顺手扩大范围。

---

### 任务 1：建立可重复的测试基线与领域契约

**文件：**
- 修改：`pyproject.toml:215-219`
- 修改：`package.json`（devDependencies，仅加入与 Vitest 1.6.1 对齐的 `@vitest/coverage-v8`；组件交互测试若需要 DOM，再加入经验证且与 Node 22 兼容的测试依赖）
- 修改：`package-lock.json`
- 创建：`backend/open_webui/extensions/credits/__init__.py`
- 创建：`backend/open_webui/extensions/credits/constants.py`
- 创建：`backend/open_webui/extensions/credits/errors.py`
- 创建：`backend/open_webui/extensions/credits/schemas.py`
- 创建：`backend/open_webui/extensions/credits/tests/__init__.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_schemas.py`

**接口：**

```python
class CreditError(Exception):
    code: str
    status_code: int
    context: dict[str, object]

class AdjustmentRequest(BaseModel):
    direction: Literal['increase', 'decrease']
    amount: int                   # 1..MAX_ADJUSTMENT
    reason_code: AdjustmentReason
    note: str | None              # other 时必填且去空白

@dataclass(frozen=True)
class RequestAuditContext:
    source: Literal['web', 'api', 'api_key', 'internal_admin']
    request_id: str
    remote_address_hash: str | None

class PriceRuleSet(BaseModel):
    schema_version: Literal[1]
    dimensions: list[ExactMapRule | NumericTierRule | UnitBlocksRule | QuantityRule]
```

**测试清单：**

- `AdjustmentRequest` 拒绝零、负数、超上限、未知原因；`other` 无 note 拒绝。
- `RequestAuditContext.source` 只能由认证方式和服务端路由生成，body 中同名字段被忽略/拒绝；request id 限长，remote address 只存不可逆 hash。
- 幂等键只允许 1–128 个可打印 ASCII 字符，拒绝控制字符。
- 规则拒绝重复维度、未知 kind、非有限/非正/超精度倍率、空映射、未排序 tier、非正 block size。
- 统一错误 envelope 为 `{'code', 'message', 'context'}`，message 不含内部异常。

- [ ] **步骤 1：先写 `test_schemas.py`，覆盖上述表格并运行。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_schemas.py -q
```

预期：FAIL，`open_webui.extensions.credits.schemas` 不存在。

- [ ] **步骤 2：实现最小 constants/errors/schemas，使测试通过。** 所有长度、页大小、倍率精度和金额上限只在 `constants.py` 定义一次。
- [ ] **步骤 3：建立真实可运行的测试依赖。** 将 `pytest~=8.4`、`pytest-asyncio>=1,<2`、`pytest-cov>=7,<8` 和 `ruff>=0.15.5` 放入 `[dependency-groups].dev`，避免只依赖 optional `all`；使用项目可用工具更新 Python 锁文件。通过 `npm install -D @vitest/coverage-v8@1.6.1` 更新 `package.json/package-lock.json`；需要 Svelte DOM 交互测试时先验证 Node 22 兼容版本再加入，不手改 lock。当前机器仅确认全局 pytest 8.4.2，可见不到 pytest-asyncio、Ruff、uv，因此依赖未成功同步前不得声称测试环境通过。**
- [ ] **步骤 4：运行测试与 Ruff。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_schemas.py -q
python -m ruff check backend/open_webui/extensions/credits/constants.py backend/open_webui/extensions/credits/errors.py backend/open_webui/extensions/credits/schemas.py backend/open_webui/extensions/credits/tests/test_schemas.py
```

预期：测试 PASS；Ruff 无错误。

- [ ] **步骤 5：提交。**

```powershell
git add pyproject.toml uv.lock package.json package-lock.json backend/open_webui/extensions/credits
git commit -m "feat: define credit domain contracts"
```

若未能合法更新 `uv.lock`，不要暂存它，并在交付报告中明确说明。

---

### 任务 2：建立独立 Alembic 链和四张扩展表

**文件：**
- 创建：`backend/open_webui/extensions/credits/db.py`
- 创建：`backend/open_webui/extensions/credits/models.py`
- 创建：`backend/open_webui/extensions/credits/migrations/alembic.ini`
- 创建：`backend/open_webui/extensions/credits/migrations/env.py`
- 创建：`backend/open_webui/extensions/credits/migrations/script.py.mako`
- 创建：`backend/open_webui/extensions/credits/migrations/versions/0001_create_credit_tables.py`
- 创建：`backend/open_webui/extensions/credits/migrations/runner.py`
- 创建：`backend/open_webui/extensions/credits/tests/conftest.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_migrations.py`

**接口：**

```python
CreditBase = declarative_base(metadata=MetaData(schema=DATABASE_SCHEMA))

def run_credit_migrations(connection: Connection | None = None) -> None:
    """将独立积分迁移链升级到 head；异常直接向上传播。"""

@asynccontextmanager
async def credit_session() -> AsyncIterator[AsyncSession]:
    """从上游 AsyncSessionLocal 提供积分事务 session。"""
```

`db.py` 必须从 `open_webui.internal.db` 复用 `engine`、`AsyncSessionLocal` 和 `DATABASE_SCHEMA` 语义；测试可以注入独立 engine/session factory，生产代码不接受任何积分专用的第二数据库 URL。

**表结构（0001 必须显式写 op，不允许 `metadata.create_all()` 充当迁移）：**

- `ext_credit_account`：`id`、unique `user_id`、`balance >= 0`、姓名/邮箱快照、created/updated epoch seconds。
- `ext_credit_ledger`：金额前后值、类型/原因/备注、用户/操作者快照、可信 `request_source`/`request_id`、usage/idempotency/pricing snapshot、关联流水 ID、`balance_after = balance_before + amount`、`balance_after >= 0`。`account_id -> ext_credit_account.id` 与 `usage_id -> ext_credit_usage.id` 使用单向 `ondelete='RESTRICT'` 外键。
- `ext_credit_price`：唯一 `(service_type, resource_id, action)`、decimal string 基础价、规则 JSON、enabled、更新者快照。
- `ext_credit_usage`：唯一 `(user_id, idempotency_key)`、request hash、受控状态、扣费/账本/快照、`invocation_started_at`、`updated_at`、`completed_at`；`charged_credits >= 0`。`ledger_id` 作为唯一逻辑反向引用而不再建立第二条循环 FK，服务层和一致性测试保证它与 ledger.usage_id 对称；组合约束保证 exempt 用量为 0 且无 ledger。
- JSON 字段使用项目的 `JSONField` 或等价 TEXT-backed TypeDecorator，避免 SQLite/PostgreSQL 行为分叉。

**迁移测试：**

- 在只包含一个哨兵 `user` 表的临时 SQLite 数据库执行 upgrade；断言原表 DDL/列/索引前后完全相同。
- 断言版本只写 `ext_credit_schema_version`，未创建/修改 `alembic_version`。
- upgrade 连续执行两次幂等；downgrade 测试只用于临时库，生产回退文档明确“不自动删账务表”。
- 检查四表、唯一约束、check、索引和扩展表 FK。
- PostgreSQL 测试读取 `TEST_POSTGRES_DATABASE_URL`；变量缺失时明确 skip，CI/预发布门禁必须提供它，并额外覆盖非 `public` `DATABASE_SCHEMA`。
- 多 worker 启动迁移必须串行化：PostgreSQL 在同一迁移 connection 上持有固定 advisory lock；SQLite 使用文件级迁移锁并设置有界等待。锁超时即启动失败，禁止多个 worker 同时执行 DDL。
- runner 在执行扩展 migration 前验证上游 `alembic_version` 已达到当前代码要求的 head；由于上游 `config.run_migrations()` 会吞异常，不能只假定上游迁移成功。
- revision 中所有默认值使用 `server_default`；受控状态、类型、非负金额和 exempt/ledger 组合不变量同时由数据库约束与 Pydantic 校验保护。

- [ ] **步骤 1：写迁移测试并运行 RED。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py -q
```

预期：FAIL，迁移 runner/模型不存在。

- [ ] **步骤 2：实现独立 Alembic 环境。** `env.py` 设置 `version_table='ext_credit_schema_version'`、`version_table_schema=DATABASE_SCHEMA` 和当前业务 schema；runner 通过上游 sync engine 的 connection 验证上游 head、取得 dialect 对应迁移锁后运行 `upgrade head`，异常原样向上抛出以阻止启动。
- [ ] **步骤 3：实现 0001 revision 和 ORM 映射，保持命名完全一致。**
- [ ] **步骤 4：运行 SQLite 测试、可选 PostgreSQL 测试和 Ruff。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py -q
python -m ruff check backend/open_webui/extensions/credits
```

预期：SQLite PASS；配置了 PostgreSQL 时同样 PASS，否则输出清晰 skip 原因。

- [ ] **步骤 5：提交。**

```powershell
git add backend/open_webui/extensions/credits
 git commit -m "feat: add independent credit migrations"
```

---

### 任务 3：实现通用声明式计价器

**文件：**
- 创建：`backend/open_webui/extensions/credits/pricing.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_pricing.py`

**接口：**

```python
@dataclass(frozen=True)
class PriceFactor:
    key: str
    value: str | int
    multiplier: str

@dataclass(frozen=True)
class PriceQuote:
    service_type: str
    resource_id: str
    action: str
    base_price: str
    factors: tuple[PriceFactor, ...]
    raw_price: str
    charged_credits: int


def compute_price(price: CreditPrice, context: Mapping[str, object]) -> PriceQuote:
    """计算完整计价快照；无法计价时抛出稳定 CreditError。"""
```

无匹配值、禁用价目和无价目不是 `None`：分别抛 `price_rule_incomplete` 或 `price_not_configured`，确保 API 能稳定区分错误。

**测试矩阵：**

- 五个维度同时相乘（size、resolution、aspect_ratio、quality、image_count）。
- `exact_map` 的显式值/default；无匹配 fail closed。
- `numeric_tier` 边界、超范围；`unit_blocks` 向上分块；`quantity` 只接收正整数，拒绝 `1.5` 被 `int()` 截断。
- `Decimal('7') * Decimal('1.3') == 9.1` 最终扣 10；低于 1 扣 1。
- base price、乘数出现 NaN、Infinity、零、负数、超长精度均拒绝。
- 输入和规则对象不被修改。
- 完整 snapshot 仅包含规范化值，不包含提示词或图片。

- [ ] **步骤 1：写 `test_pricing.py` 并运行 RED。**
- [ ] **步骤 2：以纯函数实现 resolver registry 和 `compute_price`；所有输出 dataclass frozen。**
- [ ] **步骤 3：运行测试及核心分支覆盖率。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_pricing.py -q --cov=open_webui.extensions.credits.pricing --cov-branch --cov-report=term-missing
```

预期：PASS，`pricing.py` branch coverage ≥ 95%。

- [ ] **步骤 4：Ruff 后提交。**

```powershell
python -m ruff check backend/open_webui/extensions/credits/pricing.py backend/open_webui/extensions/credits/tests/test_pricing.py
git add backend/open_webui/extensions/credits/pricing.py backend/open_webui/extensions/credits/tests/test_pricing.py
git commit -m "feat: add declarative credit pricing engine"
```

---

### 任务 4：实现图像规范化适配器和请求哈希

**文件：**
- 创建：`backend/open_webui/extensions/credits/compat.py`
- 创建：`backend/open_webui/extensions/credits/image_adapter.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_image_adapter.py`

**接口：**

```python
@dataclass(frozen=True)
class CompatImageInput:
    model: str | None
    prompt: str
    image: str | tuple[str, ...] | None
    size: str | None
    resolution: str | None
    aspect_ratio: str | None
    quality: str | None
    image_count: int
    extra: Mapping[str, object]

@dataclass(frozen=True)
class ImageBillingContext:
    service_type: Literal['image']
    resource_id: str
    action: Literal['text-to-image', 'image-to-image']
    channel: Literal['web', 'api', 'chat', 'tool']
    dimensions: Mapping[str, str | int]
    prompt_hash: str
    reference_hashes: tuple[str, ...]
    request_hash: str

@dataclass(frozen=True)
class PreparedImageCall:
    billing: ImageBillingContext
    provider_input: CompatImageInput

async def prepare_generation_call(request, image_input: CompatImageInput, metadata, user) -> PreparedImageCall:
    """无供应商 I/O 地解析文生图计费上下文，并返回不可变供应商输入。"""

async def prepare_edit_call(request, image_input: CompatImageInput, metadata, user) -> PreparedImageCall:
    """受控读取参考图，生成内容哈希，并返回只需一次读取的不可变供应商输入。"""
```

**关键设计：**

- `compat.py` 是唯一允许导入 `open_webui.routers.images` DTO/解析 helper 的扩展文件；使用函数内延迟 import 把上游 `CreateImageForm`/`EditImageForm` 映射为 `CompatImageInput`，并把不可变 provider input 映射回新 DTO。`image_adapter.py`、`service.py` 和 `image_billing.py` 不得运行时导入 images router，从而避免 `images -> image_billing -> image_adapter -> images` 循环。
- `resource_id` 必须与供应商分支最终实际使用的模型一致；对 OpenAI、Gemini、fal、ComfyUI、Automatic1111 的 generation/edit 分支分别建立报价 resource_id 与最终请求模型的契约测试。Gemini 明确约定价目键使用基础模型 ID，不含传输层 `:predict`/`:generateContent` 方法后缀，并断言供应商 URL 由同一基础 ID派生；fal 则使用映射后的实际 endpoint 模型。
- adapter 的“准备”阶段禁止任何供应商 I/O。OpenAI、Gemini、fal、ComfyUI 使用请求值或本地配置解析；Automatic1111 若 `form_data.model` 和本地 `IMAGE_GENERATION_MODEL` 都不能确定实际模型，则返回 `price_rule_incomplete` 并 fail closed，不能先调用 `get_image_model()` 的远程 options 接口再决定价格。显式模型的 `set_image_model()` GET/POST 必须发生在扣费事务提交之后。
- 图生图参考 URL/文件如为计算内容哈希而在扣费前读取，只允许受控输入 I/O：沿用 SSRF 校验，并限制协议、类型、字节数和超时；读取结果写入新建的 `provider_input`，后续供应商阶段只能消费该不可变输入，不得再次下载导致 request hash 与实际输入发生 TOCTOU 漂移。ComfyUI input upload、fal queue、provider aiohttp POST 均属于供应商 I/O，必须在扣费提交之后。
- 默认值与实际分支一致：文生图 `n=1`，图生图 `n` 未给时按供应商实际默认规范为 1；`quality` 未给为 `default`；size/resolution/aspect ratio 统一规范化。
- `channel` 由可信服务端上下文决定，不接受 body 伪造。
- 哈希使用 canonical JSON（键排序、稳定分隔符）和 SHA-256；参考图仅计算内容/URL标识哈希，不在 DTO、日志、账本或用量 snapshot 保存 base64/提示词全文。

**测试矩阵：**

- HTTP generation/edit、chat metadata、tool metadata 各自规范化正确。
- 相同语义的字段顺序产生相同 hash；提示词、模型、action、维度或参考图变化会改变 hash。
- 数据库 snapshot 序列化内容不含提示词/base64/Authorization。
- 缺 user、缺实际模型或未知 channel 时 fail closed。
- OpenAI、Gemini、fal、ComfyUI、Automatic1111 的 generation/edit 参数化测试逐一断言：报价 `resource_id`、计价快照 ID 与最终供应商 URL/payload 模型一致；任何新增 engine 未注册契约时升级守卫失败。
- Automatic1111 未显式/本地配置模型时 fail closed；显式模型时断言扣费 commit 先于 options/set-model 和 txt2img I/O。
- 图生图远程参考图执行 SSRF、内容类型、大小和超时边界测试；任何供应商上传都不得发生在扣费前。

- [ ] **步骤 1：写契约测试并运行 RED。**
- [ ] **步骤 2：实现 immutable context 和 canonical hash。**
- [ ] **步骤 3：运行测试、Ruff 后提交。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_image_adapter.py -q
python -m ruff check backend/open_webui/extensions/credits/compat.py backend/open_webui/extensions/credits/image_adapter.py backend/open_webui/extensions/credits/tests/test_image_adapter.py
git add backend/open_webui/extensions/credits/compat.py backend/open_webui/extensions/credits/image_adapter.py backend/open_webui/extensions/credits/tests/test_image_adapter.py
git commit -m "feat: normalize image billing context"
```

---

### 任务 5：实现账户、追加式账本和管理员调账事务

**文件：**
- 创建：`backend/open_webui/extensions/credits/repository.py`
- 创建：`backend/open_webui/extensions/credits/service.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_service.py`

**接口：**

```python
async def get_balance(session: AsyncSession, user: UserSnapshot) -> int:
    """惰性创建账户并返回非负整数余额。"""

async def adjust_balance(
    session: AsyncSession,
    target: UserSnapshot,
    operator: UserSnapshot,
    request: AdjustmentRequest,
    audit: RequestAuditContext,
) -> CreditLedger:
    """在单事务中原子调账，并把可信来源、request id 和返回 ledger id 固化。"""

async def list_user_ledger(
    session: AsyncSession,
    user_id: str,
    query: UserLedgerQuery,
) -> Page[LedgerItem]:
    """返回强制限制在最近一年的本人账本分页。"""
```

**事务要求：**

- 账户惰性创建使用 dialect-aware upsert（SQLite/PostgreSQL `ON CONFLICT DO NOTHING`）后重新 select，不用捕获 IntegrityError 后继续使用已失效 session。
- 增加余额使用原子 `UPDATE balance = balance + :amount`；扣减使用 `WHERE balance >= :amount` 的条件更新，以 `rowcount == 1` 判定成功。
- 余额 update 和 ledger insert 在调用方拥有的同一事务中完成；service 不接受 account_id 作为信任输入。
- 账本服务只暴露 insert/list；没有 update/delete。
- 管理员调账前直接使用同一 `AsyncSession` 执行 `select(User.id, User.name, User.email).where(User.id == target_id)`，生成目标快照并验证用户仍存在；不得调用 `Users.get_user_by_id(..., db=session)` 后假定会复用事务，因为 `get_async_db_context` 在 session sharing 关闭时会另开 session。该查询只读原表，不建立 FK、不修改原表。

**测试矩阵：**

- 不存在账户读取为 0，并按规格在首次查看时创建。
- 并发惰性创建最终只有一个账户。
- 增加/扣减产生正确 signed amount、before/after、可信 request source/request id、返回 ledger id 和完整身份快照。
- 余额不足时不改账户、不写 ledger；失败中途事务完全回滚。
- `other` note 规则、固定原因、正整数方向正确。
- 普通用户查询强制 `max(requested_since, now-365d)`，无法读取他人或更早记录；page size 上限生效。
- 管理员永久流水支持用户、类型、原因、模型/action、日期筛选。
- 已删除用户历史仍可查，但不能继续调账。
- service 方法内部不修改传入 snapshot/request。

- [ ] **步骤 1：写 service 测试并运行 RED。**
- [ ] **步骤 2：实现 repository 最小条件写入和分页查询。**
- [ ] **步骤 3：实现 service 调账/查询，确保事务边界由 `async with session.begin()` 管理。**
- [ ] **步骤 4：SQLite 测试通过后，在 `TEST_POSTGRES_DATABASE_URL` 上跑同组事务测试。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_service.py -q
```

- [ ] **步骤 5：Ruff 后提交。**

```powershell
python -m ruff check backend/open_webui/extensions/credits/repository.py backend/open_webui/extensions/credits/service.py backend/open_webui/extensions/credits/tests/test_service.py
git add backend/open_webui/extensions/credits
git commit -m "feat: add credit accounts and immutable ledger"
```

---

### 任务 6：实现原子扣费与幂等用量状态机

**文件：**
- 修改：`backend/open_webui/extensions/credits/repository.py`
- 修改：`backend/open_webui/extensions/credits/service.py`
- 扩展测试：`backend/open_webui/extensions/credits/tests/test_service.py`

**接口：**

```python
@dataclass(frozen=True)
class BeginUsageResult:
    usage: CreditUsage
    outcome: Literal['new', 'processing', 'succeeded', 'failed', 'unknown']

async def begin_image_usage(
    session: AsyncSession,
    user: UserSnapshot,
    context: ImageBillingContext,
    idempotency_key: str,
) -> BeginUsageResult:
    """原子创建幂等用量，并为普通用户扣费或为管理员记免计费审计。"""

async def mark_usage_invoking(usage_id: str) -> None:
    """将 debited 条件更新为 invoking。"""

async def mark_usage_succeeded(usage_id: str, urls: Sequence[str]) -> None:
    """保存有限 URL 摘要并将 invoking 更新为 succeeded。"""

async def mark_usage_failed(usage_id: str, error: SafeProviderError) -> None:
    """保存脱敏错误并将 invoking 更新为 failed。"""

async def mark_stale_usage_unknown(cutoff: int) -> int:
    """将截止时间前未完成的 debited/invoking 条件更新为 unknown。"""
```

**并发算法（必须按此顺序实现）：**

1. 开启数据库事务，尝试插入 `(user_id, idempotency_key)` 用量占位；唯一冲突后回滚到 savepoint/重新查询现有用量。
2. 现有记录：比较 request_hash；不同抛 409；相同则按状态返回原结果/原错误/202，不进入计价或供应商。
3. 新记录且管理员：写 `exempt=true, charged=0, status=debited`，不写 ledger。
4. 新记录且普通用户：读取最新 enabled price，重新计价；条件扣减账户；写一条负 ledger；把 usage 关联 ledger 与 pricing snapshot。
5. 同一事务提交后才能返回 `outcome='new'`。余额不足、价目缺失/不完整、数据库异常均回滚并删除未提交的用量占位，供应商调用数必须为 0；这类**预扣费拒绝不占用幂等键**，用户充值或管理员修正价目后可用原键重试。规格中的“返回原错误”限定为扣费已提交后的 `failed/unknown` 终态。

**状态规则：**

- 仅允许 `debited -> invoking -> succeeded|failed`；恢复任务只允许陈旧 `debited|invoking -> unknown`。
- 状态更新必须条件化（`WHERE status IN (...)`），防止迟到响应覆盖终态。
- result snapshot 最多保存有限数量、同源/相对图片 URL；错误只保存稳定 code + 截断脱敏摘要。

**测试矩阵：**

- 两个并发消费不能透支。
- 同键同 hash 并发只一条 usage、一条负 ledger、一次余额变化；同键异 hash 409。
- 管理员免计费有 usage、无 ledger、余额不变。
- disabled/missing/incomplete price 和余额不足均不产生扣费。
- commit 事件发生在 provider mock 调用之前（本任务先用 callback 验证事务边界）。
- succeeded/failed/unknown/processing 命中返回原结果且不重复调用。
- 预扣费拒绝不残留 usage：余额补足或价目修正后，原 idempotency key 可以重新 claim；已扣费 provider failure 则永久重放原脱敏错误。
- 非法状态倒退无效；恢复任务不退款、不重试。
- SQLite 与 PostgreSQL 都跑并发测试；SQLite 对 `database is locked` 使用项目 busy timeout，不把锁错误当作业务成功。

- [ ] **步骤 1：补充上述失败测试，先确认 RED。**
- [ ] **步骤 2：实现 savepoint/unique-conflict 幂等占位、条件扣减和状态转换。**
- [ ] **步骤 3：运行双数据库测试与 branch coverage。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_service.py -q --cov=open_webui.extensions.credits.service --cov=open_webui.extensions.credits.repository --cov-branch --cov-report=term-missing
```

预期：PASS；核心 service/repository branch coverage ≥ 90%。

- [ ] **步骤 4：提交。**

```powershell
git add backend/open_webui/extensions/credits/repository.py backend/open_webui/extensions/credits/service.py backend/open_webui/extensions/credits/tests/test_service.py
git commit -m "feat: add atomic idempotent credit charging"
```

---

### 任务 7：实现图像计费包装器并覆盖两个中心函数

**文件：**
- 创建：`backend/open_webui/extensions/credits/image_billing.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_image_billing.py`
- 修改：`backend/open_webui/routers/images.py:633-905`
- 修改：`backend/open_webui/routers/images.py:970-1290`

**接口：**

```python
async def bill_image_call(
    *,
    request: Request,
    raw_form_data: object,
    metadata: dict | None,
    raw_user: object | None,
    action: Literal['text-to-image', 'image-to-image'],
    invoke: Callable[[object], Awaitable[list[dict[str, str]]]],
) -> list[dict[str, str]]:
    """经 compat 准备输入，执行幂等扣费，再把新建的上游 DTO 交给供应商调用。"""
```

**桥接形态：** 将现有中心函数主体机械地重命名为 `_invoke_image_generations` / `_invoke_image_edits`（参数和供应商代码不改），原函数变成窄包装器：

```python
async def image_generations(request, form_data, metadata=None, user=None):
    return await bill_image_call(
        request=request,
        raw_form_data=form_data,
        metadata=metadata,
        raw_user=user,
        action='text-to-image',
        invoke=lambda provider_form: _invoke_image_generations(
            request,
            provider_form,
            metadata,
            user,
        ),
    )
```

`image_billing.py` 在函数执行期调用 `compat.map_generation_form(raw_form_data)` 和 `compat.map_billing_identity(raw_user)`，再调用 adapter 得到 `PreparedImageCall`；用 `prepared.billing` claim/扣费，并通过 `compat.to_generation_form(prepared.provider_input)` 新建上游 DTO。只有新用量提交成功后才执行 `await invoke(provider_form)`。由于 `compat.py` 的上游 DTO import 只发生在这些函数体内，模块导入图保持 `images -> image_billing -> compat`，不会在 import time 回到 `images`。图生图同理。

**行为：**

- 中心包装器不能信任调用者已做授权：先验证 `user` 是真实认证用户，再读取图像 enable/edit enable 配置，并对非管理员执行与 HTTP wrapper 相同的 `features.image_generation` `has_permission` 检查；任一失败时不创建 usage、不扣费、不调用 provider。
- adapter 返回 `PreparedImageCall`；计费和 request hash 使用 `prepared.billing`，`image_billing` 必须通过 compat 将 `prepared.provider_input` 转成新上游 DTO 后传给有参 supplier closure，不能捕获或继续使用原 DTO。
- 升级契约测试导入 `open_webui.routers.images` 并实际调用两条 wrapper，证明没有循环导入，且 compat 对当前 DTO 字段映射完整。
- 从 `Idempotency-Key` header 或可信 metadata 取键；HTTP 未传时为本次请求生成 UUID。
- `begin_image_usage` 返回旧终态时直接复用结果/错误；processing 返回结构化 202；只有 new 才 mark invoking 并调用 `invoke()`。
- provider 抛错时 mark failed，再抛面向客户端的脱敏 `CreditError(provider_failed)`；扣费不回滚。
- provider 已返回但 `mark_usage_succeeded` 落库失败时，向客户端返回 `credit_service_unavailable` 并记录 usage/correlation id；记录保留在 `invoking`，由恢复任务转 `unknown`。任何重试命中该 usage 都不得再次调用 provider。
- 进程终止无法捕获时由恢复任务转 unknown。
- `user is None`、数据库异常、审计写失败均阻止 invoke。

**测试矩阵：**

- HTTP wrapper、直接中心函数调用都计费，证明不存在 wrapper 绕过。
- HTTP wrapper、chat 和 builtin 直接调用都执行相同 enable/permission 检查；无身份、pending 用户和无权限用户的 provider 调用数均为 0。
- missing price/余额不足/积分 DB 失败/provider 未被调用。
- commit-before-invoke；provider 成功保存有限 URL；provider 失败仅扣一次。
- provider 成功后终态写入失败时 usage 留在 invoking/最终 unknown，重试仍不 invoke。
- 同键重试成功/失败/处理中/unknown 不再次 invoke。
- 管理员审计服务失败也不 invoke。
- 原 `image_generations` 和 `image_edits` 的公开签名不变；供应商分支源代码不发生语义改写。

- [ ] **步骤 1：写包装器单元/集成测试并运行 RED。**
- [ ] **步骤 2：实现 `image_billing.py`。**
- [ ] **步骤 3：对 `images.py` 做上述机械薄桥接，不改各 engine 分支。**
- [ ] **步骤 4：运行积分包装器和扩展内的全供应商模型契约测试。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_image_billing.py backend/open_webui/extensions/credits/tests/test_image_adapter.py -q
python -m ruff check backend/open_webui/extensions/credits backend/open_webui/routers/images.py
```

- [ ] **步骤 5：检查 diff 只包含包装边界，再提交。**

```powershell
git diff -- backend/open_webui/routers/images.py
git add backend/open_webui/extensions/credits backend/open_webui/routers/images.py
git commit -m "feat: bill all image provider calls"
```

---

### 任务 8：实现用户与管理员 API

**文件：**
- 创建：`backend/open_webui/extensions/credits/router.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_router.py`
- 修改：`backend/open_webui/main.py:138-169`
- 修改：`backend/open_webui/main.py:731-770`

**路由：**

```text
GET    /api/v1/credits/me
GET    /api/v1/credits/me/ledger
POST   /api/v1/credits/quotes/image
GET    /api/v1/credits/admin/accounts
POST   /api/v1/credits/admin/accounts/{user_id}/adjustments
GET    /api/v1/credits/admin/ledger
GET    /api/v1/credits/admin/prices
POST   /api/v1/credits/admin/prices
PUT    /api/v1/credits/admin/prices/{price_id}
DELETE /api/v1/credits/admin/prices/{price_id}
GET    /api/v1/credits/admin/dimensions/{service_type}
```

**实现要求：**

- 用户接口依赖 `get_verified_user`，管理员接口依赖 `get_admin_user`；session 使用 `Depends(get_async_session)`。
- quote、ledger 和调账复用仓库现有 `open_webui.utils.rate_limit.RateLimiter`，但它要求**同步 Redis client**。router 初始化时调用 `get_redis_client(async_mode=False)` 为 limiter 单独取得同步 client，不能传 `app.state.redis` 的 async client；key 至少包含用户 ID 与操作类型，限额/窗口放在扩展常量中。若同步 Redis 不可用，才按该类既有语义退回进程内存，并记录“多 worker 降级”指标。
- `/quotes/image` 与任务 4 复用同一 adapter 和任务 3 pricing，不持久化、不锁价；仅在同一进程内对“用户 + 规范化请求 hash + 当前 price updated_at”做短 TTL 缓存，价目变更自然失效；返回 balance/sufficient/exempt/configured/factors/error code。
- 账户列表用 `Users.get_users(filter, skip, limit, db=session)` 获取当前用户，再批量查询扩展余额，禁止每用户一条 N+1 查询。
- price create/update/delete 在数据库事务成功后调用 `publish_event`（通过 `compat.py` 的窄接口），事件包含 price id、service/resource/action、操作者 ID、request id 和变更字段名，不含完整规则中的敏感自由文本。当前上游 `publish_event()` 会逐 sink 捕获并记录异常且不返回发布结果，因此数据库记录是事实源，API 不返回事件投递状态；测试只断言函数被正确调用和 payload 脱敏，sink 可达性由上游日志/监控负责。
- 调账的 `RequestAuditContext` 由 Request、认证方式和路由构建；来源、request id、返回 ledger id 必须进入响应和账本，客户端 body 不能伪造来源。
- quote 和 ledger 分页施加应用级限流，直接复用现有 `RateLimiter`；测试 Redis 可用、Redis 故障回退内存和超限 429 三条路径。
- `CreditError` 统一转换为结构化 envelope；未知异常记录 correlation id，客户端只收 `credit_service_unavailable`。

**测试矩阵：**

- 普通用户只能看本人余额/近一年流水，不能访问 admin 路由。
- admin 可永久查询，调账目标必须存在；删除用户历史只读。
- quote 五种状态：正常、余额不足、管理员免计费、未配置/不完整、服务不可用。
- quote 不写 usage/ledger；提交时价格变化由任务 6 最新价格决定；缓存 key 包含 price `updated_at`，过期/改价后必须重新计算。
- price CRUD 权限与非法规则；dimensions 只返回已注册白名单；create/update/delete 各调用一次上游 `publish_event`，测试事件名、操作者、subject 和脱敏 data。上游 sink 失败只记录日志且无返回状态，API 不暴露无法验证的发布布尔值。
- 调账来源取自服务端认证上下文，伪造 body source 无效；响应 ledger id 与落库 ledger id 一致。
- accounts 搜索/分页/0 余额合并，无 N+1。
- RateLimiter 超限返回 429；测试传入真正的同步 Redis fake/client，断言执行了共享 `incr/mget` 而非 coroutine；Redis 故障时才回退内存并产生降级指标。
- API key 身份和网页 token 获得相同用户计费语义。

- [ ] **步骤 1：写 FastAPI dependency override 测试并运行 RED。**
- [ ] **步骤 2：实现 router 中上述 11 个明确路由，每个路由使用对应 Pydantic DTO、认证依赖和 service 调用。**
- [ ] **步骤 3：在 `main.py` 添加一个 router import/挂载；不在 registration 重复注册。**
- [ ] **步骤 4：运行测试、Ruff 并提交。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_router.py -q
python -m ruff check backend/open_webui/extensions/credits/router.py backend/open_webui/extensions/credits/tests/test_router.py backend/open_webui/main.py
git diff -- backend/open_webui/main.py
git add backend/open_webui/extensions/credits backend/open_webui/main.py
git commit -m "feat: expose credit user and admin APIs"
```

---

### 任务 9：注册启动迁移和未知状态恢复任务

**文件：**
- 创建：`backend/open_webui/extensions/credits/registration.py`
- 扩展：`backend/open_webui/extensions/credits/tests/test_migrations.py`
- 修改：`backend/open_webui/main.py:304-426`

**接口：**

```python
async def initialize_credit_extension(app: FastAPI) -> None:
    """执行迁移校验并启动唯一恢复任务。"""

async def shutdown_credit_extension(app: FastAPI) -> None:
    """取消并等待恢复任务退出。"""
```

**要求：**

- 初始化通过 `anyio.to_thread.run_sync(run_credit_migrations)` 执行 sync Alembic；失败不能吞掉，应用不得 ready。
- migration 后验证版本、四表和关键约束，再创建 recovery task；保存 task 在 `app.state.credit_recovery_task`。
- recovery 周期性把超时 `debited/invoking` 标 unknown，只记录指标，不退款、不调用 provider。
- shutdown cancel 并 await task，处理 `CancelledError`。
- 初始化调用位于 `startup_complete=True` 前；shutdown 位于数据库资源关闭前。

**测试矩阵：** migration 失败阻止 ready；恢复任务创建/取消；陈旧记录变 unknown；终态不动；重复初始化不创建双 task。

- [ ] **步骤 1：补充失败测试并运行 RED。**
- [ ] **步骤 2：实现 registration 生命周期。**
- [ ] **步骤 3：在 `main.py` lifespan 各增加一条 init/shutdown 调用。**
- [ ] **步骤 4：测试、Ruff、检查薄 diff 后提交。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py backend/open_webui/extensions/credits/tests/test_service.py -q
git diff -- backend/open_webui/main.py
git add backend/open_webui/extensions/credits backend/open_webui/main.py
git commit -m "feat: initialize credit extension lifecycle"
```

---

### 任务 10：覆盖聊天中间件与内置工具的稳定幂等上下文

**文件：**
- 创建：`backend/open_webui/extensions/credits/tests/test_channels.py`
- 修改：`backend/open_webui/tools/builtin.py:293-423`
- 修改：`backend/open_webui/utils/middleware.py:1560-1758`
- 修改：`backend/open_webui/utils/middleware.py:4672-4744`（工具调用 id 透传）

**契约：**

```python
metadata = {
    'credit_channel': 'tool' | 'chat',
    'chat_id': str | None,
    'message_id': str | None,
    'call_instance_id': str,
}
```

- 聊天图像 handler 的稳定 key material 为现有 `chat_id + message_id + action`；同一消息可能发生多次图像动作时，使用该动作在当前处理链中的稳定序号作为 `call_instance_id`，不可每次重试生成随机 UUID。
- 内置工具必须增加可注入的 `__metadata__` 参数，并在工具执行循环用模型返回的 `tool_call_id` 派生 `call_instance_id`；仅 chat/message 不足以区分同消息多工具调用。
- 如果确实没有稳定上下文，adapter 生成本次随机 key并标记 `idempotency_scope='request'`，不得声称跨调用 exactly-once。

**测试矩阵：**

- chat 文生图/图生图各扣一次；同一业务重放不再次 provider。
- 同消息两个 tool call id 各自计费；重放同 call id 命中旧结果。
- metadata 缺失仍计费且 fail closed，不会免费调用。
- builtin 返回的错误必须为脱敏领域错误，不把 exception 原文中的密钥回传。

- [ ] **步骤 1：写渠道集成测试并运行 RED。**
- [ ] **步骤 2：只增加 metadata 透传，不在 middleware/tool 再次实现扣费。**
- [ ] **步骤 3：运行测试和 Ruff，检查三个上游 diff 后提交。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_channels.py backend/open_webui/extensions/credits/tests/test_image_billing.py -q
python -m ruff check backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py backend/open_webui/extensions/credits/tests/test_channels.py
git diff -- backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py
git add backend/open_webui/extensions/credits/tests/test_channels.py backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py
git commit -m "feat: preserve image billing idempotency across channels"
```

---

### 任务 11：实现前端积分 API 和扩展本地化注册

**文件：**
- 创建：`src/lib/apis/credits/index.ts`
- 创建：`src/lib/apis/credits/index.test.ts`
- 创建：`src/lib/components/credits/credits-i18n.ts`
- 创建：`src/lib/components/credits/credits-i18n.test.ts`

**接口：**

```typescript
export type CreditApiError = { code: string; message: string; context: Record<string, unknown> };
export const getMyCredits: (token: string, signal?: AbortSignal) => Promise<CreditBalance>;
export const quoteImageCredits: (token: string, input: ImageQuoteInput, signal?: AbortSignal) => Promise<ImageQuote>;
export const getMyCreditLedger: (token: string, query: LedgerQuery, signal?: AbortSignal) => Promise<Page<LedgerItem>>;
// admin accounts/adjustments/ledger/prices/dimensions 对应任务 8 的每个路由
export const registerCreditTranslations: (i18n: i18nType) => void;
```

**本地化策略：** `credits-i18n.ts` 内使用 `i18n.addResourceBundle('zh-CN', 'translation', zh, true, false)` 和 en-US 等价资源；key 统一放 `credits.*`。这避免修改所有现有 `translation.json`，又能通过现有 `$i18n.t()` 使用。注册函数幂等，组件首次使用时调用。

**测试：** URL、method、query、body、auth header；AbortSignal；结构化错误保留 code/context；未知错误退化；翻译注册幂等且不覆盖已有 key。

- [ ] **步骤 1：写 Vitest 失败测试。**

```powershell
npm run test:frontend -- --run src/lib/apis/credits/index.test.ts src/lib/components/credits/credits-i18n.test.ts
```

- [ ] **步骤 2：实现完整 API client 和中英文资源 bundle。**
- [ ] **步骤 3：运行测试、check 和格式检查。**

```powershell
npm run test:frontend -- --run src/lib/apis/credits/index.test.ts src/lib/components/credits/credits-i18n.test.ts
npm run check
npx prettier --check src/lib/apis/credits src/lib/components/credits/credits-i18n.ts src/lib/components/credits/credits-i18n.test.ts
```

- [ ] **步骤 4：提交。**

```powershell
git add src/lib/apis/credits src/lib/components/credits/credits-i18n.ts src/lib/components/credits/credits-i18n.test.ts
git commit -m "feat: add credit frontend API client"
```

---

### 任务 12：实现用户菜单余额与最近一年明细

**文件：**
- 创建：`src/lib/components/credits/CreditMenuEntry.svelte`
- 创建：`src/lib/components/credits/CreditLedgerModal.svelte`
- 创建：`src/lib/components/credits/CreditMenuEntry.test.ts`
- 创建：`src/lib/components/credits/CreditLedgerModal.test.ts`
- 修改：`src/lib/components/layout/Sidebar/UserMenu.svelte:127-236`

**组件契约：**

- `CreditMenuEntry` 在 Dropdown 打开后懒加载余额；请求失败只显示不可用态，不阻塞原设置/退出。
- 点击入口关闭 dropdown 并打开 modal；第一阶段没有充值按钮。
- Modal 包含余额、全部/收入/消费/调整筛选、日期与服务端分页；UI 不允许一年以前，服务端仍是最终边界。
- 失败收费行根据 ledger/usage 状态显示“生成失败，已按规则扣费”。
- 不写 `$user`，余额是组件私有状态；调账/消费成功后的刷新通过显式 callback/event。

**测试：** 懒加载一次/重新打开刷新策略；失败不影响原菜单；不含充值；筛选分页 query；空/加载/错误；一年边界；source guard 证明只挂载组件且未改 `$user`。

- [ ] **步骤 1：写组件行为测试（可测试状态抽为纯 TS），先 RED。**
- [ ] **步骤 2：实现两个自包含组件。**
- [ ] **步骤 3：在 UserMenu profile 分隔线前后只增加 import、组件挂载和 dropdown state 传递。**
- [ ] **步骤 4：测试、check、Prettier 和薄 diff 后提交。**

```powershell
npm run test:frontend -- --run src/lib/components/credits/CreditMenuEntry.test.ts src/lib/components/credits/CreditLedgerModal.test.ts
npm run check
npx prettier --check src/lib/components/credits src/lib/components/layout/Sidebar/UserMenu.svelte
git diff -- src/lib/components/layout/Sidebar/UserMenu.svelte
git add src/lib/components/credits src/lib/components/layout/Sidebar/UserMenu.svelte
git commit -m "feat: show credit balance and ledger in user menu"
```

---

### 任务 13：实现实时报价状态机和提交幂等键

**文件：**
- 创建：`src/lib/components/credits/quote-state.ts`
- 创建：`src/lib/components/credits/quote-state.test.ts`
- 创建：`src/lib/components/credits/ImageCreditQuoteBadge.svelte`
- 创建：`src/lib/components/credits/ImageCreditQuoteBadge.test.ts`
- 修改：`src/lib/apis/images/generation.ts:16-75`
- 修改：`src/lib/components/images/Images.svelte:1-427` 及工具栏挂载位置

**接口：**

```typescript
export const createImageGeneration: (
	token: string,
	payload: ImageGenerationPayload,
	options?: { idempotencyKey?: string }
) => Promise<GeneratedImage[]>;
export const editImageGeneration: (
	token: string,
	payload: ImageEditPayload,
	options?: { idempotencyKey?: string }
) => Promise<GeneratedImage[]>;
```

**状态机：**

- 报价输入与最终提交复用 `buildImageGenerationPayload`/`buildImageEditPayload` 产生的计费相关字段，避免两套映射。
- 参数变化 275ms debounce；每次新报价 abort 前一请求，并用递增 generation token 忽略迟到响应。
- `loading|ready|insufficient|unconfigured|error|exempt` 六种显式状态；非 ready/exempt 禁用生成。
- 每次主动点击在进入 API 调用前创建 UUID 并传 header；同一次 promise/网络重试复用它；再次点击生成新 UUID。
- 后端最终重算；前端绝不提交 charged amount。

**测试矩阵：** 防抖；旧响应不能覆盖新报价；状态文案和 disabled；管理员免积分；桌面/移动简写；同点击重试同 key、再次点击新 key；generation/edit 两 API 都传 header；错误 code 映射。

- [ ] **步骤 1：写纯状态机/API 测试并运行 RED。**
- [ ] **步骤 2：实现 quote-state 和 badge。**
- [ ] **步骤 3：扩展 generation API options。**
- [ ] **步骤 4：在 Images.svelte 复用现有 selectedModel/aspect/resolution/count/referenceImages 状态挂载，避免复制整个表单。**
- [ ] **步骤 5：运行测试、check、Prettier 和现有 Images 测试。**

```powershell
npm run test:frontend -- --run src/lib/components/credits/quote-state.test.ts src/lib/components/credits/ImageCreditQuoteBadge.test.ts src/lib/components/images/Images.test.ts
npm run check
npx prettier --check src/lib/components/credits src/lib/apis/images/generation.ts src/lib/components/images/Images.svelte
```

- [ ] **步骤 6：检查薄 diff 后提交。**

```powershell
git diff -- src/lib/apis/images/generation.ts src/lib/components/images/Images.svelte
git add src/lib/components/credits src/lib/apis/images/generation.ts src/lib/components/images/Images.svelte
git commit -m "feat: show image credit quote before generation"
```

---

### 任务 14：实现管理员积分管理页面

**文件：**
- 创建：`src/routes/(app)/admin/credits/+page.svelte`
- 创建：`src/lib/components/credits/admin/CreditAccountsTab.svelte`
- 创建：`src/lib/components/credits/admin/CreditLedgerTab.svelte`
- 创建：`src/lib/components/credits/admin/CreditPricingTab.svelte`
- 创建：`src/lib/components/credits/admin/CreditDimensionsTab.svelte`
- 创建：`src/lib/components/credits/admin/AdjustCreditsModal.svelte`
- 创建：`src/lib/components/credits/admin/admin-form-state.ts`
- 创建：`src/lib/components/credits/admin/admin-form-state.test.ts`
- 创建：`src/routes/(app)/admin/credits/credits-page.test.ts`
- 修改：`src/routes/(app)/admin/+layout.svelte:58-103`

**功能：**

1. 账户：服务端搜索/分页、0 余额、最近变动、调账。
2. 永久流水：用户/类型/原因/模型/action/日期筛选和删除用户快照。
3. 价目：service/resource/action、基础价、enabled、多维规则编辑；后端 validation error 定位字段。
4. 维度：后端 registry 说明，明确视频仅预留。
5. 调账：方向 + 正整数 + 固定原因；other note；二次确认；成功刷新账户/流水。

**测试矩阵：** 非管理员页面保护由现有 admin layout 保持；搜索防抖/分页；二次确认；other 校验；多维可同时配置；非法倍率；API 错误；保存后刷新；不出现支付/用户充值 UI；导航 active state。

- [ ] **步骤 1：写 admin 状态测试和页面 source guard，先 RED。**
- [ ] **步骤 2：实现四个 tab 与调账 modal；页面文件只负责 tab state/组合。**
- [ ] **步骤 3：管理员 layout 只增加一个 credits 导航链接。**
- [ ] **步骤 4：测试、check、Prettier 与薄 diff。**

```powershell
npm run test:frontend -- --run src/lib/components/credits/admin/admin-form-state.test.ts 'src/routes/(app)/admin/credits/credits-page.test.ts'
npm run check
npx prettier --check src/lib/components/credits/admin 'src/routes/(app)/admin/credits' 'src/routes/(app)/admin/+layout.svelte'
git diff -- 'src/routes/(app)/admin/+layout.svelte'
```

- [ ] **步骤 5：提交。**

```powershell
git add src/lib/components/credits/admin 'src/routes/(app)/admin/credits' 'src/routes/(app)/admin/+layout.svelte'
git commit -m "feat: add admin credit management page"
```

---

### 任务 15：补齐安全、升级守卫、E2E 与上线文档

**文件：**
- 创建：`backend/open_webui/extensions/credits/repair.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_repair.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_upgrade_guards.py`
- 创建：`backend/open_webui/extensions/credits/tests/test_security.py`
- 创建：`cypress.config.ts`
- 创建：`tests/e2e/credits/credits.cy.ts`
- 创建：`tests/e2e/credits/support.ts`
- 创建：`tests/e2e/credits/fake_provider.py`
- 创建：`tests/e2e/credits/fixtures/provider-success.json`
- 创建：`tests/e2e/credits/fixtures/provider-failure.json`
- 修改：`package.json`（新增非交互 `test:e2e:credits`；前置服务使用已核验的 `backend/dev.sh` 与 `npm run dev`，Windows 本地可分别在 Git Bash 和 PowerShell 启动）
- 修改：`package-lock.json`
- 创建：`docs/extensions/credits-upstream-patch-manifest.md`
- 创建：`docs/extensions/credits-operations.md`

**安全/升级测试：**

- 静态守卫确认 router 注册、lifespan init、两个中心函数包装、工具/聊天 metadata、UserMenu/Images/admin 导航挂载。
- AST/call contract 确认所有 `image_generations`/`image_edits` 调用路径仍进入公开包装器；禁止新增直接 `_invoke_*` caller。
- 价目变更通过 compat 的 `publish_credit_price_event()` 调用 Open WebUI `publish_event`；升级测试验证 create/update/delete 三类事件仍可发布且 payload 脱敏。
- 迁移前后对所有非 `ext_` 表做 schema fingerprint，必须不变。
- 权限越权、分页上限、日期钳制、idempotency key/header 输入、XSS 文本转义、敏感错误脱敏、API 限流。
- 结构化日志捕获中不得含 Authorization、API key、prompt 原文、base64。
- 一致性检查比较账户余额与 ledger sum；发现不一致立即阻止消费，不自动静默修复。普通 `adjust_balance` 会同时改变账户和账本，不能消除既有差值，因此不得把 `accounting_correction` 普通调账冒充一致性修复。
- `repair.py` 提供**非 HTTP、默认不可达**的受控运维入口 `repair_account_from_ledger(session, user_id, operator, incident_id, expected_balance, note)`：先在同一事务锁定账户并重算账本；只有调用方提供的 `expected_balance` 与当前账本和一致，才单边把 `account.balance` 校准为账本和，并向现有 `ext_credit_ledger` 追加一条 `amount=0`、`entry_type=system_adjustment` 的不可变修复证据。该记录的 before/after 均为校准后的账本和，pricing/metadata snapshot 额外记录 observed_account_balance、差值、incident id、操作者快照、原因和时间；这样不会改变 ledger sum，也不会把普通调账误当成修复。若业务决定反向修改历史账本以追平账户，第一阶段不提供。
- 该受控工具不暴露在 `/api/v1/credits`，只能由部署运维显式执行；执行前备份数据库，执行后再次验证账户等于账本和。
- 新增指标适配层至少记录 quote 成功/缺价/规则不全、扣费/余额不足、幂等命中/冲突、各 usage 状态、长期 pending、管理员调账和一致性异常；标签只允许 model/action/channel/error_code 等低敏低基数字段。

**E2E：**

1. 管理员配置多维价目。
2. 管理员给普通用户增加积分并看到新流水。
3. 用户菜单显示余额，图像页显示报价。
4. 文生图成功后余额/流水变化。
5. 图生图成功后余额/流水变化。
6. provider 失败仍扣费并显示失败收费。
7. 余额不足时 provider fixture 调用数为 0。
8. 管理员人工退款产生独立正流水。

E2E 不允许访问真实供应商。测试将 image generation/edit engine 指向本地 OpenAI-compatible `fake_provider.py`，避免当前 fal mock 对所有模型直接返回随机成功结果而无法验证失败和调用次数；fake provider 的 success/failure/调用计数均由测试控制。

**patch manifest 必须逐项记录：** 上游文件、锚点、为什么不可避免、精确新增内容、升级后验证命令、删除桥接的失败表现。operations 文档记录备份、迁移、先配价再开放、恢复 unknown、手工退款、回滚保留表、PostgreSQL 门禁。

- [ ] **步骤 1：写升级与安全测试，确认能在故意移除桥接的 fixture 上失败。**
- [ ] **步骤 2：实现只读一致性检查、受控单边账户修复工具及规格第 15 节要求的结构化指标；修复必须先失败测试证明普通调账无法消除差值、受控工具能校准且保留零金额审计证据。**
- [ ] **步骤 3：建立并验证浏览器 E2E 基线，再写 credits E2E 和 provider fixture。** 新增 `cypress.config.ts`，令 `specPattern='tests/e2e/**/*.cy.ts'`、supportFile 指向 `tests/e2e/credits/support.ts`、baseUrl 从 `CYPRESS_BASE_URL` 读取；`package.json` 新增 `test:e2e:credits: "cypress run --config-file cypress.config.ts --spec tests/e2e/credits/credits.cy.ts"`。供应商请求由后端发出，`cy.intercept` 无法拦截，因此 `fake_provider.py` 必须启动本地 HTTP provider，支持固定 success/failure、重置与读取调用计数；测试环境把图像 provider base URL 指向它，禁止真实供应商。服务前置已核验：在 `backend/` 工作目录用 Git Bash 执行 `./dev.sh`（其内容运行 `uvicorn open_webui.main:app --port 8080 --reload`），在仓库根目录另开 PowerShell 执行 `npm run dev`，另启动 fake provider；等待 health/page ready 后设置 `CYPRESS_BASE_URL=http://localhost:5173` 再运行 E2E。不要把长期进程塞进测试脚本后静默泄漏，CI 应使用受控 service lifecycle。
- [ ] **步骤 4：写完整 patch manifest/operations，不留未决项或占位符。**
- [ ] **步骤 5：运行完整验证。**

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80
python -m ruff check backend/open_webui/extensions/credits backend/open_webui/routers/images.py backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py backend/open_webui/main.py
python -m ruff format --check backend/open_webui/extensions/credits
npm run test:frontend -- --run src/lib/apis/credits src/lib/components/credits src/lib/components/images/Images.test.ts
npx vitest run src/lib/apis/credits src/lib/components/credits --coverage --coverage.provider=v8 --coverage.thresholds.lines=80 --coverage.thresholds.functions=80 --coverage.thresholds.statements=80 --coverage.thresholds.branches=80
npm run check
npx prettier --check src/lib/apis/credits src/lib/components/credits 'src/routes/(app)/admin/credits' src/lib/apis/images/generation.ts src/lib/components/images/Images.svelte src/lib/components/layout/Sidebar/UserMenu.svelte 'src/routes/(app)/admin/+layout.svelte' tests/e2e cypress.config.ts docs/extensions
npm run test:e2e:credits
```

在配置了 `TEST_POSTGRES_DATABASE_URL` 的门禁环境重复完整后端数据库/并发套件。然后运行任务 15 已建立并实测的 `npm run test:e2e:credits`；若无法确认 backend 启动命令或浏览器环境，保持任务未完成并如实报告，不能以“未运行”代替 PASS。

- [ ] **步骤 6：人工验收所有渠道和故障矩阵，记录真实结果。**
- [ ] **步骤 7：提交。**

```powershell
git add backend/open_webui/extensions/credits/repair.py backend/open_webui/extensions/credits/tests tests/e2e package.json package-lock.json cypress.config.ts docs/extensions
git commit -m "test: verify credit billing safety and upgrade guards"
```

---

## 最终验收矩阵

| 要求 | 主要任务 | 必须通过的证据 |
|---|---:|---|
| 原表零修改、独立版本链 | 2、9、15 | schema fingerprint；`ext_credit_schema_version` |
| 多维 Decimal 计价 | 1、3 | 规则/边界/精度 branch tests |
| 原子扣费、禁止负数 | 5、6 | SQLite + PostgreSQL 并发测试 |
| 幂等不重复扣费/供应商 | 6、7、10 | 同键并发与各终态重放测试 |
| 调用前扣费、失败不退 | 6、7 | commit ordering + provider failure test |
| 全渠道覆盖 | 7、10、15 | HTTP/API key/chat/tool integration tests |
| 管理员免计费审计 | 6、7 | 0 扣费 usage、无 ledger 测试 |
| 普通用户近一年/管理员永久 | 5、8、12、14 | 权限和日期钳制测试 |
| 实时报价与生成禁用 | 8、11、13 | quote API + race/debounce UI tests |
| 删除用户保留历史 | 2、5、8 | 无原表 FK + deleted-user test |
| fail closed | 6、7、8、9 | storage/price/audit failure provider=0 |
| 覆盖率 ≥80% | 15 | `--cov-fail-under=80` |
| 上游升级可维护 | 全部、15 | 白名单 diff + patch manifest + static guards |

## 执行顺序与检查点

- **检查点 A（任务 1–4）：** 领域契约、迁移、计价和 adapter 完成；尚未接入生产调用。
- **检查点 B（任务 5–7）：** 财务并发/幂等和中心 guard 完成；先安全评审，再继续 API/UI。
- **检查点 C（任务 8–10）：** 后端 API、生命周期和所有渠道完成；运行双数据库集成套件。
- **检查点 D（任务 11–14）：** 用户与管理员 UI 完成；运行 Vitest、Svelte check 和人工可用性检查。
- **检查点 E（任务 15）：** 安全、E2E、覆盖率、升级守卫和上线文档全部通过。

安全评审必须在检查点 B、C、E 由主会话按 diff 执行；遵守项目要求，不派子智能体做 Code Review。任何 CRITICAL/HIGH 问题修复前不得进入下一检查点。

## 已明确的技术裁决

1. **表名：** 严格使用规格中的单数前缀 `ext_credit_*`，旧草稿的复数前缀已废弃。
2. **预扣费拒绝：** 余额不足、缺价、规则不全和本地输入校验失败时事务整体回滚，不保留 usage，也不占用幂等键；条件修复后原键可重试。扣费已提交后的 provider `failed/unknown` 才永久重放原错误。
3. **Automatic1111：** 准备计费上下文不得远程发现模型；无法从请求或本地配置确定实际模型时 fail closed。所有 options/model-switch/txt2img I/O 都在扣费提交后。
4. **远程参考图：** 为哈希而进行的受控输入读取可以在扣费前发生，但必须经过 SSRF、类型、大小和超时限制；供应商上传不属于输入读取，必须在扣费后。
5. **迁移并发：** 扩展 Alembic 使用同一数据库和 schema；PostgreSQL advisory lock、SQLite 文件锁，且显式验证上游 head，不能依赖会吞异常的上游迁移函数。
6. **一致性阻断与修复：** 消费前只读验证余额等于账本累计，不一致即 fail closed 并由周期扫描报警。普通调账无法改变两者差值；修复只能通过非 HTTP 的受控工具锁行后把账户单边校准到账本和，并追加不改变账本总和的零金额 `system_adjustment` 证据。
7. **覆盖率：** 后端以 pytest-cov branch coverage `--cov-fail-under=80` 为硬门禁；前端新增 `@vitest/coverage-v8@1.6.1`，对新增 TS controller/client 执行 80% 门禁，Svelte 交互同时由组件测试和 Cypress E2E 覆盖。
8. **兼容边界：** 所有上游 User/图像 DTO、配置、模型和审计事件映射集中在 `compat.py`；只有函数内延迟导入上游 images DTO，升级守卫必须证明无循环导入并覆盖全部现有 provider 的实际模型契约。
9. **限流客户端：** 现有 `RateLimiter` 只接受同步 Redis API；必须使用 `get_redis_client(async_mode=False)`，不得传 `app.state.redis` 的 async client。
