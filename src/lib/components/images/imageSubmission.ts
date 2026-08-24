import {
	ImageTaskRequestError,
	createImageGenerationTask
} from '$lib/apis/creations/generation-tasks';
import {
	buildImageEditPayload,
	buildImageGenerationPayload,
	type ImageAspectRatio,
	type ImageGenerationModel
} from '$lib/utils/image-generation';
import type { ImageGenerationTask } from '$lib/utils/image-generation-batches';

export type ImageSubmissionInput = {
	prompt: string;
	aspectRatio: ImageAspectRatio;
	resolution: string;
	quality: string;
	model: ImageGenerationModel | string | null;
	count: number;
	steps: number | null;
	negativePrompt: string;
	outputFormat: string;
	seed: number | null;
	guidanceScale: number | null;
	strength: number | null;
	size: string | null;
	referenceUrls: string[];
};

export const buildImageTaskPayload = (input: ImageSubmissionInput) => {
	const common = {
		prompt: input.prompt,
		aspectRatio: input.aspectRatio,
		resolution: input.resolution,
		quality: input.quality || null,
		model: input.model,
		n: input.count,
		steps: input.steps,
		negative_prompt: input.negativePrompt,
		output_format: input.outputFormat || null,
		seed: input.seed,
		guidance_scale: input.guidanceScale,
		strength: input.strength,
		size: input.size
	};
	return input.referenceUrls.length
		? buildImageEditPayload({ ...common, referenceImages: input.referenceUrls })
		: buildImageGenerationPayload(common);
};

type SubmissionIdempotency = {
	idempotencyKeyFor: (payload: object) => Promise<string>;
	clearPendingSubmission: () => void;
};

export const submitImageTask = async (
	token: string,
	input: ImageSubmissionInput,
	idempotency: SubmissionIdempotency
): Promise<ImageGenerationTask> => {
	const payload = buildImageTaskPayload(input);
	const task = await createImageGenerationTask(
		token,
		input.referenceUrls.length ? 'image-to-image' : 'text-to-image',
		payload,
		await idempotency.idempotencyKeyFor(payload)
	);
	idempotency.clearPendingSubmission();
	return task;
};

export const shouldClearImageSubmission = (error: unknown): boolean =>
	error instanceof ImageTaskRequestError &&
	error.status !== undefined &&
	error.status >= 400 &&
	error.status < 500 &&
	![408, 429].includes(error.status);
