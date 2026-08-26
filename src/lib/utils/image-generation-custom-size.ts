import type { CustomSizeConstraints } from './image-generation-capabilities';
import { DEFAULT_IMAGE_ASPECT_RATIO, type ImageAspectRatio } from './image-generation-types';

/**
 * custom_size 模型的默认比例与基线尺寸合成。
 *
 * 目录里这类模型只声明了宽高/像素约束（custom_size），没有任何比例或档位配置，
 * UI 因此只剩"自定义尺寸"输入框。这里基于约束合成一组默认比例，并为每个比例
 * 求解一个落在约束内的基线尺寸（WxH），走现有 aspectRatioSizes → payload.size
 * 链路下发（sizeField=image_size 直接生效），后端 validate_fal_image_size
 * 按同一份约束校验，不会出现 UI 可选但后端拒绝的尺寸。
 */

export type CustomSizeDefaults = {
	aspectRatios: ImageAspectRatio[];
	aspectRatioSizes: Partial<Record<ImageAspectRatio, string>>;
};

/** 无像素约束时的默认目标像素量（1024x1024，与 fal 常规基线一致）。 */
const DEFAULT_TARGET_PIXELS = 1024 * 1024;
/** 目录未声明 multiple_of 时的尺寸取整粒度。 */
const ALIGN_STEP = 16;
/** 目录未声明比例时注入的默认比例集。 */
const DEFAULT_CUSTOM_SIZE_RATIOS: readonly ImageAspectRatio[] = [
	'1:1',
	'4:3',
	'3:4',
	'16:9',
	'9:16'
];

const roundToStep = (value: number, step: number) => Math.round(value / step) * step;

const parseRatio = (ratio: ImageAspectRatio): [number, number] | null => {
	const match = /^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/.exec(ratio);
	if (!match) {
		return null;
	}
	const widthRatio = Number(match[1]);
	const heightRatio = Number(match[2]);
	return widthRatio > 0 && heightRatio > 0 ? [widthRatio, heightRatio] : null;
};

/** 目标像素量：两端都约束取几何均值，只约束一端向 1M 默认值收拢，都不约束用默认值。 */
const resolveTargetPixels = (constraints: CustomSizeConstraints) => {
	if (constraints.minPixels && constraints.maxPixels) {
		return Math.round(Math.sqrt(constraints.minPixels * constraints.maxPixels));
	}
	if (constraints.maxPixels) {
		return Math.min(constraints.maxPixels, DEFAULT_TARGET_PIXELS);
	}
	if (constraints.minPixels) {
		return Math.max(constraints.minPixels, DEFAULT_TARGET_PIXELS);
	}
	return DEFAULT_TARGET_PIXELS;
};

/**
 * 在约束内为给定比例求一个尽量接近目标像素量的尺寸。
 *
 * 把所有约束换算成"宽度可行区间"后取最接近理想值的点，再取整到粒度；
 * 任一约束无法满足（区间为空或取整后越界）即视为该比例不可行。
 */
const solveSizeForRatio = (
	[widthRatio, heightRatio]: [number, number],
	constraints: CustomSizeConstraints
): string | null => {
	const aspect = widthRatio / heightRatio;
	if (
		(constraints.aspectRatioMin !== undefined && aspect < constraints.aspectRatioMin) ||
		(constraints.aspectRatioMax !== undefined && aspect > constraints.aspectRatioMax)
	) {
		return null;
	}

	const step = Math.max(1, constraints.multipleOf ?? ALIGN_STEP);
	const target = resolveTargetPixels(constraints);
	const lowerBound = Math.max(
		constraints.minWidth ?? 0,
		(constraints.minHeight ?? 0) * aspect,
		constraints.minPixels ? Math.sqrt(constraints.minPixels * aspect) : 0
	);
	const upperBound = Math.min(
		constraints.maxWidth ?? Number.POSITIVE_INFINITY,
		(constraints.maxHeight ?? Number.POSITIVE_INFINITY) * aspect,
		constraints.maxPixels ? Math.sqrt(constraints.maxPixels * aspect) : Number.POSITIVE_INFINITY
	);
	if (lowerBound > upperBound) {
		return null;
	}

	const idealWidth = Math.min(Math.max(Math.sqrt(target * aspect), lowerBound), upperBound);
	let width = roundToStep(idealWidth, step);
	if (width > upperBound) {
		width = Math.floor(upperBound / step) * step;
	}
	if (width < lowerBound) {
		return null;
	}

	const height = roundToStep((width * heightRatio) / widthRatio, step);
	const pixels = width * height;
	const violates =
		width < 1 ||
		height < 1 ||
		(constraints.minWidth !== undefined && width < constraints.minWidth) ||
		(constraints.maxWidth !== undefined && width > constraints.maxWidth) ||
		(constraints.minHeight !== undefined && height < constraints.minHeight) ||
		(constraints.maxHeight !== undefined && height > constraints.maxHeight) ||
		(constraints.minPixels !== undefined && pixels < constraints.minPixels) ||
		(constraints.maxPixels !== undefined && pixels > constraints.maxPixels);
	if (violates) {
		return null;
	}
	return `${width}x${height}`;
};

/**
 * 为 custom_size 模型合成默认比例与基线尺寸。
 *
 * preferredRatios 为目录已声明的比例（如 gpt-image-2）；声明了比例的模型保留
 * 原列表（'auto' 保留但不合成尺寸，交由模型端自行决定），未声明的模型使用
 * 默认比例集并剔除在约束下无解的比例。
 */
export const synthesizeCustomSizeDefaults = (
	constraints: CustomSizeConstraints,
	preferredRatios?: readonly ImageAspectRatio[]
): CustomSizeDefaults | undefined => {
	const hasDeclaredRatios = Boolean(preferredRatios && preferredRatios.length > 0);
	const ratios = hasDeclaredRatios ? preferredRatios! : DEFAULT_CUSTOM_SIZE_RATIOS;
	const aspectRatios: ImageAspectRatio[] = [];
	const aspectRatioSizes: Partial<Record<ImageAspectRatio, string>> = {};
	for (const ratio of ratios) {
		if (ratio === DEFAULT_IMAGE_ASPECT_RATIO) {
			aspectRatios.push(ratio);
			continue;
		}
		const parsed = parseRatio(ratio);
		const size = parsed ? solveSizeForRatio(parsed, constraints) : null;
		// 声明了比例的模型保留原列表（个别比例无解就没有基线尺寸，行为与目录一致）；
		// 默认比例集只保留能求出合法尺寸的比例，避免出现选了却不生效的按钮。
		if (size || hasDeclaredRatios) {
			aspectRatios.push(ratio);
			if (size) {
				aspectRatioSizes[ratio] = size;
			}
		}
	}
	if (aspectRatios.length === 0) {
		return undefined;
	}
	return { aspectRatios, aspectRatioSizes };
};
