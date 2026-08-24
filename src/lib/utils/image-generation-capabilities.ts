export type ImageAdvancedFieldName =
	| 'seed'
	| 'negative_prompt'
	| 'steps'
	| 'guidance_scale'
	| 'strength';

export type ImageAdvancedField = {
	field: ImageAdvancedFieldName;
	kind: 'integer' | 'number' | 'text';
	min?: number;
	max?: number;
};

export type CustomSizeConstraints = {
	minWidth?: number;
	maxWidth?: number;
	minHeight?: number;
	maxHeight?: number;
	multipleOf?: number;
	minPixels?: number;
	maxPixels?: number;
	aspectRatioMin?: number;
	aspectRatioMax?: number;
};

export type CustomSizeValidationError = {
	field: 'width' | 'height' | 'pixels' | 'aspect';
	message: string;
	messageParams?: Record<string, string | number>;
};

const isPositiveNumber = (value: unknown): value is number =>
	typeof value === 'number' && Number.isFinite(value) && value > 0;

export const normalizeCustomSizeConstraints = (
	value: unknown
): CustomSizeConstraints | undefined => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
	const source = value as Record<string, unknown>;
	const pick = (key: string, integer = true): number | undefined => {
		const candidate = source[key];
		if (!isPositiveNumber(candidate)) return undefined;
		return integer ? Math.floor(candidate) : candidate;
	};
	const result: CustomSizeConstraints = {
		minWidth: pick('min_width'),
		maxWidth: pick('max_width'),
		minHeight: pick('min_height'),
		maxHeight: pick('max_height'),
		multipleOf: pick('multiple_of'),
		minPixels: pick('min_pixels'),
		maxPixels: pick('max_pixels'),
		aspectRatioMin: pick('aspect_ratio_min', false),
		aspectRatioMax: pick('aspect_ratio_max', false)
	};
	const entries = Object.entries(result).filter(([, candidate]) => candidate !== undefined);
	return entries.length > 0 ? Object.fromEntries(entries) : undefined;
};

export const normalizePresetSizes = (value: unknown): string[] => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
	return Object.keys(value as Record<string, unknown>)
		.filter((key) => /^\d+x\d+$/.test(key))
		.sort((a, b) => {
			const [aw, ah] = a.split('x').map(Number);
			const [bw, bh] = b.split('x').map(Number);
			return aw * ah - bw * bh;
		});
};

const ADVANCED_FIELD_NAMES = new Set<ImageAdvancedFieldName>([
	'seed',
	'negative_prompt',
	'steps',
	'guidance_scale',
	'strength'
]);

export const normalizeAdvancedFields = (value: unknown): ImageAdvancedField[] => {
	if (!Array.isArray(value)) return [];
	const seen = new Set<ImageAdvancedFieldName>();
	return value.flatMap((item) => {
		if (!item || typeof item !== 'object' || Array.isArray(item)) return [];
		const source = item as Record<string, unknown>;
		const field = source.field as ImageAdvancedFieldName;
		const kind = String(source.kind);
		if (!ADVANCED_FIELD_NAMES.has(field) || !['integer', 'number', 'text'].includes(kind))
			return [];
		if (seen.has(field)) return [];
		const min =
			typeof source.min === 'number' && Number.isFinite(source.min) ? source.min : undefined;
		const max =
			typeof source.max === 'number' && Number.isFinite(source.max) ? source.max : undefined;
		if (min !== undefined && max !== undefined && min > max) return [];
		seen.add(field);
		return [{ field, kind: kind as ImageAdvancedField['kind'], min, max }];
	});
};

const dimensionError = (
	field: CustomSizeValidationError['field'],
	message: string,
	key?: string,
	value?: number
): CustomSizeValidationError => ({
	field,
	message,
	...(key && value !== undefined && { messageParams: { [key]: value } })
});

export const validateCustomSize = (
	width: number,
	height: number,
	constraints?: CustomSizeConstraints
): CustomSizeValidationError | null => {
	if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
		return dimensionError('width', 'Width and height must be positive integers');
	}
	if (!constraints) return null;
	if (constraints.minWidth !== undefined && width < constraints.minWidth)
		return dimensionError('width', 'Width must be at least {{min}}', 'min', constraints.minWidth);
	if (constraints.maxWidth !== undefined && width > constraints.maxWidth)
		return dimensionError('width', 'Width must be at most {{max}}', 'max', constraints.maxWidth);
	if (constraints.minHeight !== undefined && height < constraints.minHeight)
		return dimensionError(
			'height',
			'Height must be at least {{min}}',
			'min',
			constraints.minHeight
		);
	if (constraints.maxHeight !== undefined && height > constraints.maxHeight)
		return dimensionError('height', 'Height must be at most {{max}}', 'max', constraints.maxHeight);
	if (constraints.multipleOf && (width % constraints.multipleOf || height % constraints.multipleOf))
		return dimensionError(
			'width',
			'Dimensions must be a multiple of {{multipleOf}}',
			'multipleOf',
			constraints.multipleOf
		);
	const pixels = width * height;
	if (constraints.minPixels !== undefined && pixels < constraints.minPixels)
		return dimensionError(
			'pixels',
			'Total pixels must be at least {{min}}',
			'min',
			constraints.minPixels
		);
	if (constraints.maxPixels !== undefined && pixels > constraints.maxPixels)
		return dimensionError(
			'pixels',
			'Total pixels must be at most {{max}}',
			'max',
			constraints.maxPixels
		);
	if (constraints.aspectRatioMin !== undefined && width / height < constraints.aspectRatioMin)
		return dimensionError(
			'aspect',
			'Aspect ratio is below the minimum ({{min}})',
			'min',
			constraints.aspectRatioMin
		);
	if (constraints.aspectRatioMax !== undefined && width / height > constraints.aspectRatioMax)
		return dimensionError(
			'aspect',
			'Aspect ratio is above the maximum ({{max}})',
			'max',
			constraints.aspectRatioMax
		);
	return null;
};
