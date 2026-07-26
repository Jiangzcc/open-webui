import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
	DiscoveryPostDetail,
	DiscoveryPostListResponse,
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
	cursor: string | null = null
) => list('/creations/discover/posts', token, limit, cursor, { sort });

export const listFavoritePosts = (token: string, limit = 20, cursor: string | null = null) =>
	list('/creations/discover/favorites', token, limit, cursor);

export const getDiscoveryPost = (token: string, postId: string) =>
	request<DiscoveryPostDetail>(`/creations/discover/posts/${encodeURIComponent(postId)}`, token);

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
