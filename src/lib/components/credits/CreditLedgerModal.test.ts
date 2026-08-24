import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

import {
	buildLedgerQuery,
	failedUsageNotice,
	formatPricingSnapshot,
	ledgerDateRangeError,
	ledgerPaginationCount,
	ledgerResourceName,
	LEDGER_PAGE_SIZE,
	oneYearAgoDate,
	resetLedgerCursor,
	toUnixTimestamp,
	updateLedgerPageCursors
} from './credit-ledger-state';

const modalSource = readFileSync(
	fileURLToPath(new URL('./CreditLedgerModal.svelte', import.meta.url)),
	'utf-8'
);

describe('CreditLedgerModal', () => {
	test('uses keyset cursors for fixed five-entry pages', () => {
		const firstCursor = { created_at: 1_700_000_000, id: 'page-2' };
		const secondCursor = { created_at: 1_699_000_000, id: 'page-3' };
		let cursors = updateLedgerPageCursors([null], 1, firstCursor);

		expect(LEDGER_PAGE_SIZE).toBe(5);
		expect(buildLedgerQuery({ limit: LEDGER_PAGE_SIZE }, cursors[0])).toEqual({
			limit: 5,
			cursor_created_at: undefined,
			cursor_id: undefined
		});
		expect(cursors).toEqual([null, firstCursor]);
		expect(ledgerPaginationCount(1, firstCursor)).toBe(6);

		cursors = updateLedgerPageCursors(cursors, 2, secondCursor);
		expect(cursors).toEqual([null, firstCursor, secondCursor]);
		expect(ledgerPaginationCount(2, secondCursor)).toBe(11);
		expect(ledgerPaginationCount(3, null)).toBe(15);
	});

	test('uses shared select and pagination components instead of native controls', () => {
		expect(modalSource).toContain("import Select from '$lib/components/common/Select.svelte'");
		expect(modalSource).toContain(
			"import Pagination from '$lib/components/common/Pagination.svelte'"
		);
		expect(modalSource).toContain('<Select');
		expect(modalSource).toContain('<Pagination');
		expect(modalSource).toContain('perPage={LEDGER_PAGE_SIZE}');
		expect(modalSource).not.toContain('<select');
		expect(modalSource).toContain('page !== requestedPage');
		expect(modalSource).toContain('(page === 1 || pageCursors[page - 1])');
		expect(modalSource).toContain('void loadLedger(page);');
		expect(modalSource).not.toContain('page > 1 &&');
		expect(modalSource).not.toContain('loadLedger(true)');
	});

	test('builds server-side filter and cursor pagination queries', () => {
		const reset = resetLedgerCursor({
			category: 'consumption',
			since: 1_700_000_000,
			until: 1_700_086_400,
			cursor_created_at: 1_699_999_999,
			cursor_id: 'old-ledger',
			limit: 50
		});

		expect(reset).toEqual({
			category: 'consumption',
			since: 1_700_000_000,
			until: 1_700_086_400,
			limit: 50
		});
		expect(buildLedgerQuery(reset, { created_at: 1_699_000_000, id: 'next-ledger' })).toEqual({
			...reset,
			cursor_created_at: 1_699_000_000,
			cursor_id: 'next-ledger'
		});
	});

	test('limits dates to the most recent 365 days while preserving the selected end date', () => {
		const now = new Date('2026-07-17T12:00:00.000Z');
		const earliest = oneYearAgoDate(now);

		expect(earliest).toBe('2025-07-17');
		expect(toUnixTimestamp('2025-07-16', now)).toBe(toUnixTimestamp(earliest, now));
		expect(toUnixTimestamp('2026-07-18', now)).toBe(toUnixTimestamp('2026-07-17', now));
		expect(toUnixTimestamp('2026-07-17', now, 'end')).toBe(
			Date.parse('2026-07-17T23:59:59.000Z') / 1000
		);
	});

	test('validates the date range before requesting the ledger', () => {
		expect(ledgerDateRangeError({ since: 200, until: 100 })).toBe(
			'credits.errors.invalidDateRange'
		);
		expect(ledgerDateRangeError({ since: 100, until: 200 })).toBeNull();
		expect(ledgerDateRangeError({ since: 100 })).toBeNull();
		expect(modalSource).toContain('const dateRangeError = ledgerDateRangeError(filters);');
		expect(modalSource).toContain('error = $i18n.t(dateRangeError);');
	});

	test('uses accessible date inputs without visible labels', () => {
		expect(modalSource.match(/type="date"/g)).toHaveLength(2);
		expect(modalSource).toContain("aria-label={$i18n.t('credits.common.from')}");
		expect(modalSource).toContain("aria-label={$i18n.t('credits.common.to')}");
		expect(modalSource).toContain('>—</span>');
		expect(modalSource).not.toContain('<label class="flex items-center');
	});

	test('maps resource ids to model display names across id namespaces', () => {
		const models = [
			{ id: 'fal-ai/z-image/turbo', name: 'fal.ai / Z Image Turbo' },
			{ id: 'fal-ai/wan/v2.6/text-to-image', publicId: 'wan-2.6', name: 'Alibaba / Wan 2.6' },
			{ id: 'fal-ai/other', name: 'Other Model' }
		];

		expect(ledgerResourceName('fal-ai/z-image/turbo', models)).toBe('Z Image Turbo');
		// 管理端列表 id 为内部 ID，账目 resource_id 为公开 ID，需按 publicId 关联。
		expect(ledgerResourceName('wan-2.6', models)).toBe('Wan 2.6');
		// 匹配不到时回退显示资源 ID 本身（后端已保证是公开 ID），避免资源列为空。
		expect(ledgerResourceName('wan-2.7-video', models)).toBe('wan-2.7-video');
		expect(ledgerResourceName(null, models)).toBe('—');
		expect(modalSource).toContain('normalizeImageGenerationModels,');
		expect(modalSource).toContain("from '$lib/utils/image-generation';");
		expect(modalSource).toContain('imageModels = normalizeImageGenerationModels(result);');
		expect(modalSource).toContain('ledgerResourceName(entry.resource_id, imageModels)');
		expect(modalSource).not.toContain("entry.resource_id ?? entry.action ?? '—'");
	});

	test('renders only bounded pricing factors without sensitive snapshot fields', () => {
		expect(
			formatPricingSnapshot({
				factors: [
					{ key: 'size', value: '1024x1024', multiplier: '1.5' },
					{ key: 'image_count', value: 2, multiplier: '2' }
				],
				base_price: '100',
				prompt: 'private prompt',
				error_snapshot: 'provider error',
				image_base64: 'data:image/png;base64,secret'
			})
		).toBe('size: 1024x1024 · image_count: 2');
	});

	test('translates pricing factor keys to user-facing dimension labels', () => {
		const labelFor = (key: string) =>
			({ image_count: '图片数量', resolution: '分辨率' })[key] ?? key;

		expect(
			formatPricingSnapshot(
				{ factors: [{ key: 'image_count', value: 1 }, { key: 'custom_key', value: 'x' }] },
				labelFor
			)
		).toBe('图片数量: 1 · custom_key: x');
		expect(modalSource).toContain('pricingFactorLabel = (key: string)');
	});

	test('uses credit-specific filter and failed-charge translations', () => {
		expect(failedUsageNotice('failed')).toBe(true);
		expect(failedUsageNotice('succeeded')).toBe(false);
		expect(modalSource).toContain("$i18n.t('credits.filters.all')");
		expect(modalSource).toContain("$i18n.t('credits.filters.income')");
		expect(modalSource).toContain("$i18n.t('credits.filters.consumption')");
		expect(modalSource).toContain("$i18n.t('credits.filters.adjustment')");
		expect(modalSource).toContain("$i18n.t('credits.status.failedCharged')");
	});

	test('loads the balance and first ledger page whenever the modal opens', () => {
		expect(modalSource).toContain('$: if (show) {');
		expect(modalSource).toContain(
			'void Promise.all([refreshBalance(), loadImageModels(), loadLedger(1)]);'
		);
		expect(modalSource).not.toContain('$: wasShown = show;');
	});
});
