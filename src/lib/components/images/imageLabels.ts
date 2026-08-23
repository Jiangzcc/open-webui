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

// 图片任务失败态的 error_code → i18n key 映射（对齐 videoLabels 的
// videoTaskErrorI18nKey 模式）。复盘 #18：此前 ImageBatchCard 只翻译 3 个码，
// 其余（provider_failed 含模型禁用降级、insufficient_credits 等）会把裸码
// 直接显示给用户。
export const imageTaskErrorI18nKey: Record<string, string> = {
	image_generation_failed: 'Image generation failed',
	server_shutdown: 'Image generation was interrupted by a server restart',
	provider_failed: 'The image provider failed to process this request',
	insufficient_credits: 'Insufficient credits',
	price_not_configured: 'Image price is not configured',
	price_rule_incomplete: 'Image price is not configured',
	credit_service_unavailable: 'Credit service is unavailable',
	usage_processing: 'Your previous request is still processing',
	idempotency_key_conflict: 'The submission changed; please try again',
	credit_account_conflict: 'Credit account was updated concurrently; please retry',
	invalid_image_size: 'Image size is invalid',
	rate_limited: 'Too many image generation requests',
	generation_cancelled: 'Cancelled'
};
