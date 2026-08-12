<script lang="ts">
	import { goto } from '$app/navigation';
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';

	import {
		deleteAdminCreation,
		deleteCreation,
		getAdminCreation,
		getCreation,
		publishAdminCreation,
		publishCreation,
		withdrawAdminCreationPublication,
		withdrawCreationPublication,
		updateCreation
	} from '$lib/apis/creations';
	import type {
		AdminCreationDetail,
		CreationDetail,
		CreationScope,
		ParamTag
	} from '$lib/utils/creations-library';
	import { buildCreationDraft, type ImageCreationDraft } from '$lib/utils/image-generation-batches';

	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Clipboard from '$lib/components/icons/Clipboard.svelte';
	import Download from '$lib/components/icons/Download.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import ArtworkViewerShell from './ArtworkViewerShell.svelte';

	import { copyToClipboard, formatDate } from '$lib/utils';
	import { extractParamTags } from '$lib/utils/creations-library';

	export let show = false;
	export let creationId: string | null = null;
	export let scope: CreationScope = 'mine';
	export let canManage = false;
	export let onUpdated: (detail: CreationDetail | AdminCreationDetail) => void = () => {};
	export let onRemoved: (creationId: string) => void = () => {};
	export let onReuse: (draft: ImageCreationDraft) => void = () => {};

	const i18n = getContext('i18n');

	type CacheEntry = {
		detail: CreationDetail | AdminCreationDetail;
		scope: CreationScope;
	};
	const detailCache = new Map<string, CacheEntry>();

	let detail: CreationDetail | AdminCreationDetail | null = null;
	let loading = false;
	let error: string | null = null;
	let detailRequestGeneration = 0;
	let wasShown = false;
	let captionDraft = '';
	let savingCaption = false;
	let removing = false;
	let confirmRemove = false;
	let showPreview = false;
	let previewSrc = '';
	let previewAlt = '';
	let publicationEditing = false;
	let publicationTitle = '';
	let publicationDescription = '';
	let publicationShowPrompt = true;
	let publishing = false;
	let withdrawingPublication = false;

	const isAdminScope = () => scope === 'all';

	const cacheKey = (sid: string, targetScope: CreationScope = scope) => `${targetScope}:${sid}`;

	const loadDetail = async (sid: string) => {
		wasShown = true;
		const requestedScope = scope;
		const generation = ++detailRequestGeneration;
		savingCaption = false;
		removing = false;
		confirmRemove = false;
		const key = cacheKey(sid, requestedScope);
		const cached = detailCache.get(key);
		if (cached) {
			detail = cached.detail;
			captionDraft = cached.detail.caption ?? '';
			publicationEditing = false;
			loading = false;
			error = null;
			return;
		}
		loading = true;
		detail = null;
		error = null;
		try {
			const fetched =
				requestedScope === 'all'
					? ((await getAdminCreation(localStorage.token, sid)) as AdminCreationDetail)
					: ((await getCreation(localStorage.token, sid)) as CreationDetail);
			detailCache.set(key, { detail: fetched, scope: requestedScope });
			if (
				generation !== detailRequestGeneration ||
				!show ||
				creationId !== sid ||
				scope !== requestedScope
			) {
				return;
			}
			detail = fetched;
			captionDraft = fetched.caption ?? '';
			publicationEditing = false;
		} catch (err) {
			if (generation !== detailRequestGeneration) return;
			error = err instanceof Error ? err.message : String(err);
			detail = null;
		} finally {
			if (generation === detailRequestGeneration) {
				loading = false;
			}
		}
	};

	$: if (show && creationId && scope) {
		void loadDetail(creationId);
	}
	$: if (!show && wasShown) {
		wasShown = false;
		detailRequestGeneration += 1;
		loading = false;
		confirmRemove = false;
		showPreview = false;
	}

	const saveCaption = async () => {
		if (!detail || !creationId) return;
		const sid = creationId;
		const requestedScope = scope;
		const currentDetail = detail;
		savingCaption = true;
		try {
			const updated = (await updateCreation(
				localStorage.token,
				sid,
				captionDraft.trim() || null
			)) as CreationDetail;
			const cachedDetail = { ...currentDetail, caption: updated.caption };
			detailCache.set(cacheKey(sid, requestedScope), {
				detail: cachedDetail,
				scope: requestedScope
			});
			if (creationId === sid && scope === requestedScope) {
				detail = cachedDetail;
				captionDraft = updated.caption ?? '';
				onUpdated(cachedDetail);
				toast.success($i18n.t('Caption saved'));
			}
		} catch {
			if (creationId === sid && scope === requestedScope) {
				toast.error($i18n.t('Failed to save caption'));
			}
		} finally {
			if (creationId === sid && scope === requestedScope) {
				savingCaption = false;
			}
		}
	};

	const removeCreation = async () => {
		if (!creationId) return;
		const sid = creationId;
		const requestedScope = scope;
		removing = true;
		try {
			await (requestedScope === 'all' ? deleteAdminCreation : deleteCreation)(
				localStorage.token,
				sid
			);
			detailCache.delete(cacheKey(sid, requestedScope));
			onRemoved(sid);
			if (creationId === sid && scope === requestedScope) {
				show = false;
			}
		} catch {
			if (creationId === sid && scope === requestedScope) {
				toast.error($i18n.t('Failed to remove creation'));
			}
		} finally {
			if (creationId === sid && scope === requestedScope) {
				removing = false;
				confirmRemove = false;
			}
		}
	};

	const beginPublicationEdit = () => {
		if (!detail) return;
		publicationTitle = detail.publication?.title ?? detail.caption ?? '';
		publicationDescription = detail.publication?.description ?? '';
		publicationShowPrompt = detail.publication?.show_prompt ?? true;
		publicationEditing = true;
	};

	const savePublication = async () => {
		if (!detail || !creationId || publishing) return;
		publishing = true;
		try {
			const publish = isAdminScope() ? publishAdminCreation : publishCreation;
			const publication = await publish(localStorage.token, creationId, {
				title: publicationTitle.trim() || null,
				description: publicationDescription.trim() || null,
				show_prompt: publicationShowPrompt
			});
			const updated = { ...detail, publication };
			detail = updated;
			detailCache.set(cacheKey(creationId), { detail: updated, scope });
			publicationEditing = false;
			onUpdated(updated);
			toast.success($i18n.t('Published to Discover'));
		} catch {
			toast.error($i18n.t('Failed to publish creation'));
		} finally {
			publishing = false;
		}
	};

	const withdrawPublication = async () => {
		if (!detail || !creationId || withdrawingPublication) return;
		withdrawingPublication = true;
		try {
			const withdraw = isAdminScope()
				? withdrawAdminCreationPublication
				: withdrawCreationPublication;
			await withdraw(localStorage.token, creationId);
			const publication = detail.publication
				? { ...detail.publication, status: 'withdrawn' as const }
				: null;
			const updated = { ...detail, publication };
			detail = updated;
			detailCache.set(cacheKey(creationId), { detail: updated, scope });
			onUpdated(updated);
			toast.success($i18n.t('Removed from Discover'));
		} catch {
			toast.error($i18n.t('Failed to remove publication'));
		} finally {
			withdrawingPublication = false;
		}
	};

	const openPreview = (url: string, alt: string) => {
		previewSrc = url;
		previewAlt = alt;
		showPreview = true;
	};

	const reuseCreation = (useAsReference = false) => {
		if (!detail) return;
		if (detail.kind === 'video') {
			localStorage.setItem(
				'video-creation-draft',
				JSON.stringify({
					task: detail.task,
					prompt: detail.prompt,
					model: detail.model_id,
					params: detail.params
				})
			);
			show = false;
			void goto('/videos');
			return;
		}
		onReuse(
			buildCreationDraft({
				prompt: detail.prompt,
				model_id: detail.model_id,
				params: detail.params,
				negative_prompt: detail.negative_prompt,
				content_url: detail.content_url,
				useAsReference
			})
		);
		show = false;
	};

	const downloadCreation = () => {
		if (!detail?.content_url) return;
		const anchor = document.createElement('a');
		anchor.href = detail.content_url;
		anchor.download = `creation-${detail.id}.${detail.kind === 'video' ? 'mp4' : 'png'}`;
		anchor.rel = 'noopener';
		anchor.click();
	};

	// Localise the curated param keys onto short chip labels. Kept tight beside
	// the consumer rather than exported, because the only writer of these keys
	// is `extractParamTags`'s PARAM_TAG_ORDER; diverging here trips nothing
	// worse than a falling-through English-ish fallback per the default arm.
	const PARAM_LABELS: Partial<Record<ParamTag['key'], string>> = {
		size: $i18n.t('Size'),
		resolution: $i18n.t('Resolution'),
		aspect_ratio: $i18n.t('Aspect ratio'),
		quality: $i18n.t('Quality'),
		image_count: $i18n.t('Image count'),
		steps: $i18n.t('Steps'),
		guidance_scale: $i18n.t('Guidance scale'),
		strength: $i18n.t('Strength'),
		seed: $i18n.t('Seed'),
		style: $i18n.t('Style'),
		output_format: $i18n.t('Format'),
		background: $i18n.t('Background'),
		acceleration: $i18n.t('Acceleration'),
		input_fidelity: $i18n.t('Input fidelity'),
		thinking_level: $i18n.t('Thinking level'),
		prompt_enhancement: $i18n.t('Prompt enhancement'),
		motion_amplitude: $i18n.t('Motion amplitude'),
		fps: $i18n.t('Frame rate'),
		output_quality: $i18n.t('Output quality'),
		edit_strength: $i18n.t('Edit strength'),
		retake_mode: $i18n.t('Retake mode'),
		start_time: $i18n.t('Start time'),
		ingredients_mode: $i18n.t('Reference mode')
	};
	const paramLabel = (key: ParamTag['key']): string => PARAM_LABELS[key] ?? key;
	$: paramTags = detail ? extractParamTags(detail.params) : [];

	// Prompt copy — reuse the shared clipboard helper rather than reinventing
	// navigator.clipboard; it owns the fallbacks for insecure contexts.
	let copyingPrompt = false;
	const copyPrompt = async () => {
		if (!detail?.prompt || copyingPrompt) return;
		copyingPrompt = true;
		try {
			await copyToClipboard(detail.prompt);
			toast.success($i18n.t('Copied'));
		} catch {
			toast.error($i18n.t('Failed to copy'));
		} finally {
			copyingPrompt = false;
		}
	};

	// Caption is demoted to an inline affordance: collapsed by default, it
	// expands in-place to a single-row editor so the prompt card keeps pride of
	// place. `captionEditing` gates the editor; cancel restores the draft to
	// the persisted value so stray keystrokes don't leak back on reopen.
	let captionEditing = false;
	const cancelCaptionEdit = () => {
		captionDraft = detail?.caption ?? '';
		captionEditing = false;
	};

	// Subtitle for the slimmed-down header: a friendly "when" paired with the
	// model name. Mirrors the chat message timestamp recipe so calendars and
	// clocks honour the user's locale.
	$: headerSubtitle = detail
		? [
				$i18n.t(formatDate(detail.created_at * 1000), {
					LOCALIZED_TIME: dayjs(detail.created_at * 1000).format('LT'),
					LOCALIZED_DATE: dayjs(detail.created_at * 1000).format('LL')
				}),
				detail.model_name ?? detail.model_id
			]
				.filter(Boolean)
				.join(' · ')
		: '';
	$: headerTitle = detail
		? isAdminScope() && 'owner' in detail
			? detail.owner.deleted
				? $i18n.t('Deleted user')
				: (detail.owner.name ?? detail.owner.user_id)
			: detail.caption || $i18n.t('My creation')
		: '';
