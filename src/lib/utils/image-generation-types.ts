import type { CustomSizeConstraints, ImageAdvancedField } from './image-generation-capabilities';

export const DEFAULT_IMAGE_ASPECT_RATIO = 'auto' as const;

export const IMAGE_ASPECT_RATIO_OPTIONS = [
	DEFAULT_IMAGE_ASPECT_RATIO,
	'1:1',
	'16:9',
	'9:16',
	'3:4',
	'4:3',
	'3:2',
	'2:3',
	'2.35:1',
	'21:9',
	'2:1',
	'1:2',
	'20:9',
	'9:20',
	'19.5:9',
	'9:19.5',
	'5:4',
	'4:5',
	'4:1',
	'1:4',
	'8:1',
	'1:8'
] as const;

export const DEFAULT_IMAGE_COUNT_OPTIONS = [1, 2, 3, 4] as const;

export type ImageAspectRatio = (typeof IMAGE_ASPECT_RATIO_OPTIONS)[number];

export type ImageGenerationPayload = {
	prompt: string;
	model?: string;
	size?: string;
	n?: number;
	steps?: number;
	negative_prompt?: string;
	aspect_ratio?: string;
	resolution?: string;
	quality?: string;
	output_format?: string;
	system_prompt?: string;
	seed?: number;
	guidance_scale?: number;
	strength?: number;
};

export type ImageEditPayload = ImageGenerationPayload & {
	image: string | string[];
	background?: string;
};

export type GeneratedImage = {
	url: string;
	prompt?: string;
	aspectRatio?: ImageAspectRatio;
	createdAt?: number;
};

export type ImageGenerationModel = {
	id: string;
	name?: string;
	provider?: string;
	task?: 'text-to-image' | 'image-to-image' | string;
	generationModel?: string;
	editModel?: string;
	isDefault?: boolean;
	aspectRatios?: ImageAspectRatio[];
	resolutions?: string[];
	imageCounts?: number[];
	maxImages?: number;
	defaultAspectRatio?: ImageAspectRatio;
	defaultResolution?: string;
	aspectRatioSizes?: Partial<Record<ImageAspectRatio, string>>;
	sizeField?: string;
	supportsAspectRatioField?: boolean;
	outputFormats?: string[];
	defaultOutputFormat?: string;
	qualityOptions?: string[];
	defaultQuality?: string;
	hosting?: string;
	basePrice?: string;
	editBasePrice?: string;
	visible?: boolean;
	enabled?: boolean;
	recommended?: boolean;
	sortOrder?: number;
	tags?: string[];
	maintenanceMessage?: string;
	imageInputMaxCount?: number;
	customSize?: CustomSizeConstraints;
	presetSizes?: string[];
	advancedFields?: ImageAdvancedField[];
};

export type ImageModelCapability = {
	aspectRatios: ImageAspectRatio[];
	resolutions: string[];
	imageCounts: number[];
	defaultAspectRatio: ImageAspectRatio;
	defaultResolution?: string;
	aspectRatioSizes: Partial<Record<ImageAspectRatio, string>>;
	sizeField?: string;
	supportsAspectRatioField?: boolean;
	outputFormats: string[];
	defaultOutputFormat?: string;
	qualityOptions: string[];
	defaultQuality?: string;
	customSize?: CustomSizeConstraints;
	presetSizes: string[];
	advancedFields: ImageAdvancedField[];
};

export type ImagePayloadInput = {
	prompt: string;
	aspectRatio?: unknown;
	model?: ImageGenerationModel | string | null;
	size?: string | null;
	resolution?: string | null;
	quality?: string | null;
	n?: number | null;
	steps?: number | null;
	negative_prompt?: string | null;
	output_format?: string | null;
	seed?: number | null;
	guidance_scale?: number | null;
	strength?: number | null;
};

export type ImageEditPayloadInput = ImagePayloadInput & {
	referenceImages: string[];
	background?: string | null;
};

export type FileLike = { name?: string; type?: string; size?: number };

export type RejectedImageFile = {
	file: FileLike;
	reason: 'unsupported_type' | 'too_large' | 'too_many';
};
