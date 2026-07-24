import { beforeEach, describe, expect, test, vi } from 'vitest';

import { deleteCreation, getCreation, listCreations, updateCreation } from './index';

const jsonResponse = (body: unknown, init?: ResponseInit) =>
	new Response(JSON.stringify(body), {
		status: 200,
		headers: { 'content-type': 'application/json' },
		...init
	});

describe('creations api', () => {
	let fetchMock: ReturnType<typeof vi.fn>;

	beforeEach(() => {
		fetchMock = vi.fn();
		vi.stubGlobal('fetch', fetchMock);
	});

	test('listCreations hits /creations/media with cursor via query params and bearer', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ items: [], next_cursor: null }));
		await listCreations('tok', 20, 'abc');
		const [url, init] = fetchMock.mock.calls[0];
		expect(String(url)).toBe('/api/v1/creations/media?limit=20&cursor=abc');
		expect(init?.method).toBeUndefined();
		expect((init?.headers as Record<string, string>).authorization).toBe('Bearer tok');
	});

	test('listCreations omits cursor when null', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ items: [], next_cursor: null }));
		await listCreations('', 20, null);
		expect(String(fetchMock.mock.calls[0][0])).toBe('/api/v1/creations/media?limit=20');
	});

	test('getCreation targets the escaped id', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ id: 'c 1' }));
		await getCreation('tok', 'c 1');
		expect(String(fetchMock.mock.calls[0][0])).toBe('/api/v1/creations/media/c%201');
		expect((fetchMock.mock.calls[0][1]?.headers as Record<string, string>).authorization).toBe(
			'Bearer tok'
		);
	});

	test('updateCreation sends PATCH with caption body', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ id: 'c1', caption: 'hi' }));
		await updateCreation('tok', 'c1', 'hi');
		const [, init] = fetchMock.mock.calls[0];
		expect(init?.method).toBe('PATCH');
		expect(init?.body).toBe(JSON.stringify({ caption: 'hi' }));
	});

	test('updateCreation sends null caption as null', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ id: 'c1', caption: null }));
		await updateCreation('tok', 'c1', null);
		expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({ caption: null }));
	});

	test('deleteCreation treats 204 as success and returns nothing', async () => {
		fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
		const result = await deleteCreation('tok', 'c1');
		expect(result).toBeUndefined();
		expect(fetchMock.mock.calls[0][1]?.method).toBe('DELETE');
	});

	test('non-ok response throws the json error body', async () => {
		fetchMock.mockResolvedValue(jsonResponse({ code: 'invalid_creation_cursor' }, { status: 422 }));
		await expect(deleteCreation('tok', 'c1')).rejects.toEqual({
			code: 'invalid_creation_cursor'
		});
	});
});
