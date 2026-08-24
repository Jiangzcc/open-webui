<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';
	import { toast } from 'svelte-sonner';

	import { quoteImageCredits, type ImageQuoteInput } from '$lib/apis/credits';
	import type { CreationScope } from '$lib/utils/creations-library';
	import {
		createImageQuoteState,
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';

	import { config, showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import { createGenerationEventStream } from '$lib/utils/generation-events';
	import { createSubmissionIdempotency } from '$lib/utils/submission-idempotency';
	import {
		DEFAULT_IMAGE_ASPECT_RATIO,
		getImageModelCapability,
		getPrimaryImageModels,
		resolveActiveImageModel,
		resolveImageEditModel,
		supportsImageEditing,
		validateCustomSize,
		validateImagePrompt,
		type GeneratedImage,
		type ImageAdvancedField,
		type ImageAspectRatio,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';
	import {
		consumePendingCreationDraft,
		mergeGenerationTask,
		type ImageCreationDraft,
		type ImageGenerationBatch
	} from '$lib/utils/image-generation-batches';

	import { groupByVendor } from '$lib/utils/images-dropdown';
	import ImagePromptForm from '$lib/components/images/ImagePromptForm.svelte';
	import ImagePageNavigation from '$lib/components/images/ImagePageNavigation.svelte';
	import ImageGenerationResults from '$lib/components/images/ImageGenerationResults.svelte';
	import ImageLibraryPanel from '$lib/components/images/ImageLibraryPanel.svelte';
	import { imageResolutionLabelKey } from '$lib/components/images/imageLabels';
	import { appendPromptText } from '$lib/components/prompt-tags/tagToggle';
	import {
		buildImageQuoteInput,
		draftForBatchEdit,
		draftForBatchGeneration,
		draftForImageGeneration,
		draftForImageReference,
		getAdvancedNumberError as validateAdvancedNumber,
		imageGenerationErrorKey,
		imageModelDisplayName,
		loadImageModelState,
		parseAdvancedNumber as parseImageAdvancedNumber
	} from './imagePageState';
	import {
		loadReferenceFiles,
		referenceFileFeedback,
		type ReferenceImage
	} from './imageReferenceFiles';
	import {
		loadImageTaskPage,
		loadLinkedImageTask,
		pollActiveImageTasks,
		refreshImageTask,
		startImageTaskRuntime
	} from './imageTaskHistory';
	import { shouldClearImageSubmission, submitImageTask } from './imageSubmission';
	import { imageDraftFieldValues, prepareImageDraft } from './imageDraftState';

	const i18n = getContext<Writable<I18n>>('i18n');

	// 幂等键复用（与视频端共享实现）：网络失败后的重试复用同一载荷指纹的键，
	// 服务端幂等重放返回既有任务而不是二次扣费；收到确定性响应后清除。
	const imageSubmissionIdempotency = createSubmissionIdempotency('pending-image-submission');

	const MAX_REFERENCE_IMAGES = 4;

	let loaded = false,
		loading = false;
	let modelsLoading = false,
		modelsLoaded = false;
	let draggedOver = false,
		showAspectRatioPicker = false,
		showModelSelector = false;
	let selectedVendor = '';
	let pendingCreationDraft: ImageCreationDraft | null = null;

	let selection: 'generate' | 'mine' | 'all' = 'generate';
	let libraryRevision = 0;
	let libraryScope: CreationScope;

	$: view = selection === 'generate' ? 'generate' : 'library';
	$: libraryScope = selection === 'all' ? 'all' : 'mine';
	$: isAdmin = $user?.role === 'admin';

	let prompt = '';
	let selectedAspectRatio: ImageAspectRatio = DEFAULT_IMAGE_ASPECT_RATIO;
	let selectedModel = '';
	let selectedResolution = '',
		selectedQuality = '',
		selectedOutputFormat = '';
	let imageCount = 1;
	let negativePrompt = '';
	let promptFormElement: { focusPromptEditor: () => void } | null = null;

	// 标签只是输入快捷方式；提交的始终是编辑器里所见的纯文本。
	const handlePromptTagInsert = (event: CustomEvent<{ text: string; isNegative: boolean }>) => {
		const { text, isNegative } = event.detail;
		if (isNegative) {
			negativePrompt = appendPromptText(negativePrompt, text);
		} else {
			prompt = appendPromptText(prompt, text);
		}
	};
	let stepsInput = '',
		seedInput = '';
	let guidanceScaleInput = '',
		strengthInput = '';
	let showAdvancedSettings = false;
	let customWidth: number | null = null,
		customHeight: number | null = null;
	let useCustomSize = false;
	let imageQuoteState: ImageQuoteState = { status: 'loading' };
	let quoteInput: ImageQuoteInput | null = null;

	let models: ImageGenerationModel[] = [];
	let referenceImages: ReferenceImage[] = [];
	let generationBatches: ImageGenerationBatch[] = [];
	let recentTasksCursor: string | null = null,
		loadingMoreTasks = false;
	let canHover = true;
	let elapsedNow = Date.now();
	let stopTaskRuntime: (() => void) | null = null;
	let pollingTasks = false;

	let generationPanelElement: HTMLDivElement;

	$: modeLabel = referenceImages.length > 0 ? $i18n.t('Image to Image') : $i18n.t('Text to Image');
	$: selectedModelConfig =
		primaryModels.find((model) => model.id === selectedModel) ??
		(selectedModel === ''
			? (primaryModels.find((model) => model.isDefault && model.enabled !== false) ??
				primaryModels.find((model) => model.enabled !== false) ??
				// 全部模型维护中时回退到第一个模型，保留 UI 预填能力；提交时由
				// ensure_model_enabled 在后端拦截并提示维护信息，而非让选择器空白。
				primaryModels[0] ??
				null)
			: null);
	$: activeModelConfig = resolveActiveImageModel(
		selectedModelConfig,
		models,
		referenceImages.length > 0
	);
	$: selectedModelSupportsEditing = supportsImageEditing(selectedModelConfig, models);
	// 单图 i2i 模型按目录能力收缩槽位，其余模型沿用全局上限。
	$: effectiveMaxReferenceImages =
		resolveImageEditModel(selectedModelConfig, models)?.imageInputMaxCount ??
		selectedModelConfig?.imageInputMaxCount ??
		MAX_REFERENCE_IMAGES;
	// 主动裁剪可避免把超目录上限的旧附件继续提交给新模型。
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
	$: outputFormatOptions = selectedModelCapability.outputFormats;
	$: advancedFields = selectedModelCapability.advancedFields;
	$: seedField = advancedFields.find((field) => field.field === 'seed') ?? null;
	$: negativePromptField =
		advancedFields.find((field) => field.field === 'negative_prompt') ?? null;
	$: stepsField = advancedFields.find((field) => field.field === 'steps') ?? null;
	$: guidanceScaleField = advancedFields.find((field) => field.field === 'guidance_scale') ?? null;
	$: strengthField = advancedFields.find((field) => field.field === 'strength') ?? null;
	$: hasAdvancedSettings = advancedFields.length > 0 || outputFormatOptions.length > 0;
	$: steps = parseAdvancedNumber(stepsInput, stepsField);
	$: seed = parseAdvancedNumber(seedInput, seedField);
	$: guidanceScale = parseAdvancedNumber(guidanceScaleInput, guidanceScaleField);
	$: strength = parseAdvancedNumber(strengthInput, strengthField);
	$: advancedSettingsInvalid = Boolean(
		(stepsField && getAdvancedNumberError(stepsInput, stepsField)) ||
		(seedField && getAdvancedNumberError(seedInput, seedField)) ||
		(guidanceScaleField && getAdvancedNumberError(guidanceScaleInput, guidanceScaleField)) ||
		(strengthField && getAdvancedNumberError(strengthInput, strengthField))
	);
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
		referenceImages.map((image) => image.url),
		customSizeValue
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
		outputFormatOptions.length > 0 &&
		!outputFormatOptions.includes(selectedOutputFormat)
	) {
		selectedOutputFormat =
			selectedModelCapability.defaultOutputFormat ?? outputFormatOptions[0] ?? '';
	}
	$: if (loaded && outputFormatOptions.length === 0 && selectedOutputFormat) {
		selectedOutputFormat = '';
	}
	$: if (loaded && !seedField && seedInput) seedInput = '';
	$: if (loaded && !negativePromptField && negativePrompt) {
		negativePrompt = '';
	}
	$: if (loaded && !stepsField && stepsInput) stepsInput = '';
	$: if (loaded && !guidanceScaleField && guidanceScaleInput) guidanceScaleInput = '';
	$: if (loaded && !strengthField && strengthInput) strengthInput = '';
	$: if (loaded && !hasAdvancedSettings && showAdvancedSettings) showAdvancedSettings = false;
	$: if (
		loaded &&
		imageCountOptions.length > 0 &&
		!imageCountOptions.includes(Number(imageCount))
	) {
		imageCount = imageCountOptions[0];
	}
	$: customSizeConstraints = selectedModelCapability.customSize;
	$: supportsCustomSize = Boolean(customSizeConstraints);
	// 清空旧模型尺寸，避免切换后把不合法 size 带进新请求。
	$: if (loaded && !supportsCustomSize && useCustomSize) {
		useCustomSize = false;
		customWidth = null;
		customHeight = null;
	}
	$: if (loaded && selectedResolution) {
		const match = selectedResolution.match(/^(\d+)x(\d+)$/);
		if (match) {
			customWidth = Number(match[1]);
			customHeight = Number(match[2]);
		}
	}
	$: customWidthNum = Number(customWidth);
	$: customHeightNum = Number(customHeight);
	$: customSizeError =
		useCustomSize && customWidth && customHeight
			? validateCustomSize(customWidthNum, customHeightNum, customSizeConstraints)
			: null;
	$: customSizeValue =
		useCustomSize && customWidth && customHeight && !customSizeError
			? `${customWidthNum}x${customHeightNum}`
			: null;

	const imageQuoteStateMachine = createImageQuoteState({
		quote: (input, signal) => quoteImageCredits(localStorage.token, input, signal),
		onChange: (state) => {
			imageQuoteState = state;
		}
	});

	const imageGenerationErrorMessage = (error: unknown) => $i18n.t(imageGenerationErrorKey(error));

	// 比例值不能过 i18n（"4:3" 会被 namespace 分隔符误拆），只有 Auto 翻译。
	const getAspectRatioLabel = (ratio: ImageAspectRatio) =>
		ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio;
	const getResolutionLabel = (resolution: string) => $i18n.t(imageResolutionLabelKey(resolution));

	const translate = (key: string, values?: Record<string, number>) => $i18n.t(key, values);
	const parseAdvancedNumber = (value: string, field: ImageAdvancedField | null) =>
		parseImageAdvancedNumber(value, field, translate);

	const getAdvancedNumberError = (
		value: string,
		field: { kind: 'integer' | 'number' | 'text'; min?: number; max?: number }
	) => validateAdvancedNumber(value, field, translate);

	const reuseBatchGenerate = (batch: ImageGenerationBatch) =>
		applyCreationDraft(draftForBatchGeneration(batch));
	const reuseImageAsReference = (batch: ImageGenerationBatch, image: GeneratedImage) =>
		applyCreationDraft(draftForImageReference(batch, image));
	const reuseImageGenerate = (batch: ImageGenerationBatch, image: GeneratedImage) =>
		applyCreationDraft(draftForImageGeneration(batch, image));
	const reuseBatchEdit = (batch: ImageGenerationBatch) =>
		applyCreationDraft(draftForBatchEdit(batch));

	const getImageModelDisplayName = imageModelDisplayName;

	const loadModels = async () => {
		modelsLoading = true;
		modelsLoaded = true;
		try {
			const state = await loadImageModelState(localStorage.token, selectedModel);
			models = state.models;
			if (state.defaultCapability) {
				selectedAspectRatio = state.defaultCapability.defaultAspectRatio;
				selectedResolution = state.defaultCapability.defaultResolution ?? '';
			}
		} catch (error) {
			models = [];
			toast.error(`${error}`);
		}
		modelsLoading = false;
		if (pendingCreationDraft) {
			const draft = pendingCreationDraft;
			pendingCreationDraft = null;
			await tick();
			await applyCreationDraft(draft);
		}
	};

	const addFiles = async (files: File[]) => {
		if (!selectedModelSupportsEditing) return;
		const remainingSlots = Math.max(effectiveMaxReferenceImages - referenceImages.length, 0);
		try {
			const result = await loadReferenceFiles(files, remainingSlots, $i18n.t('Reference image'));
			for (const feedback of referenceFileFeedback(result.rejected, effectiveMaxReferenceImages)) {
				toast.error($i18n.t(feedback.key, feedback.values));
			}
			referenceImages = [...referenceImages, ...result.images];
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
		useCustomSize = false;
		customWidth = null;
		customHeight = null;
	};

	const selectModelIfEnabled = (model: ImageGenerationModel) => {
		if (model.enabled === false) {
			toast.info(model.maintenanceMessage || $i18n.t('This model is temporarily unavailable.'));
			return;
		}
		selectModel(model.id);
	};

	const selectResolution = (resolution: string) => {
		selectedResolution = resolution;
	};

	const toggleAspectRatioPicker = () => {
		showAspectRatioPicker = !showAspectRatioPicker;
		showModelSelector = false;
	};

	const removeGenerationBatch = (batchId: string) => {
		generationBatches = generationBatches.filter((item) => item.id !== batchId);
		libraryRevision += 1;
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

	const applyCreationDraft = async (draft: ImageCreationDraft) => {
		try {
			const prepared = await prepareImageDraft(
				draft,
				localStorage.token,
				primaryModels,
				models,
				$i18n.t('Previous creation')
			);
			referenceImages = prepared.referenceImages;
			if (prepared.targetModel) selectModel(prepared.targetModel.id);
			await tick();
		} catch {
			toast.error($i18n.t('Failed to load reference image'));
			return;
		}
		const fields = imageDraftFieldValues(draft, {
			aspectRatios: aspectRatioOptions,
			resolutions: resolutionOptions,
			qualities: qualityOptions,
			outputFormats: outputFormatOptions,
			negativePromptField,
			stepsField,
			seedField,
			guidanceScaleField,
			strengthField
		});
		if (fields.aspectRatio) selectedAspectRatio = fields.aspectRatio;
		if (fields.resolution) selectedResolution = fields.resolution;
		if (fields.quality) selectedQuality = fields.quality;
		if (fields.outputFormat) selectedOutputFormat = fields.outputFormat;
		negativePrompt = fields.negativePrompt;
		stepsInput = fields.steps;
		seedInput = fields.seed;
		guidanceScaleInput = fields.guidanceScale;
		strengthInput = fields.strength;
		prompt = fields.prompt;
		await selectSelection('generate');
		await tick();
		promptFormElement?.focusPromptEditor();
		toast.success($i18n.t('Creation settings loaded'));
	};

	const loadRecentGenerationTasks = async () => {
		try {
			const page = await loadImageTaskPage(localStorage.token, generationBatches);
			generationBatches = page.batches;
			recentTasksCursor = page.cursor;
		} catch {
			toast.error($i18n.t('Failed to restore generation tasks'));
		}
	};

	const loadMoreRecentTasks = async () => {
		if (loadingMoreTasks || !recentTasksCursor) return;
		loadingMoreTasks = true;
		try {
			const page = await loadImageTaskPage(
				localStorage.token,
				generationBatches,
				recentTasksCursor
			);
			generationBatches = page.batches;
			recentTasksCursor = page.cursor;
		} catch {
			toast.error($i18n.t('Failed to load more generations'));
		} finally {
			loadingMoreTasks = false;
		}
	};

	const pollGenerationTasks = async () => {
		if (pollingTasks) return;
		pollingTasks = true;
		try {
			const result = await pollActiveImageTasks(localStorage.token, generationBatches);
			generationBatches = result.batches;
			libraryRevision += result.completed;
			if (result.completed) toast.success($i18n.t('Image generation completed'));
		} catch {
			// A temporary polling failure must not turn a running server task into a
			// failed UI task. The next interval retries with the same task id.
		} finally {
			pollingTasks = false;
		}
	};

	const refreshGenerationTask = async (taskId: string) => {
		const result = await refreshImageTask(localStorage.token, generationBatches, taskId);
		generationBatches = result.batches;
		if (result.completed) {
			libraryRevision += 1;
			toast.success($i18n.t('Image generation completed'));
		}
	};

	const generationEventStream = createGenerationEventStream(
		'image',
		refreshGenerationTask,
		pollGenerationTasks
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
		if (advancedSettingsInvalid) {
			toast.error($i18n.t('Check the advanced settings'));
			return;
		}

		loading = true;
		showAspectRatioPicker = false;
		showModelSelector = false;

		try {
			const task = await submitImageTask(
				localStorage.token,
				{
					prompt: validation.prompt,
					aspectRatio: selectedAspectRatio,
					resolution: selectedResolution,
					quality: selectedQuality,
					model: activeModelConfig ?? selectedModelConfig ?? selectedModel,
					count: imageCount,
					steps,
					negativePrompt,
					outputFormat: selectedOutputFormat,
					seed,
					guidanceScale,
					strength,
					size: customSizeValue,
					referenceUrls: referenceImages.map((image) => image.url)
				},
				imageSubmissionIdempotency
			);
			generationBatches = mergeGenerationTask(generationBatches, task);
			referenceImages = [];
			prompt = '';
			await tick();
			generationPanelElement?.scrollTo({ top: 0, behavior: 'smooth' });
		} catch (error) {
			// A structured HTTP response is definitive. A network failure is not:
			// retain the same key so a retry cannot create a second paid request.
			if (shouldClearImageSubmission(error)) {
				imageSubmissionIdempotency.clearPendingSubmission();
			}
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
		canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
		await loadRecentGenerationTasks();
		const linked = await loadLinkedImageTask(
			localStorage.token,
			window.location.href,
			generationBatches
		);
		generationBatches = linked.batches;
		// SSE 断流或跨 worker 漏事件时由低频轮询补偿。
		stopTaskRuntime = startImageTaskRuntime(
			generationEventStream,
			() => void pollGenerationTasks(),
			() => (elapsedNow = Date.now())
		);
		await tick();
		if (linked.taskId) {
			document.getElementById(`image-task-${linked.taskId}`)?.scrollIntoView({
				behavior: 'smooth',
				block: 'start'
			});
		}
	});

	onDestroy(() => {
		stopTaskRuntime?.();
		imageQuoteStateMachine.dispose();
	});
</script>

<svelte:head>
	<title>{$i18n.t('Images')} • {$WEBUI_NAME}</title>
</svelte:head>

{#if loaded}
	<div
		class="relative flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
			? 'md:max-w-[calc(100%-var(--sidebar-width))]'
			: ''} max-w-full"
	>
		<ImagePageNavigation {selection} {isAdmin} onSelect={selectSelection} />

		<div
			id="images-generate-panel"
			bind:this={generationPanelElement}
			role="tabpanel"
			aria-labelledby="images-generate-tab"
			class="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 lg:px-8"
			hidden={view !== 'generate'}
		>
			<div class="mx-auto max-w-5xl min-h-full flex flex-col sm:px-2">
				<div class="flex-1">
					<ImageGenerationResults
						batches={generationBatches}
						models={primaryModels}
						{canHover}
						supportsEditing={selectedModelSupportsEditing}
						{elapsedNow}
						hasMore={Boolean(recentTasksCursor)}
						loadingMore={loadingMoreTasks}
						onReuseAsReference={reuseImageAsReference}
						onRemix={reuseImageGenerate}
						onEditAgain={reuseBatchEdit}
						onRegenerate={reuseBatchGenerate}
						onBatchRemoved={removeGenerationBatch}
						onLoadMore={() => void loadMoreRecentTasks()}
						onViewOlder={() => void selectSelection('mine')}
					/>
				</div>

				<ImagePromptForm
					bind:selectedVendor
					bind:prompt
					bind:selectedQuality
					bind:imageCount
					bind:useCustomSize
					bind:customWidth
					bind:customHeight
					bind:selectedOutputFormat
					bind:seedInput
					bind:stepsInput
					bind:guidanceScaleInput
					bind:strengthInput
					bind:negativePrompt
					bind:showModelSelector
					bind:showAspectRatioPicker
					bind:showAdvancedSettings
					bind:draggedOver
					bind:this={promptFormElement}
					{selectedModelLabel}
					{selectedModelConfig}
					{vendorList}
					{vendorModels}
					{selectedModel}
					{models}
					{selectedModelSupportsEditing}
					{selectedAspectRatio}
					{selectedResolution}
					{referenceImages}
					{aspectRatioOptions}
					{resolutionOptions}
					{qualityOptions}
					{imageCountOptions}
					{outputFormatOptions}
					{supportsCustomSize}
					{hasImageSizingOptions}
					{hasAdvancedSettings}
					{seedField}
					{stepsField}
					{guidanceScaleField}
					{strengthField}
					{negativePromptField}
					{customSizeError}
					{customWidthNum}
					{customHeightNum}
					{selectedImageSizeLabel}
					{imageQuoteState}
					{loading}
					{advancedSettingsInvalid}
					{selectModelIfEnabled}
					{selectAspectRatio}
					{selectResolution}
					{toggleAspectRatioPicker}
					{handleFileUpload}
					{handleDrop}
					{removeImage}
					{handlePromptTagInsert}
					{submitHandler}
				/>
			</div>
		</div>

		<ImageLibraryPanel
			active={view === 'library'}
			scope={libraryScope}
			revision={libraryRevision}
			labelledBy={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}
			onReuse={applyCreationDraft}
			onStartCreating={() => void selectSelection('generate')}
		/>
	</div>
{/if}
