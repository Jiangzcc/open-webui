<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { quoteImageCredits, type ImageQuoteInput } from '$lib/apis/credits';
	import type { CreationScope } from '$lib/utils/creations-library';
	import { getImageGenerationErrorCode } from '$lib/apis/images/generation';
	import {
		ImageTaskRequestError,
		createImageGenerationTask,
		deleteImageGenerationTask,
		getImageGenerationTask,
		listImageGenerationTasks
	} from '$lib/apis/creations/generation-tasks';
	import {
		createImageQuoteState,
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';

	import { getImageGenerationModels } from '$lib/apis/images';
	import { config, mobile, showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import { createGenerationEventStream } from '$lib/utils/generation-events';
	import { createSubmissionIdempotency } from '$lib/utils/submission-idempotency';
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
		validateCustomSize,
		validateImagePrompt,
		type GeneratedImage,
		type ImageAspectRatio,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';
	import {
		buildCreationDraft,
		consumePendingCreationDraft,
		isGenerationTaskTerminal,
		mergeGenerationTask,
		type ImageCreationDraft,
		type ImageGenerationBatch
	} from '$lib/utils/image-generation-batches';

	import { groupByVendor } from '$lib/utils/images-dropdown';
	import { blobExtension, downloadBlob, zipAndDownload } from '$lib/utils/download';

	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import CreationsLibrary from '$lib/components/images/CreationsLibrary.svelte';
	import ImageBatchCard from '$lib/components/images/ImageBatchCard.svelte';
	import ImagePromptForm from '$lib/components/images/ImagePromptForm.svelte';
	import {
		imageAspectRatioLabelKey,
		imageQualityLabelKey,
		imageResolutionLabelKey
	} from '$lib/components/images/imageLabels';
	import { appendPromptText } from '$lib/components/prompt-tags/tagToggle';

	const i18n = getContext('i18n');

	// 幂等键复用（与视频端共享实现）：网络失败后的重试复用同一载荷指纹的键，
	// 服务端幂等重放返回既有任务而不是二次扣费；收到确定性响应后清除。
	const imageSubmissionIdempotency = createSubmissionIdempotency('pending-image-submission');

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
	let libraryScope: CreationScope;

	$: view = selection === 'generate' ? 'generate' : 'library';
	$: libraryScope = selection === 'all' ? 'all' : 'mine';
	$: isAdmin = $user?.role === 'admin';

	let prompt = '';
	let selectedAspectRatio: ImageAspectRatio = DEFAULT_IMAGE_ASPECT_RATIO;
	let selectedModel = '';
	let selectedResolution = '';
	let selectedQuality = '';
	let selectedOutputFormat = '';
	let imageCount = 1;
	let negativePrompt = '';
	// 表单组件实例：applyCreationDraft 复用草稿后调用其 focusPromptEditor 聚焦。
	let promptFormElement: { focusPromptEditor: () => void } | null = null;

	// 标签是快捷提示词片段：点击即把 insert_text 追加进对应的输入框，
	// 提交的就是输入框里所见即所得的纯文本。
	const handlePromptTagInsert = (event: CustomEvent<{ text: string; isNegative: boolean }>) => {
		const { text, isNegative } = event.detail;
		if (isNegative) {
			negativePrompt = appendPromptText(negativePrompt, text);
		} else {
			prompt = appendPromptText(prompt, text);
		}
	};
	let stepsInput = '';
	let seedInput = '';
	let guidanceScaleInput = '';
	let strengthInput = '';
	let showAdvancedSettings = false;
	// 自定义宽高输入(WxH),仅对声明 custom_size 的模型启用。空串表示未输入。
	let customWidth = '';
	let customHeight = '';
	let useCustomSize = false;
	let imageQuoteState: ImageQuoteState = { status: 'loading' };
	let quoteInput: ImageQuoteInput | null = null;

	let models: ImageGenerationModel[] = [];
	let referenceImages: ReferenceImage[] = [];
	let generationBatches: ImageGenerationBatch[] = [];
	// 最近生成流的 keyset 分页游标。null 表示没有更早的批次可加载。
	let recentTasksCursor: string | null = null;
	let loadingMoreTasks = false;
	// 创作页只展示最近 7 天的任务，更早的需到「我的作品」里查看。
	// 时间窗以「当前时间 - 7 天」的秒级时间戳传给后端 since；进行中任务不受窗限制。
	const RECENT_WINDOW_SECONDS = 7 * 24 * 60 * 60;
	const recentSince = () => Math.floor(Date.now() / 1000) - RECENT_WINDOW_SECONDS;
	// 是否为可悬停指针（鼠标）。触屏设备为 false，浮层按钮需常驻可见，不得仅依赖 hover。
	let canHover = true;
	// 批量下载中各 batch 的 id 集合，用 Set 支持多批并发，各批独立显示 loading 态。
	let batchDownloadingIds: Set<string> = new Set();
	let batchDeletingIds: Set<string> = new Set();
	let showBatchDeleteConfirm = false;
	let batchToDelete: ImageGenerationBatch | null = null;
	let elapsedNow = Date.now();
	let taskPollTimer: ReturnType<typeof setInterval> | null = null;
	let elapsedTimer: ReturnType<typeof setInterval> | null = null;
	let pollingTasks = false;
	let showImagePreview = false;
	let previewImageUrl = '';
	let previewImageAlt = '';

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
		referenceImages,
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
	// 切到不支持自定义的模型时,关闭自定义态并清空输入,避免残留 size 污染后续请求。
	$: if (loaded && !supportsCustomSize && useCustomSize) {
		useCustomSize = false;
		customWidth = '';
		customHeight = '';
	}
	// 选中分辨率变化时同步预填自定义宽高(仅 WxH 格式),
	// 启用自定义尺寸后可直接在上面的预设基础上微调,无需另列一份预设。
	$: if (loaded && selectedResolution) {
		const match = selectedResolution.match(/^(\d+)x(\d+)$/);
		if (match) {
			customWidth = match[1];
			customHeight = match[2];
		}
	}
	$: customWidthNum = Number(customWidth);
	$: customHeightNum = Number(customHeight);
	$: customSizeError =
		useCustomSize && customWidth && customHeight
			? validateCustomSize(customWidthNum, customHeightNum, customSizeConstraints)
			: null;
	// 仅当启用自定义且输入合法时,才产出 "WxH" 作为 payload.size;后端据此发送 {width,height}。
	$: customSizeValue =
		useCustomSize && customWidth && customHeight && !customSizeError
			? `${customWidthNum}x${customHeightNum}`
			: null;

	const buildImageQuoteInput = (
		aspectRatio: ImageAspectRatio,
		resolution: string,
		quality: string,
		model: ImageGenerationModel | string | null,
		count: number,
		stepCount: number | null,
		negative: string,
		references: ReferenceImage[],
		size: string | null
	): ImageQuoteInput | null => {
		const commonPayload = {
			prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT,
			aspectRatio,
			resolution,
			quality: quality || null,
			model,
			n: count,
			steps: stepCount,
			negative_prompt: negative,
			size
		};
		const payload =
			references.length > 0
				? buildImageEditPayload({
						...commonPayload,
						referenceImages: references.map((image) => image.url)
					})
				: buildImageGenerationPayload(commonPayload);
		const image = 'image' in payload ? payload.image : undefined;
		const {
			model: resourceId,
			prompt: normalizedPrompt,
			n,
			size: normalizedSize,
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
				...(normalizedSize ? { size: normalizedSize } : {}),
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
			case 'invalid_image_size':
				return $i18n.t('Image size is invalid');
			case 'rate_limited':
				return $i18n.t('Too many image generation requests');
			default:
				return $i18n.t('credits.unavailable');
		}
	};

	const modelBasePrice = (model: ImageGenerationModel) =>
		referenceImages.length > 0 ? resolveImageEditModel(model, models)?.basePrice : model.basePrice;

	// label 显示名映射在 imageLabels.ts（与 ImageBatchCard 共享），这里包一层 $i18n.t。
	const getAspectRatioLabel = (ratio: ImageAspectRatio) => $i18n.t(imageAspectRatioLabelKey(ratio));
	const getResolutionLabel = (resolution: string) => $i18n.t(imageResolutionLabelKey(resolution));
	const getQualityLabel = (quality: string) => $i18n.t(imageQualityLabelKey(quality));

	const parseAdvancedNumber = (
		value: string,
		field: { kind: 'integer' | 'number' | 'text'; min?: number; max?: number } | null
	) => {
		if (!field || !value.trim() || getAdvancedNumberError(value, field)) return null;
		return Number(value);
	};

	const getAdvancedNumberError = (
		value: string,
		field: { kind: 'integer' | 'number' | 'text'; min?: number; max?: number }
	) => {
		if (!value.trim()) return null;
		const parsed = Number(value);
		if (!Number.isFinite(parsed) || (field.kind === 'integer' && !Number.isInteger(parsed))) {
			return $i18n.t(field.kind === 'integer' ? 'Enter a whole number' : 'Enter a number');
		}
		if (field.min !== undefined && parsed < field.min) {
			return $i18n.t('Minimum: {{value}}', { value: field.min });
		}
		if (field.max !== undefined && parsed > field.max) {
			return $i18n.t('Maximum: {{value}}', { value: field.max });
		}
		return null;
	};

	const advancedRangeLabel = (field: { min?: number; max?: number } | null) => {
		if (!field || (field.min === undefined && field.max === undefined))
			return $i18n.t('Model default');
		if (field.min !== undefined && field.max !== undefined) return `${field.min}–${field.max}`;
		if (field.min !== undefined) return `≥ ${field.min}`;
		return `≤ ${field.max}`;
	};

	// ===== 结果块（heytop 式聊天消息卡片）展示范式 =====
	// 每个 batch 是一条「消息记录」：消息头(模型短名+时间) → 全展开 prompt
	// → pill 参数行 → 图网格(正方形) → 操作行(重新编辑 i2i / 重新生成 t2i)。
	// 展示细节在 ImageBatchCard.svelte（拆分自本文件）。

	// 重新生成(t2i)：用原 prompt/参数，不带参考图。
	const reuseBatchGenerate = (batch: ImageGenerationBatch) =>
		applyCreationDraft(
			buildCreationDraft({
				prompt: batch.prompt,
				model_id: batch.modelId,
				params: batch.params
			})
		);

	// 用单张生成的图作为图生图参考：带入原批次的模型与参数，仅把参考图
	// 从"首图"换成用户指定的这一张，与 reuseBatchEdit 行为对齐。
	const reuseImageAsReference = (batch: ImageGenerationBatch, image: GeneratedImage) =>
		applyCreationDraft(
			buildCreationDraft({
				prompt: batch.prompt,
				model_id: batch.modelId,
				params: batch.params,
				content_url: image.url,
				useAsReference: true
			})
		);

	// 基于单张图的 prompt 重新生成（text-to-image）：保留原批模型与参数，
	// 仅用这张图自身的 prompt（缺省回退批次 prompt）。
	const reuseImageGenerate = (batch: ImageGenerationBatch, image: GeneratedImage) =>
		applyCreationDraft(
			buildCreationDraft({
				prompt: image.prompt?.trim() || batch.prompt,
				model_id: batch.modelId,
				params: batch.params
			})
		);

	// 重新编辑(i2i)：同样参数，但带入本批首图作为参考图（若有）。
	const reuseBatchEdit = (batch: ImageGenerationBatch) => {
		const firstImage = batch.images[0]?.url ?? null;
		return applyCreationDraft(
			buildCreationDraft({
				prompt: batch.prompt,
				model_id: batch.modelId,
				params: batch.params,
				content_url: firstImage,
				useAsReference: Boolean(firstImage)
			})
		);
	};

	const getImageModelDisplayName = (model: ImageGenerationModel) => {
		const name = model.name?.trim() || model.id;
		const separatorIndex = name.indexOf(' / ');

		return separatorIndex === -1 ? name : name.slice(separatorIndex + 3);
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
			const defaultModel =
				models.find((model) => model.isDefault && model.enabled !== false) ??
				models.find((model) => model.enabled !== false) ??
				models[0];
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
		// 切换模型时清空自定义宽高,避免上一个模型的尺寸/约束残留。
		useCustomSize = false;
		customWidth = '';
		customHeight = '';
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
			if (!response.ok) throw new Error('download failed');
			const blob = await response.blob();
			downloadBlob(
				blob,
				`generated-image-${image.createdAt ?? Date.now()}-${index + 1}.${blobExtension(blob)}`
			);
		} catch {
			toast.error($i18n.t('Failed to download image'));
		}
	};

	// 本批批量下载：打包成 ZIP，复用 $lib/utils/download 的共享方案。
	const downloadBatchImages = async (batch: ImageGenerationBatch) => {
		if (batch.images.length === 0 || batchDownloadingIds.has(batch.id)) return;
		batchDownloadingIds = new Set(batchDownloadingIds).add(batch.id);
		try {
			await zipAndDownload(
				batch.images.map((image, index) => ({
					url: image.url,
					filename: (i: number, blob: Blob) =>
						`${String(i + 1).padStart(2, '0')}.${blobExtension(blob)}`
				})),
				`generation-${batch.createdAt ?? Date.now()}.zip`
			);
		} catch {
			toast.error($i18n.t('Failed to download images'));
		} finally {
			const next = new Set(batchDownloadingIds);
			next.delete(batch.id);
			batchDownloadingIds = next;
		}
	};

	const requestDeleteBatch = (batch: ImageGenerationBatch) => {
		if (batchDeletingIds.has(batch.id)) return;
		batchToDelete = batch;
		showBatchDeleteConfirm = true;
	};

	const confirmDeleteBatch = async () => {
		const batch = batchToDelete;
		batchToDelete = null;
		if (!batch) return;

		batchDeletingIds = new Set(batchDeletingIds).add(batch.id);
		try {
			await deleteImageGenerationTask(localStorage.token, batch.id);
			generationBatches = generationBatches.filter((item) => item.id !== batch.id);
			libraryRevision += 1;
			toast.success($i18n.t('Record removed'));
		} catch {
			toast.error($i18n.t('Failed to remove record'));
		} finally {
			const next = new Set(batchDeletingIds);
			next.delete(batch.id);
			batchDeletingIds = next;
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
		referenceImages = referenceImageUrl
			? [{ url: referenceImageUrl, name: $i18n.t('Previous creation') }]
			: [];

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
		if (draft.outputFormat && outputFormatOptions.includes(draft.outputFormat)) {
			selectedOutputFormat = draft.outputFormat;
		}
		negativePrompt = negativePromptField ? (draft.negativePrompt ?? '') : '';
		stepsInput =
			stepsField && draft.steps !== null && draft.steps !== undefined ? String(draft.steps) : '';
		seedInput =
			seedField && draft.seed !== null && draft.seed !== undefined ? String(draft.seed) : '';
		guidanceScaleInput =
			guidanceScaleField && draft.guidanceScale !== null && draft.guidanceScale !== undefined
				? String(draft.guidanceScale)
				: '';
		strengthInput =
			strengthField && draft.strength !== null && draft.strength !== undefined
				? String(draft.strength)
				: '';
		prompt = draft.prompt ?? '';
		await selectSelection('generate');
		await tick();
		// 复用草稿后把焦点还给提示词输入框，恢复旧版 textarea 的交互。
		promptFormElement?.focusPromptEditor();
		toast.success($i18n.t('Creation settings loaded'));
	};

	const RECENT_TASKS_PAGE_SIZE = 10;

	const loadRecentGenerationTasks = async () => {
		try {
			const { items, next_cursor } = await listImageGenerationTasks(
				localStorage.token,
				RECENT_TASKS_PAGE_SIZE,
				undefined,
				recentSince()
			);
			for (const task of items) generationBatches = mergeGenerationTask(generationBatches, task);
			recentTasksCursor = next_cursor ?? null;
		} catch {
			toast.error($i18n.t('Failed to restore generation tasks'));
		}
	};

	const loadMoreRecentTasks = async () => {
		if (loadingMoreTasks || !recentTasksCursor) return;
		loadingMoreTasks = true;
		try {
			const { items, next_cursor } = await listImageGenerationTasks(
				localStorage.token,
				RECENT_TASKS_PAGE_SIZE,
				recentTasksCursor,
				recentSince()
			);
			for (const task of items) generationBatches = mergeGenerationTask(generationBatches, task);
			recentTasksCursor = next_cursor ?? null;
		} catch {
			toast.error($i18n.t('Failed to load more generations'));
		} finally {
			loadingMoreTasks = false;
		}
	};

	const pollGenerationTasks = async () => {
		if (pollingTasks) return;
		const active = generationBatches.filter((batch) => !isGenerationTaskTerminal(batch.status));
		if (active.length === 0) return;
		pollingTasks = true;
		try {
			const tasks = await Promise.all(
				active.map((batch) => getImageGenerationTask(localStorage.token, batch.id))
			);
			for (const task of tasks) {
				const previousStatus = generationBatches.find((batch) => batch.id === task.id)?.status;
				generationBatches = mergeGenerationTask(generationBatches, task);
				if (task.status === 'succeeded' && previousStatus !== 'succeeded') {
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

	const refreshGenerationTask = async (taskId: string) => {
		const previous = generationBatches.find((batch) => batch.id === taskId);
		const task = await getImageGenerationTask(localStorage.token, taskId);
		generationBatches = mergeGenerationTask(generationBatches, task);
		if (task.status === 'succeeded' && previous?.status !== 'succeeded') {
			libraryRevision += 1;
			toast.success($i18n.t('Image generation completed'));
		}
	};

	// SSE 事件流（含指数退避重连与断流兜底轮询）与视频页共享同一实现。
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
			const commonPayload = {
				prompt: validation.prompt,
				aspectRatio: selectedAspectRatio,
				resolution: selectedResolution,
				quality: selectedQuality || null,
				model: activeModelConfig ?? selectedModelConfig ?? selectedModel,
				n: imageCount,
				steps,
				negative_prompt: negativePrompt,
				output_format: selectedOutputFormat || null,
				seed,
				guidance_scale: guidanceScale,
				strength,
				size: customSizeValue
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
				await imageSubmissionIdempotency.idempotencyKeyFor(payload)
			);
			imageSubmissionIdempotency.clearPendingSubmission();
			generationBatches = mergeGenerationTask(generationBatches, task);
			referenceImages = [];
			prompt = '';
			await tick();
			// 新生成结果插入到列表最上面，提交后自动滚到顶，让用户立刻看到新 batch 的进度。
			generationPanelElement?.scrollTo({ top: 0, behavior: 'smooth' });
		} catch (error) {
			// A structured HTTP response is definitive. A network failure is not:
			// retain the same key so a retry cannot create a second paid request.
			if (
				error instanceof ImageTaskRequestError &&
				error.status !== undefined &&
				error.status >= 400 &&
				error.status < 500 &&
				![408, 429].includes(error.status)
			) {
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
		// 触屏设备无 hover 能力：浮层按钮需常驻可见。桌面端保持 hover 显现。
		canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
		await loadRecentGenerationTasks();
		const linkedTaskId = new URL(window.location.href).searchParams.get('task');
		if (linkedTaskId && !generationBatches.some((batch) => batch.id === linkedTaskId)) {
			const linkedTask = await getImageGenerationTask(localStorage.token, linkedTaskId).catch(
				() => null
			);
			if (linkedTask) generationBatches = mergeGenerationTask(generationBatches, linkedTask);
		}
		void generationEventStream.start();
		// SSE 断线、代理不支持流式响应或事件落在其他 worker 时，用低频轮询补偿。
		taskPollTimer = setInterval(() => void pollGenerationTasks(), 10_000);
		elapsedTimer = setInterval(() => (elapsedNow = Date.now()), 1_000);
		await tick();
		if (linkedTaskId) {
			document.getElementById(`image-task-${linkedTaskId}`)?.scrollIntoView({
				behavior: 'smooth',
				block: 'start'
			});
		}
	});

	onDestroy(() => {
		generationEventStream.stop();
		imageQuoteStateMachine.dispose();
		if (taskPollTimer) clearInterval(taskPollTimer);
		if (elapsedTimer) clearInterval(elapsedTimer);
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
		{#snippet imageTabs()}
			<div
				class="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-gray-200/80 bg-white/80 p-1 shadow-lg shadow-black/10 backdrop-blur-xl dark:border-gray-700/80 dark:bg-gray-900/80 dark:shadow-black/30"
				role="tablist"
				tabindex="-1"
				aria-label={$i18n.t('Images')}
				on:keydown={handleTabKeydown}
			>
				<button
					id="images-generate-tab"
					type="button"
					role="tab"
					aria-selected={selection === 'generate'}
					aria-controls="images-generate-panel"
					tabindex={selection === 'generate' ? 0 : -1}
					class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all sm:min-h-10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
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
					class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all sm:min-h-10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
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
						class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all sm:min-h-10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 {selection ===
						'all'
							? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
							: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
						on:click={() => selectSelection('all')}
					>
						{$i18n.t('All creations')}
					</button>
				{/if}
			</div>
		{/snippet}

		{#if $mobile}
			<!-- 移动端：sidebar 图标与创作/我的作品 tab 同处顶部一行，顶到页面最上面。
			     tab 用绝对定位相对整行居中，不被左侧 sidebar 按钮挤偏右，垂直也随行高居中。 -->
			<nav
				class="relative z-40 flex h-14 shrink-0 items-center px-3 backdrop-blur-xl drag-region select-none"
			>
				<div class="{$showSidebar ? 'md:hidden' : ''} relative z-10 flex flex-none items-center">
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
				<div
					class="pointer-events-none absolute inset-y-0 left-0 right-0 flex items-center justify-center"
				>
					{@render imageTabs()}
				</div>
			</nav>
		{:else}
			<!-- 桌面端：nav 不渲染，tab pill 浮动在内容区顶部。 -->
			<div class="pointer-events-none absolute inset-x-0 top-0 z-30 flex justify-center px-3 pt-2">
				{@render imageTabs()}
			</div>
		{/if}

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
						<!-- 连续流：每批一块极淡背景卡片。块内消息头→prompt→pill→图网格→操作行，space-y-3 统一间距。 -->
						<section class="space-y-4 pb-6 pt-4 sm:pt-18" aria-live="polite">
							{#each generationBatches as batch (batch.id)}
								<ImageBatchCard
									{batch}
									models={primaryModels}
									{canHover}
									supportsEditing={selectedModelSupportsEditing}
									{elapsedNow}
									downloading={batchDownloadingIds.has(batch.id)}
									deleting={batchDeletingIds.has(batch.id)}
									onPreview={openImagePreview}
									onDownloadImage={downloadImage}
									onReuseAsReference={reuseImageAsReference}
									onRemix={reuseImageGenerate}
									onEditAgain={reuseBatchEdit}
									onRegenerate={reuseBatchGenerate}
									onDownloadBatch={downloadBatchImages}
									onRemove={requestDeleteBatch}
								/>
							{/each}

							{#if recentTasksCursor}
								<!-- 加载更早的批次：无限滚动哨兵 + 加载态 Spinner，与作品库分页保持一致 -->
								<div class="flex justify-center py-4">
									{#if loadingMoreTasks}
										<Spinner className="size-5" />
									{:else}
										<Loader on:visible={() => void loadMoreRecentTasks()} />
									{/if}
								</div>
							{:else}
								<!-- 已无可加载的更早批次（7 天窗口内全部展示完）；提示去「我的作品」查看更早记录 -->
								<div class="flex justify-center py-4">
									<button
										type="button"
										class="text-xs text-gray-400 transition hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
										on:click={() => selectSelection('mine')}
									>
										{$i18n.t('View older creations in My Creations')}
									</button>
								</div>
							{/if}
						</section>
					{/if}
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
						{modelBasePrice}
						{getAdvancedNumberError}
						{advancedRangeLabel}
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

		<div
			id="images-library-panel"
			role="tabpanel"
			aria-labelledby={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}
			class="flex-1 min-h-0 overflow-y-auto"
			hidden={view !== 'library'}
		>
			<!--
				Top clearance belongs to the scrolling content, not to the
				panel frame: on desktop it pushes the first row below the
				floating tab pill on first paint, then scrolls away so later
				rows settle flush against the top while the
				absolutely-positioned pill keeps floating over them. On mobile
				the pill now lives in the top navbar (in-flow), so no cushion
				is needed there.
			-->
			<div class="pt-4 sm:pt-18">
				<CreationsLibrary
					active={view === 'library'}
					scope={libraryScope}
					revision={libraryRevision}
					onReuse={applyCreationDraft}
					mediaKind="image"
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

		<ConfirmDialog
			bind:show={showBatchDeleteConfirm}
			title={$i18n.t('Remove record?')}
			message={$i18n.t('Remove this record from your history?')}
			confirmLabel={$i18n.t('Remove')}
			onConfirm={confirmDeleteBatch}
		/>

		<ImagePreview bind:show={showImagePreview} src={previewImageUrl} alt={previewImageAlt} />
	</div>
{/if}
