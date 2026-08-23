import { afterEach, describe, expect, test, vi } from 'vitest';

import { getProviderOverview, syncFalProvider } from './index';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

afterEach(() => {
	fetchMock.mockReset();
});

describe('provider operations API client', () => {
	test('encodes overview filters', async () => {
		fetchMock.mockResolvedValueOnce(new Response('{}', { status: 200 }));

		await getProviderOverview('token', 'fal', 168);

		expect(fetchMock).toHaveBeenCalledWith(
			'/api/v1/provider-ops/admin/overview?provider=fal&window_hours=168',
			expect.objectContaining({
				headers: expect.objectContaining({ Authorization: 'Bearer token' })
			})
		);
	});

	test('requests all authoritative fal resources during synchronization', async () => {
		fetchMock.mockResolvedValueOnce(new Response('{}', { status: 200 }));

		await syncFalProvider('token', 24, 'hour');

		const [, init] = fetchMock.mock.calls[0];
		expect(JSON.parse(init.body)).toEqual({
			resources: ['pricing', 'requests', 'billing_events', 'usage', 'analytics'],
			window_hours: 24,
			timeframe: 'hour'
		});
	});
});
