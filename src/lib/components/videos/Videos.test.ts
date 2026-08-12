import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Videos.svelte', import.meta.url)), 'utf-8');

describe('video creation page', () => {
	test('uses a duration slider and the shared generation button', () => {
		expect(source).toContain('type="range"');
		expect(source).toContain('durationChoices[Number(event.currentTarget.value)]');
		expect(source).toContain('<GenerationSubmitButton');
		expect(source).not.toContain('grid grid-cols-4 gap-1.5 sm:grid-cols-6');
	});

	test('keeps modes and the model on one toolbar and shows short names with pricing', () => {
		// 模式标签栏改为移动端换行、不再依赖固定右内边距给模型留位
		expect(source).toContain('hidden flex-wrap gap-1 sm:flex sm:flex-nowrap sm:justify-end');
		// 模型选择器从 absolute 定位改为表单上方正常文档流
		expect(source).toContain('mb-2 flex flex-row items-center justify-between gap-2');
		expect(source).not.toContain('absolute bottom-full');
		// 模型短名与价格现在通过共享 GenerationModelSelector 渲染：
		// 页面把 VideoModel 归一化为 SelectableModel，name 走 stripVendorFromName；
		// 价格在 extras 槽里读 (model.raw as VideoModel).base_price。
		expect(source).toContain('name: stripVendorFromName(model)');
		expect(source).toContain('(model.raw as VideoModel).base_price');
		expect(source).not.toContain('<span class="min-w-0 flex-1 truncate">{model.name}</span>');
	});

	test('uses a scrollable task list and renders uploaded asset previews', () => {
		// 结果区从「单一非滚动活动任务」改为「可滚动任务列表流」，新任务插顶并轮询刷新。
		expect(source).toContain('flex-1 min-h-0 overflow-y-auto');
		expect(source).toContain('{#each history as taskItem (taskItem.id)}');
		expect(source).not.toContain("$i18n.t('Recent')");
		expect(source).toContain("item.mime_type.startsWith('image/')");
		expect(source).toContain("item.mime_type.startsWith('video/')");
		expect(source).toContain('setAdvancedParam(field, option)');
		expect(source).toContain('updateAdvancedInput(field, event)');
	});

	test('renders only curated advanced fields with responsive and accessible controls', () => {
		expect(source).toContain('selectedModel?.advanced_fields ?? []');
		expect(source).toContain('id="video-advanced-settings"');
		expect(source).toContain('aria-controls="video-advanced-settings"');
		expect(source).toContain('grid min-w-0 gap-4 sm:grid-cols-2');
		expect(source).toContain("inputmode={field.kind === 'integer' ? 'numeric' : 'decimal'}");
		expect(source).toContain('aria-describedby={advancedErrorLabel(field)');
		expect(source).toContain('normalizeVideoParamsForModel');
		expect(source).toContain('Boolean(advancedError)');
		expect(source).not.toContain('...(selectedModel.json_fields ?? [])');
		expect(source).not.toContain("field.format === 'json'");
	});

	test('matches the image parameter popover visual system', () => {
		expect(source).toContain('w-[min(27rem,calc(100vw-4rem))]');
		expect(source).toContain('rounded-2xl border border-gray-100 bg-white p-3 shadow-xl sm:p-4');
		expect(source).toContain('flex h-14 min-w-0 flex-col items-center justify-center');
		expect(source).toContain('aspectRatioPreviewStyle(value)');
		expect(source).toContain('flex min-h-11 w-full items-center justify-between rounded-xl px-1');
		expect(source).toContain("{showAdvanced ? '−' : '+'}");
		expect(source).toContain('border border-gray-200 bg-transparent');
	});

	test('renders result action row with regenerate, download, details and remove', () => {
		// 结果区操作按钮放在视频下方独立行，不再用绝对定位浮层盖住播放器控件
		expect(source).not.toContain('absolute bottom-3 right-3');
		// 操作对象由单一 activeTask 改为列表项 taskItem
		expect(source).toContain('reuseTask(taskItem)');
		expect(source).toContain('downloadResult(taskItem)');
		expect(source).toContain('requestDeleteTask(taskItem)');
		expect(source).toContain("$i18n.t('Regenerate')");
		expect(source).toContain("$i18n.t('Download')");
		expect(source).toContain("$i18n.t('View details')");
		expect(source).toContain("$i18n.t('Remove')");
		// 「查看详情并发布」文案改为单纯的「查看详情」
		expect(source).not.toContain("$i18n.t('View details and publish')");
	});

	test('renders a result card with model header, prompt, meta pills and action row', () => {
		// 学习图片结果区：消息头（厂商图标 + 模型短名 + 时间）+ prompt + pill 参数行 + 操作行
		expect(source).toContain('VIDEO_TASK_ARTICLE_CLASS');
		expect(source).toContain('getTaskModelLabel');
		expect(source).toContain('getTaskMetaPills');
		expect(source).toContain('getTaskTime');
		expect(source).toContain('videoTaskStatusLabel');
		expect(source).toContain('VendorLogo');
	});

	test('provides creation and video-only library tabs', () => {
		expect(source).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(source).toContain("['generate', 'Create art']");
		expect(source).toContain("['mine', 'My creations']");
		expect(source).toContain("selection = 'all'");
		expect(source).toContain('mediaKind="video"');
	});
});
