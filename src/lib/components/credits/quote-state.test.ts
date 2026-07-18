import { afterEach, describe, expect, test, vi } from 'vitest';

import type { ImageQuote } from '$lib/apis/credits';

import {
	createImageQuoteState,
	createImageSubmissionIdempotency,
	isImageQuoteSubmittable,
	quoteErrorMessage,
	type ImageQuoteRequest
} from './quote-state';

const readyQuote: ImageQuote = {
	balance: 20,
	sufficient: true,
	exempt: false,
	configured: true,
	factors: [],
	charged_credits: 8,
	error: null
};

const quoteInput = (prompt: string): ImageQuoteRequest => ({
	resource_id: 'image-model',
	action: 'text-to-image',
	prompt,
	dimensions: { image_count: 1 }
});

afterEach(() => {
	vi.useRealTimers();
});

describe('image credit quote state', () => {
	test('debounces quotes for 275ms', async () => {
		vi.useFakeTimers();
		const quote = vi.fn().mockResolvedValue(readyQuote);
		const state = createImageQuoteState({ quote });

		state.schedule(quoteInput('paint a lighthouse'));
		await vi.advanceTimersByTimeAsync(274);
		expect(quote).not.toHaveBeenCalled();

		await vi.advanceTimersByTimeAsync(1);
		expect(quote).toHaveBeenCalledWith(quoteInput('paint a lighthouse'), expect.any(AbortSignal));
	});

	test('does not issue an aborted request when input changes during the debounce window', async () => {
		vi.useFakeTimers();
		const quote = vi.fn().mockResolvedValue(readyQuote);
		const state = createImageQuoteState({ quote });

		state.schedule(quoteInput('first'));
		await vi.advanceTimersByTimeAsync(200);
		state.schedule(quoteInput('second'));
		await vi.advanceTimersByTimeAsync(75);
		expect(quote).not.toHaveBeenCalled();
		await vi.advanceTimersByTimeAsync(200);
		expect(quote).toHaveBeenCalledTimes(1);
		expect(quote.mock.calls[0][0]).toEqual(quoteInput('second'));
	});

	test('aborts the previous request and ignores its late response', async () => {
		let resolveFirst: (quote: ImageQuote) => void = () => {};
		let resolveSecond: (quote: ImageQuote) => void = () => {};
		const quote = vi
			.fn()
			.mockImplementationOnce(
				() =>
					new Promise<ImageQuote>((resolve) => {
						resolveFirst = resolve;
					})
			)
			.mockImplementationOnce(
				() =>
					new Promise<ImageQuote>((resolve) => {
						resolveSecond = resolve;
					})
			);
		const state = createImageQuoteState({ quote, debounceMs: 0 });

		state.schedule(quoteInput('first'));
		await vi.waitFor(() => expect(quote).toHaveBeenCalledTimes(1));
		const firstSignal = quote.mock.calls[0][1];
		state.schedule(quoteInput('second'));
		await vi.waitFor(() => expect(quote).toHaveBeenCalledTimes(2));
		expect(firstSignal.aborted).toBe(true);

		resolveSecond({ ...readyQuote, charged_credits: 4 });
		await vi.waitFor(() => expect(state.value.status).toBe('ready'));
		resolveFirst({ ...readyQuote, charged_credits: 12 });
		await Promise.resolve();

		expect(state.value).toMatchObject({ status: 'ready', chargedCredits: 4 });
	});

	test('maps quote responses to the six explicit states', async () => {
		const quote = vi.fn();
		const state = createImageQuoteState({ quote, debounceMs: 0 });

		expect(state.value.status).toBe('loading');
		quote.mockResolvedValueOnce(readyQuote);
		state.schedule(quoteInput('ready'));
		await vi.waitFor(() => expect(state.value.status).toBe('ready'));

		quote.mockResolvedValueOnce({ ...readyQuote, sufficient: false });
		state.schedule(quoteInput('insufficient'));
		await vi.waitFor(() => expect(state.value.status).toBe('insufficient'));

		quote.mockResolvedValueOnce({
			...readyQuote,
			configured: false,
			error: 'price_not_configured'
		});
		state.schedule(quoteInput('unconfigured'));
		await vi.waitFor(() => expect(state.value.status).toBe('unconfigured'));

		quote.mockResolvedValueOnce({ ...readyQuote, exempt: true, charged_credits: 0 });
		state.schedule(quoteInput('exempt'));
		await vi.waitFor(() => expect(state.value.status).toBe('exempt'));

		quote.mockRejectedValueOnce({ code: 'credit_service_unavailable' });
		state.schedule(quoteInput('error'));
		await vi.waitFor(() => expect(state.value.status).toBe('error'));
	});

	test('allows submissions only for ready and exempt states', () => {
		for (const status of ['loading', 'insufficient', 'unconfigured', 'error'] as const) {
			expect(isImageQuoteSubmittable({ status })).toBe(false);
		}
		expect(isImageQuoteSubmittable({ status: 'ready' })).toBe(true);
		expect(isImageQuoteSubmittable({ status: 'exempt' })).toBe(true);
	});

	test('reuses one idempotency key within a submission and replaces it for the next click', async () => {
		const createKey = vi.fn().mockReturnValueOnce('key-1').mockReturnValueOnce('key-2');
		const firstSubmission = createImageSubmissionIdempotency(createKey);
		const request = vi.fn().mockResolvedValue('success');

		await firstSubmission.run(request);
		await firstSubmission.run(request);
		const secondSubmission = createImageSubmissionIdempotency(createKey);
		await secondSubmission.run(request);

		expect(request.mock.calls.map(([key]) => key)).toEqual(['key-1', 'key-1', 'key-2']);
		expect(createKey).toHaveBeenCalledTimes(2);
	});

	test('maps public quote errors without exposing structured details', () => {
		expect(quoteErrorMessage({ code: 'insufficient_credits', context: { required: 8 } })).toBe(
			'Insufficient credits'
		);
		expect(
			quoteErrorMessage({ code: 'credit_service_unavailable', detail: { secret: 'value' } })
		).toBe('Credit service is unavailable');
	});
});
