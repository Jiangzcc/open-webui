import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const tabSource = readFileSync(
	fileURLToPath(new URL('./CreditReconciliationTab.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditReconciliationTab', () => {
	test('searches reconciliation cases by username or email instead of internal user id', () => {
		expect(tabSource).toContain('bind:value={userQuery}');
		expect(tabSource).toContain("$i18n.t('credits.admin.userQuery')");
		expect(tabSource).toContain('user_query: userQuery.trim() || undefined');
		expect(tabSource).not.toContain('userId');
	});
});
