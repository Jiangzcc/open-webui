import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./CreditDimensionsTab.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditDimensionsTab', () => {
	test('displays dimension keys using their original field names', () => {
		expect(source).toContain('{dimension.key}');
		expect(source).not.toContain("dimensionLabel('dimensionKeys', dimension.key)");
	});
});
