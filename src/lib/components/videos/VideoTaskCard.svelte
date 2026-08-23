<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import VendorLogo from '$lib/components/common/VendorLogo.svelte';
	import { stripVendorFromName } from '$lib/utils/images-dropdown';
	import type { VideoGenerationTask, VideoModel, VideoTask } from '$lib/apis/videos';
	import {
		videoAdvancedOptionLabels,
		videoAssetLabels,
		videoAudioLabels,
		videoTaskErrorI18nKey
	} from './videoLabels';

	const i18n = getContext<Writable<I18n>>('i18n');

	export let record: VideoGenerationTask;
	export let model: VideoModel | null;
	export let downloading = false;
	export let deleting = false;
	export let onRegenerate: (record: VideoGenerationTask) => void = () => {};
	export let onDownload: (record: VideoGenerationTask) => void = () => {};
	export let onViewDetails: (record: VideoGenerationTask) => void = () => {};
	export let onRemove: (record: VideoGenerationTask) => void = () => {};

	// 视频任务文案：复用图片结果区的状态标签口径，保持一致。
	const videoTaskErrorMessage = (task: VideoGenerationTask) =>
		$i18n.t(videoTaskErrorI18nKey[task.error_code ?? ''] ?? 'Generation failed');

	const videoTaskStatusLabel = (task: VideoGenerationTask) => {
		if (task.status === 'queued') return $i18n.t('Queued');
		if (task.status === 'running') return $i18n.t('Generating');
		if (task.status === 'failed') return videoTaskErrorMessage(task);
		return $i18n.t('Completed');
	};

	// 模型短名：剥厂商前缀，回退到「默认模型」。
	const getTaskModelLabel = (task: VideoGenerationTask) =>
		model ? stripVendorFromName(model) : $i18n.t('Default Model');

	// 关键参数 pill 行：模型 · 任务 · 时长 · 比例 · 分辨率 · 音频；与图片结果区口径一致。
	const getTaskMetaPills = (task: VideoGenerationTask) => {
		const pills: string[] = [getTaskModelLabel(task)];
		// 任务类型中文名
		const taskLabelMap: Record<VideoTask, string> = {
			'text-to-video': $i18n.t('Text to Video'),
			'image-to-video': $i18n.t('Image to Video'),
			'video-to-video': $i18n.t('Video to Video')
		};
		pills.push(taskLabelMap[task.task]);
		const durationStr = task.params?.duration;
		if (durationStr !== undefined && durationStr !== null && durationStr !== '') {
			pills.push(
				durationStr === 'auto'
					? $i18n.t('Auto')
					: durationStr === '0'
						? $i18n.t('Match source duration')
						: `${durationStr}s`
			);
		}
		if (task.params?.aspect_ratio) pills.push(String(task.params.aspect_ratio));
		if (task.params?.resolution) pills.push(String(task.params.resolution));
		if (task.params?.audio_mode) {
			pills.push(
				$i18n.t(videoAudioLabels[String(task.params.audio_mode)] ?? String(task.params.audio_mode))
			);
		}
		if (task.params?.fps) pills.push(`${task.params.fps} FPS`);
		if (task.params?.output_quality) {
			pills.push(
				$i18n.t(
					videoAdvancedOptionLabels[String(task.params.output_quality)] ??
						String(task.params.output_quality)
				)
			);
		}
		if (task.params?.motion_amplitude) {
			pills.push(
				`${$i18n.t('Motion amplitude')}: ${$i18n.t(videoAdvancedOptionLabels[String(task.params.motion_amplitude)] ?? String(task.params.motion_amplitude))}`
			);
		}
		if (task.params?.guidance_scale !== null && task.params?.guidance_scale !== undefined) {
			pills.push(`${$i18n.t('Prompt adherence')}: ${task.params.guidance_scale}`);
		}
		if (task.params?.seed !== null && task.params?.seed !== undefined) {
			pills.push(`${$i18n.t('Seed')}: ${task.params.seed}`);
		}
		if (task.params?.loop === true) pills.push($i18n.t('Loop video'));
		return pills;
	};

	// 时间：优先 completed_at，其次 started_at，回退 created_at（秒级时间戳）。
	// 与图片结果区 formatBatchTime 口径一致：今天只显示 HH:MM；今年其它天补 M/D；跨年带年份。
	const formatTaskTime = (ts: number | null) => {
		if (!ts) return '';
		const date = new Date(ts * 1000);
		if (Number.isNaN(date.getTime())) return '';
		const now = new Date();
		const hh = String(date.getHours()).padStart(2, '0');
		const mm = String(date.getMinutes()).padStart(2, '0');
		const time = `${hh}:${mm}`;
		const sameDay =
			date.getFullYear() === now.getFullYear() &&
			date.getMonth() === now.getMonth() &&
			date.getDate() === now.getDate();
		if (sameDay) return time;
		const md = `${date.getMonth() + 1}/${date.getDate()}`;
		if (date.getFullYear() === now.getFullYear()) return `${md} ${time}`;
		return `${date.getFullYear()}/${md} ${time}`;
	};
	const getTaskTime = (task: VideoGenerationTask) =>
		formatTaskTime(task.completed_at ?? task.started_at ?? task.created_at);

	// 视频结果卡片样式：与图片结果区 BATCH_ARTICLE_CLASS 同构，保持视觉统一。
	// 任务列表流式布局，卡片自然高度；播放器在卡片内靠左、固定 16:9 宽度。
	const VIDEO_TASK_ARTICLE_CLASS =
		'rounded-2xl bg-gray-50/60 p-3 dark:bg-gray-900/30 sm:p-4 mx-auto w-full max-w-5xl flex flex-col gap-3';
</script>

