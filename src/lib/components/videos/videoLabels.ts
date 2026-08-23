// 视频创作页共享的 UI 文案映射：任务模式、素材角色、音频/高级参数选项。
// 由 Videos.svelte（表单区）与 VideoTaskCard.svelte（结果卡片）共同引用，
// 保证两处的参数标签与 pill 展示口径一致。

import type { VideoAdvancedFieldKey, VideoAssetRole, VideoTask } from '$lib/apis/videos';

// 上传素材在表单内的展示形态（blob URL 预览 + 文件库 id）。
export type UploadedVideoAsset = {
	id: string;
	name: string;
	url: string;
	mime_type: string;
};

export type VideoTaskOption = { id: VideoTask; label: string; hint: string };

export const videoTaskOptions: VideoTaskOption[] = [
	{ id: 'text-to-video', label: 'Text to Video', hint: 'Describe the motion and scene' },
	{ id: 'image-to-video', label: 'Image to Video', hint: 'Animate a start frame' },
	{ id: 'video-to-video', label: 'Video to Video', hint: 'Restyle or edit a clip' }
];

export const videoAssetLabels: Record<VideoAssetRole, string> = {
	start_image: 'Start image',
	end_image: 'End image',
	source_video: 'Source video',
	reference_image: 'Reference image',
	reference_video: 'Reference video',
	reference_audio: 'Reference audio'
};

export const videoAudioLabels: Record<string, string> = {
	silent: 'Silent',
	generate: 'Generate audio',
	upload: 'Use uploaded audio',
	preserve: 'Preserve audio',
	auto: 'Auto'
};

export const videoAdvancedFieldLabels: Record<VideoAdvancedFieldKey, string> = {
	seed: 'Seed',
	negative_prompt: 'Negative Prompt',
	prompt_enhancement: 'Prompt enhancement',
	motion_amplitude: 'Motion amplitude',
	guidance_scale: 'Prompt adherence',
	fps: 'Frame rate',
	output_quality: 'Output quality',
	loop: 'Loop video',
	edit_strength: 'Edit strength',
	retake_mode: 'Retake mode',
	start_time: 'Start time',
	ingredients_mode: 'Reference mode'
};

export const videoAdvancedFieldDescriptions: Partial<Record<VideoAdvancedFieldKey, string>> = {
	seed: 'Leave empty to use a random seed.',
	negative_prompt: 'Describe what should not appear in the video.',
	prompt_enhancement: 'The model may rewrite or expand your prompt.',
	motion_amplitude: 'Controls the overall amount of subject and scene motion.',
	guidance_scale: 'Higher values follow the prompt more closely.',
	fps: 'Higher frame rates look smoother and may create larger files.',
	output_quality: 'Higher quality may create a larger file.',
	edit_strength: 'Controls how closely the edit preserves the source video.',
	start_time: 'Where the retake begins in the source video.'
};

export const videoAdvancedOptionLabels: Record<string, string> = {
	auto: 'Auto',
	on: 'On',
	off: 'Off',
	small: 'Small',
	medium: 'Medium',
	large: 'Large',
	standard: 'Standard',
	high: 'High',
	precise: 'Precise',
	creative: 'Creative',
	replace_audio: 'Replace audio',
	replace_video: 'Replace video',
	replace_audio_and_video: 'Replace audio and video',
	adhere_1: 'Preserve · Low',
	adhere_2: 'Preserve · Medium',
	adhere_3: 'Preserve · High',
	flex_1: 'Balanced · Low',
	flex_2: 'Balanced · Medium',
	flex_3: 'Balanced · High',
	reimagine_1: 'Reimagine · Low',
	reimagine_2: 'Reimagine · Medium',
	reimagine_3: 'Reimagine · High'
};

// 后端 CreditError 的 code → i18n key 映射，使余额不足/限流/价格未配置等
// 竞态错误能显示具体提示而非通用「视频生成失败」。
// 同时包含 VideoInputError 的校验码（后端返回 {detail: 'invalid_duration'} 等，
// API 层 detail 优先于 code，因此这些码通过 error.message 查找）。
export const videoCreditErrorI18nKey: Record<string, string> = {
	insufficient_credits: 'Insufficient credits',
	price_not_configured: 'Video price is not configured',
	price_rule_incomplete: 'Video price is not configured',
	rate_limited: 'Too many video generation requests',
	unknown_video_model: 'Unknown video model',
	video_model_task_mismatch: 'Video model does not support this task type',
	prompt_required: 'Please enter a prompt',
	unsupported_duration: 'Unsupported duration',
	unsupported_aspect_ratio: 'Unsupported aspect ratio',
	unsupported_resolution: 'Unsupported resolution',
	unsupported_audio_mode: 'Unsupported audio mode',
	invalid_duration: 'Invalid duration',
	invalid_aspect_ratio: 'Invalid aspect ratio',
	invalid_resolution: 'Invalid resolution',
	invalid_audio_mode: 'Invalid audio mode',
	idempotency_key_conflict: 'The video submission changed; please try again',
	video_model_unavailable: 'This model is temporarily unavailable.',
	video_fal_not_configured: 'Real video generation is not configured',
	video_fal_model_not_allowed: 'This model is not allowed for real video generation',
	video_fal_cost_limit_exceeded: 'This video exceeds the per-request cost limit',
	video_mock_scenario_invalid: 'The mock video scenario is invalid'
};

// 任务失败态的 error_code → i18n key 映射（区分供应商失败与本地交付失败）。
export const videoTaskErrorI18nKey: Record<string, string> = {
	video_delivery_failed: 'The provider generated the video, but local delivery failed',
	video_provider_failed: 'The video provider failed to generate this video',
	video_provider_timeout: 'The video provider timed out',
	video_provider_rate_limited: 'The video provider rate limited this request',
	video_result_missing: 'The video provider returned no video',
	video_result_download_failed: 'The generated video could not be downloaded',
	video_result_too_large: 'The generated video is too large',
	video_result_invalid_type: 'The video provider returned an invalid file',
	server_shutdown: 'Video generation was interrupted by a server restart'
};
