import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Discover.svelte', import.meta.url)), 'utf-8');

describe('Discover responsive shell', () => {
	test('reserves desktop space for the expanded application sidebar', () => {
		expect(source).toContain('$showSidebar');
		expect(source).toContain('md:max-w-[calc(100%-var(--sidebar-width))]');
		expect(source).toContain('transition-width');
	});

	test('provides the application sidebar toggle on mobile', () => {
		expect(source).toContain('{#if $mobile}');
		expect(source).toContain('id="sidebar-toggle-button"');
		expect(source).toContain('showSidebar.set(!$showSidebar)');
		expect(source).toContain('<SidebarIcon />');
		expect(source).toContain('aria-label={$showSidebar');
	});
});