</script>

<ArtworkViewerShell
	bind:show
	{loading}
	{error}
	{headerTitle}
	{headerSubtitle}
	mediaLabel={$i18n.t('Artwork')}
	detailsClassName="lg:w-[22rem]"
>
	<svelte:fragment slot="media">
		{#if detail}
			{#if detail.content_url && detail.kind === 'video'}
				<video
					src={detail.content_url}
					poster={detail.poster_url ?? undefined}
					class="max-h-[80dvh] max-w-full rounded-xl bg-black object-contain sm:rounded-2xl lg:max-h-[72dvh]"
					controls
					playsinline
					preload="metadata"
				></video>
			{:else if detail.content_url}
				<button
					type="button"
					class="flex max-h-[80dvh] items-center justify-center overflow-hidden rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:rounded-2xl lg:max-h-[72dvh]"
					on:click={() =>
						openPreview(detail.content_url as string, detail.caption ?? detail.prompt)}
					aria-label={$i18n.t('Preview')}
				>
					<img
						src={detail.content_url}
						alt={detail.caption ?? detail.prompt}
						loading="lazy"
						decoding="async"
						class="h-auto w-auto max-h-[80dvh] max-w-full rounded-xl object-contain sm:rounded-2xl lg:max-h-[72dvh]"
					/>
				</button>
			{:else}
				<div
					class="flex h-full min-h-64 w-full items-center justify-center rounded-2xl bg-gray-100 px-4 text-center text-sm text-gray-500 dark:bg-gray-800 dark:text-gray-400"
				>
					{$i18n.t('Source file unavailable')}
				</div>
			{/if}
		{/if}
	</svelte:fragment>

	<svelte:fragment slot="details">
		{#if detail}
			<div class="grid grid-cols-2 gap-2">
				<button
					type="button"
					class="col-span-2 inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-gray-950 px-4 text-sm font-medium text-white transition hover:bg-gray-800 focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100"
					on:click={() => reuseCreation(false)}
				>
					<Sparkles className="size-4" strokeWidth="1.8" />
					{$i18n.t('Create again')}
				</button>
				{#if detail.content_url && detail.kind === 'image'}
					<button
						type="button"
						class="inline-flex min-h-11 items-center justify-center rounded-xl border border-gray-200 px-3 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
						on:click={() => reuseCreation(true)}
					>
						{$i18n.t('Use as reference')}
					</button>
					<button
						type="button"
						class="inline-flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-gray-200 px-3 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
						on:click={downloadCreation}
					>
						<Download className="size-4" strokeWidth="1.8" />
						{$i18n.t('Download')}
					</button>
				{/if}
			</div>
			<!-- ── 区① 创作由来 ── -->
			<section class="space-y-3 lg:flex lg:flex-1 lg:min-h-0 lg:flex-col">
				<div
					class="relative rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col"
				>
					<div class="mb-1 flex items-center justify-between gap-2">
						<h3
							class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
						>
							{$i18n.t('Prompt')}
						</h3>
						<button
							type="button"
							class="-mr-1 -mt-1 inline-flex min-h-9 min-w-9 items-center justify-center rounded-md p-1.5 text-gray-400 hover:bg-gray-200/70 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 disabled:opacity-50 dark:hover:bg-gray-700 dark:hover:text-gray-200"
							disabled={!detail.prompt || copyingPrompt}
							on:click={copyPrompt}
							aria-label={$i18n.t('Copy')}
							title={$i18n.t('Copy')}
						>
							<Clipboard className="size-4" strokeWidth="2" />
						</button>
					</div>
					<p
						class="max-h-48 overflow-y-auto whitespace-pre-wrap break-words pr-1 text-sm text-gray-800 lg:flex-1 lg:max-h-none dark:text-gray-100"
					>
						{detail.prompt}
					</p>
				</div>
				{#if detail.negative_prompt}
					<p class="whitespace-pre-wrap break-words text-xs text-gray-500 dark:text-gray-400">
						<span class="font-medium">{$i18n.t('Negative Prompt')}: </span>{detail.negative_prompt}
					</p>
				{/if}
				{#if paramTags.length > 0 || detail.model_name || detail.model_id}
					<ul class="flex flex-wrap gap-1.5">
						{#if detail.model_name || detail.model_id}
							<li
								class="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
							>
								<span class="mr-1 font-medium text-gray-500 dark:text-gray-400">
									{$i18n.t('Model')}:
								</span>
								<span class="break-words">{detail.model_name ?? detail.model_id}</span>
							</li>
						{/if}
						{#each paramTags as tag (tag.key)}
							<li
								class="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
							>
								<span class="mr-1 font-medium text-gray-500 dark:text-gray-400">
									{paramLabel(tag.key)}:
								</span>
								<span class="break-words">{tag.value}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</section>

			<!-- ── 区② 素材与管理 ── -->
			<section class="space-y-3">
				{#if canManage}
					<div class="rounded-xl border border-gray-200 p-3 dark:border-gray-700">
						{#if publicationEditing}
							<div class="space-y-2.5">
								<label class="block text-xs font-medium text-gray-600 dark:text-gray-300">
									{$i18n.t('Title')}
									<input
										type="text"
										bind:value={publicationTitle}
										maxlength="200"
										class="mt-1 min-h-11 w-full rounded-lg border border-gray-200 bg-white px-3 text-sm text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
									/>
								</label>
								<label class="block text-xs font-medium text-gray-600 dark:text-gray-300">
									{$i18n.t('Description')}
									<textarea
										bind:value={publicationDescription}
										maxlength="1000"
										rows="3"
										class="mt-1 w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
									></textarea>
								</label>
								<label
									class="flex min-h-11 cursor-pointer items-center gap-2 text-sm text-gray-700 dark:text-gray-200"
								>
									<input type="checkbox" bind:checked={publicationShowPrompt} class="size-4" />
									{$i18n.t('Show prompt in Discover')}
								</label>
								<div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
									<button
										type="button"
										class="min-h-11 rounded-lg px-3 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
										on:click={() => (publicationEditing = false)}>{$i18n.t('Cancel')}</button
									>
									<button
										type="button"
										class="min-h-11 rounded-lg bg-gray-950 px-4 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-gray-950"
										disabled={publishing}
										on:click={savePublication}
										>{publishing ? $i18n.t('Publishing...') : $i18n.t('Publish')}</button
									>
								</div>
							</div>
						{:else if detail.publication?.status === 'published'}
							<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
								<div>
									<p class="text-sm font-medium text-gray-900 dark:text-gray-100">
										{$i18n.t('Published in Discover')}
									</p>
									<p class="text-xs text-gray-500 dark:text-gray-400">
										{$i18n.t('Everyone can now see this creation.')}
									</p>
								</div>
								<div class="flex gap-2">
									<button
										type="button"
										class="min-h-11 rounded-lg px-3 text-xs font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
										on:click={beginPublicationEdit}>{$i18n.t('Edit')}</button
									>
									<button
										type="button"
										class="min-h-11 rounded-lg px-3 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-950"
										disabled={withdrawingPublication}
										on:click={withdrawPublication}>{$i18n.t('Remove')}</button
									>
								</div>
							</div>
						{:else if detail.publication?.status === 'hidden'}
							<div class="space-y-3">
								<p class="text-sm text-gray-500 dark:text-gray-400">
									{$i18n.t('This publication was hidden by an administrator.')}
								</p>
								{#if isAdminScope()}
									<button
										type="button"
										class="min-h-11 w-full rounded-lg bg-gray-950 px-4 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100"
										on:click={beginPublicationEdit}
									>
										{$i18n.t('Publish to Discover')}
									</button>
								{/if}
							</div>
						{:else}
							<button
								type="button"
								class="min-h-11 w-full rounded-lg bg-gray-950 px-4 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100"
								on:click={beginPublicationEdit}
							>
								{$i18n.t('Publish to Discover')}
							</button>
						{/if}
					</div>
				{/if}
				{#if detail.references.length > 0}
					<div>
						<h3
							class="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400"
						>
							{$i18n.t('Reference images')}
						</h3>
						<div class="flex flex-wrap gap-2">
							{#each detail.references as reference (reference.position)}
								{#if reference.content_url}
									<button
										type="button"
										class="overflow-hidden rounded-xl border border-gray-100 dark:border-gray-800"
										on:click={() =>
											openPreview(reference.content_url as string, $i18n.t('Reference image'))}
										aria-label={$i18n.t('Reference image')}
									>
										<img
											src={reference.content_url}
											alt={`#${reference.position}`}
											loading="lazy"
											decoding="async"
											class="size-20 object-cover"
										/>
									</button>
								{:else}
									<div
										class="flex size-20 items-center justify-center rounded-xl border border-dashed border-gray-200 px-2 text-center text-xs text-gray-400 dark:border-gray-700 dark:text-gray-500"
									>
										{$i18n.t('Reference image unavailable')}
									</div>
								{/if}
							{/each}
						</div>
					</div>
				{/if}

				{#if canManage && !isAdminScope()}
					{#if captionEditing}
						<div class="flex items-start gap-2">
							<input
								id="creation-caption"
								type="text"
								bind:value={captionDraft}
								maxlength="1000"
								placeholder={$i18n.t('Add a note')}
								class="min-h-9 w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-sm text-gray-900 placeholder:text-gray-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:placeholder:text-gray-500"
							/>
							<button
								type="button"
								class="min-h-9 shrink-0 rounded-lg px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-50 dark:text-gray-300 dark:hover:bg-gray-800"
								disabled={savingCaption}
								on:click={saveCaption}
							>
								{savingCaption ? $i18n.t('Saving...') : $i18n.t('Save')}
							</button>
							<button
								type="button"
								class="min-h-9 shrink-0 rounded-lg px-2.5 py-1 text-xs font-medium text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
								on:click={cancelCaptionEdit}
							>
								{$i18n.t('Cancel')}
							</button>
						</div>
					{:else}
						<button
							type="button"
							class="inline-flex max-w-full items-center gap-1 rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-200/70 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
							on:click={() => {
								captionDraft = detail.caption ?? '';
								captionEditing = true;
							}}
						>
							<Pencil className="size-3 shrink-0" strokeWidth="2" />
							<span class="truncate">{detail.caption ?? $i18n.t('Add a note')}</span>
						</button>
					{/if}
				{:else if detail.caption}
					<p class="text-xs text-gray-500 dark:text-gray-400">
						{detail.caption}
					</p>
				{/if}
			</section>

			<!-- ── 区③ 危险动作 ── -->
			{#if canManage}
				<section class="mt-auto border-t border-gray-100 pt-3 dark:border-gray-800">
					{#if confirmRemove}
						<div class="space-y-2">
							<p class="text-sm text-gray-700 dark:text-gray-200">
								{isAdminScope()
									? $i18n.t("Remove this creation from the user's library?")
									: $i18n.t('Remove this creation from your library?')}
							</p>
							<p class="text-xs text-gray-500 dark:text-gray-400">
								{$i18n.t(
									'This will not delete images in chats, but it cannot be restored to the library in this version.'
								)}
							</p>
							<div class="flex justify-end gap-2">
								<button
									type="button"
									class="min-h-11 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
									on:click={() => (confirmRemove = false)}
								>
									{$i18n.t('Cancel')}
								</button>
								<button
									type="button"
									class="min-h-11 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
									disabled={removing}
									on:click={removeCreation}
								>
									{removing ? $i18n.t('Removing...') : $i18n.t('Remove from library')}
								</button>
							</div>
						</div>
					{:else}
						<button
							type="button"
							class="min-h-11 w-full rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-900/60 dark:text-red-400 dark:hover:bg-red-950"
							on:click={() => (confirmRemove = true)}
						>
							{$i18n.t('Remove from library')}
						</button>
					{/if}
				</section>
			{/if}
		{/if}
	</svelte:fragment>
</ArtworkViewerShell>

<ImagePreview bind:show={showPreview} src={previewSrc} alt={previewAlt} />
