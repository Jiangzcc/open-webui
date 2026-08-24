import { WEBUI_API_BASE_URL } from '$lib/constants';

export type PromptTagMediaKind = 'image' | 'video';

export type PromptTagModelRef = {
	media_kind: PromptTagMediaKind;
	model_id: string;
};

export type PromptTagCategoryItem = {
	id: string;
	slug: string;
	name_zh: string;
	name_en: string;
	enabled: boolean;
	sort_order: number;
	created_at: number;
	updated_at: number;
};

/** 管理端标签（含全部管理字段；公开目录同样下发 insert_text）。 */
export type PromptTagItem = {
	id: string;
	slug: string;
	category_id: string;
	label_zh: string;
	label_en: string;
	insert_text: string;
	is_negative: boolean;
	media_kinds: PromptTagMediaKind[];
	model_refs: PromptTagModelRef[];
	enabled: boolean;
	sort_order: number;
	created_at: number;
	updated_at: number;
};

/**
 * 公开目录标签：含 insert_text。标签是「快捷提示词片段」——点击标签时
 * 直接把实际文本插入输入框，所见即所得（2026-08-22 放弃保密模型）。
 */
export type PromptTagPublicItem = {
	id: string;
	slug: string;
	category_id: string;
	label_zh: string;
	label_en: string;
	insert_text: string;
	is_negative: boolean;
	media_kinds: PromptTagMediaKind[];
	model_refs: PromptTagModelRef[];
	sort_order: number;
};

export type PromptTagPublicCategory = PromptTagCategoryItem & {
	tags: PromptTagPublicItem[];
};

export type PromptTagPublicCatalog = {
	revision: number;
	categories: PromptTagPublicCategory[];
};

export type PromptTagAdminCatalog = {
	categories: PromptTagCategoryItem[];
	tags: PromptTagItem[];
};

export type PromptTagCategoryCreate = {
	slug: string;
	name_zh: string;
	name_en: string;
	enabled?: boolean;
	sort_order?: number;
};

export type PromptTagCategoryUpdate = {
	slug?: string;
	name_zh?: string;
	name_en?: string;
	enabled?: boolean;
	sort_order?: number;
};

export type PromptTagCreate = {
	slug: string;
	category_id: string;
	label_zh: string;
	label_en: string;
	insert_text: string;
	is_negative?: boolean;
	media_kinds?: PromptTagMediaKind[];
	model_refs?: PromptTagModelRef[];
	enabled?: boolean;
	sort_order?: number;
};

export type PromptTagUpdate = {
	slug?: string;
	category_id?: string;
	label_zh?: string;
	label_en?: string;
	insert_text?: string;
	is_negative?: boolean;
	media_kinds?: PromptTagMediaKind[];
	model_refs?: PromptTagModelRef[];
	enabled?: boolean;
	sort_order?: number;
};

export type PromptTagExportDocument = {
	schema_version: 1;
	exported_at: number;
	categories: Omit<PromptTagCategoryCreate, never>[];
	tags: {
		slug: string;
		category_slug: string;
		label_zh: string;
		label_en: string;
		insert_text: string;
		is_negative: boolean;
		media_kinds: PromptTagMediaKind[];
		model_refs: PromptTagModelRef[];
		enabled: boolean;
		sort_order: number;
	}[];
};

export type PromptTagImportResult = {
	dry_run: boolean;
	categories_created: number;
	categories_updated: number;
	tags_created: number;
	tags_updated: number;
};

const BASE = `${WEBUI_API_BASE_URL}/prompt-tags`;

const buildUrl = (path: string, query?: Record<string, string | undefined | null>) => {
	const url = `${BASE}${path}`;
	if (!query) return url;
	const params = new URLSearchParams();
	for (const [key, value] of Object.entries(query)) {
		if (value !== undefined && value !== null) params.set(key, value);
	}
	const serialized = params.toString();
	return serialized ? `${url}?${serialized}` : url;
};

