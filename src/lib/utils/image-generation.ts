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
	qualityOptions: string[];
	defaultQuality?: string;
};

type ImagePayloadInput = {
	prompt: string;
	aspectRatio?: unknown;
	model?: ImageGenerationModel | string | null;
	size?: string | null;
	resolution?: string | null;
	quality?: string | null;
	n?: number | null;
	steps?: number | null;
	negative_prompt?: string | null;
};

type ImageEditPayloadInput = ImagePayloadInput & {
	referenceImages: string[];
	background?: string | null;
};

type FileLike = {
	name?: string;
	type?: string;
	size?: number;
};

type RejectedImageFile = {
	file: FileLike;
	reason: 'unsupported_type' | 'too_large' | 'too_many';
};

const DEFAULT_IMAGE_ASPECT_RATIO_SIZES: Record<ImageAspectRatio, string | undefined> = {
	auto: undefined,
	'1:1': '1024x1024',
	'16:9': '1792x1024',
	'9:16': '1024x1792',
	'3:4': '768x1024',
	'4:3': '1024x768',
	'3:2': '1536x1024',
	'2:3': '1024x1536',
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

const GPT_IMAGE_ASPECT_RATIO_SIZES: Partial<Record<ImageAspectRatio, string>> = {
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

const DALL_E_3_ASPECT_RATIO_SIZES: Partial<Record<ImageAspectRatio, string>> = {
	'1:1': '1024x1024',
	'16:9': '1792x1024',
	'9:16': '1024x1792'
};

const DEFAULT_MODEL_CAPABILITY: ImageModelCapability = {
	aspectRatios: [...IMAGE_ASPECT_RATIO_OPTIONS],
	resolutions: [],
	imageCounts: [...DEFAULT_IMAGE_COUNT_OPTIONS],
	defaultAspectRatio: DEFAULT_IMAGE_ASPECT_RATIO,
	aspectRatioSizes: DEFAULT_IMAGE_ASPECT_RATIO_SIZES,
	qualityOptions: []
};

const isPositiveInteger = (value?: number | null) => {
	return Number.isInteger(value) && Number(value) > 0;
};

const trimOptional = (value?: string | null) => {
	const trimmed = value?.trim();
	return trimmed ? trimmed : undefined;
};

const getApiAspectRatio = (aspectRatio: unknown) => {
	const normalized = normalizeAspectRatio(aspectRatio);
	return normalized === DEFAULT_IMAGE_ASPECT_RATIO ? 'auto' : normalized;
};

const getModelId = (model?: ImageGenerationModel | string | null) => {
	if (typeof model === 'string') {
		return model;
	}

	return model?.id;
};

const normalizeStringList = (value: unknown) => {
	if (typeof value === 'string') {
		return value
			.split(',')
			.map((item) => item.trim())
			.filter(Boolean);
	}

	if (!Array.isArray(value)) {
		return [];
	}

	return value.flatMap((item) => {
		if (typeof item !== 'string') {
			return [];
		}

		const trimmed = item.trim();
		return trimmed ? [trimmed] : [];
	});
};

const normalizeNumberList = (value: unknown) => {
	const items = Array.isArray(value) ? value : typeof value === 'number' ? [value] : [];
	const counts = items.flatMap((item) => {
		const count = Number(item);
		return Number.isInteger(count) && count > 0 ? [count] : [];
	});

	return [...new Set(counts)].sort((a, b) => a - b);
};

const normalizeAspectRatioList = (value: unknown) => {
	const ratios = normalizeStringList(value).flatMap((item) => {
		const ratio = normalizeAspectRatio(item);
		return ratio === DEFAULT_IMAGE_ASPECT_RATIO &&
			![DEFAULT_IMAGE_ASPECT_RATIO, 'default'].includes(item)
			? []
			: [ratio];
	});

	return [...new Set(ratios)];
};

const normalizeResolutionList = (value: unknown) => {
	return [
		...new Set(
			normalizeStringList(value).filter((item) => {
				return (
					item === 'auto' ||
					item === 'square' ||
					item === 'square_hd' ||
					/^auto_\d+K$/i.test(item) ||
					/^\d+(\.\d+)?K$/i.test(item) ||
					/^\d+$/.test(item) ||
					/^\d+x\d+$/.test(item) ||
					/^[a-z]+_\d+_\d+$/i.test(item)
				);
			})
		)
	];
};

const normalizeAspectRatioSizeMap = (value: unknown) => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) {
		return {};
	}

	return Object.entries(value).reduce<Partial<Record<ImageAspectRatio, string>>>(
		(sizes, [ratioValue, sizeValue]) => {
			const ratio = normalizeAspectRatio(ratioValue);
			const size = typeof sizeValue === 'string' ? sizeValue.trim() : '';
			const isKnownRatio =
				ratio !== DEFAULT_IMAGE_ASPECT_RATIO || ratioValue === DEFAULT_IMAGE_ASPECT_RATIO;
			const isValidSize = size === 'auto' || /^\d+x\d+$/.test(size);

			return isKnownRatio && isValidSize ? { ...sizes, [ratio]: size } : sizes;
		},
		{}
	);
};

