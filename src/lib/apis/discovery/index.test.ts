import { afterEach, describe, expect, test, vi } from 'vitest';

import { deleteAdminDiscoveryCategory } from './index';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

afterEach(() => {
	fetchMock.mockReset();
});

describe('discovery API client', () => {
	test('accepts an empty 204 response when deleting a category', async () => {
		fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));

		await expect(deleteAdminDiscoveryCategory('token', 'category_photo')).resolves.toBeUndefined();
		expect(fetchMock).toHaveBeenCalledWith(
			'/api/v1/creations/admin/discover/categories/category_photo',
			expect.objectContaining({
				method: 'DELETE',
				headers: expect.objectContaining({ Authorization: 'Bearer token' })
			})
		);
	});
});
