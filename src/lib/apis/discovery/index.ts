import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
	DiscoveryPostDetail,
	DiscoveryPostListResponse,
	DiscoveryCategory,
	DiscoveryCategoryCreateInput,
	DiscoveryCategoryItem,
	DiscoveryCategoryUpdateInput,
	DiscoveryOperationInput,
	CreationPublication,
	DiscoverySort,
	ReactionKind,
	ReactionState
} from '$lib/utils/discovery';

const headers = (token: string): HeadersInit => ({
	Accept: 'application/json',
	...(token && { authorization: `Bearer ${token}` })
});

const request = async <T>(path: string, token: string, init?: RequestInit): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		...init,
		headers: { ...headers(token), ...(init?.headers ?? {}) }
	});
	if (!response.ok) throw await response.json().catch(() => null);
	if (response.status === 204) return undefined as T;
	return (await response.json()) as T;
};

const list = (
	path: string,
	token: string,
	limit: number,
	cursor: string | null,
	extra: Record<string, string> = {}
): Promise<DiscoveryPostListResponse> => {
	const params = new URLSearchParams({ ...extra, limit: String(limit) });
	if (cursor) params.set('cursor', cursor);
	return request(`${path}?${params.toString()}`, token);
};

export const listDiscoveryPosts = (
	token: string,
	sort: DiscoverySort,
	limit = 20,
	cursor: string | null = null,
	category?: DiscoveryCategory,
	mediaKind?: 'image' | 'video'
) =>
	list('/creations/discover/posts', token, limit, cursor, {
		sort,
		...(category ? { category } : {}),
		...(mediaKind ? { media_kind: mediaKind } : {})
	});

export const listFavoritePosts = (
	token: string,
	limit = 20,
	cursor: string | null = null,
	category?: DiscoveryCategory,
	mediaKind?: 'image' | 'video'
) =>
	list('/creations/discover/favorites', token, limit, cursor, {
		...(category ? { category } : {}),
		...(mediaKind ? { media_kind: mediaKind } : {})
	});

export const getDiscoveryPost = (token: string, postId: string) =>
	request<DiscoveryPostDetail>(`/creations/discover/posts/${encodeURIComponent(postId)}`, token);

export const listDiscoveryCategories = (token: string) =>
	request<DiscoveryCategoryItem[]>('/creations/discover/categories', token);

export const listAdminDiscoveryCategories = (token: string) =>
	request<DiscoveryCategoryItem[]>('/creations/admin/discover/categories', token);

export const createAdminDiscoveryCategory = (token: string, input: DiscoveryCategoryCreateInput) =>
	request<DiscoveryCategoryItem>('/creations/admin/discover/categories', token, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(input)
	});

export const updateAdminDiscoveryCategory = (
	token: string,
	categoryId: DiscoveryCategory,
	input: DiscoveryCategoryUpdateInput
) =>
	request<DiscoveryCategoryItem>(
		`/creations/admin/discover/categories/${encodeURIComponent(categoryId)}`,
		token,
		{
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(input)
		}
	);

export const deleteAdminDiscoveryCategory = (token: string, categoryId: DiscoveryCategory) =>
	request<void>(`/creations/admin/discover/categories/${encodeURIComponent(categoryId)}`, token, {
		method: 'DELETE'
	});

export const setDiscoveryReaction = (
	token: string,
	postId: string,
	kind: ReactionKind,
	active: boolean
) =>
	request<ReactionState>(
		`/creations/discover/posts/${encodeURIComponent(postId)}/reactions/${kind}`,
		token,
		{ method: active ? 'PUT' : 'DELETE' }
	);

export const updateDiscoveryOperation = (
	token: string,
	postId: string,
	input: DiscoveryOperationInput
) =>
	request<CreationPublication>(
		`/creations/admin/discover/posts/${encodeURIComponent(postId)}`,
		token,
		{
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(input)
		}
	);
