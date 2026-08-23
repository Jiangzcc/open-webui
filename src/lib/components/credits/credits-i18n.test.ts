import i18next from 'i18next';
import { writable } from 'svelte/store';
import { describe, expect, test } from 'vitest';

import zhTranslation from '$lib/i18n/locales/zh-CN/translation.json';

import { registerCreditTranslations, translateCreditApiError } from './credits-i18n';

describe('credit translations', () => {
	test('registers Chinese and English translations without replacing existing keys', async () => {
		const i18n = i18next.createInstance();
		await i18n.init({
			lng: 'en-US',
			fallbackLng: false,
			resources: {
				'en-US': { translation: { credits: { balance: 'Existing balance' } } }
			}
		});

		registerCreditTranslations(i18n);
		registerCreditTranslations(i18n);

		expect(i18n.t('credits.balance')).toBe('Existing balance');
		expect(i18n.t('credits.unavailable')).toBe('Credit service is unavailable');
		expect(i18n.t('credits.ledger')).toBe('Credit ledger');
		expect(i18n.t('credits.filters.all')).toBe('All');
		expect(i18n.t('credits.status.failedCharged')).toBe(
			'Generation failed; credits were charged according to the pricing rule'
		);
		expect(i18n.t('credits.admin.accounts')).toBe('Accounts');

		await i18n.changeLanguage('zh-CN');
		expect(i18n.t('credits.balance')).toBe('积分');
		expect(i18n.t('credits.unavailable')).toBe('积分服务暂不可用');
		expect(i18n.t('credits.filters.consumption')).toBe('消费');
		expect(i18n.t('credits.status.failedCharged')).toBe('生成失败，已按规则扣费');
		expect(i18n.t('credits.common.unit')).toBe('积分');
		expect(i18n.t('credits.admin.management')).toBe('积分管理');
		expect(i18n.t('credits.admin.accountsTitle')).toBe('积分账户');
		expect(i18n.t('credits.admin.adjustment.saved')).toBe('积分调整已保存');
		expect(i18n.t('credits.admin.pricing.ruleKinds.exact_map')).toBe('精确映射');
		expect(i18n.t('credits.admin.pricing.ruleKinds.proportional')).toBe('按单位线性计费');
		expect(i18n.t('credits.dimensionKeys.pixel_count')).toBe('像素数');
		expect(i18n.t('credits.actions.text-to-image')).toBe('文生图');
		expect(i18n.t('credits.dimensionKeys.image_count')).toBe('图片数量');
		expect(i18n.t('credits.common.applyFilters')).toBe('应用筛选');
		expect(i18n.t('credits.validation.positiveWholeNumber')).toBe('请输入正整数');
	});

	test('keeps the admin navigation label translated before the credit page mounts', () => {
		expect(zhTranslation['Credit management']).toBe('积分管理');
	});

	test('registers translations through the Svelte i18n store used by application context', async () => {
		const instance = i18next.createInstance();
		await instance.init({ lng: 'en-US', fallbackLng: false });
		const contextI18n = writable(instance);

		registerCreditTranslations(contextI18n);

		expect(instance.t('credits.balance')).toBe('Credits');
		expect(instance.t('credits.admin.accounts')).toBe('Accounts');
	});

	test('translates stable credit API error codes instead of displaying English server messages', async () => {
		const i18n = i18next.createInstance();
		await i18n.init({ lng: 'zh-CN', fallbackLng: false });
		registerCreditTranslations(i18n);

		expect(
			translateCreditApiError(
				i18n,
				{ code: 'invalid_adjustment', message: 'Credit adjustment is invalid', context: {} },
				'credits.unavailable'
			)
		).toBe('积分调整无效');
		expect(
			translateCreditApiError(
				i18n,
				{ code: 'unknown_error', message: 'Untranslated server detail', context: {} },
				'credits.admin.accountsLoadError'
			)
		).toBe('无法加载积分账户');
	});

	test('translates endpoint rate limits and surfaces backend rejection reasons', async () => {
		/** 回归（对抗性审查）：FastAPI HTTPException 形态（{code, reason?}）此前
		 * 全部回退成 credit_service_unavailable，限流被误报成基础设施故障、
		 * 修复校验失败的真实原因丢失。 */
		const i18n = i18next.createInstance();
		await i18n.init({ lng: 'zh-CN', fallbackLng: false });
		registerCreditTranslations(i18n);

		expect(
			translateCreditApiError(
				i18n,
				{ code: 'rate_limit_exceeded', message: '', context: {} },
				'credits.redeem.failed'
			)
		).toBe('请求过于频繁，请稍后再试');
		expect(
			translateCreditApiError(
				i18n,
				{
					code: 'invalid_repair_request',
					message: '',
					context: { reason: 'expected_balance does not match the ledger total' }
				},
				'credits.admin.repair.saveError'
			)
		).toBe('expected_balance does not match the ledger total');
		expect(
			translateCreditApiError(
				i18n,
				{ code: 'invalid_request_id', message: '', context: {} },
				'credits.admin.repair.saveError'
			)
		).toBe(i18n.t('credits.admin.repair.saveError'));
	});
});
