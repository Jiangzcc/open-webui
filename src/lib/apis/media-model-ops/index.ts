import { WEBUI_API_BASE_URL } from '$lib/constants';
import { extRequest } from '$lib/apis/extRequest';

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

const request = <T>(path: string, token: string, init?: RequestInit): Promise<T> =>
	extRequest<T>(`${WEBUI_API_BASE_URL}/media-model-ops${path}`, { ...init, token });

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
