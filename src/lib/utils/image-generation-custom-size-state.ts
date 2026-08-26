import type { ImageAspectRatio } from './image-generation-types';

export type ImageCustomSizeState = {
	enabled: boolean;
	aspectRatioLocked: boolean;
	width: number | null;
	height: number | null;
};

export type ImageCustomSizeAction =
	| { type: 'set-enabled'; enabled: boolean }
	| { type: 'set-dimension'; dimension: 'width' | 'height'; value: number | null }
	| { type: 'set-dimensions'; width: number; height: number }
	| { type: 'toggle-aspect-ratio-lock' }
	| { type: 'select-aspect-ratio' };

export type ImageCustomSizeContext = {
	aspectRatio: ImageAspectRatio;
	ratioSize?: string;
	fallbackSize?: string;
	multipleOf?: number;
};

export const createImageCustomSizeState = (): ImageCustomSizeState => ({
	enabled: false,
	aspectRatioLocked: true,
	width: null,
	height: null
});

const parseSize = (value?: string): [number, number] | null => {
	const match = /^(\d+)x(\d+)$/.exec(value ?? '');
	return match ? [Number(match[1]), Number(match[2])] : null;
};

const parseAspectRatio = (value: ImageAspectRatio): [number, number] | null => {
	const match = /^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/.exec(value);
	if (!match) return null;
	const ratio: [number, number] = [Number(match[1]), Number(match[2])];
	return ratio.every((part) => Number.isFinite(part) && part > 0) ? ratio : null;
};

const resolveRatio = (
	state: ImageCustomSizeState,
	context: ImageCustomSizeContext
): [number, number] | null =>
	parseAspectRatio(context.aspectRatio) ??
	parseSize(context.ratioSize) ??
	(state.width && state.height ? [state.width, state.height] : null);

const linkedDimension = (
	dimension: 'width' | 'height',
	value: number,
	state: ImageCustomSizeState,
	context: ImageCustomSizeContext
) => {
	if (!Number.isFinite(value) || value <= 0) return null;
	const ratio = resolveRatio(state, context);
	if (!ratio) return null;
	const raw = dimension === 'width' ? (value * ratio[1]) / ratio[0] : (value * ratio[0]) / ratio[1];
	const step = Math.max(1, Math.trunc(context.multipleOf ?? 1));
	return Math.max(step, Math.round(raw / step) * step);
};

const lockToCurrentRatio = (
	state: ImageCustomSizeState,
	context: ImageCustomSizeContext
): ImageCustomSizeState => {
	if (state.width !== null) {
		const height = linkedDimension('width', state.width, state, context);
		return height === null ? state : { ...state, height };
	}
	if (state.height !== null) {
		const width = linkedDimension('height', state.height, state, context);
		return width === null ? state : { ...state, width };
	}
	const baseline = parseSize(context.ratioSize) ?? parseSize(context.fallbackSize);
	return baseline ? { ...state, width: baseline[0], height: baseline[1] } : state;
};

const setDimension = (
	state: ImageCustomSizeState,
	action: Extract<ImageCustomSizeAction, { type: 'set-dimension' }>,
	context: ImageCustomSizeContext
): ImageCustomSizeState => {
	const next = { ...state, [action.dimension]: action.value };
	if (!state.enabled || !state.aspectRatioLocked || action.value === null) return next;
	const linked = linkedDimension(action.dimension, action.value, state, context);
	if (linked === null) return next;
	return action.dimension === 'width' ? { ...next, height: linked } : { ...next, width: linked };
};

export const updateImageCustomSizeState = (
	state: ImageCustomSizeState,
	action: ImageCustomSizeAction,
	context: ImageCustomSizeContext
): ImageCustomSizeState => {
	if (action.type === 'set-dimension') return setDimension(state, action, context);
	if (action.type === 'set-dimensions')
		return { ...state, width: action.width, height: action.height };
	if (action.type === 'set-enabled') {
		if (!action.enabled) return { ...state, enabled: false };
		return lockToCurrentRatio({ ...state, enabled: true, aspectRatioLocked: true }, context);
	}
	if (action.type === 'toggle-aspect-ratio-lock') {
		if (state.aspectRatioLocked) return { ...state, aspectRatioLocked: false };
		return lockToCurrentRatio({ ...state, aspectRatioLocked: true }, context);
	}
	if (!state.enabled || !state.aspectRatioLocked) return state;
	const baseline = parseSize(context.ratioSize);
	return baseline
		? { ...state, width: baseline[0], height: baseline[1] }
		: lockToCurrentRatio(state, context);
};
