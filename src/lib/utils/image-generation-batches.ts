import type {
	GeneratedImage,
	ImageAspectRatio,
	ImageEditPayload,
	ImageGenerationPayload
} from './image-generation';

export type ImageGenerationTaskStatus = 'queued' | 'running' | 'succeeded' | 'failed';
export type ImageGenerationTaskKind = 'text-to-image' | 'image-to-image';

export type ImageGenerationTask = {
	id: string;
	status: ImageGenerationTaskStatus;
	kind: ImageGenerationTaskKind;
	prompt: string;
	model_id: string | null;
	params: Record<string, unknown> | null;
	expected_count: number;
	result: GeneratedImage[];
	error_code: string | null;
	created_at: number;
	started_at: number | null;
	completed_at: number | null;
	updated_at: number;
};

export type ImageGenerationBatch = {
	id: string;
	status: ImageGenerationTaskStatus;
	kind: ImageGenerationTaskKind;
	prompt: string;
	modelId: string | null;
	params: Record<string, unknown>;
	aspectRatio: ImageAspectRatio;
	resolution: string;
	quality: string;
	expectedCount: number;
	images: GeneratedImage[];
	errorCode: string | null;
	createdAt: number;
	startedAt: number | null;
	completedAt: number | null;
};

export type ImageCreationDraft = {
	prompt: string;
	modelId: string | null;
	aspectRatio: ImageAspectRatio | null;
	resolution: string | null;
	quality: string | null;
	referenceImageUrl: string | null;
};

const PENDING_CREATION_DRAFT_KEY = 'open-webui:pending-image-creation-draft';

type DraftStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

const nullableString = (value: unknown): value is string | null =>
	typeof value === 'string' || value === null;

const isImageCreationDraft = (value: unknown): value is ImageCreationDraft => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
	const draft = value as Record<string, unknown>;
	return (
		typeof draft.prompt === 'string' &&
		nullableString(draft.modelId) &&
		nullableString(draft.aspectRatio) &&
		nullableString(draft.resolution) &&
		nullableString(draft.quality) &&
		nullableString(draft.referenceImageUrl)
	);
};

export const storePendingCreationDraft = (storage: DraftStorage, draft: ImageCreationDraft) => {
	storage.setItem(PENDING_CREATION_DRAFT_KEY, JSON.stringify(draft));
};

export const consumePendingCreationDraft = (storage: DraftStorage): ImageCreationDraft | null => {
	const serialized = storage.getItem(PENDING_CREATION_DRAFT_KEY);
	if (serialized === null) return null;
	storage.removeItem(PENDING_CREATION_DRAFT_KEY);
	try {
		const parsed: unknown = JSON.parse(serialized);
		return isImageCreationDraft(parsed) ? parsed : null;
	} catch {
		return null;
	}
};

const stringParam = (params: Record<string, unknown> | null, key: string) => {
	const value = params?.[key];
	return typeof value === 'string' && value.trim() ? value.trim() : '';
};

const aspectRatioParam = (params: Record<string, unknown> | null): ImageAspectRatio => {
	const value = stringParam(params, 'aspect_ratio');
	return (value || 'auto') as ImageAspectRatio;
};

export const taskToGenerationBatch = (task: ImageGenerationTask): ImageGenerationBatch => ({
	id: task.id,
	status: task.status,
	kind: task.kind,
	prompt: task.prompt,
	modelId: task.model_id,
	params: task.params ?? {},
	aspectRatio: aspectRatioParam(task.params),
	resolution: stringParam(task.params, 'resolution') || stringParam(task.params, 'size'),
	quality: stringParam(task.params, 'quality'),
	expectedCount: Math.max(1, task.expected_count),
	images: task.result.map((image) => ({
		...image,
		prompt: image.prompt ?? task.prompt,
		aspectRatio: image.aspectRatio ?? aspectRatioParam(task.params),
		createdAt: image.createdAt ?? task.completed_at ?? task.created_at
	})),
	errorCode: task.error_code,
	createdAt: task.created_at,
	startedAt: task.started_at,
	completedAt: task.completed_at
});

export const mergeGenerationTask = (
	batches: readonly ImageGenerationBatch[],
	task: ImageGenerationTask
): ImageGenerationBatch[] => {
	const next = taskToGenerationBatch(task);
	const existingIndex = batches.findIndex((batch) => batch.id === task.id);
	if (existingIndex === -1) {
		// batches 已按 createdAt 降序；新任务按 createdAt 定位一次插入位置即可，
		// 避免逐条 [next, ...batches].sort() 的 O(N log N) 全数组重排。
		const createdAt = next.createdAt;
		let insertAt = batches.length;
		for (let i = 0; i < batches.length; i += 1) {
			if (batches[i].createdAt <= createdAt) {
				insertAt = i;
				break;
			}
		}
		const result = batches.slice();
		result.splice(insertAt, 0, next);
		return result;
	}
	return batches.map((batch, index) => (index === existingIndex ? next : batch));
};

export const isGenerationTaskTerminal = (status: ImageGenerationTaskStatus) =>
	status === 'succeeded' || status === 'failed';

export const generationElapsedSeconds = (batch: ImageGenerationBatch, now = Date.now()) => {
	const end = batch.completedAt ?? Math.floor(now / 1000);
	return Math.max(0, end - batch.createdAt);
};

export const buildGenerationTaskRequest = (
	payload: ImageGenerationPayload | ImageEditPayload,
	kind: ImageGenerationTaskKind
) => ({ kind, payload });

export const buildCreationDraft = (input: {
	prompt: string;
	model_id?: string | null;
	params?: Record<string, unknown> | null;
	content_url?: string | null;
	useAsReference?: boolean;
}): ImageCreationDraft => ({
	prompt: input.prompt,
	modelId: input.model_id ?? null,
	aspectRatio: (stringParam(input.params ?? null, 'aspect_ratio') as ImageAspectRatio) || null,
	resolution:
		stringParam(input.params ?? null, 'resolution') ||
		stringParam(input.params ?? null, 'size') ||
		null,
	quality: stringParam(input.params ?? null, 'quality') || null,
	referenceImageUrl: input.useAsReference ? (input.content_url ?? null) : null
});
