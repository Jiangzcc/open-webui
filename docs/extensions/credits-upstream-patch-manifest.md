# 积分扩展上游补丁清单

## 目的和边界

积分功能以 `backend/open_webui/extensions/credits/`、`src/lib/apis/credits/`、
`src/lib/components/credits/` 和 `src/routes/(app)/admin/credits/` 中的独立扩展为主。本清单只记录必须落在 Open WebUI 既有文件上的薄桥接，以及为积分测试增加的构建元数据。

升级 Open WebUI 前后，先比对本清单中的稳定锚点，再运行对应命令。桥接不得通过复制或重写供应商分支来实现；上游图像逻辑继续留在原文件，积分逻辑在公共入口处包装。`docs/superpowers/`、`.gitignore` 和未在本清单列出的改动不是积分运行时桥接，不能以它们替代下列核验。

所有 Python 验证命令均在仓库根目录执行。Windows PowerShell 先设置 `PYTHONPATH`；Linux/macOS shell 使用命令前缀：

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py -q
```

```sh
PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py -q
```

下文的“升级后验证”列出在上述基线之外应额外执行的精确命令。任何静态守卫失败、迁移验证失败或桥接丢失，均应停止升级，不应临时绕开积分计费。

## 后端运行时桥接

### `backend/open_webui/main.py`

| 项目               | 内容                                                                                                                                                                                                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 稳定锚点           | `lifespan(app)`、`app.state.startup_complete = True`，以及 `app.include_router(images.router, prefix='/api/v1/images', tags=['images'])`。                                                                                                                               |
| 为什么不可避免     | 扩展迁移、schema 校验和恢复任务必须在应用宣告 ready 前完成；积分 API 也必须由主 FastAPI 应用注册。独立目录本身不能参与上游生命周期。                                                                                                                                     |
| 精确新增内容       | 导入 `initialize_credit_extension`、`shutdown_credit_extension` 与 `credits_router`；在 `startup_complete=True` 之前 `await initialize_credit_extension(app)`；在共享 session 关闭前 `await shutdown_credit_extension(app)`；注册 `app.include_router(credits_router)`。 |
| 升级后验证         | `PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py backend/open_webui/extensions/credits/tests/test_registration.py -q`。Windows PowerShell 使用本文件开头的 `$env:PYTHONPATH` 形式。                               |
| 删除桥接的失败表现 | `/api/v1/credits` 路由不可用；扩展迁移、版本和约束不再构成 ready 前门禁；恢复 worker 不会启动或在共享资源关闭后被安全停止，可能在未验证 schema 的情况下接受流量。                                                                                                        |

### `backend/open_webui/routers/images.py`

| 项目               | 内容                                                                                                                                                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | 进程内公共中心函数 `image_generations()` 和 `image_edits()`。网页 HTTP、聊天中间件和内置工具均复用这两个入口。                                                                                                                               |
| 为什么不可避免     | 仅在 HTTP 路由扣费无法覆盖聊天和工具的直接函数调用；供应商调用前的预扣费、幂等、usage 状态与 fail-closed 必须在共享中心入口执行。                                                                                                            |
| 精确新增内容       | 导入 `bill_image_call`；两个公开函数各自调用它，分别传入 `text-to-image` 与 `image-to-image` action；原供应商实现机械移动到 `_invoke_image_generations()` 与 `_invoke_image_edits()`，作为 `invoke` 回调。                                   |
| 升级后验证         | `PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py backend/open_webui/extensions/credits/tests/test_security.py backend/open_webui/extensions/credits/tests/test_image_billing.py -q`。 |
| 删除桥接的失败表现 | 直接调用中心函数的渠道可绕开预扣费和 fail-closed；同一业务调用的幂等与 usage 状态失效，导致未审计、重复供应商调用或重复计费的风险。                                                                                                          |

### `backend/open_webui/tools/builtin.py`

| 项目               | 内容                                                                                                                                                                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | 内置工具 `generate_image()`、`edit_image()`，以及已有注入上下文 `__chat_id__`、`__message_id__`。                                                                                                                                       |
| 为什么不可避免     | 工具调用必须把稳定的聊天、消息和工具调用实例传到共享图像入口；工具不应把供应商或账务内部异常原样回显给用户。                                                                                                                            |
| 精确新增内容       | 新增 `_image_credit_metadata()` 与 `_image_tool_error()`；两个工具函数接受 `__metadata__`，调用图像中心函数时传递 `credit_channel='tool'`、聊天/消息标识和 `call_instance_id`；异常返回统一积分错误 envelope。                          |
| 升级后验证         | `PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py backend/open_webui/extensions/credits/tests/test_security.py backend/open_webui/extensions/credits/tests/test_channels.py -q`。 |
| 删除桥接的失败表现 | 工具重放没有稳定业务幂等材料，可能退化为请求级随机键；原始异常、提示词或凭据相关内容可能重新暴露给调用者。                                                                                                                              |

### `backend/open_webui/utils/middleware.py`

| 项目               | 内容                                                                                                                                                                                                                   |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | `chat_image_generation_handler()`、`streaming_chat_response_handler()` 和工具执行时构造的 `extra_params`。                                                                                                             |
| 为什么不可避免     | 聊天自动图像与工具函数不经过浏览器提交路径，必须从已有 chat/message/tool-call 上下文生成可跨重放复用的业务调用标识。                                                                                                   |
| 精确新增内容       | 新增 `build_chat_image_credit_metadata()`：为每个 action 生成同一消息内稳定递增的 `call_instance_id`；新增 `build_tool_credit_metadata()`：以 `tool_call_id` 为调用实例；文生图、图生图和工具调用均传入对应 metadata。 |
| 升级后验证         | `PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests/test_upgrade_guards.py backend/open_webui/extensions/credits/tests/test_channels.py -q`。                                             |
| 删除桥接的失败表现 | 聊天和工具仍可能生成图像，但没有稳定的跨重放幂等键材料；一次消息重放可能被视为新的供应商调用和新的扣费。                                                                                                               |

## 前端运行时桥接

### `src/lib/apis/images/generation.ts`

| 项目               | 内容                                                                                                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | 既有 `/generations` 与 `/edit` 请求、Authorization header 组装处。                                                                                                                |
| 为什么不可避免     | 浏览器主动提交后的网络重试需要复用同一 `Idempotency-Key`，而不是让后端将每次请求视为新调用。                                                                                      |
| 精确新增内容       | 新增可选 `ImageGenerationOptions.idempotencyKey` 与共享 `requestImageGeneration()`；`createImageGeneration()`、`editImageGeneration()` 在有 key 时写入 `Idempotency-Key` header。 |
| 升级后验证         | `npm run test:frontend -- --run src/lib/apis/images/generation.test.ts && npm run check`。                                                                                        |
| 删除桥接的失败表现 | 浏览器重试不会传稳定 key；后端会将重试视为新请求，增加重复调用供应商或重复扣费的风险。                                                                                            |

### `src/lib/components/images/Images.svelte`

| 项目               | 内容                                                                                                                                                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | 页面已有模型、比例、分辨率、张数、参考图状态，`submitHandler` 和生成按钮的 `disabled` 条件。                                                                                                                                    |
| 为什么不可避免     | 报价必须复用实际提交将要发送的参数；提交前需在客户端阻止余额不足、未配置价格和报价异常的请求，并为一次主动提交产生稳定幂等键。                                                                                                  |
| 精确新增内容       | 挂载 `ImageCreditQuoteBadge`；从现有表单状态构造 `ImageQuoteInput` 并使用 `imageQuoteStateMachine` 调度/销毁报价；只有 `isImageQuoteSubmittable()` 时允许提交；通过 UUID 和 `createImageSubmissionIdempotency()` 传递请求 key。 |
| 升级后验证         | `npm run test:frontend -- --run src/lib/components/credits/quote-state.test.ts src/lib/components/credits/ImageCreditQuoteBadge.test.ts src/lib/components/images/Images.test.ts && npm run check`。                            |
| 删除桥接的失败表现 | 用户看不到服务端报价；缺价、余额不足和报价失败不能在提交前禁用生成；重试没有稳定 `Idempotency-Key`。                                                                                                                            |

### `src/lib/components/layout/Sidebar/UserMenu.svelte`

| 项目               | 内容                                                                                                                                                        |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | `<Dropdown bind:show ...>` 内 profile 区块和 help 区块之间的分隔区域。                                                                                      |
| 为什么不可避免     | 余额和个人账本 API 需要一个普通用户可发现的入口；把独立组件挂到既有用户菜单可避免复制 sidebar 逻辑。                                                        |
| 精确新增内容       | 导入并挂载 `CreditMenuEntry`、`CreditLedgerModal`；增加 modal 开关和 `creditRefreshKey`，在菜单项打开流水时关闭 dropdown 并刷新余额。                       |
| 升级后验证         | `npm run test:frontend -- --run src/lib/components/credits/CreditMenuEntry.test.ts src/lib/components/credits/CreditLedgerModal.test.ts && npm run check`。 |
| 删除桥接的失败表现 | 个人余额和流水 API 即使仍可访问，也没有用户菜单入口、余额刷新或流水 modal。                                                                                 |

### `src/routes/(app)/admin/+layout.svelte`

| 项目               | 内容                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| 稳定锚点           | 管理员顶部导航列表，以及现有 analytics、evaluations、functions 链接的 active-state 模式。                     |
| 为什么不可避免     | 管理页面必须在管理员导航中可发现，且应遵循上游导航的 active-state 约定。                                      |
| 精确新增内容       | 新增 `/admin/credits` 链接、`Credit management` 翻译键，以及 `includes('/admin/credits')` active-state 判断。 |
| 升级后验证         | `npm run test:frontend -- --run 'src/routes/(app)/admin/credits/credits-page.test.ts' && npm run check`。     |
| 删除桥接的失败表现 | 管理积分页面只能手工输入 URL，正常管理员导航没有入口。                                                        |

## 构建与测试元数据

这些条目不参与生产请求计费，但它们是当前实际 diff 中为积分验证新增的必要元数据，升级时应与运行时桥接一起复核。

### `package.json` 与 `package-lock.json`

| 项目               | 内容                                                                                                                                                                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 稳定锚点           | 根 `devDependencies` 及 npm lockfile 根 package 解析。                                                                                                                                                                                                 |
| 为什么不可避免     | 新增的前端积分 controller/client 测试需要与当前 Vitest 1.6.1 对齐的 V8 覆盖率提供方。                                                                                                                                                                  |
| 精确新增内容       | `package.json` 新增 `@vitest/coverage-v8: ^1.6.1`；`package-lock.json` 锁定该包及其传递依赖。当前 diff **没有** `test:e2e:credits` script。                                                                                                            |
| 升级后验证         | `npm ci && npx vitest run src/lib/apis/credits src/lib/components/credits --coverage --coverage.provider=v8 --coverage.thresholds.lines=80 --coverage.thresholds.functions=80 --coverage.thresholds.statements=80 --coverage.thresholds.branches=80`。 |
| 删除桥接的失败表现 | 前端积分覆盖率门禁不能可靠运行；不得将现有 Cypress 依赖误写成积分 E2E 已配置或已通过。                                                                                                                                                                 |

### `pyproject.toml` 与 `uv.lock`

| 项目               | 内容                                                                                                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 稳定锚点           | `all` 可选依赖组、`dependency-groups.dev` 和 uv 锁解析。                                                                                                                                                                                                     |
| 为什么不可避免     | 扩展后端测试需要 pytest 8.4、pytest-asyncio、pytest-cov 和 Ruff 的可复现开发环境。                                                                                                                                                                           |
| 精确新增内容       | `all` 组的 pytest 约束更新为 `pytest~=8.4`；dev 组声明 `pytest~=8.4`、`pytest-asyncio>=1,<2`、`pytest-cov>=7,<8`、`ruff>=0.15.5`；`uv.lock` 是该解析结果的 lockfile 更新。                                                                                   |
| 升级后验证         | `PYTHONPATH=backend python -m pytest backend/open_webui/extensions/credits/tests -q --cov=open_webui.extensions.credits --cov-branch --cov-report=term-missing --cov-fail-under=80`，随后执行 `python -m ruff check backend/open_webui/extensions/credits`。 |
| 删除桥接的失败表现 | 后端积分测试和 80% branch coverage 门禁缺少声明的依赖或无法重现；不得把 lockfile 大范围解析变更误解为运行时 schema 变更。                                                                                                                                    |

## 升级后共同验收

1. 比对所有上述锚点，确认只有薄包装、metadata 透传、路由/导航挂载和测试元数据发生了必要变化。
2. 执行 `backend/open_webui/extensions/credits/tests/test_upgrade_guards.py` 与 `test_security.py`；它们覆盖 lifecycle/router、公开图像包装器、metadata、前端挂载、原表 schema fingerprint、权限边界、敏感错误和私有供应商入口约束。
3. 启动后确认扩展版本表是 `ext_credit_schema_version`，且上游 `alembic_version` 与所有非 `ext_` 表未被积分迁移修改。
4. 不要把本清单的验证替代 PostgreSQL、浏览器 E2E 或人工渠道验收；它们是独立发布门禁，详见 [积分扩展运行手册](credits-operations.md)。
