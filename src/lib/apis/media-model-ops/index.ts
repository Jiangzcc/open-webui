import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ImageModelOperation = {
	media_kind: 'image' | 'video';
	model_id: string;
	public_id: string;
	name: string;
	provider: string;
	task: string;
	visible: boolean;
	enabled: boolean;
	recommended: boolean;
	sort_order: number;
	tags: string[];
	maintenance_message: string | null;
	updated_at: number | null;
};

export type ImageModelOperationUpdate = Partial<
	Pick<
		ImageModelOperation,
		'visible' | 'enabled' | 'recommended' | 'sort_order' | 'tags' | 'maintenance_message'
	>
>;

const request = async <T>(path: string, token: string, init?: RequestInit): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/media-model-ops${path}`, {
		...init,
		headers: {
			Accept: 'application/json',
			...(init?.body ? { 'Content-Type': 'application/json' } : {}),
			Authorization: `Bearer ${token}`,
			...(init?.headers ?? {})
		}
	});
	if (!response.ok) throw await response.json().catch(() => null);
	// 204 No Content 无响应体，直接返回 undefined。
	if (response.status === 204) return undefined as T;
	return (await response.json()) as T;
};

export const listImageModelOperations = async (token: string) =>
	(await request<{ items: ImageModelOperation[] }>('/admin/models', token)).items;

export const updateImageModelOperation = (
	token: string,
	modelId: string,
	input: ImageModelOperationUpdate
) =>
	request<ImageModelOperation>(`/admin/models/${encodeURIComponent(modelId)}`, token, {
		method: 'PATCH',
		body: JSON.stringify(input)
	});

export const updateMediaModelOperation = (
	token: string,
	mediaKind: 'image' | 'video',
	modelId: string,
	input: ImageModelOperationUpdate
) =>
	request<ImageModelOperation>(
		`/admin/media-models/${mediaKind}/${encodeURIComponent(modelId)}`,
		token,
		{
			method: 'PATCH',
			body: JSON.stringify(input)
		}
	);
