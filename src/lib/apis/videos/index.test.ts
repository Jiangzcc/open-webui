import { describe, expect, test } from 'vitest';

import { parseVideoRequestError } from './index';

describe('video API errors', () => {
	test('preserves a structured FastAPI detail code and maintenance message', () => {
		const error = parseVideoRequestError({
			detail: {
				code: 'video_model_unavailable',
				message: '该模型正在维护，请稍后再试'
			}
		});

		expect(error.code).toBe('video_model_unavailable');
		expect(error.publicMessage).toBe('该模型正在维护，请稍后再试');
		expect(error.preferPublicMessage).toBe(true);
		expect(error.message).toBe('video_model_unavailable');
	});

	test('keeps existing flat credit and string-detail errors', () => {
		const creditError = parseVideoRequestError({
			code: 'credit_service_unavailable',
			message: 'Credit service is unavailable'
		});
		expect(creditError.code).toBe('credit_service_unavailable');
		expect(creditError.publicMessage).toBe('Credit service is unavailable');
		expect(creditError.preferPublicMessage).toBe(false);
		expect(parseVideoRequestError({ detail: 'invalid_duration' }).code).toBe('invalid_duration');
		expect(parseVideoRequestError({}).code).toBe('video_request_failed');
	});

	test('preserves HTTP status so uncertain server failures keep the idempotency key', () => {
		expect(parseVideoRequestError({ detail: 'temporarily_unavailable' }, 503).status).toBe(503);
		expect(parseVideoRequestError({ detail: 'invalid_duration' }, 422).status).toBe(422);
	});
});
