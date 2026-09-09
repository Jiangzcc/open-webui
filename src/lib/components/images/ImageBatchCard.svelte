<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import VendorLogo from '$lib/components/common/VendorLogo.svelte';
	import Download from '$lib/components/icons/Download.svelte';
	import EditPencil from '$lib/components/icons/EditPencil.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Refresh from '$lib/components/icons/Refresh.svelte';
	import Trash from '$lib/components/icons/Trash.svelte';
	import { stripVendorFromName } from '$lib/utils/images-dropdown';
	import {
		generationElapsedSeconds,
		isGenerationTaskTerminal,
		type ImageGenerationBatch
	} from '$lib/utils/image-generation-batches';
	import type { GeneratedImage, ImageGenerationModel } from '$lib/utils/image-generation';
	import {
		imageAspectRatioLabel,
		imageQualityLabelKey,
		imageResolutionLabelKey,
		imageTaskErrorI18nKey
	} from './imageLabels';

	const i18n = getContext<Writable<I18n>>('i18n');

	export let batch: ImageGenerationBatch;
	export let models: ImageGenerationModel[];
	export let canHover = true;
	export let supportsEditing = false;
	export let elapsedNow = 0;
	export let downloading = false;
	export let deleting = false;

	export let onPreview: (image: GeneratedImage) => void = () => {};
	export let onDownloadImage: (image: GeneratedImage, index: number) => void = () => {};
	export let onReuseAsReference: (
		batch: ImageGenerationBatch,
		image: GeneratedImage
	) => void = () => {};
	export let onRemix: (batch: ImageGenerationBatch, image: GeneratedImage) => void = () => {};
	export let onEditAgain: (batch: ImageGenerationBatch) => void = () => {};
	export let onRegenerate: (batch: ImageGenerationBatch) => void = () => {};
	export let onDownloadBatch: (batch: ImageGenerationBatch) => void = () => {};
	export let onRemove: (batch: ImageGenerationBatch) => void = () => {};

	// ===== 结果块（heytop 式聊天消息卡片）展示范式 =====
	// 每个 batch 是一条「消息记录」：消息头(模型短名+时间) → 全展开 prompt
	// → pill 参数行 → 图网格(正方形) → 操作行(重新编辑 i2i / 重新生成 t2i)。
	// 块最大宽与输入框同宽对齐；图片一律 aspect-square 占满格，统一网格高度。
	// 桌面端最多 4 列；移动端固定 2 列，避免横向溢出。
	const BATCH_ARTICLE_CLASS =
		'rounded-2xl bg-gray-50/60 p-3 dark:bg-gray-900/30 sm:p-4 mx-auto w-full max-w-5xl flex flex-col gap-3';

	// 完成态图网格：固定列数，单张图尺寸不随数量变化。
	// 宽屏 lg 一行最多 4 张，窄屏 2 张；图卡 aspect-square 占满格，高度随列宽固定。
	const getCompletedBatchGridClass = () => 'grid grid-cols-2 gap-1.5 sm:gap-2 lg:grid-cols-4';

	// 生成中骨架网格：与完成态同构无缝替换。
	const getPendingBatchGridClass = () => 'grid grid-cols-2 gap-1.5 sm:gap-2 lg:grid-cols-4';

	// 单张图卡：group hover 下载浮层用。
	const getGeneratedImageCardClass = () => 'group relative min-w-0';

	// 图框：1px 浅边 + 圆角 8px；aspect-square 占满格，高度统一。
	const getGeneratedImageFrameClass = () =>
		'relative flex items-center justify-center overflow-hidden rounded-lg border border-gray-200/80 bg-stone-50 aspect-square w-full transition active:scale-[0.98] dark:border-gray-800/80 dark:bg-gray-900/40';

	const getGeneratedImageClass = () => 'block h-full w-full object-cover';

	// 生成中骨架保持正方形；失败状态使用紧凑提示卡，避免占据大面积空白。
	const batchSquareStyle = () => 'aspect-ratio: 1 / 1; width: 100%;';

	const generationStatusLabel = (task: ImageGenerationBatch) => {
		if (task.status === 'queued') return $i18n.t('Queued');
		if (task.status === 'running') return $i18n.t('Generating');
		if (task.status === 'failed' && task.errorCode === 'generation_cancelled') {
			return $i18n.t('Cancelled');
		}
		if (task.status === 'failed') return $i18n.t('Generation failed');
		return $i18n.t('Completed');
	};

	const generationErrorMessage = (task: ImageGenerationBatch) => {
		// 复盘 #18：错误码全部经 i18n 映射——此前白名单外的码（provider_failed、
		// insufficient_credits 等）会把裸码直接显示给用户；未知码回退通用文案。
		const key = imageTaskErrorI18nKey[task.errorCode ?? ''];
		return key ? $i18n.t(key) : $i18n.t('Image generation failed');
	};

	// 消息头模型短名：剥厂商前缀，回退到默认模型。
	// models 作为 prop 显式传入保证响应式追踪：models 异步加载完成后
	// 已渲染的 batch 消息头会随之刷新，不会停在「默认模型」回退态。
	const getBatchModel = (task: ImageGenerationBatch) =>
		models.find((m) => m.id === task.modelId) ?? null;
	// 响应式派生（{@const} 不能直接放在 <article> 下）：
	// models 异步加载完成后已渲染的卡片消息头会随之刷新。
	$: batchModel = getBatchModel(batch);

	const getBatchModelLabel = (task: ImageGenerationBatch) => {
		const model = getBatchModel(task);
		return model ? stripVendorFromName(model) : $i18n.t('Default Model');
	};

	// pill 参数：基础尺寸参数后追加用户实际提交的高级参数，便于复现。
	const getBatchMetaPills = (task: ImageGenerationBatch) => {
		const pills = [getBatchModelLabel(task), imageAspectRatioLabel(task.aspectRatio)];
		if (task.resolution) pills.push($i18n.t(imageResolutionLabelKey(task.resolution)));
		pills.push(String(task.expectedCount));
		const q = task.quality?.trim();
		if (q) pills.push($i18n.t(imageQualityLabelKey(q)));
		const outputFormat = task.params.output_format;
		if (typeof outputFormat === 'string' && outputFormat.trim()) {
			pills.push(outputFormat.trim().toUpperCase());
		}
		for (const [key, label] of [
			['steps', $i18n.t('Steps')],
			['guidance_scale', $i18n.t('Guidance scale')],
			['strength', $i18n.t('Strength')],
			['seed', $i18n.t('Seed')]
		] as const) {
			const value = task.params[key];
			if (typeof value === 'number' && Number.isFinite(value)) pills.push(`${label} ${value}`);
		}
		return pills;
	};

	// 时间：完成用 completedAt，否则 startedAt/createdAt（秒级时间戳）。
	// 今天只显示 HH:MM；今年其它天补 M月D日；跨年带年份，避免只看时分无法区分批次日期。
	const formatBatchTime = (ts: number | null) => {
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
	const getBatchTime = (task: ImageGenerationBatch) =>
		formatBatchTime(task.completedAt ?? task.startedAt ?? task.createdAt);
</script>

<article id={`image-task-${batch.id}`} class={BATCH_ARTICLE_CLASS}>
	<!-- 消息头：厂商图标 + 模型短名 + 时间 -->
	<div class="flex items-center gap-2">
		{#if batchModel?.provider}
			<VendorLogo
				provider={batchModel.provider}
				className="size-5 shrink-0 rounded-full object-cover"
			/>
		{:else}
			<span
				class="size-5 shrink-0 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-600 dark:to-gray-700"
			></span>
		{/if}
		<span class="min-w-0 truncate text-sm font-medium text-gray-800 dark:text-gray-100"
			>{getBatchModelLabel(batch)}</span
		>
		<span class="ml-auto shrink-0 text-[11px] text-gray-400 dark:text-gray-500"
			>{getBatchTime(batch)}</span
		>
	</div>

	<!-- prompt：全展开，不折叠；就是用户输入的纯文本 -->
	<p
		class="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 dark:text-gray-200"
	>
		{batch.prompt}
	</p>

	<!-- pill 参数行：基础参数与已提交的高级参数；生成中附状态 -->
	<div class="flex flex-wrap items-center gap-1.5">
		{#each getBatchMetaPills(batch) as pill, index (`${index}-${pill}`)}
			<span
				class="inline-flex min-h-6 items-center rounded-md bg-gray-100 px-2 text-[11px] text-gray-500 dark:bg-gray-800 dark:text-gray-400"
				>{pill}</span
			>
		{/each}
		{#if !isGenerationTaskTerminal(batch.status)}
			<span
				class="inline-flex min-h-6 items-center gap-1 rounded-md bg-amber-50 px-2 text-[11px] text-amber-600 dark:bg-amber-950/40 dark:text-amber-400"
			>
				<Spinner className="size-3" />
				{generationStatusLabel(batch)} · {generationElapsedSeconds(batch, elapsedNow)}s
			</span>
		{/if}
	</div>

	<div class="min-w-0">
		{#if batch.status === 'succeeded' && batch.images.length > 0}
			<!-- 图网格：宽屏一行 4 张，窄屏 2 张；图卡 aspect-square 固定尺寸 -->
			<div class={getCompletedBatchGridClass()}>
				{#each batch.images as image, index (`${image.url}-${index}`)}
					<div class={getGeneratedImageCardClass()}>
						<button
							type="button"
							class={getGeneratedImageFrameClass()}
							on:click={() => onPreview(image)}
							aria-label={$i18n.t('Preview generated image')}
						>
							<img
								src={image.url}
								alt={image.prompt ?? $i18n.t('Generated image')}
								class={getGeneratedImageClass()}
								loading="lazy"
								decoding="async"
							/>
						</button>
						<!-- 单张快捷操作浮层：触屏常驻可见，桌面端 hover 显现 -->
						<!-- 下载 + 用作参考图；基于此图 prompt 重新生成按钮见下方 -->
						<div
							class="pointer-events-none absolute right-1.5 top-1.5 flex gap-1 transition {canHover
								? 'opacity-0 group-hover:opacity-100'
								: 'opacity-100'}"
						>
							<button
								type="button"
								class="pointer-events-auto inline-flex size-11 items-center justify-center rounded-full bg-white/90 text-gray-800 shadow backdrop-blur transition hover:bg-white active:scale-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:size-7 dark:bg-gray-900/90 dark:text-gray-100 dark:hover:bg-gray-900"
								on:click|stopPropagation={() => onDownloadImage(image, index)}
								aria-label={$i18n.t('Download')}
							>
								<Download className="size-3.5" strokeWidth="2" />
							</button>
							{#if supportsEditing}
								<button
									type="button"
									class="pointer-events-auto inline-flex size-11 items-center justify-center rounded-full bg-white/90 text-gray-800 shadow backdrop-blur transition hover:bg-white active:scale-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:size-7 dark:bg-gray-900/90 dark:text-gray-100 dark:hover:bg-gray-900"
									on:click|stopPropagation={() => onReuseAsReference(batch, image)}
									aria-label={$i18n.t('Use as reference')}
								>
									<Photo className="size-3.5" strokeWidth="2" />
								</button>
							{/if}
						</div>
						<!-- 基于此图 prompt 重新生成：触屏常驻可见，桌面端 hover 显现 -->
						{#if image.prompt}
							<button
								type="button"
								class="pointer-events-auto absolute bottom-1.5 left-1.5 inline-flex min-h-11 items-center gap-1 rounded-full bg-black/60 px-2 text-[10px] font-medium text-white backdrop-blur transition hover:bg-black/75 active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:h-6 sm:min-h-0 {canHover
									? 'opacity-0 group-hover:opacity-100'
									: 'opacity-100'}"
								on:click|stopPropagation={() => onRemix(batch, image)}
								aria-label={$i18n.t('Generate from this prompt')}
							>
								<Refresh className="size-3" strokeWidth="2" />
								{$i18n.t('Remix')}
							</button>
						{/if}
					</div>
				{/each}
			</div>
		{:else if batch.status === 'failed'}
			<div
				class="flex w-full flex-col items-center justify-center rounded-lg border border-dashed border-red-200 bg-red-50/40 px-4 py-5 text-center dark:border-red-900/60 dark:bg-red-950/20 sm:px-5 sm:py-6"
			>
				<p class="text-sm font-medium text-red-600 dark:text-red-300">
					{generationStatusLabel(batch)}
				</p>
				{#if batch.errorCode && batch.errorCode !== 'generation_cancelled'}<p
						class="mt-1 text-xs text-red-500/80"
					>
						{generationErrorMessage(batch)}
					</p>{/if}
			</div>
		{:else}
			<!-- 生成中：正方形骨架占位 + 居中 Spinner -->
			<div class={getPendingBatchGridClass()}>
				{#each Array(batch.expectedCount) as _, index (index)}
					<div
						class="relative overflow-hidden rounded-lg bg-stone-100 dark:bg-gray-900/40"
						style={batchSquareStyle()}
					>
						<div
							class="absolute inset-0 animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.02]"
						></div>
						<div
							class="absolute inset-0 flex flex-col items-center justify-center gap-1.5 text-xs text-gray-400 dark:text-gray-600"
						>
							<Spinner className="size-5" />
							<span>{$i18n.t('Creating image {{index}}', { index: index + 1 })}</span>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- 操作行：再次编辑(i2i) + 重新生成(t2i) + 下载本批(ZIP)，紧凑次级按钮 -->
	<div class="flex flex-wrap items-center gap-1.5">
		{#if isGenerationTaskTerminal(batch.status)}
			<button
				type="button"
				class="inline-flex h-11 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40 sm:h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
				on:click={() => onEditAgain(batch)}
				disabled={batch.images.length === 0}
			>
				<EditPencil className="size-3.5" strokeWidth="2" />
				{$i18n.t('Edit again')}
			</button>
			<button
				type="button"
				class="inline-flex h-11 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 active:scale-[0.97] sm:h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
				on:click={() => onRegenerate(batch)}
			>
				<Refresh className="size-3.5" strokeWidth="2" />
				{$i18n.t('Regenerate')}
			</button>
			{#if batch.images.length > 1}
				<!-- 本批批量下载：打包成 ZIP，复用 $lib/utils/download 的共享方案 -->
				<button
					type="button"
					class="inline-flex h-11 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 sm:h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
					on:click={() => onDownloadBatch(batch)}
					disabled={downloading}
				>
					{#if downloading}
						<Spinner className="size-3.5" />
					{:else}
						<Download className="size-3.5" strokeWidth="2" />
					{/if}
					{$i18n.t('Download all ({{count}})', { count: batch.images.length })}
				</button>
			{/if}
			<button
				type="button"
				class="inline-flex h-11 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 sm:h-7 sm:px-2.5 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
				on:click={() => onRemove(batch)}
				disabled={deleting}
				aria-label={$i18n.t('Remove record')}
			>
				{#if deleting}
					<Spinner className="size-3.5" />
				{:else}
					<Trash className="size-3.5" strokeWidth="2" />
				{/if}
				{$i18n.t('Remove')}
			</button>
		{/if}
	</div>
</article>
