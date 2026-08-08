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

	test('uses a single non-scrolling result and renders uploaded asset previews', () => {
		expect(source).toContain('flex min-h-0 flex-1 overflow-hidden');
		expect(source).not.toContain("$i18n.t('Recent')");
		expect(source).toContain("item.mime_type.startsWith('image/')");
		expect(source).toContain("item.mime_type.startsWith('video/')");
		expect(source).toContain('setAdvancedParam(field, option)');
		expect(source).toContain('updateAdvancedInput(field, event)');
	});

	test('provides creation and video-only library tabs', () => {
		expect(source).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(source).toContain("['generate', 'Create art']");
		expect(source).toContain("['mine', 'My creations']");
		expect(source).toContain("selection = 'all'");
		expect(source).toContain('mediaKind="video"');
	});
});
