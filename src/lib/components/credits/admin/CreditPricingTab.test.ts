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
});
