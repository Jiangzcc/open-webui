import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const read = (relative: string) =>
	readFileSync(fileURLToPath(new URL(relative, import.meta.url)), 'utf-8');

// 拆分后页面源码分布在四个文件：主页面（状态/提交/SSE）、表单（模型/参数/选项）、
// 任务卡片（结果展示）与共享文案映射。
const page = read('./Videos.svelte');
const form = read('./VideoPromptForm.svelte');
const card = read('./VideoTaskCard.svelte');
const labels = read('./videoLabels.ts');
const idempotency = read('../../utils/submission-idempotency.ts');
const all = [page, form, card, labels, idempotency].join('\n');

describe('video creation page', () => {
	test('uses a duration slider and the shared generation button', () => {
		expect(form).toContain('type="range"');
		expect(form).toContain('durationChoices[Number(event.currentTarget.value)]');
		expect(form).toContain('<GenerationSubmitButton');
		expect(all).not.toContain('grid grid-cols-4 gap-1.5 sm:grid-cols-6');
	});

	test('inserts tag text into the prompt and negative-prompt param on picker click', () => {
		// 标签退化为快捷提示词片段：点击即把 insert_text 追加进输入框，
		// 提交/落库都是所见即所得的纯文本（负面标签进 negative_prompt 参数）。
		expect(page).toContain('appendPromptText(prompt, text)');
		expect(page).toContain(
			"negative_prompt: appendPromptText(String(params['negative_prompt'] ?? ''), text)"
		);
		expect(page).toContain('prompt: prompt.trim()');
		expect(all).not.toContain('composePromptWithTags');
	});

	test('keeps modes and the model on one toolbar and shows short names with pricing', () => {
		// 模式标签栏改为移动端换行、不再依赖固定右内边距给模型留位
		expect(form).toContain('hidden flex-wrap gap-1 sm:flex sm:flex-nowrap sm:justify-end');
		// 模型选择器从 absolute 定位改为表单上方正常文档流
		expect(form).toContain('mb-2 flex flex-row items-center justify-between gap-2');
		expect(all).not.toContain('absolute bottom-full');
		// 模型短名与价格现在通过共享 GenerationModelSelector 渲染：
		// 页面把 VideoModel 归一化为 SelectableModel，name 走 stripVendorFromName；
		// 价格在 extras 槽里读 (model.raw as VideoModel).base_price。
		expect(form).toContain('name: stripVendorFromName(model)');
		expect(form).toContain('(model.raw as VideoModel).base_price');
		expect(all).not.toContain('<span class="min-w-0 flex-1 truncate">{model.name}</span>');
	});

	test('uses a scrollable task list and renders uploaded asset previews', () => {
		// 结果区从「单一非滚动活动任务」改为「可滚动任务列表流」，新任务插顶并轮询刷新。
		expect(page).toContain('flex-1 min-h-0 overflow-y-auto');
		expect(page).toContain('{#each history as taskItem (taskItem.id)}');
		expect(all).not.toContain("$i18n.t('Recent')");
		expect(form).toContain("item.mime_type.startsWith('image/')");
		expect(form).toContain("item.mime_type.startsWith('video/')");
		expect(form).toContain('setAdvancedParam(field, option)');
		expect(form).toContain('updateAdvancedInput(field, event)');
	});

	test('renders only curated advanced fields with responsive and accessible controls', () => {
		expect(page).toContain('selectedModel?.advanced_fields ?? []');
		expect(form).toContain('id="video-advanced-settings"');
		expect(form).toContain('aria-controls="video-advanced-settings"');
		expect(form).toContain('grid min-w-0 gap-4 sm:grid-cols-2');
		expect(form).toMatch(
			/inputmode=\{field\.kind === 'integer'\s*\?\s*'numeric'\s*:\s*'decimal'\}/
		);
		expect(form).toContain('aria-describedby={advancedErrorLabel(field)');
		expect(page).toContain('normalizeVideoParamsForModel');
		expect(form).toContain('Boolean(advancedError)');
		expect(all).not.toContain('...(selectedModel.json_fields ?? [])');
		expect(all).not.toContain("field.format === 'json'");
	});

	test('matches the image parameter popover visual system', () => {
		expect(form).toContain('w-[min(27rem,calc(100vw-4rem))]');
		expect(form).toContain('rounded-2xl border border-gray-100 bg-white p-3 shadow-xl sm:p-4');
		expect(form).toContain('flex h-14 min-w-0 flex-col items-center');
		expect(form).toContain('aspectRatioPreviewStyle(value)');
		expect(form).toContain('flex min-h-11 w-full items-center justify-between rounded-xl px-1');
		expect(form).toContain("{showAdvanced ? '−' : '+'}");
		expect(form).toContain('border border-gray-200 bg-transparent');
	});

	test('renders result action row with regenerate, download, details and remove', () => {
		// 结果区操作按钮放在视频下方独立行，不再用绝对定位浮层盖住播放器控件
		expect(all).not.toContain('absolute bottom-3 right-3');
		// 操作对象由单一 activeTask 改为列表项（回调传给任务卡片组件）
		expect(page).toContain('onRegenerate={reuseTask}');
		expect(page).toContain('onDownload={downloadResult}');
		expect(page).toContain('onRemove={requestDeleteTask}');
		expect(card).toContain("$i18n.t('Regenerate')");
		expect(card).toContain("$i18n.t('Download')");
		expect(card).toContain("$i18n.t('View details')");
		expect(card).toContain("$i18n.t('Remove')");
		// 「查看详情并发布」文案改为单纯的「查看详情」
		expect(all).not.toContain("$i18n.t('View details and publish')");
	});

	test('renders a result card with model header, prompt, meta pills and action row', () => {
		// 学习图片结果区：消息头（厂商图标 + 模型短名 + 时间）+ prompt + pill 参数行 + 操作行
		expect(card).toContain('VIDEO_TASK_ARTICLE_CLASS');
		expect(card).toContain('getTaskModelLabel');
		expect(card).toContain('getTaskMetaPills');
		expect(card).toContain('getTaskTime');
		expect(card).toContain('videoTaskStatusLabel');
		expect(card).toContain('VendorLogo');
	});

	test('provides creation and video-only library tabs', () => {
		expect(page).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(page).toContain("['generate', 'Create art']");
		expect(page).toContain("['mine', 'My creations']");
		expect(page).toContain("selection = 'all'");
		expect(page).toContain('mediaKind="video"');
	});

	test('maps CreditError codes to specific i18n messages instead of generic failure', () => {
		// 修复 5：后端 CreditError 返回 {code, message, context}，前端需读取 code 并映射到 i18n。
		// 验证 error code → i18n key 映射表存在且覆盖关键错误码。
		expect(labels).toContain('videoCreditErrorI18nKey');
		expect(labels).toContain("insufficient_credits: 'Insufficient credits'");
		expect(labels).toContain("price_not_configured: 'Video price is not configured'");
		expect(labels).toContain('rate_limited');
		// 验证 generate() catch 块使用了映射而非通用消息
		expect(page).toContain('videoCreditErrorI18nKey[code]');
		expect(page).toContain("'Video generation failed'");
	});

	test('explains provider and local delivery failures separately', () => {
		expect(labels).toContain('videoTaskErrorI18nKey');
		expect(labels).toContain(
			"video_delivery_failed: 'The provider generated the video, but local delivery failed'"
		);
		expect(labels).toContain("video_provider_timeout: 'The video provider timed out'");
		expect(page).toContain('toast.error(videoTaskErrorMessage(next))');
	});

	test('reuses the same idempotency key after an uncertain network failure', () => {
		// 幂等键实现已泛化为 submission-idempotency.ts（图片/视频共享工厂）。
		expect(idempotency).toContain('createSubmissionIdempotency');
		expect(idempotency).toContain('stored?.fingerprint === fingerprint');
		expect(page).toContain(
			"const videoSubmissionIdempotency = createSubmissionIdempotency('pending-video-submission')"
		);
		expect(page).toContain(
			'const idempotencyKey = await videoSubmissionIdempotency.idempotencyKeyFor(submission)'
		);
		expect(page).toContain('![408, 429].includes(error.status)');
	});
});
