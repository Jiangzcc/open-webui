import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./ImageCreditQuoteBadge.svelte', import.meta.url)),
	'utf-8'
);

describe('ImageCreditQuoteBadge', () => {
	test('shows ready credits with a compact mobile label and credit unit', () => {
		expect(source).toContain("status === 'ready'");
		expect(source).toContain('chargedCredits');
		expect(source).toContain("$i18n.t('credits.common.unit')");
		expect(source).toContain('sr-only');
	});

	test('renders non-submittable quote errors without a charge amount', () => {
		for (const status of ['insufficient', 'unconfigured', 'error'] as const) {
			expect(source).toContain(`status === '${status}'`);
		}
	});

	test('renders no loading label while a quote is pending', () => {
		expect(source).not.toContain("status === 'loading'");
		expect(source).not.toContain("$i18n.t('credits.common.loading')");
	});

	test('registers translations with the i18n instance from the context store', () => {
		expect(source).toContain("getContext<Writable<I18n>>('i18n')");
		expect(source).toContain('registerCreditTranslations($i18n)');
	});

	test('renders the administrator exemption state', () => {
		expect(source).toContain("status === 'exempt'");
		expect(source).toContain("$i18n.t('credits.exempt')");
	});
});
