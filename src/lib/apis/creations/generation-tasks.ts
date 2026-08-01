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
	cursor?: string
) => {
	const params = new URLSearchParams({ limit: String(limit) });
	if (cursor) params.set('cursor', cursor);
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
