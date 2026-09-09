<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';

	import { uploadFile } from '$lib/apis/files';
	import { quoteVideoCredits, type VideoQuote } from '$lib/apis/credits';
	import {
		getVideoModels,
		getVideoTask,
		listVideoTasks,
		deleteVideoTask,
		submitVideoTask,
		VideoRequestError,
		type VideoAssetCapability,
		type VideoAssetRole,
		type VideoGenerationTask,
		type VideoModel,
		type VideoTask
	} from '$lib/apis/videos';
	import { WEBUI_NAME, showSidebar } from '$lib/stores';
	import CreationDetailsModal from '$lib/components/images/CreationDetailsModal.svelte';
	import MobileSidebarHeader from '$lib/components/common/MobileSidebarHeader.svelte';
	import type { ImageQuoteState } from '$lib/components/credits/quote-state';
	import Loader from '$lib/components/common/Loader.svelte';
	import Play from '$lib/components/icons/Play.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import { stripVendorFromName } from '$lib/utils/images-dropdown';
	import { downloadBlob } from '$lib/utils/download';
	import {
		firstVideoAdvancedError,
		normalizeVideoParamsForModel,
		videoDurationChoices
	} from '$lib/utils/video-generation';
	import { createGenerationEventStream } from '$lib/utils/generation-events';
	import { createSubmissionIdempotency } from '$lib/utils/submission-idempotency';
	import { appendPromptText } from '$lib/components/prompt-tags/tagToggle';
	import VideoTaskCard from './VideoTaskCard.svelte';
	import VideoPromptForm from './VideoPromptForm.svelte';
	import {
		defaultVideoParams,
		imageQuoteStateFromVideoQuote,
		preferredVideoModelId,
		prepareVideoSubmission,
		videoQuoteDimensions,
		type VideoSubmissionError
	} from './videoPageState';
	import {
		videoAdvancedFieldLabels,
		videoAssetLabels,
		videoCreditErrorI18nKey,
		videoTaskErrorI18nKey,
		videoTaskOptions,
		type UploadedVideoAsset
	} from './videoLabels';

	const i18n = getContext<Writable<I18n>>('i18n');

	let task: VideoTask = 'text-to-video';
	let models: VideoModel[] = [];
	let defaults: Record<VideoTask, string> | null = null;
	let modelId = '';
	let prompt = '';
	let params: Record<string, string | number | boolean | null> = {};

	// 提交幂等键：网络失败后的重试复用同一指纹的键，服务端幂等重放返回
	// 既有任务而不是二次扣费；收到确定性响应后清除。
	const videoSubmissionIdempotency = createSubmissionIdempotency('pending-video-submission');

	// 标签是快捷提示词片段：点击即把 insert_text 追加进对应的输入框，
	// 提交的就是输入框里所见即所得的纯文本（负面标签进负向提示词参数）。
	const handlePromptTagInsert = (event: CustomEvent<{ text: string; isNegative: boolean }>) => {
		const { text, isNegative } = event.detail;
		if (isNegative) {
			params = {
				...params,
				negative_prompt: appendPromptText(String(params['negative_prompt'] ?? ''), text)
			};
		} else {
			prompt = appendPromptText(prompt, text);
		}
	};
	let assets: Partial<Record<VideoAssetRole, UploadedVideoAsset[]>> = {};
	let history: VideoGenerationTask[] = [];
	let loading = true;
	let recentCursor: string | null = null;
	let loadingMore = false;
	let submitting = false;
	let showAdvanced = false;
	// 弹层开关：changeTask/changeModel 选中后需主动关闭（选择器自身不关闭）。
	let showModelSelector = false;
	let showVideoOptions = false;
	let taskFallbackPollTimer: ReturnType<typeof setInterval> | null = null;
	let quoteState: ImageQuoteState = { status: 'loading' };
	let quoteTimer: ReturnType<typeof setTimeout> | null = null;
	let quoteGeneration = 0;
	let showCreationDetails = false;
	let detailsTask: VideoGenerationTask | null = null;
	let showDeleteConfirm = false;
	let taskToDelete: VideoGenerationTask | null = null;
	let downloadingIds: Set<string> = new Set();
	let deletingIds: Set<string> = new Set();
	let selectedVendor = '';

	$: taskModels = models.filter((item) => item.task === task && item.visible !== false);
	$: selectedModel = taskModels.find((item) => item.id === modelId) ?? taskModels[0] ?? null;
	$: modelVendors = [...new Set(taskModels.map((item) => item.provider))];
	$: if (!modelVendors.includes(selectedVendor)) {
		selectedVendor = selectedModel?.provider ?? modelVendors[0] ?? '';
	}
	$: vendorModels = taskModels.filter((item) => item.provider === selectedVendor);
	$: advancedFields = selectedModel?.advanced_fields ?? [];
	$: advancedError = firstVideoAdvancedError(selectedModel, params);
	$: durationChoices = videoDurationChoices(selectedModel);
	$: quoteKey = selectedModel
		? JSON.stringify([
				task,
				selectedModel.id,
				params.duration,
				params.resolution,
				params.aspect_ratio,
				params.audio_mode,
				params.fps,
				params.output_quality
			])
		: '';
	$: if (!loading && quoteKey) scheduleQuote();

	const quoteDimensions = () => videoQuoteDimensions(params, selectedModel);

	const refreshQuote = async (
		model: VideoModel | null = selectedModel,
		dimensions: Record<string, string | number> = quoteDimensions(),
		action: VideoTask = task
	): Promise<VideoQuote | null> => {
		if (!model) return null;
		const generation = ++quoteGeneration;
		try {
			const next = await quoteVideoCredits(localStorage.token, {
				resource_id: model.id,
				action,
				dimensions
			});
			if (generation === quoteGeneration) quoteState = imageQuoteStateFromVideoQuote(next);
			return next;
		} catch {
			if (generation === quoteGeneration) {
				quoteState = { status: 'error' };
			}
			return null;
		}
	};

	const scheduleQuote = () => {
		if (quoteTimer) clearTimeout(quoteTimer);
		quoteState = { status: 'loading' };
		quoteTimer = setTimeout(refreshQuote, 250);
	};

	const videoRequestErrorMessage = (fallback: string) => $i18n.t(fallback);

	const videoTaskErrorMessage = (record: VideoGenerationTask) =>
		$i18n.t(videoTaskErrorI18nKey[record.error_code ?? ''] ?? 'Generation failed');

	const showSubmissionError = (failure: VideoSubmissionError) => {
		if (failure.kind === 'prompt') return toast.error($i18n.t('Please enter a prompt'));
		if (failure.kind === 'asset')
			return toast.error(`${$i18n.t(videoAssetLabels[failure.role])} ${$i18n.t('is required')}`);
		if (failure.kind === 'negative_prompt')
			return toast.error(
				$i18n.t('This model does not support negative prompts; remove it or pick another model.')
			);
		const { field, error } = failure.error;
		toast.error(
			`${$i18n.t(videoAdvancedFieldLabels[field.key])}: ${$i18n.t(
				error.key,
				error.value === undefined ? {} : { value: error.value }
			)}`
		);
	};

	const resetForModel = (model: VideoModel | null) => {
		assets = {};
		showAdvanced = false;
		params = defaultVideoParams(model);
	};

	const preferredModelId = (nextTask: VideoTask, preferred?: string | null) =>
		preferredVideoModelId(models, nextTask, preferred);

	const changeTask = (next: VideoTask) => {
		task = next;
		showModelSelector = false;
		showVideoOptions = false;
		modelId = preferredModelId(next, defaults?.[next]);
		resetForModel(models.find((model) => model.id === modelId) ?? null);
	};

	const changeModel = (next: string) => {
		modelId = next;
		showModelSelector = false;
		resetForModel(models.find((model) => model.id === next) ?? null);
	};

	// 创作页只展示最近 7 天的任务，更早的需到「我的作品」里查看。
	// 时间窗以「当前时间 - 7 天」的秒级时间戳传给后端 since；进行中任务不受窗限制。
	const RECENT_TASKS_PAGE_SIZE = 20;
	const RECENT_WINDOW_SECONDS = 7 * 24 * 60 * 60;
	const recentSince = () => Math.floor(Date.now() / 1000) - RECENT_WINDOW_SECONDS;

	const load = async () => {
		loading = true;
		try {
			const [catalog, tasks] = await Promise.all([
				getVideoModels(localStorage.token),
				listVideoTasks(localStorage.token, RECENT_TASKS_PAGE_SIZE, null, recentSince())
			]);
			models = catalog.models;
			defaults = catalog.defaults;
			modelId = preferredModelId(task, catalog.defaults[task]);
			resetForModel(models.find((model) => model.id === modelId) ?? null);
			const rawDraft = localStorage.getItem('video-creation-draft');
			if (rawDraft) {
				localStorage.removeItem('video-creation-draft');
				try {
					const draft = JSON.parse(rawDraft);
					const draftTask = videoTaskOptions.some((item) => item.id === draft.task)
						? (draft.task as VideoTask)
						: task;
					const draftModel = models.find(
						(item) => item.task === draftTask && item.id === draft.model
					);
					task = draftTask;
					modelId = preferredModelId(draftTask, draftModel?.id ?? catalog.defaults[draftTask]);
					resetForModel(models.find((model) => model.id === modelId) ?? null);
					prompt = typeof draft.prompt === 'string' ? draft.prompt : '';
					if (draft.params && typeof draft.params === 'object' && !Array.isArray(draft.params)) {
						const rawNegative = (draft.params as Record<string, unknown>).negative_prompt;
						const model = models.find((item) => item.id === modelId);
						if (model)
							params = normalizeVideoParamsForModel(model, {
								...params,
								...draft.params,
								...(typeof rawNegative === 'string' ? { negative_prompt: rawNegative } : {})
							});
					}
				} catch {
					// Ignore stale or malformed local drafts.
				}
			}
			history = tasks.items;
			recentCursor = tasks.next_cursor ?? null;
		} catch {
			toast.error(videoRequestErrorMessage('Failed to load video generation'));
		} finally {
			loading = false;
		}
	};

	const loadMoreTasks = async () => {
		if (loadingMore || !recentCursor) return;
		loadingMore = true;
		try {
			const tasks = await listVideoTasks(
				localStorage.token,
				RECENT_TASKS_PAGE_SIZE,
				recentCursor,
				recentSince()
			);
			// 去重合并，按 created_at 降序保持稳定；新页靠后追加，避免全量重排。
			const seen = new Set(history.map((item) => item.id));
			history = [...history, ...tasks.items.filter((item) => !seen.has(item.id))];
			recentCursor = tasks.next_cursor ?? null;
		} catch {
			toast.error(videoRequestErrorMessage('Failed to load more videos'));
		} finally {
			loadingMore = false;
		}
	};
	const uploadAsset = async (capability: VideoAssetCapability, files: FileList | null) => {
		if (!files?.length) return;
		const existing = assets[capability.role] ?? [];
		const room = capability.max_count - existing.length;
		const selected = Array.from(files).slice(0, capability.multiple ? room : 1);
		try {
			const uploadedFiles = await Promise.all(
				selected.map(async (file) => {
					if (!capability.mime_types.includes(file.type)) throw new Error('unsupported_type');
					if (file.size > capability.max_bytes) throw new Error('too_large');
					const result = await uploadFile(
						localStorage.token,
						file,
						{ video_input: true },
						false,
						false
					);
					return { file, id: result.id };
				})
			);
			// 复盘：ObjectURL 统一在上传全部成功后创建——任一文件失败时本轮
			// 不产生需要清理的已建 URL（原先在 map 内创建，Promise.all 中途
			// 失败即泄漏）。
			const uploaded = uploadedFiles.map(({ file, id }) => ({
				id,
				name: file.name,
				url: URL.createObjectURL(file),
				mime_type: file.type
			}));
			const previousUrls = existing.map((item) => item.url);
			assets = {
				...assets,
				[capability.role]: capability.multiple ? [...existing, ...uploaded] : uploaded
			};
			// 复盘：单选角色覆盖旧资产时必须释放其 ObjectURL。
			if (!capability.multiple) {
				for (const url of previousUrls) URL.revokeObjectURL(url);
			}
		} catch (error) {
			toast.error(
				videoRequestErrorMessage(
					error instanceof Error && error.message === 'unsupported_type'
						? 'Unsupported file type'
						: error instanceof Error && error.message === 'too_large'
							? 'File is too large'
							: 'Failed to upload video asset'
				)
			);
		}
	};

	const removeAsset = (role: VideoAssetRole, id: string) => {
		const current = assets[role] ?? [];
		const removed = current.find((item) => item.id === id);
		if (removed) URL.revokeObjectURL(removed.url);
		assets = { ...assets, [role]: current.filter((item) => item.id !== id) };
	};

	const applyVideoTaskUpdate = (next: VideoGenerationTask) => {
		const previous = history.find((item) => item.id === next.id);
		history = [next, ...history.filter((item) => item.id !== next.id)];
		if (next.status === 'succeeded' && previous?.status !== 'succeeded') {
			toast.success($i18n.t('Video generated'));
		} else if (next.status === 'failed' && previous?.status !== 'failed') {
			toast.error(videoTaskErrorMessage(next));
		}
	};

	const refreshVideoTask = async (taskId: string) => {
		applyVideoTaskUpdate(await getVideoTask(localStorage.token, taskId));
	};

	const pollActiveVideoTasks = async () => {
		const activeIds = history
			.filter((item) => item.status === 'queued' || item.status === 'running')
			.map((item) => item.id);
		await Promise.all(activeIds.map((taskId) => refreshVideoTask(taskId).catch(() => undefined)));
	};

	// SSE 事件流（含指数退避重连与断流兜底轮询）与图片页共享同一实现。
	const generationEventStream = createGenerationEventStream(
		'video',
		refreshVideoTask,
		pollActiveVideoTasks
	);

	const generate = async () => {
		if (!selectedModel || submitting) return;
		const submittedTask = task;
		const submitModel = models.find(
			(model) =>
				model.id === selectedModel?.id &&
				model.task === submittedTask &&
				model.visible !== false &&
				model.enabled !== false
		);
		if (!submitModel) {
			toast.error($i18n.t('This model is temporarily unavailable.'));
			return;
		}
		// 复盘：submitting 必须先于任何 await 置位——原先在 refreshQuote() 之后，
		// 报价请求的网络往返期间二次点击会重入提交流程（首单成功清理幂等键后，
		// 第二次点击拿到新键即产生真实的重复扣费请求）。
		submitting = true;
		try {
			const prepared = prepareVideoSubmission(
				submittedTask,
				submitModel,
				prompt,
				params,
				assets,
				advancedError
			);
			if (prepared.ok === false) {
				showSubmissionError(prepared.error);
				return;
			}
			const latestQuote = await refreshQuote(submitModel, quoteDimensions(), submittedTask);
			if (
				task !== submittedTask ||
				selectedModel?.id !== submitModel.id ||
				!models.some(
					(model) =>
						model.id === submitModel.id &&
						model.task === submittedTask &&
						model.visible !== false &&
						model.enabled !== false
				)
			) {
				toast.error($i18n.t('This model is temporarily unavailable.'));
				return;
			}
			if (!latestQuote?.configured) {
				toast.error($i18n.t('Video price is not configured'));
				return;
			}
			if (!latestQuote.exempt && !latestQuote.sufficient) {
				toast.error($i18n.t('Insufficient credits'));
				return;
			}
			const submission = prepared.value;
			const idempotencyKey = await videoSubmissionIdempotency.idempotencyKeyFor(submission);
			const created = await submitVideoTask(localStorage.token, submission, idempotencyKey);
			videoSubmissionIdempotency.clearPendingSubmission();
			// 新任务插入列表顶部，立刻可见其生成进度。
			// SSE 可能先于 POST 响应写入同一任务；此时保留 SSE 读到的较新状态，
			// 既避免重复卡片，也避免用 queued 响应覆盖 running/succeeded。
			if (!history.some((item) => item.id === created.id)) history = [created, ...history];
		} catch (error) {
			// A structured HTTP response is definitive. A network failure is not:
			// retain the same key so a retry cannot create a second paid request.
			if (
				error instanceof VideoRequestError &&
				error.status !== undefined &&
				error.status >= 400 &&
				error.status < 500 &&
				![408, 429].includes(error.status)
			) {
				videoSubmissionIdempotency.clearPendingSubmission();
			}
			const code = error instanceof VideoRequestError ? error.code : '';
			const i18nKey = videoCreditErrorI18nKey[code];
			toast.error(
				error instanceof VideoRequestError && error.preferPublicMessage && error.publicMessage
					? error.publicMessage
					: i18nKey
						? videoRequestErrorMessage(i18nKey)
						: error instanceof VideoRequestError && error.publicMessage
							? error.publicMessage
							: videoRequestErrorMessage('Video generation failed')
			);
		} finally {
			submitting = false;
		}
	};

	onMount(() => {
		void load();
		void generationEventStream.start();
		// SSE 断线、代理不支持流式响应或事件落在其他 worker 时，用低频轮询补偿。
		taskFallbackPollTimer = setInterval(() => void pollActiveVideoTasks(), 10_000);
	});
	onDestroy(() => {
		generationEventStream.stop();
		if (taskFallbackPollTimer) clearInterval(taskFallbackPollTimer);
		if (quoteTimer) clearTimeout(quoteTimer);
		for (const items of Object.values(assets)) {
			for (const item of items ?? []) URL.revokeObjectURL(item.url);
		}
	});

	// 复用某条历史任务：把 task/model/prompt/params 带回表单，并通过
	// localStorage 草稿在跨页面跳转回来后恢复（与 CreationDetailsModal 写入的
	// 'video-creation-draft' 同键，这里只做应用，不持久化跨刷新草稿）。
	const reuseTask = (record: VideoGenerationTask) => {
		task = record.task;
		modelId = preferredModelId(record.task, record.model_id);
		resetForModel(models.find((model) => model.id === modelId) ?? null);
		prompt = record.prompt ?? '';
		if (record.params && typeof record.params === 'object' && !Array.isArray(record.params)) {
			const rawNegative = (record.params as Record<string, unknown>).negative_prompt;
			const model = models.find((item) => item.id === modelId);
			if (model) {
				params = normalizeVideoParamsForModel(model, {
					...params,
					...(record.params as Record<string, string | number | boolean | null>),
					...(typeof rawNegative === 'string' ? { negative_prompt: rawNegative } : {})
				});
			}
		}
		toast.success($i18n.t('Parameters loaded'));
	};

	// 下载生成结果：把视频文件以 creation-<id>.mp4 落到本地。
	const downloadResult = async (record: VideoGenerationTask) => {
		const url = record.result?.url;
		if (!url) return;
		if (downloadingIds.has(record.id)) return;
		downloadingIds = new Set(downloadingIds).add(record.id);
		try {
			const response = await fetch(url);
			if (!response.ok) throw new Error('download failed');
			const blob = await response.blob();
			downloadBlob(blob, `creation-${record.id}.mp4`);
		} catch {
			toast.error($i18n.t('Failed to download video'));
		} finally {
			const next = new Set(downloadingIds);
			next.delete(record.id);
			downloadingIds = next;
		}
	};

	// 删除任务：带二次确认，删除后从列表移除该条记录。
	const requestDeleteTask = (record: VideoGenerationTask) => {
		if (deletingIds.has(record.id)) return;
		taskToDelete = record;
		showDeleteConfirm = true;
	};

	const confirmDeleteTask = async () => {
		const record = taskToDelete;
		taskToDelete = null;
		if (!record) return;
		deletingIds = new Set(deletingIds).add(record.id);
		try {
			await deleteVideoTask(localStorage.token, record.id);
			history = history.filter((item) => item.id !== record.id);
			toast.success($i18n.t('Record removed'));
		} catch {
			toast.error($i18n.t('Failed to remove record'));
		} finally {
			const next = new Set(deletingIds);
			next.delete(record.id);
			deletingIds = next;
		}
	};
	// 按任务类型查回对应模型（含 provider），供任务卡片厂商图标与模型短名使用。
	const getTaskModel = (record: VideoGenerationTask) =>
		models.find((m) => m.id === record.model_id) ?? null;

	// 打开任务详情弹窗：复用 CreationDetailsModal，指定该任务的 creation_id。
	const openTaskDetails = (record: VideoGenerationTask) => {
		detailsTask = record;
		showCreationDetails = true;
	};

	// CreationDetailsModal 回调：创作被删除时，同步从创作页历史列表移除对应任务。
	const onCreationRemoved = (creationId: string) => {
		history = history.filter((item) => item.result?.creation_id !== creationId);
	};
