import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const tabSource = readFileSync(
	fileURLToPath(new URL('./CreditLedgerTab.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditLedgerTab', () => {
	test('searches ledger by username or email instead of internal user id', () => {
		expect(tabSource).toContain("bind:value={filters.user_query}");
		expect(tabSource).toContain("$i18n.t('credits.admin.userQuery')");
		expect(tabSource).not.toContain('filters.user_id');
	});

	test('trims text filters and omits blank values before requesting', () => {
		// 管理员清空搜索框后点“应用筛选”：空值必须转为 undefined 不下发，
		// 后端字符串参数均 min_length=1，空串会触发 422。
		expect(tabSource).toContain('user_query: filters.user_query?.trim() || undefined');
		expect(tabSource).toContain('resource_id: filters.resource_id?.trim() || undefined');
		expect(tabSource).toContain('action: filters.action?.trim() || undefined');
	});
});