const hasOwn = (value: object, key: string) => {
	return Object.prototype.hasOwnProperty.call(value, key);
};

const getImageCountsFromMax = (maxImages?: number) => {
	if (!isPositiveInteger(maxImages)) {
		return [];
	}

	const max = Math.min(Number(maxImages), 10);
	return Array.from({ length: max }, (_, index) => index + 1);
};

const getModelPresetCapability = (
	model?: ImageGenerationModel | string | null
): Partial<ImageModelCapability> => {
	const id = getModelId(model)?.toLowerCase() ?? '';

	if (/dall[\s-_]?e[\s-_]?2/.test(id)) {
		return {
			aspectRatios: ['1:1'],
			resolutions: ['256x256', '512x512', '1024x1024'],
			imageCounts: getImageCountsFromMax(10),
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
			imageCounts: getImageCountsFromMax(10),
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

const getExplicitModelCapability = (model?: ImageGenerationModel | string | null) => {
	if (!model || typeof model === 'string') {
		return {};
	}

	const countsFromMax = getImageCountsFromMax(model.maxImages);

	return {
		aspectRatios: model.aspectRatios,
		resolutions: model.resolutions,
		imageCounts: model.imageCounts?.length ? model.imageCounts : countsFromMax,
		defaultAspectRatio: model.defaultAspectRatio,
		defaultResolution: model.defaultResolution,
		aspectRatioSizes: model.aspectRatioSizes,
		sizeField: model.sizeField,
		supportsAspectRatioField: model.supportsAspectRatioField,
		qualityOptions: model.qualityOptions,
		defaultQuality: model.defaultQuality
	};
};

export const normalizeAspectRatio = (value: unknown): ImageAspectRatio => {
	if (value === 'auto') {
		return DEFAULT_IMAGE_ASPECT_RATIO;
	}

	return IMAGE_ASPECT_RATIO_OPTIONS.includes(value as ImageAspectRatio)
		? (value as ImageAspectRatio)
		: DEFAULT_IMAGE_ASPECT_RATIO;
};

export const getImageModelCapability = (
	model?: ImageGenerationModel | string | null
): ImageModelCapability => {
	const preset = getModelPresetCapability(model);
	const explicit = getExplicitModelCapability(model);
	const hasExplicitAspectRatios = typeof model !== 'string' && model?.aspectRatios !== undefined;
	const hasExplicitResolutions = typeof model !== 'string' && model?.resolutions !== undefined;
	const usesExplicitCapability =
		typeof model === 'object' &&
		model !== null &&
		(model.aspectRatios !== undefined ||
			model.resolutions !== undefined ||
			model.sizeField !== undefined ||
			model.supportsAspectRatioField !== undefined);
	const aspectRatios = hasExplicitAspectRatios
		? (explicit.aspectRatios ?? [])
		: preset.aspectRatios?.length
			? preset.aspectRatios
			: usesExplicitCapability
				? []
				: DEFAULT_MODEL_CAPABILITY.aspectRatios;
	const resolutions = hasExplicitResolutions
		? (explicit.resolutions ?? [])
		: preset.resolutions?.length
			? preset.resolutions
			: DEFAULT_MODEL_CAPABILITY.resolutions;
	const imageCounts = explicit.imageCounts?.length
		? explicit.imageCounts
		: preset.imageCounts?.length
			? preset.imageCounts
			: DEFAULT_MODEL_CAPABILITY.imageCounts;
	const defaultAspectRatio = aspectRatios.includes(
		explicit.defaultAspectRatio ?? DEFAULT_IMAGE_ASPECT_RATIO
	)
		? (explicit.defaultAspectRatio ?? DEFAULT_IMAGE_ASPECT_RATIO)
		: aspectRatios.includes(preset.defaultAspectRatio ?? DEFAULT_IMAGE_ASPECT_RATIO)
			? (preset.defaultAspectRatio ?? DEFAULT_IMAGE_ASPECT_RATIO)
			: (aspectRatios[0] ?? DEFAULT_IMAGE_ASPECT_RATIO);
	const defaultResolution = resolutions.includes(explicit.defaultResolution ?? '')
		? explicit.defaultResolution
		: resolutions.includes(preset.defaultResolution ?? '')
			? preset.defaultResolution
			: resolutions[0];

	const aspectRatioSizes =
		explicit.aspectRatioSizes ??
		(!usesExplicitCapability ? preset.aspectRatioSizes : undefined) ??
		(!usesExplicitCapability ? DEFAULT_MODEL_CAPABILITY.aspectRatioSizes : {});

	const qualityOptions = explicit.qualityOptions ?? [];

	return {
		aspectRatios,
		resolutions,
		imageCounts,
		defaultAspectRatio,
		defaultResolution,
		sizeField: explicit.sizeField,
		supportsAspectRatioField: explicit.supportsAspectRatioField,
		aspectRatioSizes,
		qualityOptions,
		defaultQuality: explicit.defaultQuality
	};
};

export const getImageSizeForAspectRatio = (
	aspectRatio: unknown,
	model?: ImageGenerationModel | string | null
) => {
	const normalizedAspectRatio = normalizeAspectRatio(aspectRatio);
	return getImageModelCapability(model).aspectRatioSizes[normalizedAspectRatio];
};

export const normalizeImageGenerationModels = (items: unknown): ImageGenerationModel[] => {
	if (!Array.isArray(items)) {
		return [];
	}

	return items.flatMap((item) => {
		if (typeof item === 'string') {
			return [{ id: item }];
		}

		if (!item || typeof item !== 'object') {
			return [];
		}

		const model = item as Record<string, unknown>;
		const id =
			typeof model.id === 'string'
				? model.id
				: typeof model.model === 'string'
					? model.model
					: typeof model.name === 'string'
						? model.name
						: undefined;

		if (!id) {
			return [];
		}

		const aspectRatioKeys = ['aspectRatios', 'aspect_ratios', 'ratios'];
		const aspectRatioKey = aspectRatioKeys.find((key) => hasOwn(model, key));
		const resolutionKeys = ['resolutions', 'sizes', 'size_options'];
		const resolutionKey = resolutionKeys.find((key) => hasOwn(model, key));
		const aspectRatios = normalizeAspectRatioList(
			aspectRatioKey ? model[aspectRatioKey] : undefined
		);
		const resolutions = normalizeResolutionList(resolutionKey ? model[resolutionKey] : undefined);
		const imageCounts = normalizeNumberList(
			model.imageCounts ?? model.image_counts ?? model.counts
		);
		const maxImages = Number(model.maxImages ?? model.max_images ?? model.max_n);
		const defaultAspectRatio = normalizeAspectRatio(
			model.defaultAspectRatio ?? model.default_aspect_ratio
		);
		const defaultResolution = trimOptional(
			typeof model.defaultResolution === 'string'
				? model.defaultResolution
				: typeof model.default_resolution === 'string'
					? model.default_resolution
					: undefined
		);
		const task = trimOptional(typeof model.task === 'string' ? model.task : undefined);
		const provider = trimOptional(typeof model.provider === 'string' ? model.provider : undefined);
		const outputFormats = normalizeStringList(model.outputFormats ?? model.output_formats);
		const defaultOutputFormat = trimOptional(
			typeof model.defaultOutputFormat === 'string'
				? model.defaultOutputFormat
				: typeof model.default_output_format === 'string'
					? model.default_output_format
					: undefined
		);
		const generationModel = trimOptional(
			typeof model.generationModel === 'string'
				? model.generationModel
				: typeof model.generation_model === 'string'
					? model.generation_model
					: undefined
		);
		const editModel = trimOptional(
			typeof model.editModel === 'string'
				? model.editModel
				: typeof model.edit_model === 'string'
					? model.edit_model
					: undefined
		);
		const isDefault = model.isDefault === true || model.is_default === true;
		const sizeField = trimOptional(
			typeof model.sizeField === 'string'
				? model.sizeField
				: typeof model.custom_size_field === 'string'
					? model.custom_size_field
					: typeof model.resolution_field === 'string' && model.resolution_field === 'image_size'
						? model.resolution_field
						: undefined
		);
		const supportsAspectRatioField =
			typeof model.supportsAspectRatioField === 'boolean'
				? model.supportsAspectRatioField
				: typeof model.aspect_ratio_field === 'string' && model.aspect_ratio_field.length > 0;
		const aspectRatioSizes = normalizeAspectRatioSizeMap(
			model.aspectRatioSizes ?? model.aspect_ratio_sizes
		);
		const qualityOptions = normalizeStringList(model.qualityOptions ?? model.quality_options);
		const defaultQuality = trimOptional(
			typeof model.defaultQuality === 'string'
				? model.defaultQuality
				: typeof model.default_quality === 'string'
					? model.default_quality
					: undefined
		);

		return [
			{
				id,
				name: typeof model.name === 'string' ? model.name : undefined,
				...(provider && { provider }),
				...(task && { task }),
				...(generationModel && { generationModel }),
				...(editModel && { editModel }),
				...(isDefault && { isDefault: true }),
				...(aspectRatioKey !== undefined && { aspectRatios }),
				...(resolutionKey !== undefined && { resolutions }),
				...(imageCounts.length && { imageCounts }),
				...(Number.isInteger(maxImages) && maxImages > 0 && { maxImages }),
				...(defaultAspectRatio !== DEFAULT_IMAGE_ASPECT_RATIO && { defaultAspectRatio }),
				...(defaultResolution && { defaultResolution }),
				...(Object.keys(aspectRatioSizes).length && { aspectRatioSizes }),
				...(sizeField && { sizeField }),
				...(supportsAspectRatioField && { supportsAspectRatioField: true }),
				...(outputFormats.length && { outputFormats }),
				...(defaultOutputFormat && { defaultOutputFormat }),
				...(qualityOptions.length && { qualityOptions }),
				...(defaultQuality && { defaultQuality })
			}
		];
	});
};

export const validateImagePrompt = (prompt: string) => {
	const trimmedPrompt = prompt.trim();

	if (!trimmedPrompt) {
		return { ok: false as const, reason: 'empty_prompt' as const };
	}

	return { ok: true as const, prompt: trimmedPrompt };
};

export const canUseImagesPage = (config: any, user: any) => {
	return Boolean(
		config?.features?.enable_image_generation &&
		(user?.role === 'admin' || user?.permissions?.features?.image_generation)
	);
};

export const normalizeReferenceImages = (images: string[]) => {
	if (images.length === 0) {
		return undefined;
	}

	if (images.length === 1) {
		return images[0];
	}

	return [...images];
};

export const buildImageGenerationPayload = ({
	prompt,
	aspectRatio = DEFAULT_IMAGE_ASPECT_RATIO,
	model,
	size,
	resolution,
	quality,
	n,
	steps,
	negative_prompt
}: ImagePayloadInput): ImageGenerationPayload => {
	const payload: ImageGenerationPayload = {
		prompt: prompt.trim()
	};

	const trimmedModel = trimOptional(getModelId(model));
	const trimmedSize = trimOptional(size);
	const trimmedResolution = trimOptional(resolution);
	const capability = getImageModelCapability(model);
	const usesExplicitPayloadCapability =
		typeof model === 'object' &&
		model !== null &&
		(model.aspectRatios !== undefined ||
			model.resolutions !== undefined ||
			model.sizeField !== undefined ||
			model.supportsAspectRatioField !== undefined);
	const supportsAspectRatio = capability.aspectRatios.length > 0;
	const hasAspectRatioSizeMap = Object.keys(capability.aspectRatioSizes).length > 0;
	const outputSize =
		trimmedSize ??
		(supportsAspectRatio ? getImageSizeForAspectRatio(aspectRatio, model) : undefined);
	const trimmedNegativePrompt = trimOptional(negative_prompt);

	if (trimmedModel) {
		payload.model = trimmedModel;
	}
	if (
		outputSize &&
		(trimmedSize ||
			!usesExplicitPayloadCapability ||
			capability.sizeField === 'image_size' ||
			hasAspectRatioSizeMap)
	) {
		payload.size = outputSize;
	}
	if (
		supportsAspectRatio &&
		(!usesExplicitPayloadCapability ||
			capability.supportsAspectRatioField ||
			(!capability.sizeField && !hasAspectRatioSizeMap))
	) {
		payload.aspect_ratio = getApiAspectRatio(aspectRatio);
	}
	if (trimmedResolution) {
		payload.resolution = trimmedResolution;
	}
	const trimmedQuality = trimOptional(quality);
	if (trimmedQuality && capability.qualityOptions.includes(trimmedQuality)) {
		payload.quality = trimmedQuality;
	}
	payload.output_format = 'png';
	if (isPositiveInteger(n)) {
		payload.n = Number(n);
	}
	if (isPositiveInteger(steps)) {
		payload.steps = Number(steps);
	}
	if (trimmedNegativePrompt) {
		payload.negative_prompt = trimmedNegativePrompt;
	}

	return payload;
};

export const buildImageEditPayload = ({
	referenceImages,
	background,
	...input
}: ImageEditPayloadInput): ImageEditPayload => {
	const image = normalizeReferenceImages(referenceImages);

	if (!image) {
		throw new Error('At least one reference image is required');
	}

	const payload: ImageEditPayload = {
		...buildImageGenerationPayload(input),
		image
	};
	const trimmedBackground = trimOptional(background);

	if (trimmedBackground) {
		payload.background = trimmedBackground;
	}

	return payload;
};

export const removeReferenceImage = (images: string[], index: number) => {
	return images.filter((_, imageIndex) => imageIndex !== index);
};

export const filterImageFiles = (
	files: FileLike[],
	options: { maxCount?: number; maxBytes?: number } = {}
) => {
	const maxCount = options.maxCount ?? 4;
	const maxBytes = options.maxBytes ?? 10 * 1024 * 1024;
	const accepted: FileLike[] = [];
	const rejected: RejectedImageFile[] = [];

	for (const file of files) {
		if (!file.type?.startsWith('image/')) {
			rejected.push({ file, reason: 'unsupported_type' });
			continue;
		}

		if (file.size && file.size > maxBytes) {
			rejected.push({ file, reason: 'too_large' });
			continue;
		}

		if (accepted.length >= maxCount) {
			rejected.push({ file, reason: 'too_many' });
			continue;
		}

		accepted.push(file);
	}

	return { accepted, rejected };
};

export const normalizeImageResults = (result: unknown): GeneratedImage[] => {
	const items = Array.isArray(result)
		? result
		: Array.isArray((result as { data?: unknown[] })?.data)
			? (result as { data: unknown[] }).data
			: [];

	return items.flatMap((item) => {
		if (typeof item === 'string') {
			return [{ url: item }];
		}

		if (item && typeof item === 'object' && typeof (item as { url?: unknown }).url === 'string') {
			return [{ ...(item as Record<string, unknown>), url: (item as { url: string }).url }];
		}

		return [];
	});
};

export const prependGeneratedImages = (existing: GeneratedImage[], incoming: GeneratedImage[]) => {
	return [...incoming, ...existing];
};
