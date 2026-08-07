import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./CreditPricingTab.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditPricingTab', () => {
	test('renders and updates every exact-map entry without replacing the values object', () => {
		expect(source).toContain('Object.entries(rule.values as Record<string, string>)');
		expect(source).toContain('updateExactMapEntryKey');
		expect(source).toContain('updateExactMapEntryMultiplier');
		expect(source).not.toContain('as [entryKey, multiplier] (entryKey)');
		expect(source).not.toContain('Object.keys(rule.values as Record<string, string>)[0]');
		expect(source).not.toContain('Object.values(rule.values as Record<string, string>)[0]');
	});

	test('allows mappings to be added and removed while protecting default', () => {
		expect(source).toContain('addExactMapEntry');
		expect(source).toContain('hasBlankExactMapEntry');
		expect(source).toContain('removeExactMapEntry');
		expect(source).toContain("entryKey === 'default'");
		expect(source).toContain("'credits.admin.pricing.addMapping'");
	});

	test('configures proportional per-megapixel pricing from the maintenance form', () => {
		expect(source).toContain('value="proportional"');
		expect(source).toContain("key: 'pixel_count', kind, unit_size: '1000000'");
		expect(source).toContain("rule.kind === 'proportional'");
		expect(source).toContain("'credits.admin.pricing.unitSize'");
		expect(source).toContain("'credits.admin.pricing.proportionalDescription'");
	});

	test('offers image and video services with their supported actions', () => {
		expect(source).toContain('value="video"');
		expect(source).toContain("['text-to-video', 'image-to-video', 'video-to-video']");
		expect(source).toContain('actionsForService(form.serviceType)');
	});
});
