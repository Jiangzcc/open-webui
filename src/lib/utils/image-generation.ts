import {
	normalizeAdvancedFields,
	normalizeCustomSizeConstraints,
	normalizePresetSizes
} from './image-generation-capabilities';
import {
	DEFAULT_IMAGE_ASPECT_RATIO,
	DEFAULT_IMAGE_COUNT_OPTIONS,
	IMAGE_ASPECT_RATIO_OPTIONS,
	type FileLike,
	type GeneratedImage,
	type ImageAspectRatio,
	type ImageEditPayload,
	type ImageEditPayloadInput,
	type ImageGenerationModel,
	type ImageGenerationPayload,
	type ImageModelCapability,
	type ImagePayloadInput,
	type RejectedImageFile
} from './image-generation-types';
import {
	DALL_E_3_ASPECT_RATIO_SIZES,
	DEFAULT_IMAGE_ASPECT_RATIO_SIZES,
	DEFAULT_MODEL_CAPABILITY,
	GPT_IMAGE_ASPECT_RATIO_SIZES
} from './image-generation-presets';

export {
	validateCustomSize,
	type CustomSizeConstraints,
	type CustomSizeValidationError,
	type ImageAdvancedField,
	type ImageAdvancedFieldName
} from './image-generation-capabilities';

export {
	DEFAULT_IMAGE_ASPECT_RATIO,
	DEFAULT_IMAGE_COUNT_OPTIONS,
	IMAGE_ASPECT_RATIO_OPTIONS,
	type GeneratedImage,
	type ImageAspectRatio,
	type ImageEditPayload,
	type ImageGenerationModel,
	type ImageGenerationPayload,
	type ImageModelCapability
} from './image-generation-types';

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
		outputFormats: model.outputFormats,
		defaultOutputFormat: model.defaultOutputFormat,
		qualityOptions: model.qualityOptions,
		defaultQuality: model.defaultQuality,
		customSize: model.customSize,
		presetSizes: model.presetSizes ?? [],
		advancedFields: model.advancedFields ?? []
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

	const outputFormats = explicit.outputFormats?.length
		? explicit.outputFormats
		: preset.outputFormats?.length
			? preset.outputFormats
			: [];
	const defaultOutputFormat =
		(outputFormats.length > 0 && explicit.defaultOutputFormat) ||
		(outputFormats.length > 0 && preset.defaultOutputFormat) ||
		undefined;

	const customSize = explicit.customSize;
	const presetSizes = explicit.presetSizes ?? [];
	const advancedFields = explicit.advancedFields ?? [];

	return {
		aspectRatios,
		resolutions,
		imageCounts,
		defaultAspectRatio,
		defaultResolution,
		sizeField: explicit.sizeField,
		supportsAspectRatioField: explicit.supportsAspectRatioField,
		aspectRatioSizes,
		outputFormats,
		defaultOutputFormat,
		customSize,
		presetSizes,
		qualityOptions,
		defaultQuality: explicit.defaultQuality,
		advancedFields
	};
};

export const getImageSizeForAspectRatio = (
	aspectRatio: unknown,
	model?: ImageGenerationModel | string | null
) => {
	const normalizedAspectRatio = normalizeAspectRatio(aspectRatio);
	return getImageModelCapability(model).aspectRatioSizes[normalizedAspectRatio];
};

/**
 * Mode a generation request targets: plain text-to-image, or image-to-image
 * editing driven by one or more reference images.
 */
export type ImageGenerationMode = 'text-to-image' | 'image-to-image';

/**
 * Whether a model is eligible for selection under the given generation mode.
 *
 * Strict-by-task policy: text-to-image mode lights up everything that is not
 * an image-to-image sibling, and vice-versa. A model carrying the opposite
 * relation (e.g. a t2i model advertising `editModel`) is intentionally dimmed
 * in the foreign mode to steer users toward the dedicated sibling entry, even
 * though the backend could technically fulfill the request via flipping.
 * Models without an explicit `task` are treated as compatible with both modes
 * so legacy/third-party entries are not penalised.
 */
