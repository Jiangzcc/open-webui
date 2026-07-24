<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import dayjs from 'dayjs';

	import {
		deleteCreation,
		getAdminCreation,
		getCreation,
		updateCreation
	} from '$lib/apis/creations';
	import type {
		AdminCreationDetail,
		CreationDetail,
		CreationScope,
		ParamTag
	} from '$lib/utils/creations-library';

	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Clipboard from '$lib/components/icons/Clipboard.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	import { copyToClipboard, formatDate } from '$lib/utils';
	import { extractParamTags } from '$lib/utils/creations-library';

	export let show = false;
	export let creationId: string | null = null;
	export let scope: CreationScope = 'mine';
	export let canManage = false;
	export let onUpdated: (detail: CreationDetail | AdminCreationDetail) => void = () => {};
	export let onRemoved: (creationId: string) => void = () => {};

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
			await deleteCreation(localStorage.token, sid);
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

	const openPreview = (url: string, alt: string) => {
		previewSrc = url;
		previewAlt = alt;
		showPreview = true;
	};

	// Localise the curated param keys onto short chip labels. Kept tight beside
	// the consumer rather than exported, because the only writer of these keys
	// is `extractParamTags`'s PARAM_TAG_ORDER; diverging here trips nothing
	// worse than a falling-through English-ish fallback per the default arm.
	const PARAM_LABELS: Record<ParamTag['key'], string> = {
		size: $i18n.t('Size'),
		resolution: $i18n.t('Resolution'),
		aspect_ratio: $i18n.t('Aspect ratio'),
		quality: $i18n.t('Quality'),
		image_count: $i18n.t('Image count'),
		steps: $i18n.t('Steps'),
		guidance_scale: $i18n.t('Guidance scale'),
		seed: $i18n.t('Seed'),
		style: $i18n.t('Style'),
		output_format: $i18n.t('Format'),
		background: $i18n.t('Background'),
		acceleration: $i18n.t('Acceleration'),
		input_fidelity: $i18n.t('Input fidelity'),
		thinking_level: $i18n.t('Thinking level')
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
</script>

<Modal
	bind:show
	size="lg"
	containerClassName="px-2 py-2 sm:px-3 sm:py-4 max-h-[100dvh] flex"
	className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-2xl sm:rounded-3xl !w-fit max-w-5xl max-h-[96dvh] sm:max-h-[92dvh] overflow-hidden"
>
	<div class="flex max-h-[96dvh] min-w-0 flex-col sm:max-h-[92dvh]">
		<div
			class="flex shrink-0 items-center justify-between gap-3 px-4 pt-2.5 pb-1.5 sm:px-5 sm:pt-3"
		>
			<button
				type="button"
				class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100"
				on:click={() => (show = false)}
				aria-label={$i18n.t('Close')}
			>
				<XMark className="size-5" strokeWidth="2" />
			</button>
			<div class="flex min-w-0 items-center gap-2 text-right">
				{#if detail && isAdminScope() && 'owner' in detail}
					<!-- Admin-only owner badge: collapsed to a chip, expands the email on
					     hover/focus so audit info stops crowding everyone else's first frame. -->
					<div class="group/admn relative shrink-0">
						<span
							class="inline-flex max-w-[10rem] items-center truncate rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300"
							tabindex={detail.owner.deleted || !detail.owner.email ? '-1' : '0'}
							title={detail.owner.deleted ? '' : (detail.owner.email ?? '')}
						>
							{detail.owner.deleted
								? $i18n.t('Deleted user')
								: (detail.owner.name ?? detail.owner.user_id)}
						</span>
						{#if !detail.owner.deleted && detail.owner.email}
							<a
								href={`mailto:${detail.owner.email}`}
								class="pointer-events-none absolute right-0 top-full z-10 mt-1 hidden truncate rounded-md bg-gray-900 px-2.5 py-1 text-xs text-white shadow-lg group-hover/admn:block group-focus-within/admn:block dark:bg-gray-700"
							>
								{detail.owner.email}
							</a>
						{/if}
					</div>
				{/if}
				{#if headerSubtitle}
					<span class="truncate text-xs text-gray-500 dark:text-gray-400">
						{headerSubtitle}
					</span>
				{/if}
			</div>
		</div>

		{#if loading}
			<div class="flex flex-1 items-center justify-center py-16">
				<Spinner className="size-6" />
			</div>
		{:else if error}
			<div class="flex-1 overflow-y-auto px-5 py-10 text-center">
				<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
			</div>
		{:else if detail}
			<div
				class="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:items-start lg:overflow-hidden"
			>
				<section
					class="flex min-w-0 items-center justify-center bg-neutral-100 p-3 sm:p-4 lg:min-h-0 lg:flex-initial lg:self-stretch lg:bg-transparent lg:p-5 dark:bg-black/40 lg:dark:bg-transparent"
					aria-label={$i18n.t('Artwork')}
				>
					{#if detail.content_url}
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
				</section>

				<aside
					class="flex min-w-0 flex-col gap-5 border-t border-gray-100 px-4 py-4 lg:w-[22rem] lg:shrink-0 lg:self-stretch lg:overflow-y-auto lg:border-t-0 lg:border-l lg:px-5 dark:border-gray-800"
				>
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
								<span class="font-medium"
									>{$i18n.t('Negative Prompt')}:
								</span>{detail.negative_prompt}
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

						{#if canManage}
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
										{$i18n.t('Remove this creation from your library?')}
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
				</aside>
			</div>
		{/if}
	</div>
</Modal>

<ImagePreview bind:show={showPreview} src={previewSrc} alt={previewAlt} />
