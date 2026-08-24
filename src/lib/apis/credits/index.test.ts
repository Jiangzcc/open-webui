import { afterEach, describe, expect, test, vi } from 'vitest';

import {
	adjustCreditAccount,
	compensateCreditReconciliationCase,
	createCreditPrice,
	deleteCreditPrice,
	getAdminCreditAccounts,
	getAdminCreditDimensions,
	getAdminCreditLedger,
	getCreditPrices,
	getCreditReconciliationCases,
	getMyCreditLedger,
	getMyCredits,
	quoteImageCredits,
	updateCreditPrice,
	type CreditApiError
} from './index';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

const success = (body: unknown) =>
	new Response(JSON.stringify(body), {
		status: 200,
		headers: { 'Content-Type': 'application/json' }
	});

afterEach(() => {
	fetchMock.mockReset();
});

describe('credit API client', () => {
	test('sends authenticated credit requests with query, body, and AbortSignal', async () => {
		const controller = new AbortController();
		fetchMock
			.mockResolvedValueOnce(success({ balance: 120 }))
			.mockResolvedValueOnce(
				success({
					balance: 120,
					sufficient: true,
					exempt: false,
					configured: true,
					factors: [],
					charged_credits: 8,
					error: null
				})
			)
			.mockResolvedValueOnce(success({ items: [], next_cursor: null }))
			.mockResolvedValueOnce(success({ items: [], total: 0 }))
			.mockResolvedValueOnce(
				success({ ledger_id: 'ledger-1', source: 'api', request_id: 'request-1' })
			)
			.mockResolvedValueOnce(success({ items: [], total: 0 }))
			.mockResolvedValueOnce(success({ items: [], total: 0 }))
			.mockResolvedValueOnce(success({ id: 'price-1' }))
			.mockResolvedValueOnce(success({ id: 'price-1', enabled: false }))
			.mockResolvedValueOnce(success({ id: 'price-1' }))
			.mockResolvedValueOnce(success({ service_type: 'image', dimensions: {} }));

		await expect(getMyCredits('token', controller.signal)).resolves.toEqual({ balance: 120 });
		await expect(
			quoteImageCredits(
				'token',
				{
					resource_id: 'image-model',
					action: 'text-to-image',
					prompt: 'paint a lighthouse',
					dimensions: { image_count: 1 }
				},
				controller.signal
			)
		).resolves.toMatchObject({ charged_credits: 8 });
		await expect(
			getMyCreditLedger(
				'token',
				{ category: 'consumption', limit: 20, since: 100 },
				controller.signal
			)
		).resolves.toEqual({ items: [], next_cursor: null });
		await expect(
			getAdminCreditAccounts('token', { query: 'Ada', skip: 10, limit: 20 })
		).resolves.toEqual({
			items: [],
			total: 0
		});
		await expect(
			adjustCreditAccount('token', 'user-1', {
				direction: 'increase',
				amount: 25,
				reason_code: 'promotion_gift'
			})
		).resolves.toEqual({ ledger_id: 'ledger-1', source: 'api', request_id: 'request-1' });
		await expect(getAdminCreditLedger('token', { user_id: 'user-1', limit: 50 })).resolves.toEqual({
			items: [],
			total: 0
		});
		await expect(getCreditPrices('token', { skip: 0, limit: 50 })).resolves.toEqual({
			items: [],
			total: 0
		});
		await expect(
			createCreditPrice('token', {
				service_type: 'image',
				resource_id: 'image-model',
				action: 'text-to-image',
				base_price: '8',
				rules: { schema_version: 1, dimensions: [] },
				enabled: true
			})
		).resolves.toEqual({ id: 'price-1' });
		await expect(updateCreditPrice('token', 'price-1', { enabled: false })).resolves.toEqual({
			id: 'price-1',
			enabled: false
		});
		await expect(deleteCreditPrice('token', 'price-1')).resolves.toEqual({ id: 'price-1' });
		await expect(getAdminCreditDimensions('token', 'image')).resolves.toEqual({
			service_type: 'image',
			dimensions: {}
		});

		expect(fetchMock).toHaveBeenNthCalledWith(
			1,
			'/api/v1/credits/me',
			expect.objectContaining({
				method: 'GET',
				signal: controller.signal,
				headers: expect.objectContaining({ Authorization: 'Bearer token' })
			})
		);
		expect(fetchMock).toHaveBeenNthCalledWith(
			2,
			'/api/v1/credits/quotes/image',
			expect.objectContaining({
				method: 'POST',
				signal: controller.signal,
				body: JSON.stringify({
					resource_id: 'image-model',
					action: 'text-to-image',
					prompt: 'paint a lighthouse',
					dimensions: { image_count: 1 }
				})
			})
		);
		expect(fetchMock.mock.calls[2][0]).toBe(
			'/api/v1/credits/me/ledger?category=consumption&limit=20&since=100'
		);
		expect(fetchMock.mock.calls[3][0]).toBe(
			'/api/v1/credits/admin/accounts?query=Ada&skip=10&limit=20'
		);
		expect(fetchMock.mock.calls[4][0]).toBe('/api/v1/credits/admin/accounts/user-1/adjustments');
		expect(fetchMock.mock.calls[4][1].body).toBe(
			JSON.stringify({ direction: 'increase', amount: 25, reason_code: 'promotion_gift' })
		);
		expect(fetchMock.mock.calls[5][0]).toBe('/api/v1/credits/admin/ledger?user_id=user-1&limit=50');
		expect(fetchMock.mock.calls[6][0]).toBe('/api/v1/credits/admin/prices?skip=0&limit=50');
		expect(fetchMock.mock.calls[7][0]).toBe('/api/v1/credits/admin/prices');
		expect(fetchMock.mock.calls[8][0]).toBe('/api/v1/credits/admin/prices/price-1');
		expect(fetchMock.mock.calls[9][0]).toBe('/api/v1/credits/admin/prices/price-1');
		expect(fetchMock.mock.calls[10][0]).toBe('/api/v1/credits/admin/dimensions/image');
	});

	test('preserves structured credit API errors and degrades unknown failures safely', async () => {
		fetchMock
			.mockResolvedValueOnce(
				new Response(
					JSON.stringify({
						code: 'insufficient_credits',
						message: 'Insufficient credits',
						context: { required: 8 }
					}),
					{ status: 402, headers: { 'Content-Type': 'application/json' } }
				)
			)
			.mockResolvedValueOnce(new Response('not JSON', { status: 503 }));

		await expect(getMyCredits('token')).rejects.toMatchObject({
			code: 'insufficient_credits',
			message: 'Insufficient credits',
			context: { required: 8 }
		} satisfies Partial<CreditApiError>);
		await expect(getMyCredits('token')).rejects.toMatchObject({
			code: 'credit_service_unavailable',
			message: 'Credit service is unavailable',
			context: {}
		} satisfies Partial<CreditApiError>);
	});

	test('parses FastAPI HTTPException details instead of reporting unavailable', async () => {
		/** 回归（对抗性审查）：{detail: {code, reason?}} 形态（限流 429、修复
		 * 校验 422）此前全部回退成 credit_service_unavailable，真实原因丢失。 */
		fetchMock
			.mockResolvedValueOnce(
				new Response(JSON.stringify({ detail: { code: 'rate_limit_exceeded' } }), {
					status: 429,
					headers: { 'Content-Type': 'application/json' }
				})
			)
			.mockResolvedValueOnce(
				new Response(
					JSON.stringify({
						detail: { code: 'invalid_repair_request', reason: 'expected_balance mismatch' }
					}),
					{ status: 422, headers: { 'Content-Type': 'application/json' } }
				)
			);

		await expect(getMyCredits('token')).rejects.toMatchObject({
			code: 'rate_limit_exceeded',
			context: {}
		} satisfies Partial<CreditApiError>);
		await expect(getMyCredits('token')).rejects.toMatchObject({
			code: 'invalid_repair_request',
			context: { reason: 'expected_balance mismatch' }
		} satisfies Partial<CreditApiError>);
	});

	test('sends paginated reconciliation queries and returns compensation details', async () => {
		fetchMock
			.mockResolvedValueOnce(success({ items: [], total: 125 }))
			.mockResolvedValueOnce(success({ ledger_id: 'refund-1', created: true, amount: 12 }));

		await expect(
			getCreditReconciliationCases('token', {
				status: 'failed',
				user_id: 'user-1',
				skip: 25,
				limit: 25
			})
		).resolves.toEqual({ items: [], total: 125 });
		await expect(
			compensateCreditReconciliationCase('token', 'usage-1', ' manual refund ')
		).resolves.toEqual({ ledger_id: 'refund-1', created: true, amount: 12 });

		expect(fetchMock.mock.calls[0][0]).toBe(
			'/api/v1/credits/admin/reconciliation?status=failed&user_id=user-1&skip=25&limit=25'
		);
		expect(fetchMock.mock.calls[1][0]).toBe(
			'/api/v1/credits/admin/reconciliation/usage-1/compensate'
		);
		expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ note: 'manual refund' }));
	});
});
