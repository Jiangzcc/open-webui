import type { ImageQuoteInput } from '$lib/apis/credits';
import { getImageGenerationModels } from '$lib/apis/images';
import { getImageGenerationErrorCode } from '$lib/apis/images/generation';
import {
	buildImageEditPayload,
	buildImageGenerationPayload,
	getImageModelCapability,
	normalizeImageGenerationModels,
	type GeneratedImage,
	type ImageAspectRatio,
	type ImageEditPayload,
	type ImageGenerationPayload,
	type ImageGenerationModel
} from '$lib/utils/image-generation';
import {
	buildCreationDraft,
	type ImageCreationDraft,
	type ImageGenerationBatch
} from '$lib/utils/image-generation-batches';

type AdvancedNumberField = {
	kind: 'integer' | 'number' | 'text';
	min?: number;
	max?: number;
};

type Translate = (key: string, values?: Record<string, number>) => string;

export const CREDIT_QUOTE_PLACEHOLDER_PROMPT = 'credit-quote';

const hasReferenceImage = (
	payload: ImageGenerationPayload | ImageEditPayload
): payload is ImageEditPayload => 'image' in payload;

export const loadImageModelState = async (token: string, selectedModel: string) => {
	const models = normalizeImageGenerationModels(await getImageGenerationModels(token));
	if (selectedModel) return { models, defaultCapability: null };
	const defaultModel =
		models.find((model) => model.isDefault && model.enabled !== false) ??
		models.find((model) => model.enabled !== false) ??
		models[0];
	return {
		models,
		defaultCapability: defaultModel ? getImageModelCapability(defaultModel) : null
	};
};

export const recentImageTaskSince = () => Math.floor(Date.now() / 1000) - 7 * 24 * 60 * 60;

export const buildImageQuoteInput = (
	aspectRatio: ImageAspectRatio,
	resolution: string,
	quality: string,
	model: ImageGenerationModel | string | null,
	count: number,
	stepCount: number | null,
	negativePrompt: string,
	referenceUrls: string[],
	size: string | null
): ImageQuoteInput | null => {
	const common = {
		prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT,
		aspectRatio,
		resolution,
		quality: quality || null,
		model,
		n: count,
		steps: stepCount,
		negative_prompt: negativePrompt,
		size
	};
	const payload = referenceUrls.length
		? buildImageEditPayload({ ...common, referenceImages: referenceUrls })
		: buildImageGenerationPayload(common);
	if (!payload.model) return null;
	return {
		resource_id: payload.model,
		action: referenceUrls.length ? 'image-to-image' : 'text-to-image',
		prompt: payload.prompt,
		...(hasReferenceImage(payload) && { image: payload.image }),
		dimensions: {
			...(payload.size && { size: payload.size }),
			...(payload.resolution && { resolution: payload.resolution }),
			...(payload.aspect_ratio && { aspect_ratio: payload.aspect_ratio }),
			...(payload.quality && { quality: payload.quality }),
			image_count: payload.n ?? 1
		}
	};
};

export const imageGenerationErrorKey = (error: unknown): string => {
	switch (getImageGenerationErrorCode(error)) {
		case 'insufficient_credits':
			return 'credits.insufficient';
		case 'price_not_configured':
		case 'price_rule_incomplete':
			return 'credits.unconfigured';
		case 'invalid_image_size':
			return 'Image size is invalid';
		case 'rate_limited':
			return 'Too many image generation requests';
		default:
			return 'credits.unavailable';
	}
};

export const getAdvancedNumberError = (
	value: string,
	field: AdvancedNumberField,
	translate: Translate
): string | null => {
	if (!value.trim()) return null;
	const parsed = Number(value);
	if (!Number.isFinite(parsed) || (field.kind === 'integer' && !Number.isInteger(parsed))) {
		return translate(field.kind === 'integer' ? 'Enter a whole number' : 'Enter a number');
	}
	if (field.min !== undefined && parsed < field.min)
		return translate('Minimum: {{value}}', { value: field.min });
	if (field.max !== undefined && parsed > field.max)
		return translate('Maximum: {{value}}', { value: field.max });
	return null;
};

export const parseAdvancedNumber = (
	value: string,
	field: AdvancedNumberField | null,
	translate: Translate
): number | null =>
	!field || !value.trim() || getAdvancedNumberError(value, field, translate) ? null : Number(value);

export const advancedRangeLabel = (
	field: Pick<AdvancedNumberField, 'min' | 'max'> | null,
	translate: Translate
): string => {
	if (!field || (field.min === undefined && field.max === undefined))
		return translate('Model default');
	if (field.min !== undefined && field.max !== undefined) return `${field.min}–${field.max}`;
	return field.min !== undefined ? `≥ ${field.min}` : `≤ ${field.max}`;
};

export const imageModelDisplayName = (model: ImageGenerationModel): string => {
	const name = model.name?.trim() || model.id;
	const separatorIndex = name.indexOf(' / ');
	return separatorIndex === -1 ? name : name.slice(separatorIndex + 3);
};

export const draftForBatchGeneration = (batch: ImageGenerationBatch): ImageCreationDraft =>
	buildCreationDraft({ prompt: batch.prompt, model_id: batch.modelId, params: batch.params });

export const draftForImageReference = (
	batch: ImageGenerationBatch,
	image: GeneratedImage
): ImageCreationDraft =>
	buildCreationDraft({
		prompt: batch.prompt,
		model_id: batch.modelId,
		params: batch.params,
		content_url: image.url,
		useAsReference: true
	});

export const draftForImageGeneration = (
	batch: ImageGenerationBatch,
	image: GeneratedImage
): ImageCreationDraft =>
	buildCreationDraft({
		prompt: image.prompt?.trim() || batch.prompt,
		model_id: batch.modelId,
		params: batch.params
	});

export const draftForBatchEdit = (batch: ImageGenerationBatch): ImageCreationDraft => {
	const contentUrl = batch.images[0]?.url ?? null;
	return buildCreationDraft({
		prompt: batch.prompt,
		model_id: batch.modelId,
		params: batch.params,
		content_url: contentUrl,
		useAsReference: Boolean(contentUrl)
	});
};
