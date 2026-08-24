import {
	DEFAULT_IMAGE_ASPECT_RATIO,
	DEFAULT_IMAGE_COUNT_OPTIONS,
	IMAGE_ASPECT_RATIO_OPTIONS,
	type ImageAspectRatio,
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
