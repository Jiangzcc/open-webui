import {
	DEFAULT_IMAGE_ASPECT_RATIO,
	DEFAULT_IMAGE_COUNT_OPTIONS,
	IMAGE_ASPECT_RATIO_OPTIONS,
	MAX_SELECTABLE_IMAGE_COUNT,
	type ImageAspectRatio,
	type ImageGenerationModel,
	type ImageModelCapability
} from './image-generation-types';

export const DEFAULT_IMAGE_ASPECT_RATIO_SIZES: Record<ImageAspectRatio, string | undefined> = {
	auto: undefined,
	'1:1': '1024x1024',
	'16:9': '1792x1024',
	'9:16': '1024x1792',
	'3:4': '768x1024',
	'4:3': '1024x768',
	'3:2': '1536x1024',
	'2:3': '1024x1536',
	'2.35:1': '1536x654',
	'21:9': '1536x640',
	'2:1': '1536x768',
	'1:2': '768x1536',
	'20:9': '1536x691',
	'9:20': '691x1536',
	'19.5:9': '1536x709',
	'9:19.5': '709x1536',
	'5:4': '1280x1024',
	'4:5': '1024x1280',
	'4:1': '1536x384',
	'1:4': '384x1536',
	'8:1': '1536x192',
	'1:8': '192x1536'
};

export const GPT_IMAGE_ASPECT_RATIO_SIZES: Partial<Record<ImageAspectRatio, string>> = {
	'1:1': '1024x1024',
	'16:9': '1536x864',
	'9:16': '864x1536',
	'3:4': '1152x1536',
	'4:3': '1536x1152',
	'3:2': '1536x1024',
	'2:3': '1024x1536',
	'21:9': '1536x640',
	'5:4': '1280x1024',
	'4:5': '1024x1280'
};

export const DALL_E_3_ASPECT_RATIO_SIZES: Partial<Record<ImageAspectRatio, string>> = {
	'1:1': '1024x1024',
	'16:9': '1792x1024',
	'9:16': '1024x1792'
};

export const DEFAULT_MODEL_CAPABILITY: ImageModelCapability = {
	aspectRatios: [...IMAGE_ASPECT_RATIO_OPTIONS],
	resolutions: [],
	imageCounts: [...DEFAULT_IMAGE_COUNT_OPTIONS],
	defaultAspectRatio: DEFAULT_IMAGE_ASPECT_RATIO,
	aspectRatioSizes: DEFAULT_IMAGE_ASPECT_RATIO_SIZES,
	outputFormats: [],
	qualityOptions: [],
	presetSizes: [],
	advancedFields: []
};

const isPositiveInteger = (value?: number | null) => {
	return Number.isInteger(value) && Number(value) > 0;
};

const getPresetModelId = (model?: ImageGenerationModel | string | null) => {
	if (typeof model === 'string') {
		return model;
	}

	return model?.id;
};

export const getImageCountsFromMax = (maxImages?: number) => {
	if (!isPositiveInteger(maxImages)) {
		return [];
	}

	// 上限统一为 MAX_SELECTABLE_IMAGE_COUNT，maxImages 再大也只暴露 1..N。
	const max = Math.min(Number(maxImages), MAX_SELECTABLE_IMAGE_COUNT);
	return Array.from({ length: max }, (_, index) => index + 1);
};

export const getModelPresetCapability = (
	model?: ImageGenerationModel | string | null
): Partial<ImageModelCapability> => {
	const id = getPresetModelId(model)?.toLowerCase() ?? '';

	if (/dall[\s-_]?e[\s-_]?2/.test(id)) {
		return {
			aspectRatios: ['1:1'],
			resolutions: ['256x256', '512x512', '1024x1024'],
			imageCounts: getImageCountsFromMax(MAX_SELECTABLE_IMAGE_COUNT),
			defaultAspectRatio: '1:1',
			aspectRatioSizes: {
				'1:1': '1024x1024'
			}
		};
	}

	if (/dall[\s-_]?e[\s-_]?3/.test(id)) {
		return {
			aspectRatios: ['1:1', '16:9', '9:16'],
			resolutions: [],
			imageCounts: [1],
			defaultAspectRatio: '1:1',
			aspectRatioSizes: DALL_E_3_ASPECT_RATIO_SIZES
		};
	}

	if (/nano[\s-_]?banana[\s-_]?pro|gemini[\s-_]?3[\s-_.]?pro[\s-_]?image/.test(id)) {
		return {
			aspectRatios: [
				DEFAULT_IMAGE_ASPECT_RATIO,
				'16:9',
				'9:16',
				'1:1',
				'2:3',
				'3:2',
				'4:3',
				'3:4',
				'21:9'
			],
			resolutions: ['1K', '2K', '4K'],
			imageCounts: [...DEFAULT_IMAGE_COUNT_OPTIONS],
			defaultAspectRatio: DEFAULT_IMAGE_ASPECT_RATIO,
			defaultResolution: '1K',
			aspectRatioSizes: GPT_IMAGE_ASPECT_RATIO_SIZES
		};
	}

	if (
		/nano[\s-_]?banana|gemini[\s-_]?(25|2[\s-_.]?5|3[\s-_.]?1)[\s-_]?flash[\s-_]?image/.test(id)
	) {
		return {
			aspectRatios: ['1:1', '16:9', '9:16'],
			resolutions: [],
			imageCounts: [...DEFAULT_IMAGE_COUNT_OPTIONS],
			defaultAspectRatio: '1:1',
			aspectRatioSizes: DALL_E_3_ASPECT_RATIO_SIZES
		};
	}

	if (/gpt[\s-_]?image/.test(id)) {
		return {
			aspectRatios: [DEFAULT_IMAGE_ASPECT_RATIO, '1:1', '3:2', '2:3'],
			resolutions: ['auto', '1024x1024', '1536x1024', '1024x1536'],
			imageCounts: getImageCountsFromMax(MAX_SELECTABLE_IMAGE_COUNT),
			defaultAspectRatio: DEFAULT_IMAGE_ASPECT_RATIO,
			defaultResolution: 'auto',
			aspectRatioSizes: GPT_IMAGE_ASPECT_RATIO_SIZES
		};
	}

	if (/imagen|gemini/.test(id)) {
		return {
			aspectRatios: [DEFAULT_IMAGE_ASPECT_RATIO, '1:1', '16:9', '9:16', '3:4', '4:3'],
			resolutions: [],
			imageCounts: [...DEFAULT_IMAGE_COUNT_OPTIONS],
			defaultAspectRatio: DEFAULT_IMAGE_ASPECT_RATIO,
			aspectRatioSizes: DEFAULT_IMAGE_ASPECT_RATIO_SIZES
		};
	}

	return {};
};
