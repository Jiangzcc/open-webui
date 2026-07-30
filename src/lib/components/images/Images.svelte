<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { quoteImageCredits, type ImageQuoteInput } from '$lib/apis/credits';
	import { getImageGenerationErrorCode } from '$lib/apis/images/generation';
	import {
		createImageGenerationTask,
		getImageGenerationTask,
		listImageGenerationTasks
	} from '$lib/apis/creations/generation-tasks';
	import ImageCreditQuoteBadge from '$lib/components/credits/ImageCreditQuoteBadge.svelte';
	import {
		createImageQuoteState,
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';

	import { getImageGenerationModels } from '$lib/apis/images';
	import { config, mobile, showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import {
		buildImageEditPayload,
		buildImageGenerationPayload,
		DEFAULT_IMAGE_ASPECT_RATIO,
		filterImageFiles,
		getImageModelCapability,
		getPrimaryImageModels,
		normalizeImageGenerationModels,
		resolveActiveImageModel,
		resolveImageEditModel,
		supportsImageEditing,
		validateImagePrompt,
		type GeneratedImage,
		type ImageAspectRatio,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';
	import {
		buildCreationDraft,
		consumePendingCreationDraft,
		generationElapsedSeconds,
		isGenerationTaskTerminal,
		mergeGenerationTask,
		type ImageCreationDraft,
		type ImageGenerationBatch
	} from '$lib/utils/image-generation-batches';

	import {
		groupByVendor,
		vendorLogoUrl,
		isProxyModel,
		stripVendorFromName
	} from '$lib/utils/images-dropdown';

	import Image from '$lib/components/common/Image.svelte';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import CreationsLibrary from '$lib/components/images/CreationsLibrary.svelte';

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
	let selectedVendor = '';
	let pendingCreationDraft: ImageCreationDraft | null = null;

	let selection: 'generate' | 'mine' | 'all' = 'generate';
	let libraryRevision = 0;

	$: view = selection === 'generate' ? 'generate' : 'library';
	$: libraryScope = selection === 'all' ? 'all' : 'mine';
	$: isAdmin = $user?.role === 'admin';

	let prompt = '';
	let selectedAspectRatio: ImageAspectRatio = DEFAULT_IMAGE_ASPECT_RATIO;
	let selectedModel = '';
	let selectedResolution = '';
	let selectedQuality = '';
	let imageCount = 1;
	let negativePrompt = '';
	let steps: number | null = null;
	let imageQuoteState: ImageQuoteState = { status: 'loading' };
	let quoteInput: ImageQuoteInput | null = null;

	let models: ImageGenerationModel[] = [];
	let referenceImages: ReferenceImage[] = [];
	let generationBatches: ImageGenerationBatch[] = [];
	let elapsedNow = Date.now();
	let taskPollTimer: ReturnType<typeof setInterval> | null = null;
	let elapsedTimer: ReturnType<typeof setInterval> | null = null;
	let pollingTasks = false;
	let showImagePreview = false;
	let previewImageUrl = '';
	let previewImageAlt = '';

	let promptTextareaElement: HTMLTextAreaElement;
	let fileInputElement: HTMLInputElement;
	let modelSelectorElement: HTMLDivElement;
	let imageOptionsElement: HTMLDivElement;

	$: modeLabel = referenceImages.length > 0 ? $i18n.t('Image to Image') : $i18n.t('Text to Image');
	$: selectedModelConfig =
		primaryModels.find((model) => model.id === selectedModel) ??
		(selectedModel === ''
			? (primaryModels.find((model) => model.isDefault) ?? primaryModels[0] ?? null)
			: null);
	$: activeModelConfig = resolveActiveImageModel(
		selectedModelConfig,
		models,
		referenceImages.length > 0
	);
	$: selectedModelSupportsEditing = supportsImageEditing(selectedModelConfig, models);
	// #17:单图派 i2i 模型声明 imageInputMaxCount=1,届时参考图槽位收缩到 1;
	// 其余模型沿用全局上限 4。activeModelConfig 变化时自动跟随。
	$: effectiveMaxReferenceImages =
		resolveImageEditModel(selectedModelConfig, models)?.imageInputMaxCount ??
		selectedModelConfig?.imageInputMaxCount ??
		MAX_REFERENCE_IMAGES;
	// 切到更低容量模型时,若已持有的参考图超过新上限,裁剪多余并提示;
	// slice 后长度不再超标,reaction 自然收敛,toast 只发一次。
	$: if (loaded && referenceImages.length > effectiveMaxReferenceImages) {
		referenceImages = referenceImages.slice(0, effectiveMaxReferenceImages);
		toast.info(
			$i18n.t('Trimmed to {{count}} reference image(s) for this model.', {
				count: effectiveMaxReferenceImages
			})
		);
	}
	$: selectedModelCapability = getImageModelCapability(
		activeModelConfig ?? selectedModelConfig ?? (selectedModel || null)
	);
	$: aspectRatioOptions = selectedModelCapability.aspectRatios;
	$: resolutionOptions = selectedModelCapability.resolutions;
	$: imageCountOptions = selectedModelCapability.imageCounts;
	$: qualityOptions = selectedModelCapability.qualityOptions;
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
		selectedQuality,
		activeModelConfig ?? selectedModelConfig ?? selectedModel,
		imageCount,
		steps,
		negativePrompt,
		referenceImages
	);
	$: if (loaded && quoteInput) {
		imageQuoteStateMachine.schedule(quoteInput);
	}
	$: primaryModels = getPrimaryImageModels(models);
	$: availableModels = primaryModels;

	$: vendorGroups = groupByVendor(availableModels);
	$: vendorList = Object.keys(vendorGroups).sort((a, b) =>
		a === 'other' ? 1 : b === 'other' ? -1 : a.localeCompare(b)
	);
	$: if (selectedVendor === '' && vendorList.length > 0) {
		selectedVendor = vendorList[0];
	}
	$: vendorModels = vendorGroups[selectedVendor] ?? [];

	$: if (loaded && !modelsLoaded && !modelsLoading) {
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
	$: if (loaded && qualityOptions.length > 0 && !qualityOptions.includes(selectedQuality)) {
		selectedQuality = selectedModelCapability.defaultQuality ?? qualityOptions[0];
	}
	$: if (loaded && qualityOptions.length === 0 && selectedQuality) {
		selectedQuality = '';
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
		quality: string,
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
			quality: quality || null,
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
			quality: normalizedQuality,
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
				...(normalizedQuality ? { quality: normalizedQuality } : {}),
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

	const modelBasePrice = (model: ImageGenerationModel) =>
		referenceImages.length > 0 ? resolveImageEditModel(model, models)?.basePrice : model.basePrice;

	const getAspectRatioLabel = (ratio: ImageAspectRatio) => {
		return ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio;
	};

	const getResolutionLabel = (resolution: string) => {
		return resolution === 'auto' ? $i18n.t('Auto') : resolution;
	};

	const getQualityLabel = (quality: string) => {
		switch (quality) {
			case 'auto':
				return $i18n.t('Auto');
			case 'low':
				return $i18n.t('Low');
			case 'medium':
				return $i18n.t('Medium');
			case 'high':
				return $i18n.t('High');
			default:
				return quality;
		}
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

	const getCompletedBatchLayoutClass = () =>
		'flex flex-wrap items-start justify-center gap-3 md:gap-4';

	const getPendingBatchLayoutClass = (imageCount: number) =>
		imageCount === 1 ? 'flex justify-center' : 'grid grid-cols-1 gap-3 sm:grid-cols-2 md:gap-4';

	const getGeneratedImageCardClass = (imageCount: number) => {
		if (imageCount === 1) {
			return 'w-fit max-w-full shrink-0';
		}

		return 'w-fit max-w-full shrink-0 sm:max-w-[calc(50%_-_0.5rem)]';
	};

	const getGeneratedImageFrameClass = () =>
		'relative flex max-w-full items-center justify-center overflow-hidden bg-stone-100 text-left dark:bg-black/30';

	const getGeneratedImageClass = (imageCount: number) =>
		`block h-auto w-auto max-w-full object-contain transition duration-300 group-hover:scale-[1.01] ${
			imageCount === 1 ? 'max-h-[68dvh] sm:max-h-[72dvh]' : 'max-h-[58dvh] sm:max-h-[62dvh]'
		}`;

	const batchAspectStyle = (batch: ImageGenerationBatch) => {
		const ratio = batch.aspectRatio;
		if (/^\d+(\.\d+)?:\d+(\.\d+)?$/.test(ratio)) {
			return `aspect-ratio: ${ratio.replace(':', ' / ')}`;
		}
		const size = batch.resolution.match(/^(\d+)x(\d+)$/);
		return size ? `aspect-ratio: ${size[1]} / ${size[2]}` : 'aspect-ratio: 4 / 3';
	};

	const generationStatusLabel = (batch: ImageGenerationBatch) => {
		if (batch.status === 'queued') return $i18n.t('Queued');
		if (batch.status === 'running') return $i18n.t('Generating');
		if (batch.status === 'failed') return $i18n.t('Generation failed');
		return $i18n.t('Completed');
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
		if (pendingCreationDraft) {
			const draft = pendingCreationDraft;
			pendingCreationDraft = null;
			await tick();
			await applyCreationDraft(draft);
		}
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

	const resolveDraftReferenceImage = async (url: string) => {
		if (url.startsWith('data:') || url.startsWith('http://') || url.startsWith('https://')) {
			return url;
		}
		const response = await fetch(url, {
			headers: { authorization: `Bearer ${localStorage.token}` }
		});
		if (!response.ok) throw new Error('reference image unavailable');
		const blob = await response.blob();
		if (!blob.type.startsWith('image/') || blob.size > MAX_REFERENCE_IMAGE_BYTES) {
			throw new Error('invalid reference image');
		}
		return readFileAsDataUrl(
			new File([blob], 'previous-creation', { type: blob.type || 'image/png' })
		);
	};

	const addFiles = async (files: File[]) => {
		if (!selectedModelSupportsEditing) {
			return;
		}

		const remainingSlots = Math.max(effectiveMaxReferenceImages - referenceImages.length, 0);
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
				$i18n.t('You can attach up to {{count}} reference images.', {
					count: effectiveMaxReferenceImages
				})
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

		if (!selectedModelSupportsEditing) {
			return;
		}

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
		const selectedConfig =
			primaryModels.find((item) => item.id === model) ??
			(model === '' ? primaryModels.find((item) => item.isDefault) : undefined);
		if (referenceImages.length > 0 && !supportsImageEditing(selectedConfig, models)) {
			referenceImages = [];
			toast.info(
				$i18n.t('This model does not support reference images. Uploaded images were removed.')
			);
		}
		selectedModel = model;
		showModelSelector = false;
		const capability = getImageModelCapability(selectedConfig ?? model);
		selectedAspectRatio = capability.defaultAspectRatio;
		selectedResolution = capability.defaultResolution ?? '';
		imageCount = capability.imageCounts[0] ?? 1;
	};

	const selectModelIfEnabled = (model: ImageGenerationModel) => {
		selectModel(model.id);
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

	const selectSelection = async (next: 'generate' | 'mine' | 'all') => {
		selection = next;
		await tick();
		const tabId =
			next === 'generate'
				? 'images-generate-tab'
				: next === 'all'
					? 'images-admin-tab'
					: 'images-library-tab';
		document.getElementById(tabId)?.focus();
	};

	const handleTabKeydown = (event: KeyboardEvent) => {
		if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
			event.preventDefault();
			const order: Array<'generate' | 'mine' | 'all'> = isAdmin
				? ['generate', 'mine', 'all']
				: ['generate', 'mine'];
			const idx = order.indexOf(selection);
			if (idx === -1) return;
			const dir = event.key === 'ArrowRight' ? 1 : -1;
			const nextIdx = (idx + dir + order.length) % order.length;
			void selectSelection(order[nextIdx]);
		}
	};

	const applyCreationDraft = async (draft: ImageCreationDraft) => {
		let referenceImageUrl: string | null = null;
		if (draft.referenceImageUrl) {
			try {
				referenceImageUrl = await resolveDraftReferenceImage(draft.referenceImageUrl);
			} catch {
				toast.error($i18n.t('Failed to load reference image'));
				return;
			}
		}

		let targetModel = primaryModels.find(
			(model) => model.id === draft.modelId || model.editModel === draft.modelId
		);
		if (referenceImageUrl && (!targetModel || !supportsImageEditing(targetModel, models))) {
			targetModel = primaryModels.find((model) => supportsImageEditing(model, models));
		}
		if (targetModel) {
			selectModel(targetModel.id);
			await tick();
		}
		if (draft.aspectRatio && aspectRatioOptions.includes(draft.aspectRatio)) {
			selectedAspectRatio = draft.aspectRatio;
		}
		if (draft.resolution && resolutionOptions.includes(draft.resolution)) {
			selectedResolution = draft.resolution;
		}
		if (draft.quality && qualityOptions.includes(draft.quality)) {
			selectedQuality = draft.quality;
		}
		prompt = draft.prompt;
		referenceImages = referenceImageUrl
			? [{ url: referenceImageUrl, name: $i18n.t('Previous creation') }]
			: [];
		await selectSelection('generate');
		await tick();
		resizePromptTextarea();
		promptTextareaElement?.focus();
		toast.success($i18n.t('Creation settings loaded'));
	};

	const loadRecentGenerationTasks = async () => {
		try {
			const tasks = await listImageGenerationTasks(localStorage.token, 20);
			for (const task of tasks) generationBatches = mergeGenerationTask(generationBatches, task);
		} catch {
			toast.error($i18n.t('Failed to restore generation tasks'));
		}
	};

	const pollGenerationTasks = async () => {
		if (pollingTasks) return;
		const active = generationBatches.filter((batch) => !isGenerationTaskTerminal(batch.status));
		if (active.length === 0) return;
		pollingTasks = true;
		try {
			const previousStatuses = new Map(active.map((batch) => [batch.id, batch.status]));
			const tasks = await Promise.all(
				active.map((batch) => getImageGenerationTask(localStorage.token, batch.id))
			);
			for (const task of tasks) {
				generationBatches = mergeGenerationTask(generationBatches, task);
				if (task.status === 'succeeded' && previousStatuses.get(task.id) !== 'succeeded') {
					libraryRevision += 1;
					toast.success($i18n.t('Image generation completed'));
				}
			}
		} catch {
			// A temporary polling failure must not turn a running server task into a
			// failed UI task. The next interval retries with the same task id.
		} finally {
			pollingTasks = false;
		}
	};

	const reuseBatch = (batch: ImageGenerationBatch) =>
		applyCreationDraft(
			buildCreationDraft({
				prompt: batch.prompt,
				model_id: batch.modelId,
				params: batch.params
			})
		);

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
				quality: selectedQuality || null,
				model: activeModelConfig ?? selectedModelConfig ?? selectedModel,
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
			const task = await createImageGenerationTask(
				localStorage.token,
				referenceImages.length > 0 ? 'image-to-image' : 'text-to-image',
				payload,
				uuidv4()
			);
			generationBatches = mergeGenerationTask(generationBatches, task);
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
		pendingCreationDraft = consumePendingCreationDraft(sessionStorage);
		loaded = true;
		await loadRecentGenerationTasks();
		taskPollTimer = setInterval(() => void pollGenerationTasks(), 2_000);
		elapsedTimer = setInterval(() => (elapsedNow = Date.now()), 1_000);
		await tick();
		resizePromptTextarea();
	});

	onDestroy(() => {
		imageQuoteStateMachine.dispose();
		if (taskPollTimer) clearInterval(taskPollTimer);
		if (elapsedTimer) clearInterval(elapsedTimer);
	});
</script>

<svelte:window on:pointerdown={handleWindowPointerDown} />

<svelte:head>
	<title>{$i18n.t('Images')} • {$WEBUI_NAME}</title>
</svelte:head>

{#if loaded}
	<div
		class="relative flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
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

		<!-- Floating tab switcher: lifted out of the flow so the panels beneath reclaim the height -->
		<div
			class="pointer-events-none absolute inset-x-0 top-14 z-30 flex justify-center px-3 sm:top-0 sm:pt-2"
			role="tablist"
			aria-label={$i18n.t('Images')}
			on:keydown={handleTabKeydown}
		>
			<div
				class="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-gray-200/80 bg-white/80 p-1 shadow-lg shadow-black/10 backdrop-blur-xl dark:border-gray-700/80 dark:bg-gray-900/80 dark:shadow-black/30"
			>
				<button
					id="images-generate-tab"
					type="button"
					role="tab"
					aria-selected={selection === 'generate'}
					aria-controls="images-generate-panel"
					tabindex={selection === 'generate' ? 0 : -1}
					class="min-h-10 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
					'generate'
						? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
						: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
					on:click={() => selectSelection('generate')}
				>
					{$i18n.t('Create art')}
				</button>
				<button
					id="images-library-tab"
					type="button"
					role="tab"
					aria-selected={selection === 'mine'}
					aria-controls="images-library-panel"
					tabindex={selection === 'mine' ? 0 : -1}
					class="min-h-10 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
					'mine'
						? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
						: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
					on:click={() => selectSelection('mine')}
				>
					{$i18n.t('My creations')}
				</button>
				{#if isAdmin}
					<button
						id="images-admin-tab"
						type="button"
						role="tab"
						aria-selected={selection === 'all'}
						aria-controls="images-library-panel"
						tabindex={selection === 'all' ? 0 : -1}
						class="min-h-10 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
						'all'
							? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
							: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
						on:click={() => selectSelection('all')}
					>
						{$i18n.t('All creations')}
					</button>
				{/if}
			</div>
		</div>

		<div
			id="images-generate-panel"
			role="tabpanel"
			aria-labelledby="images-generate-tab"
			class="flex-1 min-h-0 overflow-y-auto px-3 md:px-6"
			hidden={view !== 'generate'}
		>
			<div class="mx-auto max-w-6xl min-h-full flex flex-col">
				<div class="flex-1">
					{#if generationBatches.length === 0}
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
						<section class="space-y-6 pb-6 pt-18 sm:pt-18" aria-live="polite">
							{#each generationBatches as batch (batch.id)}
								<article
									class="overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm dark:border-gray-850 dark:bg-gray-900/60"
								>
									<header
										class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
									>
										<div class="min-w-0">
											<p class="line-clamp-1 text-sm font-medium text-gray-900 dark:text-gray-100">
												{batch.prompt}
											</p>
											<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
												{batch.modelId ?? $i18n.t('Default Model')} · {getAspectRatioLabel(
													batch.aspectRatio
												)} · {batch.expectedCount}
											</p>
										</div>
										<div class="flex shrink-0 items-center gap-2 text-xs">
											<span
												class="inline-flex min-h-8 items-center gap-2 rounded-full px-3 {batch.status ===
												'failed'
													? 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300'
													: batch.status === 'succeeded'
														? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
														: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'}"
											>
												{#if !isGenerationTaskTerminal(batch.status)}
													<Spinner className="size-3.5" />
												{/if}
												{generationStatusLabel(batch)}
												{#if !isGenerationTaskTerminal(batch.status)}
													· {generationElapsedSeconds(batch, elapsedNow)}s
												{/if}
											</span>
											<button
												type="button"
												class="min-h-8 rounded-full px-3 font-medium text-gray-600 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
												on:click={() => reuseBatch(batch)}
											>
												{$i18n.t('Create again')}
											</button>
										</div>
									</header>

									<div class="px-3 pb-3 sm:px-4 sm:pb-4">
										<div
											class={batch.status === 'succeeded' && batch.images.length > 0
												? getCompletedBatchLayoutClass()
												: getPendingBatchLayoutClass(batch.expectedCount)}
										>
											{#if batch.status === 'succeeded' && batch.images.length > 0}
												{#each batch.images as image, index (`${image.url}-${index}`)}
													<div
														class="group overflow-hidden rounded-2xl border border-gray-100 dark:border-gray-800 {getGeneratedImageCardClass(
															batch.images.length
														)}"
													>
														<button
															type="button"
															class={getGeneratedImageFrameClass()}
															on:click={() => openImagePreview(image)}
															aria-label={$i18n.t('Preview generated image')}
														>
															<img
																src={image.url}
																alt={image.prompt ?? $i18n.t('Generated image')}
																class={getGeneratedImageClass(batch.images.length)}
															/>
														</button>
														<div class="flex items-center justify-end gap-1 px-2 py-2">
															<button
																type="button"
																class="min-h-9 rounded-full px-3 text-xs text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
																on:click={() => openImagePreview(image)}
																>{$i18n.t('Preview')}</button
															>
															<button
																type="button"
																class="min-h-9 rounded-full px-3 text-xs font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
																on:click={() => downloadImage(image, index)}
																>{$i18n.t('Download')}</button
															>
														</div>
													</div>
												{/each}
											{:else if batch.status === 'failed'}
												<div
													class="col-span-full flex min-h-44 flex-col items-center justify-center rounded-2xl border border-dashed border-red-200 bg-red-50/40 px-5 text-center dark:border-red-900/60 dark:bg-red-950/20"
													style={batchAspectStyle(batch)}
												>
													<p class="text-sm font-medium text-red-600 dark:text-red-300">
														{$i18n.t('Generation failed')}
													</p>
													{#if batch.errorCode}<p class="mt-1 text-xs text-red-500/80">
															{batch.errorCode}
														</p>{/if}
													<button
														type="button"
														class="mt-3 min-h-11 rounded-full bg-gray-950 px-4 text-sm font-medium text-white dark:bg-white dark:text-gray-950"
														on:click={() => reuseBatch(batch)}>{$i18n.t('Load settings')}</button
													>
												</div>
											{:else}
												{#each Array(batch.expectedCount) as _, index (index)}
													<div
														class="relative min-h-48 overflow-hidden rounded-2xl bg-stone-100 dark:bg-gray-800"
														style={batchAspectStyle(batch)}
													>
														<div
															class="absolute inset-0 animate-pulse bg-gradient-to-br from-transparent via-white/45 to-transparent dark:via-white/5"
														></div>
														<div
															class="absolute inset-0 flex items-center justify-center text-xs text-gray-400 dark:text-gray-500"
														>
															{$i18n.t('Creating image {{index}}', { index: index + 1 })}
														</div>
													</div>
												{/each}
											{/if}
										</div>
									</div>
								</article>
							{/each}
						</section>
					{/if}
				</div>

				<div
					class="sticky bottom-0 z-20 -mx-3 md:-mx-6 px-3 md:px-6 pt-10 pb-3 bg-gradient-to-t from-white via-white/95 to-white/0 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0"
				>
					<div class="mx-auto w-full sm:max-w-[40rem] lg:max-w-[52rem] xl:max-w-[60rem]">
						<form
							class="relative rounded-[1.5rem] border border-gray-100/90 bg-white/95 shadow-xl shadow-gray-200/50 backdrop-blur-xl dark:border-gray-800/90 dark:bg-gray-950/95 dark:shadow-black/25"
							on:submit|preventDefault={submitHandler}
							on:dragover={(event) => {
								event.preventDefault();
								draggedOver =
									selectedModelSupportsEditing &&
									(event.dataTransfer?.types?.includes('Files') ?? false);
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
								<div
									class="relative mb-3 inline-flex min-w-0 max-w-[12rem] shrink"
									bind:this={modelSelectorElement}
								>
									<button
										type="button"
										class="inline-flex h-8 min-w-0 max-w-full items-center gap-2 rounded-[10px] bg-black/[0.06] px-2 text-sm font-medium text-gray-700 transition hover:bg-black/[0.1] dark:bg-white/[0.08] dark:text-gray-200 dark:hover:bg-white/[0.12]"
										on:click={toggleModelSelector}
										aria-expanded={showModelSelector}
										aria-haspopup="listbox"
									>
										{#if selectedModelConfig?.provider}
											<img
												src={vendorLogoUrl(selectedModelConfig.provider)}
												alt=""
												class="size-4 shrink-0 rounded-sm"
												loading="lazy"
												decoding="async"
											/>
										{:else}
											<Photo className="size-4 shrink-0" strokeWidth="2" />
										{/if}
										<span class="truncate">{selectedModelLabel}</span>
										<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">⌄</span>
									</button>

									{#if showModelSelector}
										<div
											class="fixed inset-x-3 bottom-14 z-50 max-h-[60dvh] min-w-0 overflow-y-auto overscroll-contain rounded-2xl border border-gray-100 bg-white p-2 shadow-xl sm:absolute sm:inset-x-auto sm:bottom-10 sm:left-0 sm:z-30 sm:h-80 sm:w-[30rem] sm:p-2 dark:border-gray-800 dark:bg-gray-900"
											role="listbox"
											aria-label={$i18n.t('Select image model')}
										>
											<div class="flex h-full gap-2 sm:min-w-[22rem] sm:flex-row flex-col">
												<!-- Brand level (left/top) -->
												<ul
													class="flex shrink-0 snap-x snap-mandatory gap-1 overflow-x-auto pb-1 sm:w-40 sm:flex-col sm:overflow-visible sm:border-r sm:border-gray-100 sm:pr-1 sm:pb-0 dark:sm:border-gray-800"
													role="group"
													aria-label={$i18n.t('Brands')}
												>
													{#each vendorList as vendor}
														<li class="snap-start">
															<button
																type="button"
																class="flex w-full shrink-0 items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition {selectedVendor ===
																vendor
																	? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
																	: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
																on:click={() => (selectedVendor = vendor)}
																aria-pressed={selectedVendor === vendor}
															>
																<img
																	src={vendorLogoUrl(vendor)}
																	alt={vendor}
																	class="size-4 shrink-0 rounded-sm"
																	loading="lazy"
																	decoding="async"
																/>
																<span class="whitespace-nowrap capitalize">{vendor}</span>
															</button>
														</li>
													{/each}
												</ul>
												<!-- Model level (right/bottom) -->
												<ul
													class="h-72 overflow-y-auto sm:h-full sm:flex-1"
													role="group"
													aria-label={$i18n.t('Models')}
												>
													{#each vendorModels as model}
														<li>
															<button
																type="button"
																class="flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition {selectedModel ===
																model.id
																	? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
																	: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
																on:click={() => selectModelIfEnabled(model)}
																role="option"
																aria-selected={selectedModel === model.id}
															>
																{#if model.provider}
																	<img
																		src={vendorLogoUrl(model.provider)}
																		alt=""
																		class="size-4 shrink-0 rounded-sm"
																		loading="lazy"
																		decoding="async"
																	/>
																{/if}
																<span class="min-w-0 flex-1 truncate text-left"
																	>{stripVendorFromName(model)}</span
																>
																{#if supportsImageEditing(model, models)}
																	<Tooltip content={$i18n.t('Supports reference images')}>
																		<span
																			class="inline-flex size-5 shrink-0 items-center justify-center rounded-md bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-300"
																			aria-label={$i18n.t('Supports reference images')}
																		>
																			<Photo className="size-3.5" strokeWidth="2" />
																		</span>
																	</Tooltip>
																{/if}
																{#if modelBasePrice(model)}
																	<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">
																		{modelBasePrice(model)}
																		{$i18n.t('credits.common.unit')}
																	</span>
																{/if}
																{#if isProxyModel(model)}
																	<span class="shrink-0 text-xs text-amber-600 dark:text-amber-400">
																		{$i18n.t('First image may be slower')}
																	</span>
																{/if}
															</button>
														</li>
													{/each}
												</ul>
											</div>
										</div>
									{/if}
								</div>

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

								<div class="mt-2 flex min-w-0 items-center justify-between gap-2">
									<div class="flex min-w-0 items-center gap-2">
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
												{#if qualityOptions.length > 0 && selectedQuality}
													<span class="hidden truncate min-[360px]:inline">
														{getQualityLabel(selectedQuality)}
													</span>
												{/if}
												{#if imageCountOptions.length > 1}
													<span class="inline-flex items-center gap-1">
														<Photo className="size-4" strokeWidth="2" />
														{imageCount}
													</span>
												{/if}
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

													{#if qualityOptions.length > 0}
														<section class={hasImageSizingOptions ? 'mt-5' : ''}>
															<h3
																class="px-1 pb-2 text-sm font-medium text-gray-900 dark:text-gray-100"
															>
																{$i18n.t('Quality')}
															</h3>
															<div class="grid grid-cols-4 gap-1.5">
																{#each qualityOptions as quality}
																	<button
																		type="button"
																		class="h-9 rounded-xl border text-sm capitalize transition {selectedQuality ===
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
													{/if}
												</div>
											{/if}
										</div>
									</div>

									<div class="flex min-w-0 items-center justify-between gap-2 sm:justify-end">
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

		<div
			id="images-library-panel"
			role="tabpanel"
			aria-labelledby={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}
			class="flex-1 min-h-0 overflow-y-auto"
			hidden={view !== 'library'}
		>
			<!--
				Top clearance belongs to the scrolling content, not to the
				panel frame: it pushes the first row below the floating tab
				pill on first paint, then scrolls away so later rows settle
				flush against the top while the absolutely-positioned pill
				keeps floating over them. Mobile sits the pill at top-14 +
				sm:pt-2, hence the taller mobile cushion.
			-->
			<div class="pt-18 sm:pt-18">
				<CreationsLibrary
					active={view === 'library'}
					scope={libraryScope}
					revision={libraryRevision}
					onReuse={applyCreationDraft}
				/>
			</div>
		</div>

		{#if view === 'library'}
			<!-- Floating "start creating" capsule: mirrors the tab pill's glass
			     styling so the two float as siblings. Lifted out of the rolling
			     panels so neither scroll nor the narrow sidebar shift moves it. -->
			<div
				class="pointer-events-none absolute inset-x-0 bottom-0 z-30 flex justify-center px-3 pb-4 sm:pb-5"
			>
				<button
					type="button"
					class="pointer-events-auto inline-flex min-h-11 items-center gap-2 rounded-full border border-gray-200/80 bg-white/85 px-5 text-sm font-medium text-gray-800 shadow-lg shadow-black/10 backdrop-blur-xl transition hover:bg-white hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:border-gray-700/80 dark:bg-gray-900/85 dark:text-gray-100 dark:hover:bg-gray-900 dark:hover:text-white"
					on:click={() => selectSelection('generate')}
				>
					<Sparkles
						className="size-4 shrink-0 text-gray-500 dark:text-gray-400"
						strokeWidth="1.5"
					/>
					{$i18n.t('Start creating')}
				</button>
			</div>
		{/if}

		<ImagePreview bind:show={showImagePreview} src={previewImageUrl} alt={previewImageAlt} />
	</div>
{/if}
