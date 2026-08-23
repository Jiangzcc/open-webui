import type { VideoAdvancedField, VideoModel } from '$lib/apis/videos';

export type VideoAdvancedValidationError =
	| 'Enter a whole number'
	| 'Enter a number'
	| 'Minimum: {{value}}'
	| 'Maximum: {{value}}'
	| 'Value is not supported'
	| 'Text is too long';

const STANDARD_PARAM_KEYS = ['duration', 'aspect_ratio', 'resolution', 'audio_mode'] as const;

export const videoAdvancedFieldValue = (
	field: VideoAdvancedField,
	values: Record<string, unknown>
): string | number | boolean => {
	const value = values[field.key] ?? field.default ?? '';
	return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
		? value
		: '';
};

export const videoAdvancedFieldError = (
	field: VideoAdvancedField,
	raw: unknown
): { key: VideoAdvancedValidationError; value?: number } | null => {
	if (raw === null || raw === undefined || raw === '') return null;
	if (field.kind === 'option') {
		return typeof raw === 'string' && field.options?.includes(raw)
			? null
			: { key: 'Value is not supported' };
	}
	if (field.kind === 'boolean') {
		return typeof raw === 'boolean' ? null : { key: 'Value is not supported' };
	}
	if (field.kind === 'text') {
		return typeof raw !== 'string' ||
			(field.max_length !== undefined && raw.length > field.max_length)
			? { key: 'Text is too long' }
			: null;
	}
	const value = typeof raw === 'number' ? raw : Number(String(raw).trim());
	if (!Number.isFinite(value)) {
		return { key: field.kind === 'integer' ? 'Enter a whole number' : 'Enter a number' };
	}
	if (field.kind === 'integer' && !Number.isInteger(value)) {
		return { key: 'Enter a whole number' };
	}
	if (field.min !== null && field.min !== undefined && value < field.min) {
		return { key: 'Minimum: {{value}}', value: field.min };
	}
	if (field.max !== null && field.max !== undefined && value > field.max) {
		return { key: 'Maximum: {{value}}', value: field.max };
	}
	return null;
};

const normalizedAdvancedValue = (
	field: VideoAdvancedField,
	raw: unknown
): string | number | boolean | null => {
	if (raw === null || raw === undefined || raw === '') return null;
	if (field.kind === 'integer' || field.kind === 'number') return Number(String(raw).trim());
	if (field.kind === 'text') return String(raw).trim() || null;
	return raw as string | boolean;
};

export const normalizeVideoParamsForModel = (
	model: VideoModel,
	values: Record<string, unknown>
): Record<string, string | number | boolean | null> => {
	const normalized: Record<string, string | number | boolean | null> = {};
	for (const key of STANDARD_PARAM_KEYS) {
		const value = values[key];
		if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
			normalized[key] = value;
		}
	}
	for (const field of model.advanced_fields ?? []) {
		const raw = values[field.key] ?? field.default;
		if (videoAdvancedFieldError(field, raw)) continue;
		const value = normalizedAdvancedValue(field, raw);
		if (value !== null) normalized[field.key] = value;
	}
	return normalized;
};

export const firstVideoAdvancedError = (
	model: VideoModel | null,
	values: Record<string, unknown>
): {
	field: VideoAdvancedField;
	error: { key: VideoAdvancedValidationError; value?: number };
} | null => {
	for (const field of model?.advanced_fields ?? []) {
		const error = videoAdvancedFieldError(field, values[field.key] ?? field.default);
		if (error) return { field, error };
	}
	return null;
};

// 时长候选：优先显式 durations 列表；否则按 min/max/step 枚举。步进除以 2 的
// 容差用于吸收浮点步进累积误差（如 0.1 步进 10 次后略超 max）。
export const videoDurationChoices = (model: VideoModel | null): string[] => {
	if (model?.durations?.length) return model.durations;
	if (model?.duration_min === null || model?.duration_min === undefined) return [];
	if (model.duration_max === null || model.duration_max === undefined) return [];
	const step = model.duration_step ?? 1;
	const values: string[] = [];
	for (let value = model.duration_min; value <= model.duration_max + step / 2; value += step) {
		values.push(String(Number(value.toFixed(3))));
	}
	return values;
};
