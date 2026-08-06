<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { quoteImageCredits, type ImageQuoteInput } from '$lib/apis/credits';
	import { getImageGenerationErrorCode } from '$lib/apis/images/generation';
	import {
		createImageGenerationTask,
		deleteImageGenerationTask,
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
		isProxyModel,
		stripVendorFromName
	} from '$lib/utils/images-dropdown';
	import { blobExtension, downloadBlob, zipAndDownload } from '$lib/utils/download';

	import Image from '$lib/components/common/Image.svelte';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import VendorLogo from '$lib/components/common/VendorLogo.svelte';
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
	// 最近生成流的 keyset 分页游标。null 表示没有更早的批次可加载。
	let recentTasksCursor: string | null = null;
	let loadingMoreTasks = false;
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

	let promptTextareaElement: HTMLTextAreaElement;
	let fileInputElement: HTMLInputElement;
	let modelSelectorElement: HTMLDivElement;
	let imageOptionsElement: HTMLDivElement;
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

	// ===== 结果块（heytop 式聊天消息卡片）展示范式 =====
	// 每个 batch 是一条「消息记录」：消息头(模型短名+时间) → 全展开 prompt
	// → pill 参数行 → 图网格(正方形) → 操作行(重新编辑 i2i / 重新生成 t2i)。
	// 块最大宽与输入框同宽对齐；图片一律 aspect-square 占满格，统一网格高度。
	// 桌面端 1×4 横排正方形；中屏 2 列；移动端单图占满、2–4 图横滚 strip。
	// 用 flex flex-col gap-3 统一行间距，避免 space-y 的 margin 被 m-0 等覆盖导致行间塌陷。
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
		'relative flex items-center justify-center overflow-hidden rounded-lg border border-gray-200/80 bg-stone-50 aspect-square w-full dark:border-gray-800/80 dark:bg-gray-900/40';

	const getGeneratedImageClass = () => 'block h-full w-full object-cover';

	// 生成中骨架保持正方形；失败状态使用紧凑提示卡，避免占据大面积空白。
	const batchSquareStyle = () => 'aspect-ratio: 1 / 1; width: 100%;';

	// 长 prompt 不再折叠：heytop 式全展开，让块自然变高。
	const generationStatusLabel = (batch: ImageGenerationBatch) => {
		if (batch.status === 'queued') return $i18n.t('Queued');
		if (batch.status === 'running') return $i18n.t('Generating');
		if (batch.status === 'failed') return $i18n.t('Generation failed');
		return $i18n.t('Completed');
	};

	// 消息头模型短名：剥厂商前缀，回退到默认模型。
	// 注意：必须把 primaryModels 作为参数显式传入并在模板里写出，
	// 否则 Svelte 4 不会把 primaryModels 当作响应式依赖 —— models 异步加载
	// 完成后已渲染的 batch 消息头不会刷新，会一直停在「默认模型」回退态，
	// 直到 generationBatches 因新生成而重渲染才“突然”显示真名。
	// 按 batch.modelId 在当前模型列表里查回 model 对象（含 provider），供消息头厂商图标使用。
	// 同样需把 modelList 作为参数显式传入，保证 Svelte 响应式追踪。
	const getBatchModel = (batch: ImageGenerationBatch, modelList: ImageGenerationModel[]) =>
		modelList.find((m) => m.id === batch.modelId) ?? null;

	const getBatchModelLabel = (batch: ImageGenerationBatch, modelList: ImageGenerationModel[]) => {
		const model = getBatchModel(batch, modelList);
		return model ? stripVendorFromName(model) : $i18n.t('Default Model');
	};

	// pill 参数：模型 · 比例 · 分辨率(若有) · 张数 · 质量(若有)。
	// 同样需显式传 modelList，让模板引用 primaryModels 触发响应式。
	const getBatchMetaPills = (batch: ImageGenerationBatch, modelList: ImageGenerationModel[]) => {
		const pills = [getBatchModelLabel(batch, modelList), getAspectRatioLabel(batch.aspectRatio)];
		if (batch.resolution) pills.push(getResolutionLabel(batch.resolution));
		pills.push(String(batch.expectedCount));
		const q = batch.quality?.trim();
		if (q) pills.push(getQualityLabel(q));
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
	const getBatchTime = (batch: ImageGenerationBatch) =>
		formatBatchTime(batch.completedAt ?? batch.startedAt ?? batch.createdAt);

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
			toast.success($i18n.t('Record removed'));
		} catch {
			toast.error($i18n.t('Failed to remove record'));
		} finally {
			const next = new Set(batchDeletingIds);
			next.delete(batch.id);
			batchDeletingIds = next;
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

	const RECENT_TASKS_PAGE_SIZE = 10;

	const loadRecentGenerationTasks = async () => {
		try {
			const { items, next_cursor } = await listImageGenerationTasks(
				localStorage.token,
				RECENT_TASKS_PAGE_SIZE
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
				recentTasksCursor
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
			// 新生成结果插入到列表最上面，提交后自动滚到顶，让用户立刻看到新 batch 的进度。
			generationPanelElement?.scrollTo({ top: 0, behavior: 'smooth' });
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
		taskPollTimer = setInterval(() => void pollGenerationTasks(), 2_000);
		elapsedTimer = setInterval(() => (elapsedNow = Date.now()), 1_000);
		await tick();
		if (linkedTaskId) {
			document.getElementById(`image-task-${linkedTaskId}`)?.scrollIntoView({
				behavior: 'smooth',
				block: 'start'
			});
		}
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
						<section class="space-y-4 pb-6 pt-18 sm:pt-18" aria-live="polite">
							{#each generationBatches as batch (batch.id)}
								<article id={`image-task-${batch.id}`} class={BATCH_ARTICLE_CLASS}>
									<!-- 消息头：厂商图标 + 模型短名 + 时间 -->
									<div class="flex items-center gap-2">
										{#if getBatchModel(batch, primaryModels)?.provider}
											<VendorLogo
												provider={getBatchModel(batch, primaryModels).provider}
												className="size-5 shrink-0 rounded-full object-cover"
											/>
										{:else}
											<span
												class="size-5 shrink-0 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-600 dark:to-gray-700"
											></span>
										{/if}
										<span
											class="min-w-0 truncate text-sm font-medium text-gray-800 dark:text-gray-100"
											>{getBatchModelLabel(batch, primaryModels)}</span
										>
										<span class="ml-auto shrink-0 text-[11px] text-gray-400 dark:text-gray-500"
											>{getBatchTime(batch)}</span
										>
									</div>

									<!-- prompt：全展开，不折叠 -->
									<p
										class="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed text-gray-700 dark:text-gray-200"
									>
										{batch.prompt}
									</p>

									<!-- pill 参数行：模型 · 比例 · 分辨率 · 张数 · 质量；生成中附状态 -->
									<div class="flex flex-wrap items-center gap-1.5">
										{#each getBatchMetaPills(batch, primaryModels) as pill, index (`${index}-${pill}`)}
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
												{generationStatusLabel(batch)} · {generationElapsedSeconds(
													batch,
													elapsedNow
												)}s
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
															on:click={() => openImagePreview(image)}
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
																class="pointer-events-auto inline-flex size-7 items-center justify-center rounded-full bg-white/90 text-gray-800 shadow backdrop-blur transition hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:bg-gray-900/90 dark:text-gray-100 dark:hover:bg-gray-900"
																on:click|stopPropagation={() => downloadImage(image, index)}
																aria-label={$i18n.t('Download')}
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
																	><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" /></svg
																>
															</button>
															{#if selectedModelSupportsEditing}
																<button
																	type="button"
																	class="pointer-events-auto inline-flex size-7 items-center justify-center rounded-full bg-white/90 text-gray-800 shadow backdrop-blur transition hover:bg-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:bg-gray-900/90 dark:text-gray-100 dark:hover:bg-gray-900"
																	on:click|stopPropagation={() =>
																		reuseImageAsReference(batch, image)}
																	aria-label={$i18n.t('Use as reference')}
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
																		><rect x="3" y="3" width="18" height="18" rx="2" /><circle
																			cx="8.5"
																			cy="9"
																			r="1.5"
																		/><path d="M21 15l-5-5L5 21" /></svg
																	>
																</button>
															{/if}
														</div>
														<!-- 基于此图 prompt 重新生成：触屏常驻可见，桌面端 hover 显现 -->
														{#if image.prompt}
															<button
																type="button"
																class="pointer-events-auto absolute bottom-1.5 left-1.5 inline-flex h-6 items-center gap-1 rounded-full bg-black/60 px-2 text-[10px] font-medium text-white backdrop-blur transition hover:bg-black/75 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white {canHover
																	? 'opacity-0 group-hover:opacity-100'
																	: 'opacity-100'}"
																on:click|stopPropagation={() => reuseImageGenerate(batch, image)}
																aria-label={$i18n.t('Generate from this prompt')}
															>
																<svg
																	class="size-3"
																	viewBox="0 0 24 24"
																	fill="none"
																	stroke="currentColor"
																	stroke-width="2"
																	stroke-linecap="round"
																	stroke-linejoin="round"
																	aria-hidden="true"
																	><path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5" /></svg
																>
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
													{$i18n.t('Generation failed')}
												</p>
												{#if batch.errorCode}<p class="mt-1 text-xs text-red-500/80">
														{batch.errorCode}
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
															<span
																>{$i18n.t('Creating image {{index}}', { index: index + 1 })}</span
															>
														</div>
													</div>
												{/each}
											</div>
										{/if}
									</div>

									<!-- 操作行：再次编辑(i2i) + 重新生成(t2i) + 下载本批(ZIP)，紧凑次级按钮 -->
									<div class="flex flex-wrap items-center gap-1.5">
										<button
											type="button"
											class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-2.5 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
											on:click={() => reuseBatchEdit(batch)}
											disabled={batch.images.length === 0}
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
												><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg
											>
											{$i18n.t('Edit again')}
										</button>
										<button
											type="button"
											class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-2.5 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
											on:click={() => reuseBatchGenerate(batch)}
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
										{#if batch.images.length > 1}
											<!-- 本批批量下载：打包成 ZIP，复用 $lib/utils/download 的共享方案 -->
											<button
												type="button"
												class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-2.5 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
												on:click={() => downloadBatchImages(batch)}
												disabled={batchDownloadingIds.has(batch.id)}
											>
												{#if batchDownloadingIds.has(batch.id)}
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
												{$i18n.t('Download all ({{count}})', { count: batch.images.length })}
											</button>
										{/if}
										<button
											type="button"
											class="inline-flex h-7 items-center justify-center gap-1.5 rounded-lg bg-gray-100 px-2.5 text-xs font-medium text-gray-600 transition hover:bg-gray-200 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-gray-100"
											on:click={() => requestDeleteBatch(batch)}
											disabled={batchDeletingIds.has(batch.id)}
											aria-label={$i18n.t('Remove record')}
										>
											{#if batchDeletingIds.has(batch.id)}
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
							{/if}
						</section>
					{/if}
				</div>

				<div
					class="sticky bottom-0 z-20 -mx-3 md:-mx-6 px-3 md:px-6 pt-10 pb-3 bg-gradient-to-t from-white via-white/95 to-white/0 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0"
				>
					<div class="mx-auto w-full max-w-5xl sm:px-2">
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
											<VendorLogo
												provider={selectedModelConfig.provider}
												className="size-4 shrink-0 rounded-sm"
											/>
										{:else}
											<Photo className="size-4 shrink-0" strokeWidth="2" />
										{/if}
										<span class="truncate">{selectedModelLabel}</span>
										<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">⌄</span>
									</button>

									{#if showModelSelector}
										<div
											class="fixed inset-x-3 bottom-14 z-50 h-[min(60dvh,28rem)] min-w-0 overflow-hidden overscroll-contain rounded-2xl border border-gray-100 bg-white p-2 shadow-xl sm:absolute sm:inset-x-auto sm:bottom-10 sm:left-0 sm:z-30 sm:h-80 sm:w-[30rem] sm:p-2 dark:border-gray-800 dark:bg-gray-900"
											role="listbox"
											aria-label={$i18n.t('Select image model')}
										>
											<div class="flex h-full min-h-0 min-w-0 flex-row gap-2 sm:min-w-[22rem]">
												<!-- Brand level (left/top) -->
												<ul
													class="flex min-h-0 w-28 shrink-0 flex-col gap-1 overflow-y-auto overflow-x-hidden overscroll-contain border-r border-gray-100 pr-1 dark:border-gray-800 sm:w-40 sm:pr-1"
													role="group"
													aria-label={$i18n.t('Brands')}
												>
													{#each vendorList as vendor}
														<li class="snap-start">
															<button
																type="button"
																class="flex min-w-0 w-full shrink-0 items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition {selectedVendor ===
																vendor
																	? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
																	: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
																on:click={() => (selectedVendor = vendor)}
																aria-pressed={selectedVendor === vendor}
															>
																<VendorLogo
																	provider={vendor}
																	alt={vendor}
																	className="size-4 shrink-0 rounded-sm"
																/>
																<span class="min-w-0 truncate capitalize">{vendor}</span>
															</button>
														</li>
													{/each}
												</ul>
												<!-- Model level (right/bottom) -->
												<ul
													class="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain sm:h-full"
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
																	: model.enabled === false
																		? 'cursor-not-allowed text-gray-400 dark:text-gray-600'
																		: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
																on:click={() => selectModelIfEnabled(model)}
																role="option"
																aria-selected={selectedModel === model.id}
																aria-disabled={model.enabled === false}
															>
																{#if model.provider}
																	<VendorLogo
																		provider={model.provider}
																		className="size-4 shrink-0 rounded-sm"
																	/>
																{/if}
																<span class="min-w-0 flex-1 text-left">
																	<span class="flex min-w-0 items-center gap-1.5">
																		<span class="truncate">{stripVendorFromName(model)}</span>
																		{#if model.recommended}<span
																				class="shrink-0 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
																				>{$i18n.t('Recommended')}</span
																			>{/if}
																	</span>
																	{#if model.tags?.length}<span
																			class="mt-0.5 block truncate text-[11px] text-gray-400"
																			>{model.tags.join(' · ')}</span
																		>{/if}
																	{#if model.maintenanceMessage}<span
																			class="mt-0.5 block line-clamp-2 text-[11px] text-orange-600 dark:text-orange-400"
																			>{model.maintenanceMessage}</span
																		>{/if}
																</span>
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
