import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const tabSource = readFileSync(
	fileURLToPath(new URL('./CreditPricingTab.svelte', import.meta.url)),
	'utf-8'
);

const modalSource = readFileSync(
	fileURLToPath(new URL('./CreditPriceModal.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditPricingTab', () => {
	test('delegates create and edit to the modal and keeps filters plus pagination in the tab', () => {
		// 新建/编辑改走弹窗：表格行只保留触发入口，表单状态由 CreditPriceModal 持有。
		expect(tabSource).toContain("import CreditPriceModal from './CreditPriceModal.svelte'");
		expect(tabSource).toContain('bind:show={showPriceModal}');
		expect(tabSource).toContain('price={editingPrice}');
		expect(tabSource).not.toContain('on:submit|preventDefault');
		expect(tabSource).not.toContain('addRule');
		// 筛选与页码分页留在 tab 层。
		expect(tabSource).toContain('bind:page count={total}');
		expect(tabSource).toContain('applyFilters');
	});

	test('normalizes cleared resource filters before requesting a page', () => {
		expect(tabSource).toContain('resource_id: filters.resource_id?.trim() || undefined');
	});

	test('returns to the previous page after deleting its final row', () => {
		expect(tabSource).toContain('if (prices.length === 1 && page > 1)');
		expect(tabSource).toContain('page -= 1');
	});

	test('keeps the i18n context typed as a writable store', () => {
		expect(tabSource).toContain("getContext<Writable<I18n>>('i18n')");
		expect(modalSource).toContain("getContext<Writable<I18n>>('i18n')");
	});

	test('renders and updates every exact-map entry without replacing the values object', () => {
		expect(modalSource).toContain('Object.entries(rule.values as Record<string, string>)');
		expect(modalSource).toContain('updateExactMapEntryKey');
		expect(modalSource).toContain('updateExactMapEntryMultiplier');
		expect(modalSource).not.toContain('as [entryKey, multiplier] (entryKey)');
		expect(modalSource).not.toContain('Object.keys(rule.values as Record<string, string>)[0]');
		expect(modalSource).not.toContain('Object.values(rule.values as Record<string, string>)[0]');
	});

	test('allows mappings to be added and removed while protecting default', () => {
		expect(modalSource).toContain('addExactMapEntry');
		expect(modalSource).toContain('hasBlankExactMapEntry');
		expect(modalSource).toContain('removeExactMapEntry');
		expect(modalSource).toContain("entryKey === 'default'");
		expect(modalSource).toContain("'credits.admin.pricing.addMapping'");
	});

	test('configures proportional per-megapixel pricing from the maintenance form', () => {
		expect(modalSource).toContain('value="proportional"');
		expect(modalSource).toContain("key: 'pixel_count', kind, unit_size: '1000000'");
		expect(modalSource).toContain("rule.kind === 'proportional'");
		expect(modalSource).toContain("'credits.admin.pricing.unitSize'");
		expect(modalSource).toContain("'credits.admin.pricing.proportionalDescription'");
	});

	test('offers image and video services with their supported actions', () => {
		expect(modalSource).toContain('value="video"');
		expect(modalSource).toContain("['text-to-video', 'image-to-video', 'video-to-video']");
		expect(modalSource).toContain('actionsForService(form.serviceType)');
	});
});
