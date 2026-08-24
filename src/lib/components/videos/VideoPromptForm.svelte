<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GenerationModelSelector from '$lib/components/common/GenerationModelSelector.svelte';
	import GenerationSubmitButton from '$lib/components/common/GenerationSubmitButton.svelte';
	import ImageCreditQuoteBadge from '$lib/components/credits/ImageCreditQuoteBadge.svelte';
	import {
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';
	import PromptTagPicker from '$lib/components/prompt-tags/PromptTagPicker.svelte';
	import { mobile } from '$lib/stores';
	import { stripVendorFromName } from '$lib/utils/images-dropdown';
	import { videoAdvancedFieldError, videoAdvancedFieldValue } from '$lib/utils/video-generation';
	import type {
		VideoAdvancedField,
		VideoAssetCapability,
		VideoAssetRole,
		VideoModel,
		VideoTask
	} from '$lib/apis/videos';
	import {
		videoAdvancedFieldDescriptions,
		videoAdvancedFieldLabels,
		videoAdvancedOptionLabels,
		videoAssetLabels,
		videoAudioLabels,
		videoTaskOptions,
		type UploadedVideoAsset
	} from './videoLabels';

	const i18n = getContext<Writable<I18n>>('i18n');

	// 表单所需的模型/参数状态由父组件持有并双向绑定；仅弹层开关为本地 UI 状态。
	export let task: VideoTask;
	export let modelId: string;
	export let selectedVendor: string;
	export let prompt: string;
	export let params: Record<string, string | number | boolean | null>;
	export let assets: Partial<Record<VideoAssetRole, UploadedVideoAsset[]>>;
	export let showAdvanced: boolean;
	export let selectedModel: VideoModel | null;
	export let modelVendors: string[];
	export let vendorModels: VideoModel[];
	export let advancedFields: VideoAdvancedField[];
	export let durationChoices: string[];
	export let quoteState: ImageQuoteState;
	export let submitting = false;
	export let advancedError: {
		field: VideoAdvancedField;
		error: { key: string; value?: number };
	} | null = null;

	export let onTaskChange: (task: VideoTask) => void = () => {};
	export let onModelChange: (modelId: string) => void = () => {};
	export let onUploadAsset: (
		capability: VideoAssetCapability,
		files: FileList | null
	) => void = () => {};
	export let onRemoveAsset: (role: VideoAssetRole, id: string) => void = () => {};
	export let onPromptTagInsert: (
		event: CustomEvent<{ text: string; isNegative: boolean }>
	) => void = () => {};
	export let onSubmit: () => void = () => {};

	// 弹层开关由父组件持有并 bind（changeTask/changeModel 需要主动关闭弹层）。
	export let showModelSelector = false;
	export let showVideoOptions = false;
	let showTaskSelector = false;

	$: durationIndex = Math.max(0, durationChoices.indexOf(String(params.duration ?? '')));
	$: videoOptionsLabel = [
		params.duration === 'auto'
			? $i18n.t('Auto')
			: params.duration === '0'
				? $i18n.t('Match source duration')
				: params.duration
					? `${params.duration}s`
					: null,
		params.aspect_ratio,
		params.resolution,
		params.audio_mode
			? $i18n.t(videoAudioLabels[String(params.audio_mode)] ?? String(params.audio_mode))
			: null
	]
		.filter(Boolean)
		.join(' · ');

	const durationLabel = (value: string) =>
		value === 'auto'
			? $i18n.t('Auto')
			: value === '0'
				? $i18n.t('Match source duration')
				: `${value}s`;

	const fieldValue = (field: VideoAdvancedField) => videoAdvancedFieldValue(field, params);
	const setAdvancedParam = (field: VideoAdvancedField, value: string | number | boolean) => {
		params = { ...params, [field.key]: value };
	};
	const updateAdvancedInput = (
		field: VideoAdvancedField,
		event: Event & { currentTarget: HTMLInputElement }
	) => {
		setAdvancedParam(field, event.currentTarget.value);
	};
	const advancedErrorLabel = (field: VideoAdvancedField) => {
		const error = videoAdvancedFieldError(field, params[field.key] ?? field.default);
		return error ? $i18n.t(error.key, error.value === undefined ? {} : { value: error.value }) : '';
	};
	const advancedRangeLabel = (field: VideoAdvancedField) => {
		if (field.min === undefined && field.max === undefined) return $i18n.t('Model default');
		if (field.min !== undefined && field.max !== undefined) return `${field.min}–${field.max}`;
		if (field.min !== undefined) return `≥ ${field.min}`;
		return `≤ ${field.max}`;
	};
	const aspectRatioPreviewClass = (ratio: string) =>
		ratio === 'auto' ? 'size-5 rounded-full' : 'rounded-[3px]';
	const aspectRatioPreviewStyle = (ratio: string) => {
		if (ratio === 'auto') return '';
		const [width, height] = ratio.split(':').map(Number);
		if (!width || !height) return '';
		const previewSize = 20;
		const minimumPreviewSize = 12;
		return width >= height
			? `width: ${previewSize}px; height: ${Math.max(minimumPreviewSize, (previewSize * height) / width)}px;`
			: `width: ${Math.max(minimumPreviewSize, (previewSize * width) / height)}px; height: ${previewSize}px;`;
	};
</script>

<section
	class="sticky bottom-0 z-20 -mx-3 md:-mx-6 px-3 md:px-6 pt-10 pb-3 bg-gradient-to-t from-white via-white/95 to-white/0 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0"
>
	<div class="mx-auto w-full max-w-5xl sm:px-2">
		<!-- 模型选择器 + 任务选择：移动端下拉框、桌面端按钮标签，始终保持单行 -->
		<div class="mb-2 flex flex-row items-center justify-between gap-2">
			<div class="flex min-w-0 items-center gap-2">
				<div class="inline-flex min-w-0 max-w-[12rem] shrink">
					<GenerationModelSelector
						bind:show={showModelSelector}
						label={selectedModel ? stripVendorFromName(selectedModel) : $i18n.t('Model')}
						provider={selectedModel?.provider}
						vendors={modelVendors}
						bind:selectedVendor
						models={vendorModels.map((model) => ({
							id: model.id,
							name: stripVendorFromName(model),
							provider: model.provider,
							recommended: model.recommended,
							tags: model.tags,
							maintenance: model.maintenance_message,
							enabled: model.enabled,
							raw: model
						}))}
						selectedId={modelId}
						onSelectVendor={(vendor) => (selectedVendor = vendor)}
						onSelectModel={(model) => {
							const videoModel = model.raw as VideoModel;
							if (videoModel.enabled !== false) onModelChange(videoModel.id);
						}}
						listboxLabel={$i18n.t('Model')}
					>
						<svelte:fragment slot="extras" let:model>
							<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">
								{#if (model.raw as VideoModel).base_price}
									{(model.raw as VideoModel).base_price} {$i18n.t('credits.common.unit')}
								{:else}
									{$i18n.t('credits.unconfigured')}
								{/if}
							</span>
						</svelte:fragment>
					</GenerationModelSelector>
				</div>
			</div>

			{#snippet taskIcon(id: string, className: string = 'size-4 shrink-0')}
				{#if id === 'text-to-video'}
					<svg
						class={className}
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<path
							d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
						/>
					</svg>
				{:else if id === 'image-to-video'}
					<svg
						class={className}
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect x="3" y="3" width="18" height="18" rx="2" />
						<circle cx="9" cy="9" r="2" />
						<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
					</svg>
				{:else if id === 'video-to-video'}
					<svg
						class={className}
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.8"
						stroke-linecap="round"
						stroke-linejoin="round"
						aria-hidden="true"
					>
						<rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
						<path d="M7 2v20M17 2v20M2 12h20M2 7h5M2 17h5M17 7h5M17 17h5" />
					</svg>
				{/if}
			{/snippet}

			<!-- 移动端：紧凑下拉框（复用项目 Dropdown 组件），风格与模型选择器一致 -->
			<div class="shrink-0 sm:hidden">
				<Dropdown
					bind:show={showTaskSelector}
					side="top"
					align="end"
					visualViewportAware={$mobile}
					contentClass="z-50 w-40 overflow-y-auto rounded-2xl border border-gray-200/90 bg-white/98 p-2 shadow-2xl backdrop-blur-xl dark:border-gray-700 dark:bg-gray-900/98"
				>
					<button
						type="button"
						class="inline-flex h-11 items-center gap-2 overflow-hidden rounded-[10px] bg-gray-100 px-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
						aria-expanded={showTaskSelector}
						aria-haspopup="true"
					>
						{@render taskIcon(task)}
						<span class="truncate"
							>{$i18n.t(videoTaskOptions.find((item) => item.id === task)?.label ?? '')}</span
						>
						<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">⌄</span>
					</button>

					<div slot="content" class="flex flex-col gap-0.5">
						{#each videoTaskOptions as option}
							<button
								type="button"
								class="flex min-h-11 w-full items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition {task ===
								option.id
									? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
									: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
								on:click={() => {
									onTaskChange(option.id);
									showTaskSelector = false;
								}}
								aria-pressed={task === option.id}
								>{@render taskIcon(option.id)}{$i18n.t(option.label)}</button
							>
						{/each}
					</div>
				</Dropdown>
			</div>

			<!-- 桌面端：按钮标签 -->
			<div
				class="pointer-events-auto hidden flex-wrap gap-1 sm:flex sm:flex-nowrap sm:justify-end"
				role="tablist"
				tabindex="-1"
				aria-label={$i18n.t('Video mode')}
			>
				{#each videoTaskOptions as option}
					<button
						type="button"
						role="tab"
						aria-selected={task === option.id}
						class="inline-flex min-h-9 items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition {task ===
						option.id
							? 'bg-gray-900 text-white shadow-sm dark:bg-gray-100 dark:text-gray-900'
							: 'bg-gray-50 text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
						on:click={() => onTaskChange(option.id)}
						>{@render taskIcon(option.id, 'size-3.5 shrink-0')}{$i18n.t(option.label)}</button
					>
				{/each}
			</div>
		</div>

		<form
			class="relative rounded-[1.5rem] border border-gray-100/90 bg-white/95 p-4 shadow-xl shadow-gray-200/50 backdrop-blur-xl dark:border-gray-800/90 dark:bg-gray-950/95 dark:shadow-black/25"
			on:submit|preventDefault={onSubmit}
		>
			{#if selectedModel?.asset_inputs?.length}
				<div class="mb-3 flex gap-2 overflow-x-auto pb-1 scrollbar-hidden">
					{#each selectedModel.asset_inputs as capability}
						<label
							class="flex h-14 min-w-36 cursor-pointer items-center gap-2 rounded-2xl border border-gray-100 bg-gray-50 px-3 text-xs text-gray-600 transition hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850"
						>
							<span
								class="flex size-7 shrink-0 items-center justify-center rounded-full bg-white text-lg text-gray-500 shadow-sm dark:bg-gray-800"
								>+</span
							>
							<span class="truncate"
								>{$i18n.t(videoAssetLabels[capability.role])}{capability.required ? ' *' : ''}</span
							>
							<span class="ml-2 text-gray-400"
								>{assets[capability.role]?.length ?? 0}/{capability.max_count}</span
							>
							<input
								class="sr-only"
								type="file"
								accept={capability.mime_types.join(',')}
								multiple={capability.multiple}
								on:change={(event) => onUploadAsset(capability, event.currentTarget.files)}
							/>
						</label>
					{/each}
				</div>
				{#if Object.values(assets).some((items) => items?.length)}
					<div class="mb-3 flex gap-2 overflow-x-auto pb-1 scrollbar-hidden">
						{#each Object.entries(assets) as [role, items]}
							{#each items ?? [] as item (item.id)}
								<div
									class="group relative flex w-44 shrink-0 items-center gap-2 overflow-hidden rounded-xl border border-gray-100 bg-gray-50 p-1.5 text-[11px] dark:border-gray-800 dark:bg-gray-900"
								>
									<div
										class="flex aspect-video w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-gray-200 text-gray-500 dark:bg-gray-800"
									>
										{#if item.mime_type.startsWith('image/')}<img
												class="size-full object-cover"
												src={item.url}
												alt={item.name}
											/>{:else if item.mime_type.startsWith('video/')}<video
												class="size-full object-cover"
												src={item.url}
												muted
												playsinline
												preload="metadata"
											></video>{:else}<span aria-hidden="true">♪</span>{/if}
									</div>
									<div class="min-w-0 flex-1">
										<div class="truncate font-medium text-gray-700 dark:text-gray-200">
											{$i18n.t(videoAssetLabels[role as VideoAssetRole])}
										</div>
										<div class="mt-0.5 truncate text-gray-400" title={item.name}>
											{item.name}
										</div>
									</div>
									<button
										type="button"
										class="absolute right-1 top-1 flex size-11 items-center justify-center rounded-full bg-white/90 text-sm text-gray-600 shadow-sm transition hover:text-gray-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:size-8 dark:bg-gray-800/90 dark:text-gray-300 dark:hover:text-white"
										aria-label={$i18n.t('Remove')}
										on:click={() => onRemoveAsset(role as VideoAssetRole, item.id)}>×</button
									>
								</div>
							{/each}
						{/each}
					</div>
				{/if}
			{/if}

			<div class="min-w-0 flex-1">
				<textarea
					bind:value={prompt}
					rows="3"
					class="w-full flex-1 resize-none bg-transparent py-2 text-base leading-normal text-gray-900 outline-none placeholder:text-gray-400 dark:text-gray-100 dark:placeholder:text-gray-500"
					placeholder={$i18n.t(videoTaskOptions.find((item) => item.id === task)?.hint ?? '')}
					aria-label={$i18n.t('Video prompt')}
				></textarea>
			</div>

			<div class="mt-2 flex min-w-0 items-center justify-between gap-2">
				<div class="flex min-w-0 items-center gap-2">
					<Dropdown
						bind:show={showVideoOptions}
						side="top"
						align="start"
						maxHeight="min(75dvh, 34rem)"
						contentClass="z-50 w-[min(27rem,calc(100vw-1.5rem))] min-w-0 overflow-y-auto overscroll-contain rounded-2xl border border-gray-100 bg-white p-3 shadow-xl sm:p-4 dark:border-gray-800 dark:bg-gray-900"
					>
						<button
							type="button"
							class="inline-flex h-11 min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-[10px] bg-gray-100 px-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 sm:h-8 sm:gap-4 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
						>
							<svg
								class="size-4 shrink-0"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="1.8"
								aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6" /></svg
							>
							<span class="truncate">{videoOptionsLabel}</span>
						</button>

						<div slot="content" class="min-w-0">
							{#if durationChoices.length}
								<section>
									<div class="flex items-center justify-between gap-3 px-1 pb-2">
										<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">
											{$i18n.t('Duration')}
										</h3>
										<output
											class="rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium tabular-nums dark:bg-gray-800"
											>{durationLabel(durationChoices[durationIndex])}</output
										>
									</div>
									<div class="px-1">
										<input
											type="range"
											class="h-11 w-full cursor-pointer accent-gray-900 sm:h-8 dark:accent-gray-100"
											min="0"
											max={durationChoices.length - 1}
											step="1"
											value={durationIndex}
											on:input={(event) =>
												(params = {
													...params,
													duration: durationChoices[Number(event.currentTarget.value)]
												})}
											aria-label={$i18n.t('Duration')}
										/>
										<div class="flex justify-between text-[10px] text-gray-400">
											<span>{durationLabel(durationChoices[0])}</span>
											<span>{durationLabel(durationChoices[durationChoices.length - 1])}</span>
										</div>
									</div>
								</section>
							{/if}
							{#if selectedModel?.aspect_ratios}
								<section class="mt-5">
									<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
										{$i18n.t('Ratio')}
									</h3>
									<div class="grid min-w-0 grid-cols-3 gap-1.5 sm:grid-cols-5">
										{#each selectedModel.aspect_ratios as value}<button
												type="button"
												class="flex h-14 min-w-0 flex-col items-center justify-center gap-1 rounded-xl border text-xs transition {params.aspect_ratio ===
												value
													? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
													: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
												on:click={() => (params = { ...params, aspect_ratio: value })}
												aria-pressed={params.aspect_ratio === value}
												><span class="flex size-6 items-center justify-center"
													><span
														class="border border-current/60 {aspectRatioPreviewClass(value)}"
														style={aspectRatioPreviewStyle(value)}
													></span></span
												><span class="min-w-0 truncate">{value}</span></button
											>{/each}
									</div>
								</section>
							{/if}
							{#if selectedModel?.resolutions}<section class="mt-5">
									<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
										{$i18n.t('Resolution')}
									</h3>
									<div class="grid grid-cols-3 gap-1.5">
										{#each selectedModel.resolutions as value}<button
												type="button"
												class="h-11 rounded-xl border text-sm transition sm:h-9 {params.resolution ===
												value
													? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
													: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
												on:click={() => (params = { ...params, resolution: value })}
												aria-pressed={params.resolution === value}>{value}</button
											>{/each}
									</div>
								</section>{/if}
							{#if selectedModel?.audio_options}<section class="mt-5">
									<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
										{$i18n.t('Audio')}
									</h3>
									<div class="grid grid-cols-2 gap-1.5">
										{#each selectedModel.audio_options as value}<button
												type="button"
												class="h-11 rounded-xl border px-2 text-sm transition sm:h-9 {params.audio_mode ===
												value.mode
													? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
													: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
												on:click={() => (params = { ...params, audio_mode: value.mode })}
												aria-pressed={params.audio_mode === value.mode}
												>{$i18n.t(videoAudioLabels[value.mode] ?? value.mode)}</button
											>{/each}
									</div>
								</section>{/if}
							{#if advancedFields.length}
								<section class="mt-5 border-t border-gray-100 pt-3 dark:border-gray-800">
									<button
										type="button"
										class="flex min-h-11 w-full items-center justify-between rounded-xl px-1 text-left text-sm font-medium text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:text-gray-100"
										aria-expanded={showAdvanced}
										aria-controls="video-advanced-settings"
										on:click={() => (showAdvanced = !showAdvanced)}
										><span>{$i18n.t('Advanced')}</span><span
											class="text-gray-400"
											aria-hidden="true">{showAdvanced ? '−' : '+'}</span
										></button
									>
									{#if showAdvanced}<div
											id="video-advanced-settings"
											class="mt-2 grid min-w-0 gap-4 sm:grid-cols-2"
										>
											{#each advancedFields as field}<div
													class="min-w-0 text-xs font-medium text-gray-600 dark:text-gray-300 {field.kind ===
													'text'
														? 'sm:col-span-2'
														: ''}"
												>
													<span class="flex justify-between gap-2"
														><span>{$i18n.t(videoAdvancedFieldLabels[field.key])}</span
														>{#if field.kind === 'integer' || field.kind === 'number'}<span
																class="font-normal text-gray-400">{advancedRangeLabel(field)}</span
															>{/if}</span
													>
													{#if videoAdvancedFieldDescriptions[field.key]}<p
															class="mt-1 text-[11px] font-normal leading-4 text-gray-400"
														>
															{$i18n.t(videoAdvancedFieldDescriptions[field.key] ?? '')}
														</p>{/if}
													{#if field.kind === 'text'}<textarea
															id="video-advanced-{field.key}"
															class="mt-1 min-h-24 w-full resize-y rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm font-normal text-gray-900 outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
															rows="3"
															maxlength={field.max_length ?? undefined}
															value={String(fieldValue(field))}
															aria-label={$i18n.t(videoAdvancedFieldLabels[field.key])}
															on:input={(event) =>
																setAdvancedParam(field, event.currentTarget.value)}
														></textarea>{:else if field.kind === 'option' && field.options}<div
															class="mt-1 grid grid-cols-2 gap-1.5"
															role="group"
															aria-label={$i18n.t(videoAdvancedFieldLabels[field.key])}
														>
															{#each field.options as option}<button
																	type="button"
																	class="min-h-11 rounded-xl border px-3 py-2 text-xs transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {fieldValue(
																		field
																	) === option
																		? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
																		: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
																	on:click={() => setAdvancedParam(field, option)}
																	aria-pressed={fieldValue(field) === option}
																	>{$i18n.t(videoAdvancedOptionLabels[option] ?? option)}</button
																>{/each}
														</div>{:else if field.kind === 'boolean'}<button
															id="video-advanced-{field.key}"
															type="button"
															class="mt-1 flex min-h-11 w-full items-center justify-between rounded-xl border border-gray-200 bg-transparent px-3 py-2 font-normal text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:border-gray-700 dark:text-gray-100"
															role="switch"
															aria-checked={Boolean(fieldValue(field))}
															aria-label={$i18n.t(videoAdvancedFieldLabels[field.key])}
															on:click={() => setAdvancedParam(field, !Boolean(fieldValue(field)))}
															><span
																>{Boolean(fieldValue(field)) ? $i18n.t('On') : $i18n.t('Off')}</span
															><span
																class="h-5 w-9 rounded-full p-0.5 transition {Boolean(
																	fieldValue(field)
																)
																	? 'bg-gray-900 dark:bg-gray-100'
																	: 'bg-gray-300 dark:bg-gray-600'}"
																><span
																	class="block size-4 rounded-full bg-white transition {Boolean(
																		fieldValue(field)
																	)
																		? 'translate-x-4 dark:bg-gray-900'
																		: ''}"
																></span></span
															></button
														>{:else}<input
															id="video-advanced-{field.key}"
															class="mt-1 min-h-11 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm font-normal tabular-nums text-gray-900 outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
															type="text"
															inputmode={field.kind === 'integer' ? 'numeric' : 'decimal'}
															value={fieldValue(field)}
															placeholder={$i18n.t('Model default')}
															aria-label={$i18n.t(videoAdvancedFieldLabels[field.key])}
															aria-invalid={Boolean(advancedErrorLabel(field))}
															aria-describedby={advancedErrorLabel(field)
																? `video-advanced-error-${field.key}`
																: undefined}
															on:input={(event) => updateAdvancedInput(field, event)}
														/>{/if}
													{#if advancedErrorLabel(field)}<p
															id="video-advanced-error-{field.key}"
															class="mt-1 text-[11px] font-normal text-red-600 dark:text-red-400"
															aria-live="polite"
														>
															{advancedErrorLabel(field)}
														</p>{/if}
												</div>{/each}
										</div>{/if}
								</section>
							{/if}
						</div>
					</Dropdown>
					<!-- 标签选择入口在参数按钮右侧：点击标签即插入实际文本 -->
					<PromptTagPicker
						mediaKind="video"
						modelId={selectedModel?.id ?? null}
						negativeSupported={advancedFields.some((field) => field.key === 'negative_prompt')}
						on:insert={onPromptTagInsert}
					/>
				</div>

				<div class="flex shrink-0 items-center gap-2">
					<ImageCreditQuoteBadge {quoteState} />
					<GenerationSubmitButton
						loading={submitting}
						disabled={submitting ||
							!selectedModel ||
							selectedModel.enabled === false ||
							Boolean(advancedError) ||
							!isImageQuoteSubmittable(quoteState)}
						label={$i18n.t('Generate video')}
					/>
				</div>
			</div>
		</form>
	</div>
</section>
