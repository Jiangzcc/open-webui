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
});
