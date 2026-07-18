import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const pageSource = readFileSync(fileURLToPath(new URL('./+page.svelte', import.meta.url)), 'utf-8');
const layoutSource = readFileSync(
	fileURLToPath(new URL('../+layout.svelte', import.meta.url)),
	'utf-8'
);

describe('admin credit page composition', () => {
	test('composes the four dedicated credit tabs without embedding their state', () => {
		expect(pageSource).toContain(
			"import CreditAccountsTab from '$lib/components/credits/admin/CreditAccountsTab.svelte'"
		);
		expect(pageSource).toContain(
			"import CreditLedgerTab from '$lib/components/credits/admin/CreditLedgerTab.svelte'"
		);
		expect(pageSource).toContain(
			"import CreditPricingTab from '$lib/components/credits/admin/CreditPricingTab.svelte'"
		);
		expect(pageSource).toContain(
			"import CreditDimensionsTab from '$lib/components/credits/admin/CreditDimensionsTab.svelte'"
		);
		expect(pageSource).toContain("let selectedTab: CreditTab = 'accounts'");
		expect(pageSource).toContain('<CreditAccountsTab />');
		expect(pageSource).toContain('<CreditLedgerTab />');
		expect(pageSource).toContain('<CreditPricingTab />');
		expect(pageSource).toContain('<CreditDimensionsTab />');
	});

	test('adds a credit navigation entry with an active state and no payment UI', () => {
		expect(layoutSource).toContain("$page.url.pathname.includes('/admin/credits')");
		expect(layoutSource).toContain('href="/admin/credits"');
		expect(pageSource).not.toMatch(/payment|充值|recharge/i);
	});
});
