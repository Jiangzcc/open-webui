import { afterEach, describe, expect, test, vi } from 'vitest';

import { createImageGeneration, editImageGeneration } from './generation';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

afterEach(() => {
	fetchMock.mockReset();
});

describe('image generation API', () => {
	test('sends the idempotency key for generation requests', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify([{ url: '/generated.png' }]), { status: 200 })
		);

		await createImageGeneration(
			'token',
			{ prompt: 'paint a lighthouse' },
			{ idempotencyKey: 'key-1' }
		);

		expect(fetchMock).toHaveBeenCalledWith(
			expect.stringContaining('/generations'),
			expect.objectContaining({
				headers: expect.objectContaining({
					authorization: 'Bearer token',
					'Idempotency-Key': 'key-1'
				})
			})
		);
	});

	test('sends the idempotency key for edit requests', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify([{ url: '/edited.png' }]), { status: 200 })
		);

		await editImageGeneration(
			'token',
			{ prompt: 'make it blue', image: 'data:image/png;base64,abc' },
			{ idempotencyKey: 'key-2' }
		);

		expect(fetchMock).toHaveBeenCalledWith(
			expect.stringContaining('/edit'),
			expect.objectContaining({
				headers: expect.objectContaining({ 'Idempotency-Key': 'key-2' })
			})
		);
	});

	test('sends selected sizing fields in the generation request body', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify([{ url: '/generated.png' }]), { status: 200 })
		);

		await createImageGeneration('token', {
			prompt: 'paint a landscape',
			model: 'nano-banana-pro',
			aspect_ratio: '16:9',
			resolution: '2K'
		});

		expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toMatchObject({
			aspect_ratio: '16:9',
			resolution: '2K'
		});
	});

	test('sends selected sizing fields in the edit request body', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify([{ url: '/edited.png' }]), { status: 200 })
		);

		await editImageGeneration('token', {
			prompt: 'make it blue',
			image: 'data:image/png;base64,abc',
			model: 'z-image-turbo/edit',
			size: '1536x864'
		});

		expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toMatchObject({
			size: '1536x864'
		});
	});

	test('does not expose structured server errors', async () => {
		fetchMock.mockResolvedValue(
			new Response(JSON.stringify({ detail: { database: 'internal details' } }), { status: 500 })
		);

		await expect(createImageGeneration('token', { prompt: 'paint a lighthouse' })).rejects.toEqual({
			code: 'image_generation_failed'
		});
	});

	test('maps public credit errors to safe messages', async () => {
		fetchMock.mockResolvedValue(
			new Response(
				JSON.stringify({
					code: 'insufficient_credits',
					message: 'Insufficient credits',
					context: { balance: 0 }
				}),
				{ status: 402 }
			)
		);

		await expect(createImageGeneration('token', { prompt: 'paint a lighthouse' })).rejects.toEqual({
			code: 'insufficient_credits'
		});
	});

	test.each([
		'idempotency_key_conflict',
		'usage_processing',
		'credit_account_conflict',
		'invalid_adjustment'
	])('keeps the public %s credit error code without its server details', async (code) => {
		fetchMock.mockResolvedValue(
			new Response(
				JSON.stringify({
					code,
					message: 'A public error message',
					context: { internal: 'must not reach the UI' }
				}),
				{ status: 409 }
			)
		);

		await expect(createImageGeneration('token', { prompt: 'paint a lighthouse' })).rejects.toEqual({
			code
		});
	});

	test('preserves cancellation errors for callers', async () => {
		const abortError = new DOMException('The request was aborted', 'AbortError');
		fetchMock.mockRejectedValue(abortError);

		await expect(createImageGeneration('token', { prompt: 'paint a lighthouse' })).rejects.toBe(
			abortError
		);
	});
});