export const getPrimaryImageModels = (models: ImageGenerationModel[]): ImageGenerationModel[] =>
	models.filter((model) => model.task !== 'image-to-image');

export const resolveImageEditModel = (
	primaryModel: ImageGenerationModel | null | undefined,
	models: ImageGenerationModel[]
): ImageGenerationModel | null => {
	if (!primaryModel?.editModel) {
		return null;
	}

	return models.find((model) => model.id === primaryModel.editModel) ?? null;
};

export const supportsImageEditing = (
	primaryModel: ImageGenerationModel | null | undefined,
	models: ImageGenerationModel[]
): boolean => resolveImageEditModel(primaryModel, models) !== null;

export const resolveActiveImageModel = (
	primaryModel: ImageGenerationModel | null | undefined,
	models: ImageGenerationModel[],
	hasReferenceImages: boolean
): ImageGenerationModel | null => {
	if (!primaryModel) {
		return null;
	}

	return hasReferenceImages
		? (resolveImageEditModel(primaryModel, models) ?? primaryModel)
		: primaryModel;
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
		const imageInputMaxCountRaw = Number(model.imageInputMaxCount ?? model.image_input_max_count);
		const imageInputMaxCount = isPositiveInteger(imageInputMaxCountRaw)
			? imageInputMaxCountRaw
			: undefined;
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
		const basePrice = trimOptional(
			typeof model.basePrice === 'string'
				? model.basePrice
				: typeof model.base_price === 'string'
					? model.base_price
					: undefined
		);
		const editBasePrice = trimOptional(
			typeof model.editBasePrice === 'string'
				? model.editBasePrice
				: typeof model.edit_base_price === 'string'
					? model.edit_base_price
					: undefined
		);
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
		const customSize = normalizeCustomSizeConstraints(model.customSize ?? model.custom_size);
		const advancedFields = normalizeAdvancedFields(model.advancedFields ?? model.advanced_fields);
		// Preset chips for the custom-size input come from the model's curated
		// image_size_whitelist keys (already WxH strings).
		const rawPresets = model.image_size_whitelist ?? model.imageSizeWhitelist;
		const presetSizes = normalizePresetSizes(rawPresets);
		const qualityOptions = normalizeStringList(model.qualityOptions ?? model.quality_options);
		const defaultQuality = trimOptional(
			typeof model.defaultQuality === 'string'
				? model.defaultQuality
				: typeof model.default_quality === 'string'
					? model.default_quality
					: undefined
		);
		const hasEnabled = hasOwn(model, 'enabled');
		const hasVisible = hasOwn(model, 'visible');
		const enabled = model.enabled !== false;
		const visible = model.visible !== false;
		const recommended = model.recommended === true;
		const sortOrderValue = Number(model.sortOrder ?? model.sort_order);
		const tags = normalizeStringList(model.tags);
		const maintenanceMessage = trimOptional(
			typeof model.maintenanceMessage === 'string'
				? model.maintenanceMessage
				: typeof model.maintenance_message === 'string'
					? model.maintenance_message
					: undefined
		);

		const publicId = trimOptional(
			typeof model.publicId === 'string'
				? model.publicId
				: typeof model.public_id === 'string'
					? model.public_id
					: undefined
		);

		return [
			{
				id,
				...(publicId && { publicId }),
				name: typeof model.name === 'string' ? model.name : undefined,
				...(provider && { provider }),
				...(task && { task }),
				...(basePrice && { basePrice }),
				...(editBasePrice && { editBasePrice }),
				...(hasVisible && { visible }),
				...(hasEnabled && { enabled }),
				...(recommended && { recommended: true }),
				...(Number.isInteger(sortOrderValue) &&
					sortOrderValue >= 0 && {
						sortOrder: sortOrderValue
					}),
				...(tags.length && { tags }),
				...(maintenanceMessage && { maintenanceMessage }),
				...(generationModel && { generationModel }),
				...(editModel && { editModel }),
				...(isDefault && { isDefault: true }),
				...(aspectRatioKey !== undefined && { aspectRatios }),
				...(resolutionKey !== undefined && { resolutions }),
				...(imageCounts.length && { imageCounts }),
				...(Number.isInteger(maxImages) && maxImages > 0 && { maxImages }),
				...(imageInputMaxCount && { imageInputMaxCount }),
				...(defaultAspectRatio !== DEFAULT_IMAGE_ASPECT_RATIO && { defaultAspectRatio }),
				...(defaultResolution && { defaultResolution }),
				...(Object.keys(aspectRatioSizes).length && { aspectRatioSizes }),
				...(sizeField && { sizeField }),
				...(supportsAspectRatioField && { supportsAspectRatioField: true }),
				...(outputFormats.length && { outputFormats }),
				...(defaultOutputFormat && { defaultOutputFormat }),
				...(qualityOptions.length && { qualityOptions }),
				...(defaultQuality && { defaultQuality }),
				...(customSize && { customSize }),
				...(presetSizes.length && { presetSizes }),
				...(advancedFields.length && { advancedFields })
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

export const buildImageGenerationPayload = ({
	prompt,
	aspectRatio = DEFAULT_IMAGE_ASPECT_RATIO,
	model,
	size,
	resolution,
	quality,
	n,
	steps,
	negative_prompt,
	output_format,
	seed,
	guidance_scale,
	strength
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
	// 分辨率档位模型（目录声明 resolutions 且带比例尺寸表，如 seedream 的 1K/2K/4K）：
	// 比例基线 size 不随请求下发，档位 × 基线的合成由后端统一完成（校验/计价同源），
	// 否则派生基线会抢占档位语义（复盘 P0-2：UI 选 4K 实际生成 1K 的根因）。
	const usesResolutionSelector =
		usesExplicitPayloadCapability && capability.resolutions.length > 0 && hasAspectRatioSizeMap;
	const outputSize =
		trimmedSize ??
		(supportsAspectRatio && !usesResolutionSelector
			? getImageSizeForAspectRatio(aspectRatio, model)
			: undefined);
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
		(usesResolutionSelector ||
			!usesExplicitPayloadCapability ||
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
	// 只在模型声明了可选输出格式时才写入，默认值取模型声明的 defaultOutputFormat，
	// 没有声明时回退 png（fal 后端亦以 png 为兜底）。避免对无 output_formats 能力的
	// 模型强写一个它不接受或非首选的格式。
	if (capability.outputFormats.length > 0) {
		const requestedOutputFormat = trimOptional(output_format);
		payload.output_format =
			(requestedOutputFormat && capability.outputFormats.includes(requestedOutputFormat)
				? requestedOutputFormat
				: trimOptional(capability.defaultOutputFormat)) ?? 'png';
	}
	if (isPositiveInteger(n)) {
		payload.n = Number(n);
	}
	if (isPositiveInteger(steps)) {
		payload.steps = Number(steps);
	}
	if (trimmedNegativePrompt) {
		payload.negative_prompt = trimmedNegativePrompt;
	}
	if (Number.isInteger(seed)) {
		payload.seed = Number(seed);
	}
	if (typeof guidance_scale === 'number' && Number.isFinite(guidance_scale)) {
		payload.guidance_scale = guidance_scale;
	}
	if (typeof strength === 'number' && Number.isFinite(strength)) {
		payload.strength = strength;
	}

	return payload;
};

const normalizeReferenceImages = (images: string[]) => {
	if (images.length === 0) {
		return undefined;
	}

	if (images.length === 1) {
		return images[0];
	}

	return [...images];
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
