<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { uploadFile } from '$lib/apis/files';
	import { quoteVideoCredits, type VideoQuote } from '$lib/apis/credits';
	import {
		getVideoModels,
		getVideoTask,
		listVideoTasks,
		submitVideoTask,
		type VideoAssetCapability,
		type VideoAssetRole,
		type VideoField,
		type VideoGenerationTask,
		type VideoModel,
		type VideoTask
	} from '$lib/apis/videos';
	import { WEBUI_NAME, mobile, showSidebar, user } from '$lib/stores';
	import CreationDetailsModal from '$lib/components/images/CreationDetailsModal.svelte';
	import CreationsLibrary from '$lib/components/images/CreationsLibrary.svelte';
	import ImageCreditQuoteBadge from '$lib/components/credits/ImageCreditQuoteBadge.svelte';
	import {
		isImageQuoteSubmittable,
		type ImageQuoteState
	} from '$lib/components/credits/quote-state';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GenerationSubmitButton from '$lib/components/common/GenerationSubmitButton.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import VendorLogo from '$lib/components/common/VendorLogo.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import { stripVendorFromName } from '$lib/utils/images-dropdown';

	const i18n = getContext('i18n');
	const taskOptions: { id: VideoTask; label: string; hint: string }[] = [
		{ id: 'text-to-video', label: 'Text to Video', hint: 'Describe the motion and scene' },
		{ id: 'image-to-video', label: 'Image to Video', hint: 'Animate a start frame' },
		{ id: 'video-to-video', label: 'Video to Video', hint: 'Restyle or edit a clip' }
	];
	const assetLabels: Record<VideoAssetRole, string> = {
		start_image: 'Start image',
		end_image: 'End image',
		source_video: 'Source video',
		reference_image: 'Reference image',
		reference_video: 'Reference video',
		reference_audio: 'Reference audio'
	};
	const audioLabels: Record<string, string> = {
		silent: 'Silent',
		generate: 'Generate audio',
		upload: 'Use uploaded audio',
		preserve: 'Preserve audio',
		auto: 'Auto'
	};
	type UploadedVideoAsset = {
		id: string;
		name: string;
		url: string;
		mime_type: string;
	};

	let task: VideoTask = 'text-to-video';
	let models: VideoModel[] = [];
	let defaults: Record<VideoTask, string> | null = null;
	let modelId = '';
	let prompt = '';
	let params: Record<string, string | number | boolean | null> = {};
	let assets: Partial<Record<VideoAssetRole, UploadedVideoAsset[]>> = {};
	let history: VideoGenerationTask[] = [];
	let activeTask: VideoGenerationTask | null = null;
	let loading = true;
	let submitting = false;
	let showAdvanced = false;
	let pollingTimer: ReturnType<typeof setTimeout> | null = null;
	let quote: VideoQuote | null = null;
	let quoteState: ImageQuoteState = { status: 'loading' };
	let quoteTimer: ReturnType<typeof setTimeout> | null = null;
	let quoteGeneration = 0;
	let showCreationDetails = false;
	let showModelSelector = false;
	let showVideoOptions = false;
	let selectedVendor = '';
	let selection: 'generate' | 'mine' | 'all' = 'generate';
	let creationRevision = 0;
	$: isAdmin = $user?.role === 'admin';

	$: taskModels = models.filter((item) => item.task === task && item.visible !== false);
	$: selectedModel = taskModels.find((item) => item.id === modelId) ?? taskModels[0] ?? null;
	$: modelVendors = [...new Set(taskModels.map((item) => item.provider))];
	$: if (!modelVendors.includes(selectedVendor)) {
		selectedVendor = selectedModel?.provider ?? modelVendors[0] ?? '';
	}
	$: vendorModels = taskModels.filter((item) => item.provider === selectedVendor);
	$: advancedFields = selectedModel
		? [
				...(selectedModel.option_fields ?? []),
				...(selectedModel.boolean_fields ?? []),
				...(selectedModel.integer_fields ?? []),
				...(selectedModel.number_fields ?? []),
				...(selectedModel.text_fields ?? []),
				...(selectedModel.json_fields ?? [])
			].filter((field) => field.advanced)
		: [];
	$: durationChoices = (() => {
		if (selectedModel?.durations?.length) return selectedModel.durations;
		if (selectedModel?.duration_min === null || selectedModel?.duration_min === undefined)
			return [];
		if (selectedModel.duration_max === null || selectedModel.duration_max === undefined) return [];
		const step = selectedModel.duration_step ?? 1;
		const values: string[] = [];
		for (
			let value = selectedModel.duration_min;
			value <= selectedModel.duration_max + step / 2;
			value += step
		) {
			values.push(String(Number(value.toFixed(3))));
		}
		return values;
	})();
	$: durationIndex = Math.max(0, durationChoices.indexOf(String(params.duration ?? '')));
	$: quoteKey = selectedModel
		? JSON.stringify([
				task,
				selectedModel.id,
				params.duration,
				params.resolution,
				params.aspect_ratio,
				params.audio_mode
			])
		: '';
	$: if (!loading && quoteKey) scheduleQuote();
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
			? $i18n.t(audioLabels[String(params.audio_mode)] ?? String(params.audio_mode))
			: null
	]
		.filter(Boolean)
		.join(' · ');

	const quoteDimensions = (): Record<string, string | number> => ({
		duration: String(params.duration ?? selectedModel?.default_duration ?? '1'),
		resolution: String(params.resolution ?? selectedModel?.default_resolution ?? 'default'),
		aspect_ratio: String(params.aspect_ratio ?? selectedModel?.default_aspect_ratio ?? 'default'),
		audio_mode: String(params.audio_mode ?? selectedModel?.default_audio_mode ?? 'default')
	});

	const refreshQuote = async (): Promise<VideoQuote | null> => {
		if (!selectedModel) return null;
		const generation = ++quoteGeneration;
		try {
			const next = await quoteVideoCredits(localStorage.token, {
				resource_id: selectedModel.id,
				action: task,
				dimensions: quoteDimensions()
			});
			if (generation === quoteGeneration) {
				quote = next;
				quoteState = next.exempt
					? { status: 'exempt', chargedCredits: 0 }
					: !next.configured
						? { status: 'unconfigured', errorCode: next.error ?? undefined }
						: !next.sufficient
							? { status: 'insufficient', chargedCredits: next.charged_credits ?? undefined }
							: next.charged_credits === null
								? { status: 'error' }
								: { status: 'ready', chargedCredits: next.charged_credits };
			}
			return next;
		} catch {
			if (generation === quoteGeneration) {
				quote = null;
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

	const fieldKey = (field: VideoField) => field.source || field.field;
	const fieldValue = (field: VideoField, values = params) =>
		values[fieldKey(field)] ?? field.default ?? '';
	const setAdvancedParam = (field: VideoField, value: string | number | boolean) => {
		params = { ...params, [fieldKey(field)]: value };
	};
	const updateAdvancedInput = (
		field: VideoField,
		event: Event & { currentTarget: HTMLInputElement }
	) => {
		const input = event.currentTarget;
		setAdvancedParam(field, input.type === 'number' ? Number(input.value) : input.value);
	};
	const durationLabel = (value: string) =>
		value === 'auto'
			? $i18n.t('Auto')
			: value === '0'
				? $i18n.t('Match source duration')
				: `${value}s`;

	const videoRequestErrorMessage = (fallback: string) => $i18n.t(fallback);

	const resetForModel = (model: VideoModel | null) => {
		params = {};
		assets = {};
		showAdvanced = false;
		if (!model) return;
		if (model.default_duration) params.duration = model.default_duration;
		if (model.default_aspect_ratio) params.aspect_ratio = model.default_aspect_ratio;
		if (model.default_resolution) params.resolution = model.default_resolution;
		if (model.default_audio_mode) params.audio_mode = model.default_audio_mode;
		for (const field of [
			...(model.option_fields ?? []),
			...(model.boolean_fields ?? []),
			...(model.integer_fields ?? []),
			...(model.number_fields ?? [])
		]) {
			if (field.default !== null && field.default !== undefined) {
				params[fieldKey(field)] = field.default;
			}
		}
	};

	const preferredModelId = (nextTask: VideoTask, preferred?: string | null) =>
		models.find(
			(model) =>
				model.task === nextTask &&
				model.id === preferred &&
				model.visible !== false &&
				model.enabled !== false
		)?.id ??
		models.find(
			(model) => model.task === nextTask && model.visible !== false && model.enabled !== false
		)?.id ??
		models.find((model) => model.task === nextTask && model.visible !== false)?.id ??
		'';

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

	const load = async () => {
		loading = true;
		try {
			const [catalog, tasks] = await Promise.all([
				getVideoModels(localStorage.token),
				listVideoTasks(localStorage.token, 20)
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
					const draftTask = taskOptions.some((item) => item.id === draft.task)
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
						params = { ...params, ...draft.params };
					}
				} catch {
					// Ignore stale or malformed local drafts.
				}
			}
			history = tasks.items;
			activeTask = tasks.items.find((item) => item.result) ?? tasks.items[0] ?? null;
		} catch {
			toast.error(videoRequestErrorMessage('Failed to load video generation'));
		} finally {
			loading = false;
		}
	};

	const uploadAsset = async (capability: VideoAssetCapability, files: FileList | null) => {
		if (!files?.length) return;
		const existing = assets[capability.role] ?? [];
		const room = capability.max_count - existing.length;
		const selected = Array.from(files).slice(0, capability.multiple ? room : 1);
		try {
			const uploaded = await Promise.all(
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
					return {
						id: result.id,
						name: file.name,
						url: URL.createObjectURL(file),
						mime_type: file.type
					};
				})
			);
			assets = {
				...assets,
				[capability.role]: capability.multiple ? [...existing, ...uploaded] : uploaded
			};
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

	const pollTask = async (taskId: string) => {
		if (pollingTimer) clearTimeout(pollingTimer);
		try {
			const next = await getVideoTask(localStorage.token, taskId);
			activeTask = next;
			history = [next, ...history.filter((item) => item.id !== next.id)];
			if (next.status === 'queued' || next.status === 'running') {
				pollingTimer = setTimeout(() => pollTask(taskId), 900);
			} else if (next.status === 'succeeded') {
				creationRevision += 1;
				toast.success($i18n.t('Video generated'));
			} else {
				toast.error($i18n.t('Video generation failed'));
			}
		} catch {
			toast.error(videoRequestErrorMessage('Failed to update video generation'));
		}
	};

	const generate = async () => {
		if (!selectedModel || submitting) return;
		if (selectedModel.prompt_required && !prompt.trim()) {
			toast.error($i18n.t('Please enter a prompt'));
			return;
		}
		for (const capability of selectedModel.asset_inputs ?? []) {
			if (capability.required && !(assets[capability.role]?.length ?? 0)) {
				toast.error(`${$i18n.t(assetLabels[capability.role])} ${$i18n.t('is required')}`);
				return;
			}
		}
		for (const field of selectedModel.json_fields ?? []) {
			if (field.required && !String(fieldValue(field)).trim()) {
				toast.error(`${$i18n.t(fieldKey(field).replaceAll('_', ' '))} ${$i18n.t('is required')}`);
				return;
			}
		}
		const latestQuote = await refreshQuote();
		if (!latestQuote?.configured) {
			toast.error($i18n.t('Video price is not configured'));
			return;
		}
		if (!latestQuote.exempt && !latestQuote.sufficient) {
			toast.error($i18n.t('Insufficient credits'));
			return;
		}
		submitting = true;
		try {
			const created = await submitVideoTask(
				localStorage.token,
				{
					task,
					model: selectedModel.id,
					prompt: prompt.trim(),
					assets: Object.entries(assets).flatMap(([role, items]) =>
						(items ?? []).map((item) => ({ role: role as VideoAssetRole, file_id: item.id }))
					),
					params
				},
				uuidv4()
			);
			activeTask = created;
			history = [created, ...history];
			await pollTask(created.id);
		} catch {
			toast.error(videoRequestErrorMessage('Video generation failed'));
		} finally {
			submitting = false;
		}
	};

	onMount(() => {
		void load();
	});
	onDestroy(() => {
		if (pollingTimer) clearTimeout(pollingTimer);
		if (quoteTimer) clearTimeout(quoteTimer);
		for (const items of Object.values(assets)) {
			for (const item of items ?? []) URL.revokeObjectURL(item.url);
		}
	});
</script>

<svelte:head>
	<title>{$i18n.t('Videos')} • {$WEBUI_NAME}</title>
</svelte:head>

<div
	class="relative flex h-screen max-h-[100dvh] w-full max-w-full min-w-0 flex-col bg-white text-gray-900 transition-width duration-200 ease-in-out dark:bg-gray-950 dark:text-gray-100 {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''}"
>
	{#if $mobile}
		<nav class="relative z-40 shrink-0 px-3 pb-2 pt-2 backdrop-blur-xl drag-region select-none">
			<div class="flex flex-none items-center">
				<Tooltip
					content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
					interactive={true}
				>
					<button
						id="sidebar-toggle-button"
						type="button"
						class="flex min-h-10 min-w-10 cursor-pointer items-center justify-center rounded-lg transition hover:bg-gray-100 dark:hover:bg-gray-850"
						on:click={() => showSidebar.set(!$showSidebar)}
						aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
					>
						<SidebarIcon />
					</button>
				</Tooltip>
			</div>
		</nav>
	{/if}

	<div
		class="pointer-events-none absolute inset-x-0 top-14 z-30 flex justify-center px-3 sm:top-0 sm:pt-2"
	>
		<div
			class="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-gray-200/80 bg-white/80 p-1 shadow-lg shadow-black/10 backdrop-blur-xl dark:border-gray-700/80 dark:bg-gray-900/80 dark:shadow-black/30"
			role="tablist"
			tabindex="-1"
			aria-label={$i18n.t('Videos')}
		>
			{#each [['generate', 'Create art'], ['mine', 'My creations']] as tab}
				<button
					type="button"
					role="tab"
					aria-selected={selection === tab[0]}
					class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all sm:min-h-10 {selection ===
					tab[0]
						? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
						: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
					on:click={() => (selection = tab[0] as 'generate' | 'mine')}
				>
					{$i18n.t(tab[1])}
				</button>
			{/each}
			{#if isAdmin}<button
					type="button"
					role="tab"
					aria-selected={selection === 'all'}
					class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all sm:min-h-10 {selection ===
					'all'
						? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
						: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
					on:click={() => (selection = 'all')}>{$i18n.t('All creations')}</button
				>{/if}
		</div>
	</div>

	{#if selection === 'generate'}
		{#if loading}
			<div class="flex flex-1 items-center justify-center text-sm text-gray-500">
				{$i18n.t('Loading...')}
			</div>
		{:else}
			<div class="flex min-h-0 flex-1 pt-14">
				<main class="flex min-h-0 flex-1 overflow-hidden p-3 sm:p-6">
					<div class="mx-auto flex h-full min-h-0 w-full max-w-5xl items-center justify-center">
						{#if activeTask?.result}
							<div
								class="flex h-full max-h-[68vh] w-full flex-col overflow-hidden rounded-2xl bg-black shadow-sm"
							>
								<video
									class="min-h-0 w-full flex-1 bg-black object-contain"
									controls
									playsinline
									preload="metadata"
									poster={activeTask.result.poster_url}
									src={activeTask.result.url}
								></video>
								<div class="flex justify-end border-t border-white/10 bg-gray-950 px-3 py-2">
									<button
										type="button"
										class="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-900 hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-offset-2"
										on:click={() => (showCreationDetails = true)}
										>{$i18n.t('View details and publish')}</button
									>
								</div>
							</div>
						{:else if activeTask?.status === 'queued' || activeTask?.status === 'running'}
							<div class="flex max-w-sm flex-col items-center text-center">
								<div
									class="mb-4 size-12 animate-pulse rounded-full bg-gray-100 dark:bg-gray-800"
								></div>
								<div class="font-medium">{$i18n.t('Creating your video')}</div>
								<div class="mt-1 text-sm text-gray-500">
									{$i18n.t('The result will appear here shortly')}
								</div>
							</div>
						{:else}
							<div class="max-w-md text-center">
								<div
									class="mx-auto mb-4 flex aspect-video w-56 items-center justify-center rounded-2xl border border-dashed border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900"
								>
									<svg
										class="size-10 text-gray-300 dark:text-gray-600"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="1.5"
										><path
											d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14M4 6h9a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z"
										/></svg
									>
								</div>
								<h2 class="font-medium">{$i18n.t('Start with a video idea')}</h2>
								<p class="mt-1 text-sm text-gray-500">
									{$i18n.t('Choose a mode, add material when needed, then describe the motion')}
								</p>
							</div>
						{/if}
					</div>
				</main>
			</div>

			<section
				class="shrink-0 bg-gradient-to-t from-white via-white/95 to-white/0 px-3 pb-3 pt-8 dark:from-gray-950 dark:via-gray-950/95 dark:to-gray-950/0 sm:px-6"
			>
				<div class="mx-auto max-w-5xl">
					<div
						class="mb-2 flex gap-1 overflow-x-auto pb-0.5 pr-36 sm:pr-48"
						role="tablist"
						tabindex="-1"
						aria-label={$i18n.t('Video mode')}
					>
						{#each taskOptions as option}
							<button
								type="button"
								role="tab"
								aria-selected={task === option.id}
								class="min-h-11 whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition sm:min-h-0 {task ===
								option.id
									? 'bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900'
									: 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'}"
								on:click={() => changeTask(option.id)}>{$i18n.t(option.label)}</button
							>
						{/each}
					</div>

					<form
						class="relative rounded-[1.5rem] border border-gray-100/90 bg-white/95 p-4 shadow-xl shadow-gray-200/50 backdrop-blur-xl dark:border-gray-800/90 dark:bg-gray-950/95 dark:shadow-black/25"
						on:submit|preventDefault={generate}
					>
						<div
							class="absolute bottom-full right-0 mb-2 max-w-[min(11rem,calc(100vw-2rem))] sm:max-w-[16rem]"
						>
							<Dropdown
								bind:show={showModelSelector}
								side="top"
								align="start"
								maxHeight="min(60dvh, 28rem)"
								contentClass="z-50 w-[min(34rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-gray-100 bg-white p-2 shadow-xl dark:border-gray-800 dark:bg-gray-900"
							>
								<button
									type="button"
									class="inline-flex min-h-11 min-w-0 max-w-full items-center gap-2 rounded-[10px] border border-gray-200/90 bg-white/95 px-2 text-sm font-medium text-gray-700 shadow-sm backdrop-blur-xl transition hover:bg-white sm:h-8 sm:min-h-0 dark:border-gray-700 dark:bg-gray-900/95 dark:text-gray-200 dark:hover:bg-gray-900"
								>
									<svg
										class="size-4 shrink-0"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="1.8"
										aria-hidden="true"
										><path
											d="M15 10l4.55-2.28A1 1 0 0 1 21 8.62v6.76a1 1 0 0 1-1.45.9L15 14M4 6h9a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z"
										/></svg
									>
									<span class="truncate"
										>{selectedModel ? stripVendorFromName(selectedModel) : $i18n.t('Model')}</span
									>
									<span class="shrink-0 text-xs text-gray-500">⌄</span>
								</button>
								<div
									slot="content"
									class="flex h-80 min-h-0 gap-2"
									role="listbox"
									aria-label={$i18n.t('Model')}
								>
									<div
										class="w-32 shrink-0 overflow-y-auto border-r border-gray-100 pr-2 dark:border-gray-800 sm:w-40"
									>
										{#each modelVendors as vendor}
											<button
												type="button"
												class="flex min-h-11 w-full items-center gap-2 rounded-xl px-2 py-2 text-left text-sm transition sm:min-h-9 {vendor ===
												selectedVendor
													? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
													: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
												on:click={() => (selectedVendor = vendor)}
												aria-pressed={vendor === selectedVendor}
											>
												<VendorLogo provider={vendor} className="size-4 shrink-0 rounded-sm" />
												<span class="min-w-0 truncate capitalize">{vendor}</span>
											</button>
										{/each}
									</div>
									<div class="min-w-0 flex-1 overflow-y-auto">
										{#each vendorModels as model}
											<button
												type="button"
												class="flex min-h-11 w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition sm:min-h-9 {model.id ===
												modelId
													? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
													: model.enabled === false
														? 'cursor-not-allowed text-gray-400 dark:text-gray-600'
														: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
												on:click={() => model.enabled !== false && changeModel(model.id)}
												role="option"
												aria-selected={model.id === modelId}
												aria-disabled={model.enabled === false}
											>
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
													{#if model.maintenance_message}<span
															class="mt-0.5 block line-clamp-2 text-[11px] text-orange-600 dark:text-orange-400"
															>{model.maintenance_message}</span
														>{/if}
												</span>
												<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">
													{#if model.base_price}
														{$i18n.t('Estimated')}
														{model.base_price}{$i18n.t('credits.common.unit')}
													{:else}
														{$i18n.t('credits.unconfigured')}
													{/if}
												</span>
											</button>
										{/each}
									</div>
								</div>
							</Dropdown>
						</div>

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
											>{$i18n.t(assetLabels[capability.role])}{capability.required
												? ' *'
												: ''}</span
										>
										<span class="ml-2 text-gray-400"
											>{assets[capability.role]?.length ?? 0}/{capability.max_count}</span
										>
										<input
											class="sr-only"
											type="file"
											accept={capability.mime_types.join(',')}
											multiple={capability.multiple}
											on:change={(event) => uploadAsset(capability, event.currentTarget.files)}
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
														{$i18n.t(assetLabels[role as VideoAssetRole])}
													</div>
													<div class="mt-0.5 truncate text-gray-400" title={item.name}>
														{item.name}
													</div>
												</div>
												<button
													type="button"
													class="absolute right-1 top-1 flex size-11 items-center justify-center rounded-full bg-white/90 text-sm text-gray-600 shadow-sm transition hover:text-gray-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:size-8 dark:bg-gray-800/90 dark:text-gray-300 dark:hover:text-white"
													aria-label={$i18n.t('Remove')}
													on:click={() => removeAsset(role as VideoAssetRole, item.id)}>×</button
												>
											</div>
										{/each}
									{/each}
								</div>
							{/if}
						{/if}

						<textarea
							bind:value={prompt}
							rows="3"
							class="max-h-44 min-h-20 w-full resize-none bg-transparent py-2 text-base outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500"
							placeholder={$i18n.t(taskOptions.find((item) => item.id === task)?.hint ?? '')}
						></textarea>

						<div class="mt-2 flex min-w-0 items-center justify-between gap-2">
							<Dropdown
								bind:show={showVideoOptions}
								side="top"
								align="start"
								maxHeight="min(75dvh, 36rem)"
								contentClass="z-50 w-[min(30rem,calc(100vw-2rem))] overflow-y-auto rounded-2xl border border-gray-100 bg-white p-4 shadow-xl dark:border-gray-800 dark:bg-gray-900"
							>
								<button
									type="button"
									class="inline-flex h-8 max-w-[min(70vw,32rem)] items-center gap-2 overflow-hidden rounded-[10px] bg-black/[0.06] px-2 text-sm font-medium text-gray-700 transition hover:bg-black/[0.1] dark:bg-white/[0.08] dark:text-gray-200 dark:hover:bg-white/[0.12]"
								>
									<svg
										class="size-4 shrink-0"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="1.8"
										aria-hidden="true"
										><path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6" /></svg
									>
									<span class="truncate">{videoOptionsLabel}</span>
								</button>

								<div slot="content" class="space-y-4">
									{#if durationChoices.length}
										<section>
											<div class="mb-2 flex items-center justify-between gap-3">
												<h3 class="text-sm font-medium">{$i18n.t('Duration')}</h3>
												<output
													class="rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium tabular-nums dark:bg-gray-800"
													>{durationLabel(durationChoices[durationIndex])}</output
												>
											</div>
											<div class="px-1">
												<input
													type="range"
													class="h-8 w-full cursor-pointer accent-gray-900 dark:accent-gray-100"
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
										<section>
											<h3 class="mb-2 text-sm font-medium">{$i18n.t('Aspect ratio')}</h3>
											<div class="grid grid-cols-3 gap-1.5 sm:grid-cols-5">
												{#each selectedModel.aspect_ratios as value}<button
														type="button"
														class="h-10 rounded-xl border text-xs transition {params.aspect_ratio ===
														value
															? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
															: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300'}"
														on:click={() => (params = { ...params, aspect_ratio: value })}
														aria-pressed={params.aspect_ratio === value}>{value}</button
													>{/each}
											</div>
										</section>
									{/if}
									<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
										{#if selectedModel?.resolutions}<section>
												<h3 class="mb-2 text-sm font-medium">{$i18n.t('Resolution')}</h3>
												<div class="grid grid-cols-2 gap-1.5">
													{#each selectedModel.resolutions as value}<button
															type="button"
															class="h-9 rounded-xl border text-xs transition {params.resolution ===
															value
																? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
																: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300'}"
															on:click={() => (params = { ...params, resolution: value })}
															aria-pressed={params.resolution === value}>{value}</button
														>{/each}
												</div>
											</section>{/if}
										{#if selectedModel?.audio_options}<section>
												<h3 class="mb-2 text-sm font-medium">{$i18n.t('Audio')}</h3>
												<div class="grid grid-cols-2 gap-1.5">
													{#each selectedModel.audio_options as value}<button
															type="button"
															class="h-9 rounded-xl border px-2 text-xs transition {params.audio_mode ===
															value.mode
																? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
																: 'border-gray-100 bg-gray-50 text-gray-600 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300'}"
															on:click={() => (params = { ...params, audio_mode: value.mode })}
															aria-pressed={params.audio_mode === value.mode}
															>{$i18n.t(audioLabels[value.mode] ?? value.mode)}</button
														>{/each}
												</div>
											</section>{/if}
									</div>
									{#if advancedFields.length}
										<section class="border-t border-gray-100 pt-3 dark:border-gray-800">
											<button
												type="button"
												class="min-h-11 rounded-lg px-2 py-1.5 text-xs text-gray-500 hover:bg-gray-100 sm:min-h-0 dark:hover:bg-gray-800"
												aria-expanded={showAdvanced}
												on:click={() => (showAdvanced = !showAdvanced)}
												>{$i18n.t('Advanced')} {showAdvanced ? '↑' : '↓'}</button
											>
											{#if showAdvanced}<div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
													{#each advancedFields as field}<div
															class="text-xs text-gray-500 {field.format === 'json'
																? 'sm:col-span-2'
																: ''}"
														>
															<span class="mb-1.5 block"
																>{$i18n.t(fieldKey(field).replaceAll('_', ' '))}{field.required
																	? ' *'
																	: ''}</span
															>{#if field.format === 'json'}<textarea
																	class="min-h-24 w-full resize-y rounded-xl bg-gray-100 px-3 py-2 font-mono text-xs text-gray-900 outline-none dark:bg-gray-800 dark:text-gray-100"
																	rows="4"
																	value={String(fieldValue(field, params))}
																	placeholder={$i18n.t('Enter a JSON array or object')}
																	aria-label={$i18n.t(fieldKey(field).replaceAll('_', ' '))}
																	on:input={(event) =>
																		setAdvancedParam(field, event.currentTarget.value)}
																></textarea>{:else if field.options}<div
																	class="flex flex-wrap gap-1.5"
																>
																	{#each field.options as option}<button
																			type="button"
																			class="rounded-xl border px-3 py-2 text-xs {fieldValue(
																				field,
																				params
																			) === option
																				? 'border-gray-300 bg-gray-100 text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100'
																				: 'border-gray-100 bg-gray-50 text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300'}"
																			on:click={() => setAdvancedParam(field, option)}
																			aria-pressed={fieldValue(field, params) === option}
																			>{option}</button
																		>{/each}
																</div>{:else if typeof field.default === 'boolean'}<button
																	type="button"
																	class="flex w-full items-center justify-between rounded-xl bg-gray-100 px-3 py-2 text-gray-900 dark:bg-gray-800 dark:text-gray-100"
																	on:click={() =>
																		setAdvancedParam(field, !Boolean(fieldValue(field, params)))}
																	><span
																		>{Boolean(fieldValue(field, params))
																			? $i18n.t('On')
																			: $i18n.t('Off')}</span
																	><span
																		class="h-5 w-9 rounded-full p-0.5 transition {Boolean(
																			fieldValue(field, params)
																		)
																			? 'bg-gray-900 dark:bg-gray-100'
																			: 'bg-gray-300 dark:bg-gray-600'}"
																		><span
																			class="block size-4 rounded-full bg-white transition {Boolean(
																				fieldValue(field, params)
																			)
																				? 'translate-x-4 dark:bg-gray-900'
																				: ''}"
																		></span></span
																	></button
																>{:else}<input
																	class="w-full rounded-xl bg-gray-100 px-3 py-2 text-gray-900 outline-none dark:bg-gray-800 dark:text-gray-100"
																	type={field.min !== undefined ? 'number' : 'text'}
																	min={field.min ?? undefined}
																	max={field.max ?? undefined}
																	step={field.step ?? undefined}
																	value={fieldValue(field, params)}
																	on:input={(event) => updateAdvancedInput(field, event)}
																/>{/if}
														</div>{/each}
												</div>{/if}
										</section>
									{/if}
								</div>
							</Dropdown>

							<div class="flex shrink-0 items-center gap-2">
								<ImageCreditQuoteBadge {quoteState} />
								<GenerationSubmitButton
									loading={submitting}
									disabled={submitting ||
										!selectedModel ||
										selectedModel.enabled === false ||
										!isImageQuoteSubmittable(quoteState)}
									label={$i18n.t('Generate video')}
								/>
							</div>
						</div>
					</form>
				</div>
			</section>
		{/if}
	{:else}
		<div class="min-h-0 flex-1 overflow-y-auto pt-18">
			<CreationsLibrary
				active={selection !== 'generate'}
				scope={selection === 'all' ? 'all' : 'mine'}
				revision={creationRevision}
				mediaKind="video"
			/>
		</div>
	{/if}
</div>

<CreationDetailsModal
	bind:show={showCreationDetails}
	creationId={activeTask?.result?.creation_id ?? null}
	scope="mine"
/>
