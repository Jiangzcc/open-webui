import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
	ImageGenerationTask,
	ImageGenerationTaskKind
} from '$lib/utils/image-generation-batches';
import type { ImageEditPayload, ImageGenerationPayload } from '$lib/utils/image-generation';

const headers = (token: string, idempotencyKey?: string): HeadersInit => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	...(token && { authorization: `Bearer ${token}` }),
	...(idempotencyKey && { 'Idempotency-Key': idempotencyKey })
});

const requestJson = async <T>(path: string, token: string, init: RequestInit = {}): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...headers(token), ...(init.headers ?? {}) }
	});
	if (!response.ok) {
		throw await response.json().catch(() => null);
	}
	return (await response.json()) as T;
};

const requestNoContent = async (path: string, token: string, init: RequestInit = {}) => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...headers(token), ...(init.headers ?? {}) }
	});
	if (!response.ok) {
		throw await response.json().catch(() => null);
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

export const cancelImageGenerationTask = (token: string, taskId: string) =>
	requestJson<ImageGenerationTask>(
		`/creations/generation-tasks/${encodeURIComponent(taskId)}/cancel`,
		token,
		{ method: 'POST' }
	);

export const deleteImageGenerationTask = (token: string, taskId: string) =>
	requestNoContent(`/creations/generation-tasks/${encodeURIComponent(taskId)}`, token, {
		method: 'DELETE'
	});

export type GenerationEvent = {
	kind: 'image' | 'video' | string;
	task_id: string;
	status: 'queued' | 'running' | 'succeeded' | 'failed' | string;
	error_code?: string | null;
	type?: string;
};

export const GENERATION_EVENT_RECONNECT_INITIAL_MS = 3_000;
export const GENERATION_EVENT_RECONNECT_MAX_MS = 30_000;

export const nextGenerationEventReconnectDelay = (current: number): number =>
	Math.min(
		GENERATION_EVENT_RECONNECT_MAX_MS,
		Math.max(GENERATION_EVENT_RECONNECT_INITIAL_MS, current * 2)
	);

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
