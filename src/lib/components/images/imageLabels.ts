// 图片创作页共享的「值 → i18n key」映射：调用方用 $i18n.t(key) 渲染。
// 未匹配的原始值（如 '16:9'、'2k'）原样返回，i18next 无匹配时会显示原值。

import { DEFAULT_IMAGE_ASPECT_RATIO, type ImageAspectRatio } from '$lib/utils/image-generation';

export const imageAspectRatioLabelKey = (ratio: ImageAspectRatio): string =>
	ratio === DEFAULT_IMAGE_ASPECT_RATIO ? 'Auto' : ratio;

// 比例标签（"4:3" 等）是技术值，不得再经 i18next 翻译：i18next 的
// nsSeparator（":"）会把 "4:3" 拆成 ns "4" + key "3"，miss 后只返回 "3"。
export const imageAspectRatioLabel = (ratio: ImageAspectRatio): string =>
	ratio === DEFAULT_IMAGE_ASPECT_RATIO ? 'Auto' : ratio;

export const imageResolutionLabelKey = (resolution: string): string =>
	resolution === 'auto' ? 'Auto' : resolution;

export const imageQualityLabelKey = (quality: string): string => {
	switch (quality) {
		case 'auto':
			return 'Auto';
		case 'low':
			return 'Low';
		case 'medium':
			return 'Medium';
		case 'high':
			return 'High';
		default:
			return quality;
	}
};
