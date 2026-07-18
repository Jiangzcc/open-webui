# 积分扩展运行手册

## 适用范围和上线原则

本手册适用于独立积分扩展。扩展使用自己的表和版本链：

- `ext_credit_account`
- `ext_credit_ledger`
- `ext_credit_price`
- `ext_credit_usage`
- `ext_credit_schema_version`

它不修改 Open WebUI 原 `user` 表，也不在原表上建立外键。普通用户的图像调用在供应商调用前预扣积分；价格、账务、审计或一致性验证不可用时必须 fail closed。管理员图像调用免积分，但仍写入 usage 审计；审计不可用时同样不得调用供应商。

第一阶段**没有真实支付、用户充值按钮、自动退款或通过修改历史流水修正余额的功能**。积分来源是管理员调账，退款是新建一笔正向流水。不要以关闭积分计费来处理 Redis、迁移或报价故障。

## 运行进程

已核验的本地启动方式如下。前后端是两个长期进程，应在不同终端运行；不要把它们塞进临时脚本后让进程静默泄漏。

### Windows

在仓库根目录的 PowerShell 中启动前端：

```powershell
npm run dev
```

在 Git Bash 中启动后端：

```sh
cd backend
./dev.sh
```

`backend/dev.sh` 启动 `uvicorn open_webui.main:app --port 8080 --reload`。不要在 PowerShell 中杜撰等价的后端启动命令。

### Linux/macOS

在仓库根目录的 shell 中启动前端：

```sh
npm run dev
```

在另一个 shell 中启动后端：

```sh
cd backend
./dev.sh
```

## 发布前备份和恢复演练

1. 在维护窗口前，对实际数据库执行与所用数据库引擎相匹配的一致性备份；备份必须包含上游表与全部 `ext_credit_*` 表、`ext_credit_schema_version`。
2. 记录备份的时间、数据库/schema、校验方式和对应发布版本；不要在生产数据库上把“备份命令成功返回”当作可恢复证明。
3. 在隔离的恢复环境恢复该备份，并确认至少包括：`ext_credit_account`、`ext_credit_ledger`、`ext_credit_price`、`ext_credit_usage`、`ext_credit_schema_version`；确认上游 `alembic_version` 仍存在。
4. 在恢复环境启动应用，使扩展迁移与 schema 校验运行；确认原用户表、原上游表和 `alembic_version` 没有被扩展迁移改写。
5. 仅在上述恢复演练可追溯且结果可用后，执行生产发布。受控一致性修复还要求该备份已被人工确认，见“受控一致性修复”。

## 启动、迁移与 ready 门禁

应用启动期间会执行以下顺序：

1. 使用上游同一数据库 engine 执行扩展迁移。
2. 在运行迁移前确认上游 `alembic_version` 已到上游 head。
3. 使用 PostgreSQL advisory lock 或 SQLite `${数据库文件}.credit-migrations.lock` 文件锁串行化扩展迁移，锁等待上限为 10 秒。
4. 检查 `ext_credit_schema_version` 的 head、所需 `ext_*` 表以及关键约束。
5. 只有以上全部成功，才创建 stale usage 恢复任务，并随后把应用标记为 ready。

因此迁移、锁、上游版本或 schema 校验失败时，应用必须保持非 ready；不要手工跳过扩展迁移、删除版本表或先开放流量再补迁移。先查看完整异常、修复数据库状态并在隔离环境复现，再重新部署。

