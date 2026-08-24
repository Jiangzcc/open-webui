import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./GenerationModelSelector.svelte', import.meta.url)),
	'utf-8'
);

describe('GenerationModelSelector', () => {
	test('uses dialog semantics instead of an incomplete listbox pattern', () => {
		expect(source).toContain('aria-haspopup="dialog"');
		expect(source).toContain('role="dialog"');
		expect(source).not.toContain('role="listbox"');
		expect(source).not.toContain('role="option"');
	});

	test('uses native disabled behavior and mobile touch targets', () => {
		expect(source).toContain('disabled={model.enabled === false}');
		expect(source).toContain('min-h-11');
		expect(source).toContain('sm:h-8');
	});
});
