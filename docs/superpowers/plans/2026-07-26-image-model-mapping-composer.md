# 图片页主模型映射与 Composer 布局实施计划

**依据：** `docs/superpowers/specs/2026-07-26-image-model-mapping-composer-design.md`

## 约束

- 仅修改前端图片页、纯函数、测试和中英文 i18n。
- 禁止 worktree；禁止子智能体 Code Review；不 commit、push、PR 或 merge。
- 每项行为先写失败测试并观察预期 RED，再写最小实现并验证 GREEN。
- 参考图缩略图区域保持原位置。
- Composer 在移动与桌面端均响应式、关键操作支持触屏、键盘和 ARIA。

## Task 1：主模型映射纯函数

**文件：**
- `src/lib/utils/image-generation.test.ts`
- `src/lib/utils/image-generation.ts`

1. 为主模型过滤、有效/悬空编辑映射、支持判断、active model 派生添加失败测试。
2. 运行该测试文件，确认因缺少新导出而失败。
3. 添加最小纯函数实现。
4. 运行该测试文件，确认通过。

## Task 2：图片页组件交互

**文件：**
- `src/lib/components/images/Images.test.ts`
- `src/lib/components/images/Images.svelte`

1. 添加失败守卫：模型按钮位于 textarea 前、参考图位置不变、底部单行、弹窗仅主模型且无灰显、能力图标、按支持性控制上传/拖放、显式选择时清除参考图、报价与提交使用 active model。
2. 运行组件测试，确认预期失败。
3. 调整派生状态和事件处理函数，删除旧模式灰显/fallback。
4. 调整 Composer 与模型弹窗模板。
5. 运行组件与纯函数测试，确认通过。

## Task 3：i18n

**文件：**
- `src/lib/i18n/locales/en-US/translation.json`
- `src/lib/i18n/locales/zh-CN/translation.json`

1. 增加“支持参考图片”和“不支持时已移除参考图”的中英文文案。
2. 用 JSON 解析和组件测试验证键名与调用一致。

## Task 4：自动化验证

1. 运行两个定向 Vitest 文件。
2. 对四个前端改动文件和两份翻译运行 Prettier check。
3. 运行 `npm run check`；若被既有诊断阻塞，保存输出并确认改动路径诊断为零。
4. 运行 `git diff --check`。

## Task 5：浏览器验收

1. 桌面视口验证模型按钮、弹窗主模型过滤、图标、参考图映射和清除提示。
2. 移动窄屏验证底部工具栏单行、无横向溢出、弹窗边界和触屏入口。
3. 检查键盘焦点、ARIA、深浅色与中文长度。