扩展迁移从不写入上游 `alembic_version`。上线后核验扩展 head 和原表未变的建议命令如下：

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py backend/open_webui/extensions/credits/tests/test_registration.py -q
```

```sh
PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_migrations.py backend/open_webui/extensions/credits/tests/test_registration.py -q
```

这些命令是验证命令，不是生产迁移替代品；未执行时不能称其通过。

## 首次开放顺序

首次上线遵循以下顺序，避免普通用户因默认零余额或未配价目而产生无意义请求：

1. 部署并确认应用仅在扩展迁移和 schema 验证成功后 ready。
2. 以管理员身份配置并启用每个实际图像模型、每种 action（`text-to-image`、`image-to-image`）及其全部必需维度的价目。价格缺失或规则不完整时，普通用户请求会 fail closed，且供应商不应被调用。
3. 使用管理员积分管理界面对目标普通用户执行人工加分；初始账户余额为 `0`，账户可以惰性创建。每次加分必须填写适当的原因和可审计说明。
4. 抽样以普通用户身份获取报价，确认报价、余额和提交按钮都符合价目；仅在预期模型、文生图和图生图路径都验证后开放普通用户流量。
5. 观察 usage 状态、扣费、失败、unknown、限流降级和一致性指标；上线早期不要凭主观判断关闭任何 fail-closed 保护。

管理员调用不扣积分，但必须保留 usage 审计。普通用户调用在本地校验、权限、计价和余额检查成功后先提交预扣费，再进入供应商调用。

## Usage 状态、unknown 恢复与幂等

### 正常状态

正常调用的 usage 状态依次为：`debited`、`invoking`，然后成为 `succeeded` 或 `failed`。预扣费已提交后，即使供应商失败，账本消费流水也不自动删除或反向冲销。

### stale usage 恢复

恢复任务每 60 秒扫描一次；已持续超过 15 分钟的 `debited` 或 `invoking` usage 被标为 `unknown`。它只改变 usage 状态，不改变余额或账本。

对 `unknown` 的处理契约是：

- 不自动重试供应商。
- 不自动退款或补余额。
- 不把同一幂等键当作新请求。
- 记录关联 usage、供应商侧可核验事实和人工处置结论。

对于同一 `(user_id, idempotency_key)`，`failed` 或 `unknown` 的重放复用既有终态，不再次调用供应商也不再次扣费。余额不足、缺价、规则不完整或本地输入校验等预扣费前拒绝会整体回滚 usage 占位；条件恢复后，原幂等键可以重新提交。

当 `webui.credits.usage.long_pending`、`webui.credits.usage.unknown` 或 `webui.credits.usage.recovered_unknown` 持续出现时，先保留证据并调查数据库、进程重启、供应商超时与网络事件；不要通过自动重放或批量退款掩盖事实。

## 人工退款和普通调账

管理员通过 `POST /api/v1/credits/admin/accounts/{user_id}/adjustments` 执行人工加减积分。人工退款必须：

1. 使用增加方向。
2. 选择 `manual_refund` 作为 `reason_code`。
3. 在 note 中写明支持工单或 incident 标识、原 usage/ledger 标识和批准理由，且不写入 prompt、Authorization、API key、base64 或原始 IP。
4. 核对返回的新账本行，以及用户余额和管理流水筛选结果。

退款会追加新的正向、不可变 `admin_adjustment` 流水；`manual_refund` 是 reason code，不是独立的 entry type。严禁修改或删除原消费流水、修改 usage 的计价快照，或把“供应商失败”直接等同于自动退款条件。

普通 `accounting_correction` 调账会同时修改账户余额和账本总额，无法消除既有两者差额。因此它只能用于业务加减分，不能用作账务一致性修复。

## 受控一致性修复

消费前会锁定账户并重算完整账本总额；账户余额与账本总额不一致时，消费 fail closed，并增加 `webui.credits.consistency.anomaly`。不得绕开该阻断。

唯一的修复入口是非 HTTP 运维函数：

```python
repair_account_from_ledger(
    session,
    user_id,
    operator,
    incident_id,
    expected_balance,
    note,
    backup_confirmed=True,
)
```

它不由 `/api/v1/credits` router 暴露。操作步骤和不可省略的安全约束如下：

1. 停止对目标账户的人工变更，并取得、验证当前数据库备份；只有完成恢复演练或等效核验后，操作者才可传入 `backup_confirmed=True`。
2. 确认目标用户、incident ID、操作者身份、调查笔记和预计的完整账本总额。incident ID 必须唯一、可打印且能关联工单。
3. 在受控运维环境中调用该函数；它会在同一事务中锁定账户行，重新计算完整账本和，并要求调用方的 `expected_balance` 等于这个刚计算的值。
4. 函数仅将 `account.balance` 单边校准到账本和，随后追加一条 `amount=0`、`entry_type='system_adjustment'` 的不可变证据。证据记录 incident ID、修复前账户余额、差额、操作者快照、原因和时间；它不改变 ledger sum。
5. 函数提交前再次验证账户余额等于账本总额。验证不一致、备份未确认、expected 值过期或账户不存在时，事务回滚。
6. 同一 incident ID 是幂等的：已修复且账户仍一致时返回既有零金额证据。账户之后再次变化时，使用新的 incident ID，并重新备份与调查。
7. 修复后由第二名授权人员核对零金额 evidence、账户余额和完整账本和，并把核验结论写入 incident。

第一阶段不支持反向改写历史账本来追平账户，也不支持通过公开 API 触发受控修复。

## 应用回滚

应用版本回滚的默认策略是**保留**所有 `ext_credit_*` 表、`ext_credit_schema_version`、账户、账本、价目和 usage 数据。不要在应用回滚时删除扩展表、清空 usage 或回退账本流水。

回滚前确认目标应用版本能够读取现有扩展 schema；若不能，停止回滚并准备兼容发布或受控数据迁移。回滚后仍必须通过生命周期迁移和 schema 验证才能 ready。迁移失败时保持 fail closed，恢复到已验证的应用/数据库组合，而不是删除扩展版本记录。

## Redis 限流降级

积分 quote、流水查询和管理员调账使用同步 Redis client。Redis 不可用或 Redis 调用失败时，限流会退回**当前进程**内存，并记录：

- 指标：`webui.credits.rate_limit.fallbacks`
- warning 日志：`Credit rate limiting is using single-process fallback`

多 worker 部署中，进程内存限流不是全局限流。出现 fallback 后：

1. 立即告警并确认 Redis 连通性、认证、TLS、超时和客户端健康状态。
2. 评估当前 worker 数、每个 worker 的请求量及 quote/ledger/adjustment 端点异常增长。
3. 修复 Redis 并观察 fallback 指标恢复为零；必要时扩容或在上游网关临时增加受控限流，但不关闭积分计费或放宽管理员授权。
4. 对 fallback 时段的管理员调账和异常 quote 量进行审计。

## 可观测性和数据最小化

关注以下指标：

- 报价：`webui.credits.quote.success`、`webui.credits.quote.charged_credits`、`webui.credits.quote.price_not_configured`、`webui.credits.quote.price_rule_incomplete`、`webui.credits.quote.rejected`
- 扣费与幂等：`webui.credits.debit.success`、`webui.credits.debit.charged_credits`、`webui.credits.debit.insufficient`、`webui.credits.debit.rejected`、`webui.credits.idempotency.hit`、`webui.credits.idempotency.conflict`
- usage：`webui.credits.usage.debited`、`webui.credits.usage.invoking`、`webui.credits.usage.succeeded`、`webui.credits.usage.failed`、`webui.credits.usage.unknown`、`webui.credits.usage.long_pending`、`webui.credits.usage.recovered_unknown`
- 运维：`webui.credits.admin_adjustment.increase`、`webui.credits.admin_adjustment.decrease`、`webui.credits.admin_adjustment.amount`、`webui.credits.consistency.anomaly`、`webui.credits.rate_limit.fallbacks`

积分 telemetry 标签只允许受控、低敏且有界的 `model`、`action`、`channel`、`error_code`。不得把下列数据写入 metrics attribute、结构化日志、退款 note 或 incident 公共字段：prompt 原文、用户 ID、原始 IP、request ID、Authorization、API key、cookie、base64、完整外部 URL，或来自不受控输入的 model label。指标导出失败是 best-effort，不能改变账务结论。

建议告警：连续的扣费拒绝、幂等冲突异常激增、usage 长期 pending/unknown、恢复任务频繁工作、一致性 anomaly、Redis fallback，以及价目缺失/规则不完整。告警响应应先保全证据并查明原因，不能自动退款或重试供应商。

## PostgreSQL 发布门禁

SQLite 测试不能替代 PostgreSQL 迁移、约束、并发和非 `public` schema 验证。`TEST_POSTGRES_DATABASE_URL` 未设置时，相关 pytest 用例会被 skip；这种 skip 对 CI 和预发布不是可接受的发布证据。

在 CI 和预发布环境必须由 secret 或受控部署配置注入一个隔离、可清理的 PostgreSQL 数据库 URL，并运行完整积分后端套件：

```powershell
if (-not $env:TEST_POSTGRES_DATABASE_URL) { throw 'TEST_POSTGRES_DATABASE_URL must be provided by CI or pre-production secrets' }
$env:PYTHONPATH = 'backend'
python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80
```

```sh
test -n "$TEST_POSTGRES_DATABASE_URL" || { >&2 printf '%s\n' 'TEST_POSTGRES_DATABASE_URL must be provided by CI or pre-production secrets'; exit 1; }
PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80
```

URL 只能由 CI secret 或受控部署配置提供，绝不写入仓库、文档提交或日志。门禁必须覆盖 PostgreSQL 扩展迁移锁、非 `public` schema、约束、原表 fingerprint、并发以及 repair 测试；缺少该变量而被 skip 时，应阻止发布。

## 浏览器 E2E 与真实供应商边界

浏览器验收已落地在 `cypress.config.ts`、`tests/e2e/credits/` 和 `package.json` 的 `test:e2e:credits` script。它覆盖管理员配置多维价目和加分、用户菜单余额、文生图/图生图报价与扣费、供应商失败仍保留已提交扣费、余额不足时供应商调用数为零，以及人工退款新增独立正向流水。

验收使用本地、受控的 OpenAI-compatible `fake_provider.py`，固定 success/failure 并可读取调用计数；绝不访问真实图像供应商，也不能仅用浏览器 `cy.intercept` 代替后端实际供应商请求验证。运行前按仓库已核验方式分别启动 backend、frontend 和 fake provider，并设置 `CYPRESS_BASE_URL`、`API_URL`、`PROVIDER_URL`；确认 Cypress 二进制已经安装后执行：

```powershell
npm run test:e2e:credits
```

缺少浏览器二进制、服务未启动或命令未完整结束时，必须把 E2E 标为未运行或失败，不能以单元测试替代 PASS。

## 上线前最低验证集

以下命令仅在对应环境已准备好依赖后执行；它们不会启动后端长期进程。Windows PowerShell：

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80
python -m ruff check backend/open_webui/extensions/credits backend/open_webui/routers/images.py backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py backend/open_webui/main.py
python -m ruff format --check backend/open_webui/extensions/credits
npm run test:frontend -- --run src/lib/apis/credits src/lib/components/credits src/lib/components/images/Images.test.ts
npx vitest run src/lib/apis/credits/index.test.ts src/lib/components/credits/quote-state.test.ts src/lib/components/credits/admin/admin-form-state.test.ts --coverage --coverage.provider=v8 --coverage.reporter=text --coverage.all=false --coverage.thresholds.lines=80 --coverage.thresholds.functions=80 --coverage.thresholds.statements=80 --coverage.thresholds.branches=80
npm run check
npx prettier --check docs/extensions
npm run test:e2e:credits
```

Linux/macOS shell：

```sh
PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80
PYTHONPATH=backend python -m ruff check backend/open_webui/extensions/credits backend/open_webui/routers/images.py backend/open_webui/tools/builtin.py backend/open_webui/utils/middleware.py backend/open_webui/main.py
PYTHONPATH=backend python -m ruff format --check backend/open_webui/extensions/credits
npm run test:frontend -- --run src/lib/apis/credits src/lib/components/credits src/lib/components/images/Images.test.ts
npx vitest run src/lib/apis/credits/index.test.ts src/lib/components/credits/quote-state.test.ts src/lib/components/credits/admin/admin-form-state.test.ts --coverage --coverage.provider=v8 --coverage.reporter=text --coverage.all=false --coverage.thresholds.lines=80 --coverage.thresholds.functions=80 --coverage.thresholds.statements=80 --coverage.thresholds.branches=80
npm run check
npx prettier --check docs/extensions
npm run test:e2e:credits
```

浏览器 E2E 文件、受控 fake provider 和非交互脚本已经落地；上线前验证必须追加 `npm run test:e2e:credits` 和 PostgreSQL 门禁，不得访问真实支付或真实图像供应商。缺少 Cypress 二进制或依赖服务时，该项保持未通过。
