import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./focusTrap.ts', import.meta.url)), 'utf-8');

describe('trapFocus', () => {
	test('cancels deferred focus and excludes hidden or inert targets', () => {
		expect(source).toContain('cancelAnimationFrame(focusFrame)');
		expect(source).toContain("!element.closest('[inert]')");
		expect(source).toContain('element.getClientRects().length > 0');
	});

	test('removes its temporary tabindex and restores only a live trigger', () => {
		expect(source).toContain("if (addedNodeTabIndex) node.removeAttribute('tabindex')");
		expect(source).toContain('previouslyFocused?.isConnected');
	});

	test('lets keyboard users dismiss a modal with Escape', () => {
		expect(source).toContain("if (e.key === 'Escape')");
		expect(source).toContain('close?.()');
	});
});
