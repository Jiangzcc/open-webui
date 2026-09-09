import { WEBUI_API_BASE_URL } from '$lib/constants';

import type {
	AdminCreationDetail,
	AdminCreationListResponse,
	CreationDetail,
	CreationListFilters,
	CreationListResponse,
	CreationPublication
} from '$lib/utils/creations-library';

const authHeaders = (token: string): HeadersInit => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	...(token && { authorization: `Bearer ${token}` })
});

// 时间窗口 UI 键 → 秒数；since 在请求时换算，保证窗口随请求时刻滚动。
const SINCE_WINDOW_SECONDS: Record<
	Exclude<CreationListFilters['since'], '' | undefined>,
	number
> = {
	'24h': 24 * 60 * 60,
	'7d': 7 * 24 * 60 * 60,
	'30d': 30 * 24 * 60 * 60
};

const throwIfNotOk = async (response: Response) => {
	if (!response.ok) {
		throw await response.json().catch(() => null);
	}
};

const requestCreationList = async (
	path: string,
	token: string,
	limit: number,
	cursor: string | null,
	filters: CreationListFilters = {}
): Promise<CreationListResponse | AdminCreationListResponse> => {
	const params = new URLSearchParams({ limit: String(limit) });
	if (cursor) {
		params.set('cursor', cursor);
	}
	if (filters.search?.trim()) params.set('search', filters.search.trim());
	if (filters.kind) params.set('kind', filters.kind);
	if (filters.task) params.set('task', filters.task);
	if (filters.publicationStatus) params.set('publication_status', filters.publicationStatus);
	if (filters.sort) params.set('sort', filters.sort);
	if (filters.since) {
		params.set(
			'since',
			String(Math.floor(Date.now() / 1000) - SINCE_WINDOW_SECONDS[filters.since])
		);
	}
	if (filters.clarity) params.set('clarity', filters.clarity);
	if (filters.aspectRatio) params.set('aspect_ratio', filters.aspectRatio);
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}?${params.toString()}`, {
		headers: authHeaders(token)
	});
	await throwIfNotOk(response);
	return (await response.json()) as CreationListResponse;
};

const requestCreationDetail = async <T extends CreationDetail | AdminCreationDetail>(
	path: string,
	token: string
): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		headers: authHeaders(token)
	});
	await throwIfNotOk(response);
	return (await response.json()) as T;
};

const requestJson = async <T = CreationDetail>(
	path: string,
	token: string,
	init: RequestInit
): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...authHeaders(token), ...(init.headers ?? {}) }
	});
	await throwIfNotOk(response);
	return (await response.json()) as T;
};

const requestNoContent = async (path: string, token: string, init: RequestInit): Promise<void> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...authHeaders(token), ...(init.headers ?? {}) }
	});
	await throwIfNotOk(response);
};

export const listCreations = (
	token = '',
	limit = 20,
	cursor: string | null = null,
	filters: CreationListFilters = {}
) =>
	requestCreationList(
		'/creations/media',
		token,
		limit,
		cursor,
		filters
	) as Promise<CreationListResponse>;

export const listAdminCreations = (
	token = '',
	limit = 20,
	cursor: string | null = null,
	filters: CreationListFilters = {}
) =>
	requestCreationList(
		'/creations/admin/media',
		token,
		limit,
		cursor,
		filters
	) as Promise<AdminCreationListResponse>;

export const getCreation = (token: string, id: string) =>
	requestCreationDetail<CreationDetail>(`/creations/media/${encodeURIComponent(id)}`, token);

export const getAdminCreation = (token: string, id: string) =>
	requestCreationDetail<AdminCreationDetail>(
		`/creations/admin/media/${encodeURIComponent(id)}`,
		token
	);

export const updateCreation = (token: string, id: string, caption: string | null) =>
	requestJson(`/creations/media/${encodeURIComponent(id)}`, token, {
		method: 'PATCH',
		body: JSON.stringify({ caption })
	});

export const deleteCreation = (token: string, id: string) =>
	requestNoContent(`/creations/media/${encodeURIComponent(id)}`, token, { method: 'DELETE' });

export const deleteAdminCreation = (token: string, id: string) =>
	requestNoContent(`/creations/admin/media/${encodeURIComponent(id)}`, token, { method: 'DELETE' });

export const deleteCreations = (token: string, ids: string[]) =>
	requestJson<{ removed_ids: string[] }>('/creations/media/bulk-delete', token, {
		method: 'POST',
		body: JSON.stringify({ ids })
	});

export const publishCreation = async (
	token: string,
	id: string,
	payload: { title: string | null; description: string | null; show_prompt: boolean }
): Promise<CreationPublication> => {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/creations/media/${encodeURIComponent(id)}/publish`,
		{
			method: 'POST',
			headers: authHeaders(token),
			body: JSON.stringify(payload)
		}
	);
	await throwIfNotOk(response);
	return (await response.json()) as CreationPublication;
};

export const publishAdminCreation = async (
	token: string,
	id: string,
	payload: { title: string | null; description: string | null; show_prompt: boolean }
): Promise<CreationPublication> => {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/creations/admin/media/${encodeURIComponent(id)}/publish`,
		{
			method: 'POST',
			headers: authHeaders(token),
			body: JSON.stringify(payload)
		}
	);
	await throwIfNotOk(response);
	return (await response.json()) as CreationPublication;
};

export const withdrawCreationPublication = (token: string, id: string) =>
	requestNoContent(`/creations/media/${encodeURIComponent(id)}/publish`, token, {
		method: 'DELETE'
	});

export const withdrawAdminCreationPublication = (token: string, id: string) =>
	requestNoContent(`/creations/admin/media/${encodeURIComponent(id)}/publish`, token, {
		method: 'DELETE'
	});

export type {
	AdminCreationDetail,
	AdminCreationListResponse,
	AdminOwner,
	CreationDetail,
	CreationListResponse,
	CreationListFilters,
	CreationPublication,
	CreationReference,
	CreationScope,
	CreationSummary
} from '$lib/utils/creations-library';
