import { WEBUI_API_BASE_URL } from '$lib/constants';

export type VideoTask = 'text-to-video' | 'image-to-video' | 'video-to-video';
export type VideoAssetRole =
	| 'start_image'
	| 'end_image'
	| 'source_video'
	| 'reference_image'
	| 'reference_video'
	| 'reference_audio';

export type VideoAssetCapability = {
	role: VideoAssetRole;
	required: boolean;
	multiple: boolean;
	max_count: number;
	mime_types: string[];
	max_bytes: number;
};

export type VideoField = {
	field: string;
	source?: string | null;
	options?: string[];
	default?: string | number | boolean | null;
	min?: number | null;
	max?: number | null;
	step?: number | null;
	max_length?: number;
	required?: boolean;
	format?: 'json';
	advanced: boolean;
};

export type VideoAdvancedFieldKey =
	| 'seed'
	| 'negative_prompt'
	| 'prompt_enhancement'
	| 'motion_amplitude'
	| 'guidance_scale'
	| 'fps'
	| 'output_quality'
	| 'loop'
	| 'edit_strength'
	| 'retake_mode'
	| 'start_time'
	| 'ingredients_mode';

export type VideoAdvancedField = {
	key: VideoAdvancedFieldKey;
	kind: 'option' | 'boolean' | 'integer' | 'number' | 'text';
	options?: string[];
	default?: string | number | boolean | null;
	min?: number | null;
	max?: number | null;
	step?: number | null;
	max_length?: number;
};

export type VideoModel = {
	id: string;
	name: string;
	provider: string;
	task: VideoTask;
	prompt_required: boolean;
	durations?: string[] | null;
	default_duration?: string | null;
	duration_min?: number | null;
	duration_max?: number | null;
	duration_step?: number | null;
	aspect_ratios?: string[] | null;
	default_aspect_ratio?: string | null;
	resolutions?: string[] | null;
	default_resolution?: string | null;
	audio_options?: { mode: string }[] | null;
	default_audio_mode?: string | null;
	asset_inputs?: VideoAssetCapability[] | null;
	option_fields?: VideoField[] | null;
	boolean_fields?: VideoField[] | null;
	integer_fields?: VideoField[] | null;
	number_fields?: VideoField[] | null;
	text_fields?: VideoField[] | null;
	json_fields?: VideoField[] | null;
	advanced_fields?: VideoAdvancedField[] | null;
	visible?: boolean;
	enabled?: boolean;
	recommended?: boolean;
	sort_order?: number;
	tags?: string[];
	maintenance_message?: string | null;
	base_price?: string | null;
};

export type VideoTaskResult = {
	creation_id: string;
	file_id: string;
	poster_file_id: string;
	url: string;
	poster_url: string;
	duration_seconds: number;
	mime_type: 'video/mp4';
};

export type VideoGenerationTask = {
	id: string;
	status: 'queued' | 'running' | 'succeeded' | 'failed';
	task: VideoTask;
	prompt: string;
	model_id: string;
	params: Record<string, unknown>;
	assets: { role: VideoAssetRole; file_id: string }[];
	result: VideoTaskResult | null;
	error_code: string | null;
	created_at: number;
	started_at: number | null;
	completed_at: number | null;
	updated_at: number;
};

export class VideoRequestError extends Error {
	code: string;
	publicMessage?: string;
	preferPublicMessage: boolean;

	constructor(code: string, publicMessage?: string, preferPublicMessage = false) {
		super(code);
		this.name = 'VideoRequestError';
		this.code = code;
		this.publicMessage = publicMessage;
		this.preferPublicMessage = preferPublicMessage;
	}
}

export const parseVideoRequestError = (payload: unknown): VideoRequestError => {
	if (!payload || typeof payload !== 'object') return new VideoRequestError('video_request_failed');

	const body = payload as Record<string, unknown>;
	if (body.detail && typeof body.detail === 'object') {
		const detail = body.detail as Record<string, unknown>;
		const code = typeof detail.code === 'string' ? detail.code : 'video_request_failed';
		const publicMessage = typeof detail.message === 'string' ? detail.message : undefined;
		return new VideoRequestError(code, publicMessage, true);
	}
	if (typeof body.detail === 'string') return new VideoRequestError(body.detail);
	if (typeof body.code === 'string') {
		const publicMessage = typeof body.message === 'string' ? body.message : undefined;
		return new VideoRequestError(body.code, publicMessage);
	}
	return new VideoRequestError('video_request_failed');
};

const request = async <T>(token: string, path: string, init?: RequestInit): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/videos${path}`, {
		...init,
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`,
			...(init?.headers ?? {})
		}
	});
	if (!response.ok) {
		const payload = await response.json().catch(() => ({}));
		throw parseVideoRequestError(payload);
	}
	return response.status === 204 ? (undefined as T) : response.json();
};

export const getVideoModels = (token: string) =>
	request<{ defaults: Record<VideoTask, string>; models: VideoModel[] }>(token, '/models');

export const submitVideoTask = (
	token: string,
	payload: {
		task: VideoTask;
		model: string;
		prompt: string;
		assets: { role: VideoAssetRole; file_id: string }[];
		params: Record<string, string | number | boolean | null>;
	},
	idempotencyKey: string
) =>
	request<VideoGenerationTask>(token, '/tasks', {
		method: 'POST',
		headers: { 'Idempotency-Key': idempotencyKey },
		body: JSON.stringify(payload)
	});

export const getVideoTask = (token: string, taskId: string) =>
	request<VideoGenerationTask>(token, `/tasks/${encodeURIComponent(taskId)}`);

export const listVideoTasks = (
	token: string,
	limit = 20,
	cursor?: string | null,
	since?: number | null
) => {
	const search = new URLSearchParams({ limit: String(limit) });
	if (cursor) search.set('cursor', cursor);
	if (since !== undefined && since !== null) search.set('since', String(since));
	return request<{ items: VideoGenerationTask[]; next_cursor: string | null }>(
		token,
		`/tasks?${search}`
	);
};

export const deleteVideoTask = (token: string, taskId: string) =>
	request<void>(token, `/tasks/${encodeURIComponent(taskId)}`, { method: 'DELETE' });