</script>

<svelte:head>
	<title>{$i18n.t('Videos')} • {$WEBUI_NAME}</title>
</svelte:head>

<div
	class="relative flex h-screen max-h-[100dvh] w-full max-w-full min-w-0 flex-col bg-white text-gray-900 transition-width duration-200 ease-in-out dark:bg-gray-950 dark:text-gray-100 {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''}"
>
	<MobileSidebarHeader />

	<!-- 面板必须是 flex-1 + min-h-0 的 flex 列，否则内部 <main class="overflow-y-auto">
	     的父级无有界高度，滚动容器失效，sticky 输入框会被推到内容最底部（需滚到页底才可见）。
	     对齐 Images.svelte 的 #images-generate-panel 高度链。 -->
	<div class="flex min-h-0 flex-1 flex-col">
		{#if loading}
			<!-- 首载骨架屏：任务卡（头行 + 16:9 播放器）+ 底部表单的页面形状，
			     与发现页/作品库同一 shimmer 模式，替代纯文字 Loading 的「卡住」观感。 -->
			<main class="flex-1 px-4 pt-4 sm:px-6 sm:pt-8 lg:px-8" aria-hidden="true">
				<div class="mx-auto flex min-h-full w-full max-w-5xl flex-col gap-3 sm:px-2">
					{#each Array(2) as _, index (index)}
						<div class="flex flex-col gap-2">
							<div class="flex items-center gap-2">
								<div class="size-5 rounded-full bg-gray-100 dark:bg-white/5"></div>
								<div class="h-3 w-28 rounded bg-gray-100 dark:bg-white/5"></div>
							</div>
							<div class="aspect-video overflow-hidden rounded-2xl bg-gray-100 dark:bg-white/5">
								<div
									class="h-full w-full animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.03]"
								></div>
							</div>
						</div>
					{/each}
					<div class="h-48 overflow-hidden rounded-2xl bg-gray-100 dark:bg-white/5">
						<div
							class="h-full w-full animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.03]"
						></div>
					</div>
				</div>
			</main>
		{:else}
			<div class="flex min-h-0 flex-1 flex-col">
				<main class="flex-1 min-h-0 overflow-y-auto px-4 pt-4 sm:px-6 sm:pt-8 lg:px-8">
					<div class="mx-auto w-full max-w-5xl min-h-full flex flex-col sm:px-2">
						{#if history.length === 0}
							<!-- flex-1 占满剩余高度把表单推到容器底（min-h 硬算在视口/表单高度变化时留残差），对齐 Images.svelte 空态结构 -->
							<section
								class="flex min-h-[calc(100dvh-22rem)] flex-1 items-center justify-center py-12"
							>
								<div class="max-w-md text-center">
									<div
										class="mx-auto mb-4 flex aspect-video w-56 items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900"
									>
										<Play className="size-10 text-gray-300 dark:text-gray-600" strokeWidth="1.5" />
										>
									</div>
									<h2 class="font-medium">{$i18n.t('Start with a video idea')}</h2>
									<p class="mt-1 text-sm text-gray-500">
										{$i18n.t('Choose a mode, add material when needed, then describe the motion')}
									</p>
								</div>
							</section>
						{:else}
							<!-- 任务列表流：每个任务一块卡片，消息头→prompt→pill→播放器→操作行 -->
							<section class="flex flex-col gap-3" aria-live="polite">
								{#each history as taskItem (taskItem.id)}
									<VideoTaskCard
										record={taskItem}
										model={getTaskModel(taskItem)}
										downloading={downloadingIds.has(taskItem.id)}
										deleting={deletingIds.has(taskItem.id)}
										onRegenerate={reuseTask}
										onDownload={downloadResult}
										onViewDetails={openTaskDetails}
										onRemove={requestDeleteTask}
									/>
								{/each}

								{#if recentCursor}
									<!-- 加载更早的任务：无限滚动哨兵 + 加载态 Spinner -->
									<div class="flex justify-center py-4">
										{#if loadingMore}
											<Spinner className="size-5" />
										{:else}
											<Loader on:visible={() => void loadMoreTasks()} />
										{/if}
									</div>
								{:else}
									<!-- 已无可加载的更早任务（7 天窗口内全部展示完）；提示去「资产」查看更早作品 -->
									<div class="flex justify-center py-4">
										<button
											type="button"
											class="min-h-11 text-xs text-gray-400 transition hover:text-gray-600 active:opacity-60 dark:text-gray-500 dark:hover:text-gray-300"
											on:click={() => void goto('/assets')}
										>
											{$i18n.t('View older creations in Assets')}
										</button>
									</div>
								{/if}
							</section>
						{/if}

						<VideoPromptForm
							bind:task
							bind:modelId
							bind:selectedVendor
							bind:prompt
							bind:params
							bind:assets
							bind:showAdvanced
							bind:showModelSelector
							bind:showVideoOptions
							{selectedModel}
							{modelVendors}
							{vendorModels}
							{advancedFields}
							{durationChoices}
							{quoteState}
							{submitting}
							{advancedError}
							onTaskChange={changeTask}
							onModelChange={changeModel}
							onUploadAsset={uploadAsset}
							onRemoveAsset={removeAsset}
							onPromptTagInsert={handlePromptTagInsert}
							onSubmit={generate}
						/>
					</div>
				</main>
			</div>
		{/if}
	</div>
</div>

<CreationDetailsModal
	bind:show={showCreationDetails}
	creationId={detailsTask?.result?.creation_id ?? null}
	scope="mine"
	canManage
	onRemoved={onCreationRemoved}
/>

<ConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Remove record?')}
	message={$i18n.t('Remove this record from your history?')}
	confirmLabel={$i18n.t('Remove')}
	onConfirm={confirmDeleteTask}
/>
