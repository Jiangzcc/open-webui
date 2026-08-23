import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
	ImageGenerationTask,
	ImageGenerationTaskKind
} from '$lib/utils/image-generation-batches';
import type { ImageEditPayload, ImageGenerationPayload } from '$lib/utils/image-generation';
import type { GenerationTaskStatus } from '$lib/utils/generation-task-status';

const headers = (token: string, idempotencyKey?: string): HeadersInit => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	...(token && { authorization: `Bearer ${token}` }),
	...(idempotencyKey && { 'Idempotency-Key': idempotencyKey })
});

// 结构化请求错误：code 供既有 getImageGenerationErrorCode 映射文案，
// status 供提交方区分「确定被拒」（4xx 清除幂等键）与「响应不确定」
//（网络错误/5xx 保留幂等键，重试不会二次扣费）。
export class ImageTaskRequestError extends Error {
	code: string;
	status?: number;

	constructor(code: string, status?: number) {
		super(code);
		this.name = 'ImageTaskRequestError';
		this.code = code;
		this.status = status;
	}
}

const errorFromResponse = async (response: Response): Promise<ImageTaskRequestError> => {
	const payload: unknown = await response.json().catch(() => null);
	let code = 'image_task_failed';
	if (payload && typeof payload === 'object') {
		const body = payload as Record<string, unknown>;
		const detail = body.detail;
		if (typeof body.code === 'string') code = body.code;
		else if (
			detail &&
			typeof detail === 'object' &&
			typeof (detail as Record<string, unknown>).code === 'string'
		) {
			code = (detail as Record<string, unknown>).code as string;
		} else if (typeof detail === 'string') {
			code = detail;
		}
	}
	return new ImageTaskRequestError(code, response.status);
};

const requestJson = async <T>(path: string, token: string, init: RequestInit = {}): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...headers(token), ...(init.headers ?? {}) }
	});
	if (!response.ok) {
		throw await errorFromResponse(response);
	}
	return (await response.json()) as T;
};

const requestNoContent = async (path: string, token: string, init: RequestInit = {}) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...headers(token), ...(init.headers ?? {}) }
	});
	if (!response.ok) {
		throw await errorFromResponse(response);
	}
};

export const createImageGenerationTask = (
	token: string,
	kind: ImageGenerationTaskKind,
	payload: ImageGenerationPayload | ImageEditPayload,
	idempotencyKey: string
) =>
	requestJson<ImageGenerationTask>('/creations/generation-tasks', token, {
		method: 'POST',
		headers: headers(token, idempotencyKey),
		// 提示词是所见即所得的纯文本（标签点击即插入 insert_text，无 token
		// 解析层），提交体也不携带标签目录快照。
		body: JSON.stringify({ kind, payload })
	});

export const listImageGenerationTasks = async (
	token: string,
	limit = 10,
	cursor?: string,
	since?: number | null
) => {
	const params = new URLSearchParams({ limit: String(limit) });
	if (cursor) params.set('cursor', cursor);
	if (since !== undefined && since !== null) params.set('since', String(since));
	const response = await requestJson<{ items: ImageGenerationTask[]; next_cursor: string | null }>(
		`/creations/generation-tasks?${params.toString()}`,
		token
	);
	return response;
};

export const getImageGenerationTask = (token: string, taskId: string) =>
	requestJson<ImageGenerationTask>(
		`/creations/generation-tasks/${encodeURIComponent(taskId)}`,
		token
	);

export const deleteImageGenerationTask = (token: string, taskId: string) =>
	requestNoContent(`/creations/generation-tasks/${encodeURIComponent(taskId)}`, token, {
		method: 'DELETE'
	});

export type GenerationEvent = {
	kind: 'image' | 'video';
	task_id: string;
	status: GenerationTaskStatus;
	error_code?: string | null;
	type?: string;
};

export const GENERATION_EVENT_RECONNECT_INITIAL_MS = 3_000;
export const GENERATION_EVENT_RECONNECT_MAX_MS = 30_000;

// 指数退避 + 随机抖动，避免大量客户端在服务端恢复后同时重连（惊群效应）。
// 达到最大退避时改为向下抖动，否则 Math.min 会把所有客户端固定在同一个 30s 时刻。
export const nextGenerationEventReconnectDelay = (current: number): number => {
	const base = Math.min(
		GENERATION_EVENT_RECONNECT_MAX_MS,
		Math.max(GENERATION_EVENT_RECONNECT_INITIAL_MS, current * 2)
	);
	const jitter = Math.random() * 1000;
	return base === GENERATION_EVENT_RECONNECT_MAX_MS
		? Math.max(GENERATION_EVENT_RECONNECT_INITIAL_MS, base - jitter)
		: Math.min(GENERATION_EVENT_RECONNECT_MAX_MS, base + jitter);
};

export const subscribeToGenerationEvents = (token: string, signal?: AbortSignal) =>
	fetch(`${WEBUI_API_BASE_URL}/creations/generation-events`, {
		signal,
		headers: {
			Accept: 'text/event-stream',
			authorization: `Bearer ${token}`
		}
	});

export async function* iterateGenerationEvents(
	responsePromise: Promise<Response>
): AsyncGenerator<GenerationEvent, void, unknown> {
	const response = await responsePromise;
	if (!response.ok || !response.body) {
		throw new Error('generation_events_unavailable');
	}
	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			let separator: RegExpExecArray | null;
			while ((separator = /\r\n\r\n|\r\r|\n\n/.exec(buffer)) !== null) {
				const frame = buffer.slice(0, separator.index);
				buffer = buffer.slice(separator.index + separator[0].length);
				const event = parseSseFrame(frame);
				if (event) yield event;
			}
		}
	} finally {
		reader.releaseLock();
	}
}

const parseSseFrame = (frame: string): GenerationEvent | null => {
	const dataLines: string[] = [];
	for (const line of frame.split(/\r\n|\r|\n/)) {
		if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
	}
	const data = dataLines.join('\n');
	if (!data) return null;
	try {
		return JSON.parse(data) as GenerationEvent;
	} catch {
		return null;
	}
};
