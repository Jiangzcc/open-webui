import type {
	VideoAdvancedField,
	VideoAssetRole,
	VideoModel,
	VideoTask,
	VideoTaskSubmission
} from '$lib/apis/videos';
import type { VideoQuote } from '$lib/apis/credits';
import type { ImageQuoteState } from '$lib/components/credits/quote-state';
import {
	normalizeVideoParamsForModel,
	type VideoAdvancedValidationError
} from '$lib/utils/video-generation';
import type { UploadedVideoAsset } from './videoLabels';

type AdvancedError = {
	field: VideoAdvancedField;
	error: { key: VideoAdvancedValidationError; value?: number };
} | null;

export type VideoSubmissionError =
	| { kind: 'prompt' }
	| { kind: 'asset'; role: VideoAssetRole }
	| { kind: 'advanced'; error: NonNullable<AdvancedError> }
	| { kind: 'negative_prompt' };

export type PreparedVideoSubmission =
	| { ok: true; value: VideoTaskSubmission }
	| { ok: false; error: VideoSubmissionError };

export const preferredVideoModelId = (
	models: VideoModel[],
	task: VideoTask,
	preferred?: string | null
): string =>
	models.find(
		(model) =>
			model.task === task &&
			model.id === preferred &&
			model.visible !== false &&
			model.enabled !== false
	)?.id ??
	models.find((model) => model.task === task && model.visible !== false && model.enabled !== false)
		?.id ??
	models.find((model) => model.task === task && model.visible !== false)?.id ??
	'';

export const defaultVideoParams = (
	model: VideoModel | null
): Record<string, string | number | boolean | null> => {
	if (!model) return {};
	const params: Record<string, string | number | boolean | null> = {};
	if (model.default_duration) params.duration = model.default_duration;
	if (model.default_aspect_ratio) params.aspect_ratio = model.default_aspect_ratio;
	if (model.default_resolution) params.resolution = model.default_resolution;
	if (model.default_audio_mode) params.audio_mode = model.default_audio_mode;
	return normalizeVideoParamsForModel(model, params);
};

export const videoQuoteDimensions = (
	params: Record<string, string | number | boolean | null>,
	model: VideoModel | null
): Record<string, string | number> => ({
	duration: String(params.duration ?? model?.default_duration ?? '1'),
	resolution: String(params.resolution ?? model?.default_resolution ?? 'default'),
	aspect_ratio: String(params.aspect_ratio ?? model?.default_aspect_ratio ?? 'default'),
	audio_mode: String(params.audio_mode ?? model?.default_audio_mode ?? 'default'),
	...(params.fps !== null && params.fps !== undefined && { fps: String(params.fps) }),
	...(params.output_quality !== null &&
		params.output_quality !== undefined && { output_quality: String(params.output_quality) })
});

export const imageQuoteStateFromVideoQuote = (quote: VideoQuote): ImageQuoteState => {
	if (quote.exempt) return { status: 'exempt', chargedCredits: 0 };
	if (!quote.configured) return { status: 'unconfigured', errorCode: quote.error ?? undefined };
	if (!quote.sufficient)
		return { status: 'insufficient', chargedCredits: quote.charged_credits ?? undefined };
	return quote.charged_credits === null
		? { status: 'error' }
		: { status: 'ready', chargedCredits: quote.charged_credits };
};

export const prepareVideoSubmission = (
	task: VideoTask,
	model: VideoModel,
	prompt: string,
	params: Record<string, string | number | boolean | null>,
	assets: Partial<Record<VideoAssetRole, UploadedVideoAsset[]>>,
	advancedError: AdvancedError
): PreparedVideoSubmission => {
	if (model.prompt_required && !prompt.trim()) return { ok: false, error: { kind: 'prompt' } };
	const missing = (model.asset_inputs ?? []).find(
		(capability) => capability.required && !(assets[capability.role]?.length ?? 0)
	);
	if (missing) return { ok: false, error: { kind: 'asset', role: missing.role } };
	if (advancedError) return { ok: false, error: { kind: 'advanced', error: advancedError } };
	const negativePrompt = String(params.negative_prompt ?? '').trim();
	const normalized = normalizeVideoParamsForModel(model, {
		...params,
		...(negativePrompt && { negative_prompt: negativePrompt })
	});
	if (negativePrompt && !('negative_prompt' in normalized)) {
		return { ok: false, error: { kind: 'negative_prompt' } };
	}
	return {
		ok: true,
		value: {
			task,
			model: model.id,
			prompt: prompt.trim(),
			assets: Object.entries(assets).flatMap(([role, items]) =>
				(items ?? []).map((item) => ({ role: role as VideoAssetRole, file_id: item.id }))
			),
			params: normalized
		}
	};
};
