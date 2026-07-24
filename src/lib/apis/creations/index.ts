import { WEBUI_API_BASE_URL } from '$lib/constants';

import type {
	AdminCreationDetail,
	AdminCreationListResponse,
	CreationDetail,
	CreationListResponse
} from '$lib/utils/creations-library';

const authHeaders = (token: string): HeadersInit => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	...(token && { authorization: `Bearer ${token}` })
});

const throwIfNotOk = async (response: Response) => {
	if (!response.ok) {
		throw await response.json().catch(() => null);
	}
};

const requestCreationList = async (
	path: string,
	token: string,
	limit: number,
	cursor: string | null
): Promise<CreationListResponse | AdminCreationListResponse> => {
	const params = new URLSearchParams({ limit: String(limit) });
	if (cursor) {
		params.set('cursor', cursor);
	}
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

const requestJson = async (
	path: string,
	token: string,
	init: RequestInit
): Promise<CreationDetail> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...authHeaders(token), ...(init.headers ?? {}) }
	});
	await throwIfNotOk(response);
	return (await response.json()) as CreationDetail;
};

const requestNoContent = async (path: string, token: string, init: RequestInit): Promise<void> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...authHeaders(token), ...(init.headers ?? {}) }
	});
	await throwIfNotOk(response);
};

export const listCreations = (token = '', limit = 20, cursor: string | null = null) =>
	requestCreationList('/creations/media', token, limit, cursor) as Promise<CreationListResponse>;

export const listAdminCreations = (token = '', limit = 20, cursor: string | null = null) =>
	requestCreationList(
		'/creations/admin/media',
		token,
		limit,
		cursor
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

export type {
	AdminCreationDetail,
	AdminCreationListResponse,
	AdminOwner,
	CreationDetail,
	CreationListResponse,
	CreationReference,
	CreationScope,
	CreationSummary
} from '$lib/utils/creations-library';
