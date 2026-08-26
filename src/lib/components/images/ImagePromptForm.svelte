<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import ImageCreditQuoteBadge from '$lib/components/credits/ImageCreditQuoteBadge.svelte';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GenerationModelSelector from '$lib/components/common/GenerationModelSelector.svelte';
	import GenerationSubmitButton from '$lib/components/common/GenerationSubmitButton.svelte';
	import {
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';
	import Image from '$lib/components/common/Image.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Link from '$lib/components/icons/Link.svelte';
	import LinkSlash from '$lib/components/icons/LinkSlash.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import PromptTagPicker from '$lib/components/prompt-tags/PromptTagPicker.svelte';
	import { isProxyModel, stripVendorFromName } from '$lib/utils/images-dropdown';
	import {
		DEFAULT_IMAGE_ASPECT_RATIO,
		resolveImageEditModel,
		supportsImageEditing,
		type ImageAspectRatio,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';
	import { imageQualityLabelKey, imageResolutionLabelKey } from './imageLabels';
	import {
		advancedRangeLabel as formatAdvancedRangeLabel,
		getAdvancedNumberError as validateAdvancedNumber
	} from './imagePageState';

	const i18n = getContext<Writable<I18n>>('i18n');

	// ---- 由父组件持有并双向绑定的表单状态 ----
	export let selectedVendor = '';
	export let prompt = '';
	export let selectedQuality = '';
	export let imageCount: number | string = 1;
	export let useCustomSize = false;
	export let customWidth: number | null = null;
	export let customHeight: number | null = null;
	export let customSizeAspectRatioLocked = true;
	export let selectedOutputFormat: string | null = null;
	export let seedInput = '';
	export let stepsInput = '';
	export let guidanceScaleInput = '';
	export let strengthInput = '';
	export let negativePrompt = '';
	export let showModelSelector = false;
	export let showAspectRatioPicker = false;
	export let showAdvancedSettings = false;
	export let draggedOver = false;

	// ---- 只读展示数据 ----
	export let selectedModelLabel = '';
	export let selectedModelConfig: ImageGenerationModel | null = null;
	export let vendorList: string[] = [];
	export let vendorModels: ImageGenerationModel[] = [];
	export let selectedModel = '';
	export let models: ImageGenerationModel[] = [];
	export let selectedModelSupportsEditing = false;
	export let selectedAspectRatio: ImageAspectRatio | null = null;
	export let selectedResolution: string | null = null;
	export let referenceImages: { url: string; name: string }[] = [];
	export let aspectRatioOptions: ImageAspectRatio[] = [];
	export let resolutionOptions: string[] = [];
	export let qualityOptions: string[] = [];
	export let imageCountOptions: number[] = [];
	export let outputFormatOptions: string[] = [];
	export let supportsCustomSize = false;
	export let hasImageSizingOptions = false;
	export let hasAdvancedSettings = false;
	export let seedField: { kind: 'integer' | 'number' | 'text'; min?: number; max?: number } | null =
		null;
	export let stepsField: {
		kind: 'integer' | 'number' | 'text';
		min?: number;
		max?: number;
	} | null = null;
	export let guidanceScaleField: {
		kind: 'integer' | 'number' | 'text';
		min?: number;
		max?: number;
	} | null = null;
	export let strengthField: {
		kind: 'integer' | 'number' | 'text';
		min?: number;
		max?: number;
	} | null = null;
	export let negativePromptField: object | null = null;
	export let customSizeError: {
		message: string;
		messageParams?: Record<string, string | number>;
	} | null = null;
	export let customWidthNum = 0;
	export let customHeightNum = 0;
	export let selectedImageSizeLabel = '';
	export let imageQuoteState: ImageQuoteState = { status: 'loading' };
	export let loading = false;
	export let advancedSettingsInvalid = false;

	// ---- 依赖父组件状态的函数与事件回调 ----
	export let selectModelIfEnabled: (model: ImageGenerationModel) => void = () => {};
	export let selectAspectRatio: (ratio: ImageAspectRatio) => void = () => {};
	export let selectResolution: (resolution: string) => void = () => {};
	export let onCustomSizeEnabledChange: (enabled: boolean) => void = () => {};
	export let onCustomWidthInput: (value: number | null) => void = () => {};
	export let onCustomHeightInput: (value: number | null) => void = () => {};
	export let onCustomSizeAspectRatioToggle: () => void = () => {};
	// 参数弹窗打开时由父组件关闭相邻弹窗（如模型选择器），保持互斥。
	export let onOptionsOpen: () => void = () => {};
	export let handleFileUpload: (event: Event) => void = () => {};
	export let handleDrop: (event: DragEvent) => void = () => {};
	export let removeImage: (index: number) => void = () => {};
	export let handlePromptTagInsert: (
		event: CustomEvent<{ text: string; isNegative: boolean }>
	) => void = () => {};
	export let submitHandler: () => void = () => {};

	// ---- 本地元素引用 ----
	let fileInputElement: HTMLInputElement;
	let promptEditorElement: HTMLTextAreaElement | null = null;
	const IMAGE_OPTIONS_DIALOG_ID = 'image-generation-options';

	// 草稿复用后把焦点还给提示词输入框（父组件 applyCreationDraft 调用）。
	export function focusPromptEditor() {
		promptEditorElement?.focus();
	}

	// ---- 纯展示函数（值 → i18n key / 预览样式） ----
	// 比例是技术值不过 i18next（nsSeparator 会把 "4:3" 拆坏），仅 Auto 走翻译。
	const getAspectRatioLabel = (ratio: ImageAspectRatio) =>
		ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio;
	const getResolutionLabel = (resolution: string) => $i18n.t(imageResolutionLabelKey(resolution));
	const getQualityLabel = (quality: string) => $i18n.t(imageQualityLabelKey(quality));
	const translate = (key: string, values?: Record<string, number>) => $i18n.t(key, values);
	const getAdvancedNumberError = (
		value: string,
		field: { kind: 'integer' | 'number' | 'text'; min?: number; max?: number } | null
	) => (field ? validateAdvancedNumber(value, field, translate) : null);
	const advancedRangeLabel = (field: { min?: number; max?: number } | null) =>
		formatAdvancedRangeLabel(field, translate);
	const numericInputValue = (event: Event) => {
		const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
		return Number.isFinite(value) ? value : null;
	};
	const modelBasePrice = (model: ImageGenerationModel) =>
		referenceImages.length ? resolveImageEditModel(model, models)?.basePrice : model.basePrice;
	// 参数按钮摘要：与视频侧一致，用「·」分隔当前参数值。
	$: imageOptionsLabel = [
		selectedImageSizeLabel,
		aspectRatioOptions.length > 0 && selectedResolution
			? getResolutionLabel(selectedResolution)
			: null,
		qualityOptions.length > 0 && selectedQuality ? getQualityLabel(selectedQuality) : null,
		imageCountOptions.length > 1 ? String(imageCount) : null
	]
		.filter(Boolean)
		.join(' · ');
	const getAspectRatioPreviewClass = (ratio: ImageAspectRatio) => {
		return ratio === DEFAULT_IMAGE_ASPECT_RATIO ? 'size-5 rounded-full' : 'rounded-[3px]';
	};
	const getAspectRatioPreviewStyle = (ratio: ImageAspectRatio) => {
		if (ratio === DEFAULT_IMAGE_ASPECT_RATIO) {
			return '';
		}
		const [width, height] = ratio.split(':').map(Number);
		if (!width || !height) {
			return '';
		}
		const previewSize = 20;
		const minimumPreviewSize = 12;
		if (width >= height) {
			return `width: ${previewSize}px; height: ${Math.max(minimumPreviewSize, (previewSize * height) / width)}px;`;
		}
		return `width: ${Math.max(minimumPreviewSize, (previewSize * width) / height)}px; height: ${previewSize}px;`;
	};
</script>

<!-- 参数弹窗的开关/外点关闭/Esc/定位统一由 Dropdown 组件处理（与标签、模型选择器一致） -->

<div
	class="sticky bottom-0 z-20 -mx-3 md:-mx-6 px-3 md:px-6 pt-10 pb-3 bg-gradient-to-t from-white via-white/95 to-white/0 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0"
>
	<div class="mx-auto w-full max-w-5xl sm:px-2">
		<!-- 模型选择器：放在表单上方（正常文档流），避免绝对定位与结果图片重叠 -->
		<div class="mb-2 flex flex-row items-center gap-2">
			<div class="inline-flex min-w-0 max-w-[12rem] shrink">
				<GenerationModelSelector
					bind:show={showModelSelector}
					label={selectedModelLabel}
					provider={selectedModelConfig?.provider}
					vendors={vendorList}
					bind:selectedVendor
					models={vendorModels.map((model) => ({
						id: model.id,
						name: stripVendorFromName(model),
						provider: model.provider,
						recommended: model.recommended,
						tags: model.tags,
						maintenance: model.maintenanceMessage,
						enabled: model.enabled,
						raw: model
					}))}
					selectedId={selectedModel}
					onSelectVendor={(vendor) => (selectedVendor = vendor)}
					onSelectModel={(model) => selectModelIfEnabled(model.raw as ImageGenerationModel)}
					listboxLabel={$i18n.t('Select image model')}
				>
					<svelte:fragment slot="extras" let:model>
						{#if supportsImageEditing(model.raw as ImageGenerationModel, models)}
							<Tooltip content={$i18n.t('Supports reference images')}>
								<span
									class="inline-flex size-5 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300"
									aria-label={$i18n.t('Supports reference images')}
								>
									<Photo className="size-3.5" strokeWidth="2" />
								</span>
							</Tooltip>
						{/if}
						{#if modelBasePrice(model.raw as ImageGenerationModel)}
							<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">
								{modelBasePrice(model.raw as ImageGenerationModel)}
								{$i18n.t('credits.common.unit')}
							</span>
						{:else}
							<span class="shrink-0 text-xs text-gray-400 dark:text-gray-500"
								>{$i18n.t('credits.unconfigured')}</span
							>
						{/if}
						{#if isProxyModel(model.raw as ImageGenerationModel)}
							<span class="shrink-0 text-xs text-amber-600 dark:text-amber-400">
								{$i18n.t('First image may be slower')}
							</span>
						{/if}
					</svelte:fragment>
				</GenerationModelSelector>
			</div>
		</div>
		<form
			class="relative rounded-[1.5rem] border border-gray-100/90 bg-white/95 shadow-xl shadow-gray-200/50 backdrop-blur-xl dark:border-gray-800/90 dark:bg-gray-950/95 dark:shadow-black/25"
			on:submit|preventDefault={submitHandler}
			on:dragover={(event) => {
				event.preventDefault();
				draggedOver =
					selectedModelSupportsEditing && (event.dataTransfer?.types?.includes('Files') ?? false);
			}}
			on:dragleave={() => {
				draggedOver = false;
			}}
			on:drop={handleDrop}
		>
			{#if draggedOver}
				<div
					class="absolute inset-2 z-20 rounded-[1.25rem] border-2 border-dashed border-gray-400 bg-white/85 text-sm font-medium text-gray-700 dark:border-gray-500 dark:bg-gray-950/85 dark:text-gray-200 flex items-center justify-center"
				>
					{$i18n.t('Drop reference images here')}
				</div>
			{/if}

			<input
				bind:this={fileInputElement}
				type="file"
				accept="image/*"
				multiple
				class="hidden"
				on:change={handleFileUpload}
			/>

			<div class="p-4">
				{#if referenceImages.length > 0}
					<div class="mb-3 flex gap-2 overflow-x-auto scrollbar-hidden pb-1">
						{#each referenceImages as image, index (`${image.url}-${index}`)}
							<div class="relative shrink-0 group">
								<Image
									src={image.url}
									alt={image.name}
									className="size-14"
									imageClassName="size-14 rounded-2xl object-cover border border-gray-100 dark:border-gray-800"
								/>
								<button
									type="button"
									class="absolute -right-2 -top-2 inline-flex size-11 items-center justify-center rounded-full border border-gray-100 bg-white text-gray-900 opacity-100 shadow transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 md:-right-1.5 md:-top-1.5 md:size-6 md:opacity-0 md:group-hover:opacity-100 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
									on:click={() => removeImage(index)}
									aria-label={$i18n.t('Remove image')}
								>
									<XMark className="size-4" strokeWidth="2" />
								</button>
							</div>
						{/each}
					</div>
				{/if}

				<div class="flex min-w-0 gap-4">
					{#if selectedModelSupportsEditing}
						<button
							type="button"
							class="mt-2 flex h-[3.8rem] w-[3.125rem] shrink-0 items-center justify-center rounded-2xl border border-gray-100 bg-gray-50 text-gray-500 transition hover:bg-gray-100 hover:text-gray-800 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850 dark:hover:text-gray-100"
							on:click={() => fileInputElement?.click()}
							aria-label={$i18n.t('Upload reference image')}
						>
							<Plus className="size-6" strokeWidth="1.8" />
						</button>
					{/if}

					<div class="min-w-0 flex-1">
						<textarea
							bind:this={promptEditorElement}
							bind:value={prompt}
							rows="3"
							class="w-full flex-1 resize-none bg-transparent py-2 text-base leading-normal text-gray-900 outline-none placeholder:text-gray-400 dark:text-gray-100 dark:placeholder:text-gray-500"
							placeholder={$i18n.t(
								'Upload a reference image, then describe the image you want to create.'
							)}
							aria-label={$i18n.t('Image prompt')}
						></textarea>
					</div>
				</div>

				<div class="mt-2 flex min-w-0 items-center justify-between gap-2">
					<div class="flex min-w-0 items-center gap-2">
						<Dropdown
							bind:show={showAspectRatioPicker}
							side="top"
							align="start"
							contentRole="dialog"
							maxHeight="min(75dvh, 34rem)"
							onOpenChange={(open) => open && onOptionsOpen()}
							contentClass="z-50 w-[min(27rem,calc(100vw-1.5rem))] min-w-0 overflow-y-auto overscroll-contain rounded-2xl border border-gray-100 bg-white p-3 shadow-xl sm:p-4 dark:border-gray-800 dark:bg-gray-900"
						>
							<button
								type="button"
								class="inline-flex h-11 min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-[10px] bg-gray-100 px-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 sm:h-8 sm:gap-4 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
								aria-expanded={showAspectRatioPicker}
								aria-haspopup="dialog"
								aria-controls={IMAGE_OPTIONS_DIALOG_ID}
							>
								<svg
									class="size-4 shrink-0"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="1.8"
									aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6" /></svg
								>
								<span class="truncate">{imageOptionsLabel}</span>
							</button>

							<div
								slot="content"
								id={IMAGE_OPTIONS_DIALOG_ID}
								class="min-w-0"
								role="dialog"
								aria-label={$i18n.t('Parameters')}
							>
								{#if aspectRatioOptions.length > 0}
									<section>
										<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
											{$i18n.t('Ratio')}
										</h3>
										<div class="grid min-w-0 grid-cols-3 gap-1.5 sm:grid-cols-5">
											{#each aspectRatioOptions as ratio}
												<button
													type="button"
													class="flex h-14 flex-col items-center justify-center gap-1 rounded-xl border text-xs transition {selectedAspectRatio ===
													ratio
														? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
														: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
													on:click={() => selectAspectRatio(ratio)}
													aria-pressed={selectedAspectRatio === ratio}
												>
													<span class="flex size-6 items-center justify-center">
														<span
															class="border border-current/60 {getAspectRatioPreviewClass(ratio)}"
															style={getAspectRatioPreviewStyle(ratio)}
														></span>
													</span>
													<span class="min-w-0 truncate">{getAspectRatioLabel(ratio)}</span>
												</button>
											{/each}
										</div>
									</section>
								{/if}

								{#if resolutionOptions.length > 0}
									<section class="mt-5">
										<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
											{$i18n.t('Resolution')}
										</h3>
										<div class="grid grid-cols-3 gap-1.5">
											{#each resolutionOptions as resolution}
												<button
													type="button"
													class="h-11 rounded-xl border text-sm transition sm:h-9 {selectedResolution ===
													resolution
														? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
														: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
													on:click={() => selectResolution(resolution)}
													aria-pressed={selectedResolution === resolution}
												>
													{getResolutionLabel(resolution)}
												</button>
											{/each}
										</div>
									</section>
								{/if}

								{#if supportsCustomSize}
									<section class="mt-5">
										<div class="flex items-center justify-between px-1 pb-2">
											<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">
												{$i18n.t('Custom Size')}
											</h3>
											<label
												class="flex min-h-11 items-center gap-1.5 text-xs text-gray-500 sm:min-h-0 dark:text-gray-400"
											>
												<input
													type="checkbox"
													class="size-3.5 rounded border-gray-300 dark:border-gray-600"
													checked={useCustomSize}
													on:change={(event) =>
														onCustomSizeEnabledChange(event.currentTarget.checked)}
												/>
												{$i18n.t('Enable')}
											</label>
										</div>
										{#if useCustomSize}
											<div class="flex items-center gap-2">
												<input
													type="number"
													inputmode="numeric"
													min="1"
													value={customWidth ?? ''}
													on:input={(event) => onCustomWidthInput(numericInputValue(event))}
													placeholder="1024"
													aria-label={$i18n.t('Width')}
													class="h-11 min-w-0 flex-1 rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums dark:border-gray-700 dark:text-gray-100 sm:h-9"
												/>
												<Tooltip
													className="flex shrink-0"
													content={$i18n.t(
														customSizeAspectRatioLocked
															? 'Unlock aspect ratio'
															: 'Lock aspect ratio'
													)}
												>
													<button
														type="button"
														class="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:size-9 {customSizeAspectRatioLocked
															? 'border-gray-300 bg-gray-100 text-gray-700 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200'
															: 'border-gray-200 bg-transparent text-gray-400 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-500 dark:hover:bg-gray-800'}"
														on:click={onCustomSizeAspectRatioToggle}
														aria-label={$i18n.t('Keep aspect ratio')}
														aria-pressed={customSizeAspectRatioLocked}
													>
														{#if customSizeAspectRatioLocked}
															<Link className="size-4" strokeWidth="2" />
														{:else}
															<LinkSlash className="size-4" strokeWidth="2" />
														{/if}
													</button>
												</Tooltip>
												<input
													type="number"
													inputmode="numeric"
													min="1"
													value={customHeight ?? ''}
													on:input={(event) => onCustomHeightInput(numericInputValue(event))}
													placeholder="1024"
													aria-label={$i18n.t('Height')}
													class="h-11 min-w-0 flex-1 rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums dark:border-gray-700 dark:text-gray-100 sm:h-9"
												/>
											</div>
											{#if customSizeError}
												<p class="mt-2 px-1 text-xs text-red-600 dark:text-red-400">
													{$i18n.t(customSizeError.message, customSizeError.messageParams)}
												</p>
											{:else if customWidth && customHeight}
												<p class="mt-2 px-1 text-xs text-gray-400 dark:text-gray-500">
													{customWidthNum * customHeightNum >= 0
														? (customWidthNum * customHeightNum).toLocaleString()
														: ''} px · {customWidthNum || 0}:{customHeightNum || 0}
												</p>
											{/if}
										{/if}
									</section>
								{/if}

								{#if qualityOptions.length > 0}
									<section class={hasImageSizingOptions ? 'mt-5' : ''}>
										<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
											{$i18n.t('Quality')}
										</h3>
										<div class="grid grid-cols-4 gap-1.5">
											{#each qualityOptions as quality}
												<button
													type="button"
													class="h-11 rounded-xl border text-sm capitalize transition sm:h-9 {selectedQuality ===
													quality
														? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
														: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
													on:click={() => {
														selectedQuality = quality;
													}}
													aria-pressed={selectedQuality === quality}
												>
													{getQualityLabel(quality)}
												</button>
											{/each}
										</div>
									</section>
								{/if}

								{#if imageCountOptions.length > 1}
									<section class={hasImageSizingOptions ? 'mt-5' : ''}>
										<h3 class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100">
											{$i18n.t('Quantity')}
										</h3>
										<div class="grid grid-cols-4 gap-1.5">
											{#each imageCountOptions as count}
												<button
													type="button"
													class="h-11 rounded-xl border text-sm transition sm:h-9 {Number(
														imageCount
													) === count
														? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
														: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
													on:click={() => {
														imageCount = count;
													}}
													aria-pressed={Number(imageCount) === count}
												>
													{count}
												</button>
											{/each}
										</div>
									</section>
								{/if}

								{#if hasAdvancedSettings}
									<section class="mt-5 border-t border-gray-100 pt-3 dark:border-gray-800">
										<button
											type="button"
											class="flex min-h-11 w-full items-center justify-between rounded-xl px-1 text-left text-sm font-medium text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:text-gray-100"
											on:click={() => (showAdvancedSettings = !showAdvancedSettings)}
											aria-expanded={showAdvancedSettings}
											aria-controls="image-advanced-settings"
										>
											<span>{$i18n.t('Advanced')}</span>
											<span class="text-gray-400" aria-hidden="true"
												>{showAdvancedSettings ? '−' : '+'}</span
											>
										</button>

										{#if showAdvancedSettings}
											<div
												id="image-advanced-settings"
												class="mt-2 grid min-w-0 gap-4 sm:grid-cols-2"
											>
												{#if outputFormatOptions.length > 0}
													<div class="min-w-0 sm:col-span-2">
														<div
															class="mb-1.5 text-xs font-medium text-gray-600 dark:text-gray-300"
														>
															{$i18n.t('Output Format')}
														</div>
														<div class="grid grid-cols-3 gap-1.5">
															{#each outputFormatOptions as format}
																<button
																	type="button"
																	class="min-h-11 rounded-xl border text-sm uppercase transition {selectedOutputFormat ===
																	format
																		? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
																		: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300 dark:hover:bg-gray-850'}"
																	on:click={() => (selectedOutputFormat = format)}
																	aria-pressed={selectedOutputFormat === format}
																>
																	{format}
																</button>
															{/each}
														</div>
													</div>
												{/if}

												{#if seedField}
													<label
														class="min-w-0 text-xs font-medium text-gray-600 dark:text-gray-300"
													>
														<span class="flex justify-between gap-2"
															><span>{$i18n.t('Seed')}</span><span class="font-normal text-gray-400"
																>{advancedRangeLabel(seedField)}</span
															></span
														>
														<input
															type="text"
															inputmode="numeric"
															value={seedInput}
															on:input={(event) => (seedInput = event.currentTarget.value)}
															placeholder={$i18n.t('Model default')}
															aria-invalid={Boolean(getAdvancedNumberError(seedInput, seedField))}
															class="mt-1 min-h-11 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
														/>
														{#if getAdvancedNumberError(seedInput, seedField)}<span
																class="mt-1 block font-normal text-red-600 dark:text-red-400"
																>{getAdvancedNumberError(seedInput, seedField)}</span
															>{/if}
													</label>
												{/if}

												{#if stepsField}
													<label
														class="min-w-0 text-xs font-medium text-gray-600 dark:text-gray-300"
													>
														<span class="flex justify-between gap-2"
															><span>{$i18n.t('Steps')}</span><span
																class="font-normal text-gray-400"
																>{advancedRangeLabel(stepsField)}</span
															></span
														>
														<input
															type="text"
															inputmode="numeric"
															value={stepsInput}
															on:input={(event) => (stepsInput = event.currentTarget.value)}
															placeholder={$i18n.t('Model default')}
															aria-invalid={Boolean(getAdvancedNumberError(stepsInput, stepsField))}
															class="mt-1 min-h-11 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
														/>
														{#if getAdvancedNumberError(stepsInput, stepsField)}<span
																class="mt-1 block font-normal text-red-600 dark:text-red-400"
																>{getAdvancedNumberError(stepsInput, stepsField)}</span
															>{/if}
													</label>
												{/if}

												{#if guidanceScaleField}
													<label
														class="min-w-0 text-xs font-medium text-gray-600 dark:text-gray-300"
													>
														<span class="flex justify-between gap-2"
															><span>{$i18n.t('Guidance scale')}</span><span
																class="font-normal text-gray-400"
																>{advancedRangeLabel(guidanceScaleField)}</span
															></span
														>
														<input
															type="text"
															inputmode="decimal"
															value={guidanceScaleInput}
															on:input={(event) => (guidanceScaleInput = event.currentTarget.value)}
															placeholder={$i18n.t('Model default')}
															aria-invalid={Boolean(
																getAdvancedNumberError(guidanceScaleInput, guidanceScaleField)
															)}
															class="mt-1 min-h-11 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
														/>
														{#if getAdvancedNumberError(guidanceScaleInput, guidanceScaleField)}<span
																class="mt-1 block font-normal text-red-600 dark:text-red-400"
																>{getAdvancedNumberError(
																	guidanceScaleInput,
																	guidanceScaleField
																)}</span
															>{/if}
													</label>
												{/if}

												{#if strengthField}
													<label
														class="min-w-0 text-xs font-medium text-gray-600 dark:text-gray-300"
													>
														<span class="flex justify-between gap-2"
															><span>{$i18n.t('Strength')}</span><span
																class="font-normal text-gray-400"
																>{advancedRangeLabel(strengthField)}</span
															></span
														>
														<input
															type="text"
															inputmode="decimal"
															value={strengthInput}
															on:input={(event) => (strengthInput = event.currentTarget.value)}
															placeholder={$i18n.t('Model default')}
															aria-invalid={Boolean(
																getAdvancedNumberError(strengthInput, strengthField)
															)}
															class="mt-1 min-h-11 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm tabular-nums outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
														/>
														{#if getAdvancedNumberError(strengthInput, strengthField)}<span
																class="mt-1 block font-normal text-red-600 dark:text-red-400"
																>{getAdvancedNumberError(strengthInput, strengthField)}</span
															>{/if}
													</label>
												{/if}

												{#if negativePromptField}
													<label
														class="min-w-0 text-xs font-medium text-gray-600 sm:col-span-2 dark:text-gray-300"
													>
														<span>{$i18n.t('Negative Prompt')}</span>
														<textarea
															bind:value={negativePrompt}
															rows="3"
															class="mt-1 w-full resize-y rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm font-normal text-gray-900 outline-none focus:border-gray-400 dark:border-gray-700 dark:text-gray-100"
															placeholder={$i18n.t('Describe what should not appear')}
															aria-label={$i18n.t('Negative Prompt')}
														></textarea>
													</label>
												{/if}
											</div>
										{/if}
									</section>
								{/if}
							</div>
						</Dropdown>
						<!-- 标签选择入口在参数按钮右侧：点击标签即插入实际文本 -->
						<PromptTagPicker
							mediaKind="image"
							modelId={selectedModel || null}
							negativeSupported={Boolean(negativePromptField)}
							on:insert={handlePromptTagInsert}
						/>
					</div>

					<div class="flex min-w-0 items-center justify-between gap-2 sm:justify-end">
						<ImageCreditQuoteBadge quoteState={imageQuoteState} />
						<GenerationSubmitButton
							{loading}
							disabled={!prompt.trim() ||
								!isImageQuoteSubmittable(imageQuoteState) ||
								(useCustomSize && Boolean(customSizeError)) ||
								advancedSettingsInvalid ||
								loading}
							label={referenceImages.length > 0 ? $i18n.t('Edit Image') : $i18n.t('Generate')}
						/>
					</div>
				</div>
			</div>
		</form>
	</div>
</div>
