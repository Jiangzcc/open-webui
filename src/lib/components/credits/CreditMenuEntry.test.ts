import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

import {
	idleCreditBalanceState,
	shouldRefreshCreditBalance,
	unavailableCreditBalanceState
} from './credit-ledger-state';

const componentSource = readFileSync(
	fileURLToPath(new URL('./CreditMenuEntry.svelte', import.meta.url)),
	'utf-8'
);
const userMenuSource = readFileSync(
	fileURLToPath(new URL('../layout/Sidebar/UserMenu.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditMenuEntry', () => {
	test('loads when the dropdown opens and refreshes after it is reopened', () => {
		expect(shouldRefreshCreditBalance(false, true)).toBe(true);
		expect(shouldRefreshCreditBalance(true, true)).toBe(false);
		expect(shouldRefreshCreditBalance(true, false)).toBe(false);
		expect(shouldRefreshCreditBalance(false, true)).toBe(true);
	});

	test('keeps the rest of the menu usable when the balance service is unavailable', () => {
		expect(unavailableCreditBalanceState(idleCreditBalanceState())).toEqual({
			status: 'unavailable',
			balance: null
		});
	});

	test('uses a thin UserMenu bridge without a recharge or payment action', () => {
		expect(userMenuSource).toContain(
			"import CreditMenuEntry from '$lib/components/credits/CreditMenuEntry.svelte';"
		);
		expect(userMenuSource).toContain('<CreditMenuEntry');
		expect(userMenuSource).toMatch(/show = false;\s+showCreditLedgerModal = true;/);
		expect(componentSource).not.toMatch(/recharge|payment/i);
	});

	test('matches the compact visual language of the upstream UserMenu items', () => {
		expect(componentSource).toContain('h-11');
		expect(componentSource).toContain('sm:h-[1.6875rem]');
		expect(componentSource).toContain('gap-2 rounded-xl px-2 text-left text-[13px]');
		expect(componentSource).toContain('hover:bg-gray-50/40');
		expect(componentSource).toContain('dark:hover:bg-gray-800/40');
		expect(componentSource).toContain("import CreditCoins from './CreditCoins.svelte'");
		expect(componentSource).toContain('CreditCoins className="size-3.5"');
		expect(componentSource).not.toContain('ChartBar');
		expect(componentSource).toContain('text-[11px] leading-none text-gray-500 tabular-nums');
		expect(componentSource).not.toContain('rounded-xl px-3 py-1.5');
	});

	test('lets only the latest balance request update visible state', () => {
		expect(componentSource).toContain('if (requestController !== controller) return;');
		expect(componentSource).toContain(
			'if (requestController === controller) requestController = null;'
		);
	});
});