<article id={`video-task-${record.id}`} class={VIDEO_TASK_ARTICLE_CLASS}>
	<!-- 消息头：厂商图标 + 模型短名 + 时间 -->
	<div class="flex items-center gap-2">
		{#if model?.provider}
			<VendorLogo provider={model.provider} className="size-5 shrink-0 rounded-full object-cover" />
		{:else}
			<span
				class="size-5 shrink-0 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-600 dark:to-gray-700"
			></span>
		{/if}
		<span class="min-w-0 truncate text-sm font-medium text-gray-800 dark:text-gray-100"
			>{getTaskModelLabel(record)}</span
		>
		<span class="ml-auto shrink-0 text-[11px] text-gray-400 dark:text-gray-500">{getTaskTime(record)}</span>
	</div>

	<!-- prompt：全展开，不折叠；就是用户输入的纯文本 -->
	{#if record.prompt}
		<p class="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 dark:text-gray-200">
			{record.prompt}
		</p>
	{/if}

	<!-- pill 参数行：模型 · 任务 · 时长 · 比例 · 分辨率 · 音频 -->
	<div class="flex flex-wrap items-center gap-1.5">
		{#each getTaskMetaPills(record) as pill, index (`${index}-${pill}`)}
			<span
				class="inline-flex min-h-6 items-center rounded-md bg-gray-100 px-2 text-[11px] text-gray-500 dark:bg-gray-800 dark:text-gray-400"
				>{pill}</span
			>
		{/each}
		{#if record.status === 'queued' || record.status === 'running'}
			<span
				class="inline-flex min-h-6 items-center gap-1 rounded-md bg-amber-50 px-2 text-[11px] text-amber-600 dark:bg-amber-950/40 dark:text-amber-400"
			>
				<Spinner className="size-3" />
				{videoTaskStatusLabel(record)}
			</span>
		{/if}
	</div>

	{#if record.result}
		<!-- 结果区：固定 16:9 宽度的播放器盒子，靠左对齐；视频 object-contain。
		     盒子尺寸与 poster/video 内在比例解耦，消除 poster→播放的高度跳变；
		     横屏/竖屏视频共用同一播放器宽度，竖屏视频自动 letterbox。 -->
		<div class="flex w-full justify-start overflow-hidden">
			<div class="relative aspect-video w-full max-w-[36rem]">
				<video
					class="absolute inset-0 h-full w-full rounded-2xl object-contain shadow-sm dark:shadow-black/40"
					controls
					playsinline
					preload="metadata"
					poster={record.result.poster_url}
					src={record.result.url}
				></video>
			</div>
		</div>
	{:else if record.status === 'queued' || record.status === 'running'}
		<!-- 生成中：占位骨架 + 提示（对齐图片页 animate-pulse 骨架风格） -->
		<div class="flex w-full justify-start overflow-hidden">
			<div
				class="relative flex aspect-video w-full max-w-[36rem] flex-col items-center justify-center overflow-hidden rounded-lg border border-dashed border-gray-200 bg-gray-50 px-4 py-8 text-center dark:border-gray-700 dark:bg-gray-900 sm:px-5 sm:py-10"
			>
				<!-- 骨架 shimmer 覆盖层，与 Images.svelte 生成中占位一致 -->
				<div
					class="absolute inset-0 animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.02]"
				></div>
				<div class="relative flex flex-col items-center gap-3">
					<Spinner className="size-6" />
					<p class="text-sm font-medium text-gray-600 dark:text-gray-300">
						{$i18n.t('Creating your video')}
					</p>
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('The result will appear here shortly')}
					</p>
				</div>
			</div>
		</div>
	{:else if record.status === 'failed'}
		<div class="flex w-full justify-start overflow-hidden">
			<div
				class="flex aspect-video w-full max-w-[36rem] flex-col items-center justify-center rounded-lg border border-dashed border-red-200 bg-red-50/40 px-4 py-5 text-center dark:border-red-900/60 dark:bg-red-950/20 sm:px-5 sm:py-6"
			>
				<p class="text-sm font-medium text-red-600 dark:text-red-300">
					{videoTaskStatusLabel(record)}
				</p>
			</div>
		</div>
	{/if}

	<!-- 操作行：再次生成 · 下载 · 查看详情 · 移除，紧凑次级按钮，触屏常驻可见 -->
	<div class="flex flex-wrap items-center gap-1.5">
		<button
			type="button"
			class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40 sm:min-h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
			on:click={() => onRegenerate(record)}
			aria-label={$i18n.t('Regenerate')}
		>
			<svg
				class="size-3.5"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5" /></svg
			>
			{$i18n.t('Regenerate')}
		</button>
		<button
			type="button"
			class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 sm:min-h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
			on:click={() => onDownload(record)}
			disabled={downloading}
			aria-label={$i18n.t('Download')}
		>
			{#if downloading}
				<Spinner className="size-3.5" />
			{:else}
				<svg
					class="size-3.5"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" /></svg
				>
			{/if}
			{$i18n.t('Download')}
		</button>
		<button
			type="button"
			class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 sm:min-h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
			on:click={() => onViewDetails(record)}
			aria-label={$i18n.t('View details')}
		>
			<svg
				class="size-3.5"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
				aria-hidden="true"
				><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg
			>
			{$i18n.t('View details')}
		</button>
		<button
			type="button"
			class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 sm:min-h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
			on:click={() => onRemove(record)}
			disabled={deleting}
			aria-label={$i18n.t('Remove record')}
		>
			{#if deleting}
				<Spinner className="size-3.5" />
			{:else}
				<svg
					class="size-3.5"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					aria-hidden="true"
					><path d="M3 6h18M8 6V4h8v2m-9 0 1 14h8l1-14M10 10v6m4-6v6" /></svg
				>
			{/if}
			{$i18n.t('Remove')}
		</button>
	</div>
</article>
