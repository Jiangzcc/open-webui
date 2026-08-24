import { afterEach, describe, expect, test, vi } from 'vitest';

import {
	GENERATION_EVENT_RECONNECT_INITIAL_MS,
	createImageGenerationTask,
	ImageTaskRequestError,
	iterateGenerationEvents,
	nextGenerationEventReconnectDelay,
	subscribeToGenerationEvents
} from './generation-tasks';

afterEach(() => {
	vi.unstubAllGlobals();
});

describe('generation task events', () => {
	test('backs off reconnects and caps the delay', () => {
		// 指数退避后叠加 [0, 1000) ms 随机抖动，避免惊群效应。
		// 基础退避值 = max(3_000, current * 2)，抖动后仍受 30_000 上限约束。
		const first = nextGenerationEventReconnectDelay(GENERATION_EVENT_RECONNECT_INITIAL_MS);
		expect(first).toBeGreaterThanOrEqual(6_000);
		expect(first).toBeLessThan(7_000);
		// 达到上限后仍保留向下抖动，避免所有客户端固定在同一个 30s 时刻重连。
		const capped = nextGenerationEventReconnectDelay(24_000);
		expect(capped).toBeGreaterThan(29_000);
		expect(capped).toBeLessThanOrEqual(30_000);
		const repeated = nextGenerationEventReconnectDelay(30_000);
		expect(repeated).toBeGreaterThan(29_000);
		expect(repeated).toBeLessThanOrEqual(30_000);
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

describe('generation task request errors', () => {
	// 提交方依赖 code（映射文案）与 status（区分确定拒绝与响应不确定，
	// 决定是否保留幂等键重试）。服务端错误体有三种形态：顶层 code
	//（credits to_envelope）、detail.code、detail 字符串。
	test.each([
		['top-level code envelope', { code: 'insufficient_credits' }, 'insufficient_credits'],
		[
			'nested detail code',
			{ detail: { code: 'idempotency_key_conflict' } },
			'idempotency_key_conflict'
		],
		['plain detail string', { detail: 'idempotency_key_conflict' }, 'idempotency_key_conflict'],
		['unparseable body', null, 'image_task_failed']
	])('throws ImageTaskRequestError with status for %s', async (_label, body, expectedCode) => {
		vi.stubGlobal(
			'fetch',
			vi
				.fn()
				.mockResolvedValue(
					new Response(body === null ? 'not json' : JSON.stringify(body), { status: 402 })
				)
		);

		const error = await createImageGenerationTask(
			'token-1',
			'text-to-image',
			{ prompt: 'x' } as never,
			'key-1'
		).catch((thrown: unknown) => thrown);

		expect(error).toBeInstanceOf(ImageTaskRequestError);
		expect((error as ImageTaskRequestError).code).toBe(expectedCode);
		expect((error as ImageTaskRequestError).status).toBe(402);
	});
});