const request = async <T>({
	method,
	path,
	token,
	query,
	body,
	signal
}: {
	method: string;
	path: string;
	token: string;
	query?: Record<string, string | undefined | null>;
	body?: unknown;
	signal?: AbortSignal;
}): Promise<T> => {
	let response: Response;
	try {
		response = await fetch(buildUrl(path, query), {
			method,
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			...(body ? { body: JSON.stringify(body) } : {}),
			...(signal ? { signal } : {})
		});
	} catch (error) {
		if (error instanceof DOMException && error.name === 'AbortError') throw error;
		throw new Error('promptTags.unavailable');
	}

	if (response.status === 204) return undefined as T;

	const payload = await response.json().catch(() => null);
	if (!response.ok) {
		const code = payload?.detail ?? `promptTags.http_${response.status}`;
		throw typeof code === 'string' ? new Error(code) : new Error('promptTags.requestFailed');
	}
	return payload as T;
};

/* ---------- public ---------- */

export const getPromptTagCatalog = (
	token: string,
	mediaKind?: PromptTagMediaKind,
	modelId?: string,
	signal?: AbortSignal
) =>
	request<PromptTagPublicCatalog>({
		method: 'GET',
		path: '',
		token,
		query: { media_kind: mediaKind, model_id: modelId },
		signal
	});

/* ---------- admin: catalog ---------- */

export const getAdminPromptTagCatalog = (token: string, signal?: AbortSignal) =>
	request<PromptTagAdminCatalog>({ method: 'GET', path: '/admin/catalog', token, signal });

/* ---------- admin: categories ---------- */

export const createPromptTagCategory = (
	token: string,
	body: PromptTagCategoryCreate,
	signal?: AbortSignal
) =>
	request<PromptTagCategoryItem>({
		method: 'POST',
		path: '/admin/categories',
		token,
		body,
		signal
	});

export const updatePromptTagCategory = (
	token: string,
	categoryId: string,
	body: PromptTagCategoryUpdate,
	signal?: AbortSignal
) =>
	request<PromptTagCategoryItem>({
		method: 'PATCH',
		path: `/admin/categories/${encodeURIComponent(categoryId)}`,
		token,
		body,
		signal
	});

export const deletePromptTagCategory = (
	token: string,
	categoryId: string,
	cascade = false,
	signal?: AbortSignal
) =>
	request<void>({
		method: 'DELETE',
		path: `/admin/categories/${encodeURIComponent(categoryId)}`,
		token,
		query: { cascade: cascade ? 'true' : undefined },
		signal
	});

/* ---------- admin: tags ---------- */

export const createPromptTag = (token: string, body: PromptTagCreate, signal?: AbortSignal) =>
	request<PromptTagItem>({ method: 'POST', path: '/admin/tags', token, body, signal });

export const updatePromptTag = (
	token: string,
	tagId: string,
	body: PromptTagUpdate,
	signal?: AbortSignal
) =>
	request<PromptTagItem>({
		method: 'PATCH',
		path: `/admin/tags/${encodeURIComponent(tagId)}`,
		token,
		body,
		signal
	});

export const deletePromptTag = (token: string, tagId: string, signal?: AbortSignal) =>
	request<void>({
		method: 'DELETE',
		path: `/admin/tags/${encodeURIComponent(tagId)}`,
		token,
		signal
	});

/* ---------- admin: import / export ---------- */

export const exportPromptTags = (token: string, signal?: AbortSignal) =>
	request<PromptTagExportDocument>({ method: 'GET', path: '/admin/export', token, signal });

export const importPromptTags = (
	token: string,
	body: PromptTagExportDocument,
	options: { dryRun?: boolean; upsert?: boolean } = {},
	signal?: AbortSignal
) =>
	request<PromptTagImportResult>({
		method: 'POST',
		path: '/admin/import',
		token,
		body: { ...body, dry_run: options.dryRun ?? false, upsert: options.upsert ?? false },
		signal
	});
