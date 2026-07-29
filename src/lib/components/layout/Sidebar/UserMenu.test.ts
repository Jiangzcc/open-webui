import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./UserMenu.svelte', import.meta.url)), 'utf-8');

describe('user menu merge contracts', () => {
	test('uses the upstream icon names for the custom Images entry', () => {
		expect(source).toContain("import Photo from '$lib/components/icons/Photo.svelte'");
		expect(source).toContain('<Photo className="size-5"');
		expect(source).toContain('<PinIcon className="size-3.5"');
		expect(source).toContain('<PinSlashIcon className="size-3.5"');
		expect(source).not.toMatch(/<(Pin|PinSlash)\s/);
	});
});
