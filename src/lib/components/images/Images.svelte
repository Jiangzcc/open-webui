<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { quoteImageCredits, type ImageQuoteInput } from '$lib/apis/credits';
	import {
		createImageGeneration,
		editImageGeneration,
		getImageGenerationErrorCode
	} from '$lib/apis/images/generation';
	import ImageCreditQuoteBadge from '$lib/components/credits/ImageCreditQuoteBadge.svelte';
	import {
		createImageQuoteState,
		createImageSubmissionIdempotency,
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';

	import { getImageGenerationModels } from '$lib/apis/images';
	import { config, mobile, showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import {
		buildImageEditPayload,
		buildImageGenerationPayload,
		canUseImagesPage,
		DEFAULT_IMAGE_ASPECT_RATIO,
		filterImageFiles,
		getImageModelCapability,
		normalizeImageGenerationModels,
		normalizeImageResults,
		validateImagePrompt,
		type GeneratedImage,
		type ImageAspectRatio,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';

	import Image from '$lib/components/common/Image.svelte';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	const MAX_REFERENCE_IMAGES = 4;
	const MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024;
	const CREDIT_QUOTE_PLACEHOLDER_PROMPT = 'credit-quote';

	type ReferenceImage = {
		url: string;
		name: string;
	};

	let loaded = false;
	let loading = false;
	let modelsLoading = false;
	let modelsLoaded = false;
	let draggedOver = false;
	let showAspectRatioPicker = false;
	let showModelSelector = false;

	let prompt = '';
	let selectedAspectRatio: ImageAspectRatio = DEFAULT_IMAGE_ASPECT_RATIO;
	let selectedModel = '';
	let selectedResolution = '';
	let imageCount = 1;
	let negativePrompt = '';
	let steps: number | null = null;
	let imageQuoteState: ImageQuoteState = { status: 'loading' };
	let quoteInput: ImageQuoteInput | null = null;

	let models: ImageGenerationModel[] = [];
	let referenceImages: ReferenceImage[] = [];
	let generatedImages: GeneratedImage[] = [];
	let showImagePreview = false;
	let previewImageUrl = '';
	let previewImageAlt = '';

	let promptTextareaElement: HTMLTextAreaElement;
	let fileInputElement: HTMLInputElement;
	let modelSelectorElement: HTMLDivElement;
	let imageOptionsElement: HTMLDivElement;

	$: canUseImages = canUseImagesPage($config, $user);
	$: modeLabel = referenceImages.length > 0 ? $i18n.t('Image to Image') : $i18n.t('Text to Image');
	$: selectedModelConfig =
		models.find((model) => model.id === selectedModel) ??
		(selectedModel === '' ? (models.find((model) => model.isDefault) ?? models[0] ?? null) : null);
	$: selectedModelCapability = getImageModelCapability(
		selectedModelConfig ?? (selectedModel || null)
	);
	$: aspectRatioOptions = selectedModelCapability.aspectRatios;
	$: resolutionOptions = selectedModelCapability.resolutions;
	$: imageCountOptions = selectedModelCapability.imageCounts;
	$: hasImageSizingOptions = aspectRatioOptions.length > 0 || resolutionOptions.length > 0;
	$: selectedImageSizeLabel = hasImageSizingOptions
		? aspectRatioOptions.length > 0
			? getAspectRatioLabel(selectedAspectRatio)
			: selectedResolution
				? getResolutionLabel(selectedResolution)
				: $i18n.t('Resolution')
		: $i18n.t('Quantity');
	$: selectedModelLabel = modelsLoading
		? $i18n.t('Loading...')
		: selectedModelConfig
			? getImageModelDisplayName(selectedModelConfig)
			: $i18n.t('Default Model');
	$: quoteInput = buildImageQuoteInput(
		selectedAspectRatio,
		selectedResolution,
		selectedModelConfig ?? selectedModel,
		imageCount,
		steps,
		negativePrompt,
		referenceImages
	);
	$: if (loaded && quoteInput) {
		imageQuoteStateMachine.schedule(quoteInput);
	}
	$: availableModels =
		referenceImages.length > 0
			? models.filter((model) => model.task !== 'text-to-image')
			: models.filter((model) => model.task !== 'image-to-image');
	$: if (loaded && selectedModelConfig?.task === 'text-to-image' && referenceImages.length > 0) {
		const editModel = selectedModelConfig.editModel ?? `${selectedModelConfig.id}/edit`;
		selectModel(models.some((model) => model.id === editModel) ? editModel : '');
	}
	$: if (loaded && selectedModelConfig?.task === 'image-to-image' && referenceImages.length === 0) {
		selectModel(selectedModelConfig.generationModel ?? '');
	}
	$: if (loaded && canUseImages && !modelsLoaded && !modelsLoading) {
		void loadModels();
	}
	$: if (
		loaded &&
		aspectRatioOptions.length > 0 &&
		!aspectRatioOptions.includes(selectedAspectRatio)
	) {
		selectedAspectRatio = selectedModelCapability.defaultAspectRatio;
	}
	$: if (loaded && selectedResolution && !resolutionOptions.includes(selectedResolution)) {
		selectedResolution = selectedModelCapability.defaultResolution ?? '';
	}
	$: if (
		loaded &&
		imageCountOptions.length > 0 &&
		!imageCountOptions.includes(Number(imageCount))
	) {
		imageCount = imageCountOptions[0];
	}

	const buildImageQuoteInput = (
		aspectRatio: ImageAspectRatio,
		resolution: string,
		model: ImageGenerationModel | string | null,
		count: number,
		stepCount: number | null,
		negative: string,
		references: ReferenceImage[]
	): ImageQuoteInput | null => {
		const commonPayload = {
			prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT,
			aspectRatio,
			resolution,
			model,
			n: count,
			steps: stepCount,
			negative_prompt: negative
		};
		const payload =
			references.length > 0
				? buildImageEditPayload({
						...commonPayload,
						referenceImages: references.map((image) => image.url)
					})
				: buildImageGenerationPayload(commonPayload);
		const {
			model: resourceId,
			prompt: normalizedPrompt,
			image,
			n,
			size,
			resolution: normalizedResolution,
			aspect_ratio
		} = payload;

		if (!resourceId) {
			return null;
		}

		return {
			resource_id: resourceId,
			action: references.length > 0 ? 'image-to-image' : 'text-to-image',
			prompt: normalizedPrompt,
			...(image ? { image } : {}),
			dimensions: {
				...(size ? { size } : {}),
				...(normalizedResolution ? { resolution: normalizedResolution } : {}),
				...(aspect_ratio ? { aspect_ratio } : {}),
				image_count: n ?? 1
			}
		};
	};

	const imageQuoteStateMachine = createImageQuoteState({
		quote: (input, signal) => quoteImageCredits(localStorage.token, input, signal),
		onChange: (state) => {
			imageQuoteState = state;
		}
	});

	const imageGenerationErrorMessage = (error: unknown) => {
		switch (getImageGenerationErrorCode(error)) {
			case 'insufficient_credits':
				return $i18n.t('credits.insufficient');
			case 'price_not_configured':
			case 'price_rule_incomplete':
				return $i18n.t('credits.unconfigured');
			default:
				return $i18n.t('credits.unavailable');
		}
	};

	const getAspectRatioLabel = (ratio: ImageAspectRatio) => {
		return ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio;
	};

	const getResolutionLabel = (resolution: string) => {
		return resolution === 'auto' ? $i18n.t('Auto') : resolution;
	};

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

	const getGeneratedBatchLayoutClass = (imageCount: number) => {
		if (imageCount === 1) {
			return 'flex justify-center';
		}

		if (imageCount === 2) {
			return 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-3 md:gap-4';
		}

		return 'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 md:gap-4';
	};

	const getGeneratedImageCardClass = (imageCount: number) => {
		if (imageCount === 1) {
			return 'w-full max-w-5xl';
		}

		return 'w-full';
	};

	const getGeneratedImageFrameClass = (imageCount: number) => {
		const baseClass = 'relative w-full bg-gray-50 dark:bg-gray-900 overflow-hidden text-left';

		if (imageCount === 1) {
			return `${baseClass} flex h-[calc(100dvh-24rem)] min-h-[16rem] max-h-[36rem] items-center justify-center`;
		}

		return `${baseClass} block aspect-square`;
	};

	const getGeneratedImageClass = (imageCount: number) => {
		if (imageCount <= 1) {
			return 'h-full w-full object-cover transition duration-300 group-hover:scale-[1.01]';
		}

		return 'h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]';
	};

	const getImageModelDisplayName = (model: ImageGenerationModel) => {
		const name = model.name?.trim() || model.id;
		const separatorIndex = name.indexOf(' / ');

		return separatorIndex === -1 ? name : name.slice(separatorIndex + 3);
	};

	const resizePromptTextarea = () => {
		if (promptTextareaElement) {
			promptTextareaElement.style.height = '';
			promptTextareaElement.style.height = Math.min(promptTextareaElement.scrollHeight, 180) + 'px';
		}
	};

	const loadModels = async () => {
		modelsLoading = true;
		modelsLoaded = true;

		const result = await getImageGenerationModels(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return [];
		});

		models = normalizeImageGenerationModels(result);
		if (!selectedModel) {
			const defaultModel = models.find((model) => model.isDefault) ?? models[0];
			if (defaultModel) {
				selectedAspectRatio = getImageModelCapability(defaultModel).defaultAspectRatio;
				selectedResolution = getImageModelCapability(defaultModel).defaultResolution ?? '';
			}
		}
		modelsLoading = false;
	};

	const readFileAsDataUrl = (file: File) => {
		return new Promise<string>((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = (event) => {
				if (typeof event.target?.result === 'string') {
					resolve(event.target.result);
					return;
				}

				reject(new Error('Invalid file content'));
			};
			reader.onerror = () => reject(reader.error ?? new Error('Failed to read file'));
			reader.readAsDataURL(file);
		});
	};

	const addFiles = async (files: File[]) => {
		const remainingSlots = Math.max(MAX_REFERENCE_IMAGES - referenceImages.length, 0);
		const { accepted, rejected } = filterImageFiles(files, {
			maxCount: remainingSlots,
			maxBytes: MAX_REFERENCE_IMAGE_BYTES
		});

		if (rejected.some((item) => item.reason === 'unsupported_type')) {
			toast.error($i18n.t('Only image files are supported.'));
		}
		if (rejected.some((item) => item.reason === 'too_large')) {
			toast.error($i18n.t('Images must be smaller than 10 MB.'));
		}
		if (rejected.some((item) => item.reason === 'too_many')) {
			toast.error(
				$i18n.t('You can attach up to {{count}} reference images.', { count: MAX_REFERENCE_IMAGES })
			);
		}

		if (accepted.length === 0) {
			return;
		}

		try {
			const uploadedImages = await Promise.all(
				accepted.map(async (file) => ({
					url: await readFileAsDataUrl(file as File),
					name: file.name || $i18n.t('Reference image')
				}))
			);

			referenceImages = [...referenceImages, ...uploadedImages];
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	const handleFileUpload = async (event: Event) => {
		const input = event.target as HTMLInputElement;

		if (input.files) {
			await addFiles(Array.from(input.files));
			input.value = '';
		}
	};

	const handleDrop = async (event: DragEvent) => {
		event.preventDefault();
		draggedOver = false;

		if (event.dataTransfer?.files) {
			await addFiles(Array.from(event.dataTransfer.files));
		}
	};

	const removeImage = (index: number) => {
		referenceImages = referenceImages.filter((_, imageIndex) => imageIndex !== index);
	};

	const selectAspectRatio = (ratio: ImageAspectRatio) => {
		selectedAspectRatio = ratio;
	};

	const selectModel = (model: string) => {
		selectedModel = model;
		showModelSelector = false;
		const selectedConfig =
			models.find((item) => item.id === model) ??
			(model === '' ? models.find((item) => item.isDefault) : undefined);
		const capability = getImageModelCapability(selectedConfig ?? model);
		selectedAspectRatio = capability.defaultAspectRatio;
		selectedResolution = capability.defaultResolution ?? '';
		imageCount = capability.imageCounts[0] ?? 1;
	};

	const selectResolution = (resolution: string) => {
		selectedResolution = resolution;
	};

	const toggleAspectRatioPicker = () => {
		showAspectRatioPicker = !showAspectRatioPicker;
		showModelSelector = false;
	};

	const toggleModelSelector = () => {
		showModelSelector = !showModelSelector;
		showAspectRatioPicker = false;
	};

	const openImagePreview = (image: GeneratedImage) => {
		previewImageUrl = image.url;
		previewImageAlt = image.prompt ?? $i18n.t('Generated image');
		showImagePreview = true;
		showAspectRatioPicker = false;
		showModelSelector = false;
	};

	const downloadImage = async (image: GeneratedImage, index: number) => {
		try {
			const response = await fetch(image.url);
			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			const anchor = document.createElement('a');
			anchor.href = blobUrl;
			anchor.download = `generated-image-${image.createdAt ?? Date.now()}-${index + 1}.png`;
			anchor.click();
			URL.revokeObjectURL(blobUrl);
		} catch {
			toast.error($i18n.t('Failed to download image'));
		}
	};

	const handleWindowPointerDown = (event: PointerEvent) => {
		const target = event.target as Node;

		if (showModelSelector && modelSelectorElement && !modelSelectorElement.contains(target)) {
			showModelSelector = false;
		}

		if (showAspectRatioPicker && imageOptionsElement && !imageOptionsElement.contains(target)) {
			showAspectRatioPicker = false;
		}
	};

	const submitHandler = async () => {
		const validation = validateImagePrompt(prompt);
		if (!validation.ok) {
			toast.error($i18n.t('Please enter a prompt'));
			return;
		}
		if (!isImageQuoteSubmittable(imageQuoteState)) {
			return;
		}

		loading = true;
		showAspectRatioPicker = false;
		showModelSelector = false;

		try {
			const commonPayload = {
				prompt: validation.prompt,
				aspectRatio: selectedAspectRatio,
				resolution: selectedResolution,
				model: selectedModelConfig ?? selectedModel,
				n: imageCount,
				steps,
				negative_prompt: negativePrompt
			};
			const payload =
				referenceImages.length > 0
					? buildImageEditPayload({
							...commonPayload,
							referenceImages: referenceImages.map((image) => image.url)
						})
					: buildImageGenerationPayload(commonPayload);
			const submission = createImageSubmissionIdempotency(uuidv4);
			const result =
				referenceImages.length > 0
					? await submission.run((idempotencyKey) =>
							editImageGeneration(localStorage.token, payload, { idempotencyKey })
						)
					: await submission.run((idempotencyKey) =>
							createImageGeneration(localStorage.token, payload, { idempotencyKey })
						);

			const images = normalizeImageResults(result).map((image) => ({
				...image,
				prompt: validation.prompt,
				aspectRatio: selectedAspectRatio,
				createdAt: Date.now()
			}));

			if (images.length === 0) {
				toast.error($i18n.t('No images were returned.'));
				return;
			}

			generatedImages = [...images, ...generatedImages];
			referenceImages = [];
			prompt = '';
			await tick();
			resizePromptTextarea();
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				toast.error(imageGenerationErrorMessage(error));
			}
		} finally {
			loading = false;
		}
	};

	onMount(async () => {
		loaded = true;
		await tick();
		resizePromptTextarea();
	});

	onDestroy(() => {
		imageQuoteStateMachine.dispose();
	});
</script>

<svelte:window on:pointerdown={handleWindowPointerDown} />

<svelte:head>
	<title>{$i18n.t('Images')} • {$WEBUI_NAME}</title>
</svelte:head>

{#if loaded}
	<div
		class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-var(--sidebar-width))]'
			: ''} max-w-full"
	>
		{#if $mobile}
			<nav class="relative z-40 px-3 pt-2 pb-2 backdrop-blur-xl drag-region select-none shrink-0">
				<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							id="sidebar-toggle-button"
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							on:click={() => showSidebar.set(!$showSidebar)}
							type="button"
						>
							<div class="self-center p-1.5">
								<SidebarIcon />
							</div>
						</button>
					</Tooltip>
				</div>
			</nav>
		{/if}

		{#if canUseImages}
			<div class="flex-1 min-h-0 overflow-y-auto px-3 md:px-6">
				<div class="mx-auto max-w-6xl min-h-full flex flex-col">
					<div class="flex-1">
						{#if generatedImages.length === 0}
							<section class="min-h-[calc(100dvh-20rem)] flex items-center justify-center py-12">
								<div class="text-center px-4">
									<div
										class="mx-auto mb-5 size-16 rounded-[1.5rem] bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-200 flex items-center justify-center"
									>
										<Sparkles className="size-7" strokeWidth="1.75" />
									</div>
									<h1
										class="text-3xl md:text-4xl font-semibold tracking-tight text-gray-900 dark:text-gray-100"
									>
										{$i18n.t('What do you want to create?')}
									</h1>
									<p class="mt-3 text-base text-gray-500 dark:text-gray-400">
										{$i18n.t(
											'Describe an image, or upload a reference image to create a new version.'
										)}
									</p>
								</div>
							</section>
						{:else}
							<section class="mt-4">
								<div class={getGeneratedBatchLayoutClass(generatedImages.length)}>
									{#each generatedImages as image, index (`${image.url}-${index}`)}
										<div
											class="group rounded-3xl overflow-hidden border border-gray-100 dark:border-gray-850 bg-white dark:bg-gray-900/60 shadow-sm {getGeneratedImageCardClass(
												generatedImages.length
											)}"
										>
											<button
												type="button"
												class={getGeneratedImageFrameClass(generatedImages.length)}
												on:click={() => openImagePreview(image)}
												aria-label={$i18n.t('Preview generated image')}
											>
												<img
													src={image.url}
													alt={image.prompt ?? $i18n.t('Generated image')}
													class={getGeneratedImageClass(generatedImages.length)}
												/>
												<div
													class="absolute inset-x-3 bottom-3 flex justify-end opacity-0 transition group-hover:opacity-100"
												>
													<span
														class="rounded-full bg-white/90 px-3 py-1 text-xs font-medium text-gray-800 shadow-sm backdrop-blur dark:bg-gray-950/90 dark:text-gray-100"
													>
														{$i18n.t('Preview')}
													</span>
												</div>
											</button>
											<div class="px-3 py-2.5">
												<div
													class="text-xs text-gray-500 dark:text-gray-400 flex justify-between gap-2"
												>
													<span>
														{image.aspectRatio
															? getAspectRatioLabel(image.aspectRatio)
															: $i18n.t('Smart')}
													</span>
													<span>{modeLabel}</span>
												</div>
												{#if image.prompt}
													<div class="mt-1 text-sm text-gray-800 dark:text-gray-200 line-clamp-2">
														{image.prompt}
													</div>
												{/if}
												<div class="mt-2 flex items-center justify-end gap-2">
													<button
														type="button"
														class="rounded-full px-3 py-1 text-xs font-medium text-gray-600 transition hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-850 dark:hover:text-gray-100"
														on:click={() => openImagePreview(image)}
													>
														{$i18n.t('Preview')}
													</button>
													<button
														type="button"
														class="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-200 dark:bg-gray-850 dark:text-gray-200 dark:hover:bg-gray-800"
														on:click={() => downloadImage(image, index)}
													>
														{$i18n.t('Download')}
													</button>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</section>
						{/if}
					</div>

					<div
						class="sticky bottom-0 z-20 -mx-3 md:-mx-6 px-3 md:px-6 pt-10 pb-3 bg-gradient-to-t from-white via-white/95 to-white/0 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0"
					>
						<div class="mx-auto w-full max-w-[42rem]">
							<form
								class="relative rounded-[1.5rem] border border-gray-100/90 bg-white/95 shadow-xl shadow-gray-200/50 backdrop-blur-xl dark:border-gray-800/90 dark:bg-gray-950/95 dark:shadow-black/25"
								on:submit|preventDefault={submitHandler}
								on:dragover={(event) => {
									event.preventDefault();
									draggedOver = event.dataTransfer?.types?.includes('Files') ?? false;
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
														class="absolute -right-1.5 -top-1.5 rounded-full bg-white p-0.5 text-gray-900 shadow border border-gray-100 opacity-100 transition dark:border-gray-700 dark:bg-gray-800 dark:text-white md:opacity-0 md:group-hover:opacity-100"
														on:click={() => removeImage(index)}
														aria-label={$i18n.t('Remove image')}
													>
														<XMark className="size-4" strokeWidth="2" />
													</button>
												</div>
											{/each}
										</div>
									{/if}

									<div class="flex gap-4">
										<button
											type="button"
											class="mt-2 flex h-[3.8rem] w-[3.125rem] shrink-0 items-center justify-center rounded-2xl border border-gray-100 bg-gray-50 text-gray-500 transition hover:bg-gray-100 hover:text-gray-800 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850 dark:hover:text-gray-100"
											on:click={() => fileInputElement?.click()}
											aria-label={$i18n.t('Upload reference image')}
										>
											<Plus className="size-6" strokeWidth="1.8" />
										</button>

										<textarea
											bind:this={promptTextareaElement}
											bind:value={prompt}
											class="min-h-20 max-h-44 flex-1 resize-none bg-transparent py-2 text-base text-gray-900 outline-none placeholder:text-gray-400 dark:text-gray-100 dark:placeholder:text-gray-500"
											placeholder={$i18n.t(
												'Upload a reference image, then describe the image you want to create.'
											)}
											on:input={resizePromptTextarea}
											aria-label={$i18n.t('Image prompt')}
										></textarea>
									</div>

									<div class="mt-2 flex h-8 items-center justify-between gap-2">
										<div class="flex min-w-0 items-center gap-2">
											<div
												class="relative inline-flex min-w-0 max-w-[12rem] shrink"
												bind:this={modelSelectorElement}
											>
												<button
													type="button"
													class="inline-flex h-8 min-w-0 max-w-full items-center gap-2 rounded-[10px] bg-black/[0.06] px-2 text-sm font-medium text-gray-700 transition hover:bg-black/[0.1] dark:bg-white/[0.08] dark:text-gray-200 dark:hover:bg-white/[0.12]"
													on:click={toggleModelSelector}
													aria-expanded={showModelSelector}
													aria-haspopup="listbox"
												>
													<Photo className="size-4 shrink-0" strokeWidth="2" />
													<span class="truncate">{selectedModelLabel}</span>
													<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">⌄</span>
												</button>

												{#if showModelSelector}
													<div
														class="fixed inset-x-3 bottom-14 z-50 max-h-[calc(100dvh-5rem)] min-w-0 overflow-y-auto overscroll-contain rounded-2xl border border-gray-100 bg-white p-2 shadow-xl sm:absolute sm:inset-x-auto sm:bottom-10 sm:left-0 sm:z-30 sm:max-h-96 sm:w-80 dark:border-gray-800 dark:bg-gray-900"
														role="listbox"
														aria-label={$i18n.t('Select image model')}
													>
														<button
															type="button"
															class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-850 {selectedModel ===
															''
																? 'bg-gray-50 text-gray-900 dark:bg-gray-850 dark:text-gray-100'
																: 'text-gray-700 dark:text-gray-200'}"
															on:click={() => selectModel('')}
															role="option"
															aria-selected={selectedModel === ''}
														>
															<span>{$i18n.t('Default Model')}</span>
															{#if selectedModel === ''}<span>✓</span>{/if}
														</button>

														{#each availableModels as model}
															<button
																type="button"
																class="flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-850 {selectedModel ===
																model.id
																	? 'bg-gray-50 text-gray-900 dark:bg-gray-850 dark:text-gray-100'
																	: 'text-gray-700 dark:text-gray-200'}"
																on:click={() => selectModel(model.id)}
																role="option"
																aria-selected={selectedModel === model.id}
															>
																<span class="truncate">{model.name ?? model.id}</span>
																{#if selectedModel === model.id}<span>✓</span>{/if}
															</button>
														{/each}
													</div>
												{/if}
											</div>

											<div class="relative" bind:this={imageOptionsElement}>
												<button
													type="button"
													class="inline-flex h-8 min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-[10px] bg-black/[0.06] px-2 text-sm font-medium text-gray-700 transition hover:bg-black/[0.1] sm:gap-4 dark:bg-white/[0.08] dark:text-gray-200 dark:hover:bg-white/[0.12]"
													on:click={toggleAspectRatioPicker}
													aria-expanded={showAspectRatioPicker}
												>
													<span class="truncate">{selectedImageSizeLabel}</span>
													{#if aspectRatioOptions.length > 0 && selectedResolution}
														<span class="hidden truncate min-[360px]:inline">
															{getResolutionLabel(selectedResolution)}
														</span>
													{/if}
													<span class="inline-flex items-center gap-1">
														<Photo className="size-4" strokeWidth="2" />
														{imageCount}
													</span>
												</button>

												{#if showAspectRatioPicker}
													<div
														class="fixed inset-x-3 bottom-14 z-50 max-h-[calc(100dvh-5rem)] min-w-0 overflow-y-auto overscroll-contain rounded-2xl border border-gray-100 bg-white p-3 shadow-xl sm:absolute sm:inset-x-auto sm:bottom-10 sm:left-0 sm:z-30 sm:w-[27rem] sm:max-w-[calc(100vw-2rem)] sm:p-4 dark:border-gray-800 dark:bg-gray-900"
													>
														{#if aspectRatioOptions.length > 0}
															<section>
																<h3
																	class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100"
																>
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
																					class="border border-current/60 {getAspectRatioPreviewClass(
																						ratio
																					)}"
																					style={getAspectRatioPreviewStyle(ratio)}
																				></span>
																			</span>
																			<span class="min-w-0 truncate"
																				>{getAspectRatioLabel(ratio)}</span
																			>
																		</button>
																	{/each}
																</div>
															</section>
														{/if}

														{#if resolutionOptions.length > 0}
															<section class="mt-5">
																<h3
																	class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100"
																>
																	{$i18n.t('Resolution')}
																</h3>
																<div class="grid grid-cols-3 gap-1.5">
																	{#each resolutionOptions as resolution}
																		<button
																			type="button"
																			class="h-9 rounded-xl border text-sm transition {selectedResolution ===
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

														<section class={hasImageSizingOptions ? 'mt-5' : ''}>
															<h3
																class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100"
															>
																{$i18n.t('Quantity')}
															</h3>
															<div class="grid grid-cols-4 gap-1.5">
																{#each imageCountOptions as count}
																	<button
																		type="button"
																		class="h-9 rounded-xl border text-sm transition {Number(
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
													</div>
												{/if}
											</div>
										</div>

										<div class="flex min-w-0 items-center gap-2">
											<ImageCreditQuoteBadge quoteState={imageQuoteState} />
											<button
												type="submit"
												class="flex size-8 items-center justify-center rounded-full transition {prompt.trim() &&
												!loading
													? 'bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100'
													: 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-800 dark:text-gray-500'}"
												disabled={!prompt.trim() ||
													!isImageQuoteSubmittable(imageQuoteState) ||
													loading}
												aria-label={referenceImages.length > 0
													? $i18n.t('Edit Image')
													: $i18n.t('Generate')}
											>
												{#if loading}
													<Spinner className="size-4" />
												{:else}
													<Sparkles className="size-4" strokeWidth="2" />
												{/if}
											</button>
										</div>
									</div>
								</div>
							</form>
						</div>
					</div>
				</div>
			</div>
		{:else}
			<div class="flex-1 flex items-center justify-center px-6">
				<div class="max-w-md text-center">
					<div
						class="mx-auto size-14 rounded-3xl bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-300 flex items-center justify-center mb-4"
					>
						<Photo className="size-6" strokeWidth="2" />
					</div>
					<div class="text-xl font-medium text-gray-900 dark:text-gray-100">
						{$i18n.t('Image generation is not available')}
					</div>
					<div class="mt-2 text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Ask an administrator to enable image generation for your account.')}
					</div>
				</div>
			</div>
		{/if}

		<ImagePreview bind:show={showImagePreview} src={previewImageUrl} alt={previewImageAlt} />
	</div>
{/if}
