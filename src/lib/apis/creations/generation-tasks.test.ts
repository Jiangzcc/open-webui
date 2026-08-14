import { afterEach, describe, expect, test, vi } from 'vitest';

import {
	GENERATION_EVENT_RECONNECT_INITIAL_MS,
	iterateGenerationEvents,
	nextGenerationEventReconnectDelay,
	subscribeToGenerationEvents
} from './generation-tasks';

afterEach(() => {
	vi.unstubAllGlobals();
});

describe('generation task events', () => {
	test('backs off reconnects and caps the delay', () => {
		expect(nextGenerationEventReconnectDelay(GENERATION_EVENT_RECONNECT_INITIAL_MS)).toBe(6_000);
		expect(nextGenerationEventReconnectDelay(24_000)).toBe(30_000);
		expect(nextGenerationEventReconnectDelay(30_000)).toBe(30_000);
	});

	test('parses data frames and ignores heartbeat frames', async () => {
		const response = new Response(
			'data: {"type":"hello"}\n\n: keepalive\n\ndata: {"kind":"video","task_id":"v1","status":"succeeded"}\n\n'
		);
		const events = [];
		for await (const event of iterateGenerationEvents(Promise.resolve(response))) {
			events.push(event);
		}

		expect(events).toEqual([
			{ type: 'hello' },
			{ kind: 'video', task_id: 'v1', status: 'succeeded' }
		]);
	});

	test('parses CRLF-delimited frames', async () => {
		const response = new Response(
			'data: {"kind":"video","task_id":"v1","status":"running"}\r\n\r\n'
		);
		const events = [];
		for await (const event of iterateGenerationEvents(Promise.resolve(response))) {
			events.push(event);
		}

		expect(events).toEqual([{ kind: 'video', task_id: 'v1', status: 'running' }]);
	});

	test('joins multiple data lines with a newline', async () => {
		const response = new Response(
			'data: {"kind":"image",\ndata: "task_id":"i1","status":"succeeded"}\n\n'
		);
		const events = [];
		for await (const event of iterateGenerationEvents(Promise.resolve(response))) {
			events.push(event);
		}

		expect(events).toEqual([{ kind: 'image', task_id: 'i1', status: 'succeeded' }]);
	});

	test('passes authentication and abort signal to the SSE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(''));
		vi.stubGlobal('fetch', fetchMock);
		const controller = new AbortController();

		await subscribeToGenerationEvents('token-1', controller.signal);

		expect(fetchMock).toHaveBeenCalledWith(
			'/api/v1/creations/generation-events',
			expect.objectContaining({
				signal: controller.signal,
				headers: expect.objectContaining({ authorization: 'Bearer token-1' })
			})
		);
	});
});
