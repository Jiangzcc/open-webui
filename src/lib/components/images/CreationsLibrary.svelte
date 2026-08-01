<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { deleteCreations, listAdminCreations, listCreations } from '$lib/apis/creations';
	import {
		applyCreationPage,
		assignLanes,
		beginCreationRequest,
		createCreationScopeState,
		markCreationScopeStale,
		removeCreationOptimistically,
		type AdminCreationDetail,
		type CreationDetail,
		type CreationListFilters,
		type CreationScope,
		type CreationSummary
	} from '$lib/utils/creations-library';
	import { blobExtension, zipAndDownload } from '$lib/utils/download';
	import type { ImageCreationDraft } from '$lib/utils/image-generation-batches';

	import { onDestroy, onMount } from 'svelte';

	import Loader from '$lib/components/common/Loader.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import CreationDetailsModal from './CreationDetailsModal.svelte';

	export let active = false;
	export let scope: CreationScope = 'mine';
	export let revision = 0;
	export let onReuse: (draft: ImageCreationDraft) => void = () => {};

	const i18n = getContext('i18n');

	const PAGE_SIZE = 20;

	// Keep personal assets calmer than the public discovery feed: two touch-safe
	// lanes on phones, three on tablets, and four on desktop. Deterministic
	// round-robin lanes never reshuffle existing items when another page arrives.
	const LANE_BREAKPOINTS: ReadonlyArray<[string, number]> = [
		['(min-width: 1024px)', 4],
		['(min-width: 768px)', 3],
		['(min-width: 640px)', 2],
		['(min-width: 0px)', 2]
	];
	const laneQueries =
		typeof window === 'undefined' ? [] : LANE_BREAKPOINTS.map(([mq]) => window.matchMedia(mq));

	// Resolve the lane count afresh from the live matchMedia state. We never
	// *trust* a memoised value across viewport changes: programmatic resizes
	// and some browser quirks skip the `change` event, so callers recompute on
	// every cue (mount, matchMedia change, window resize) instead of reacting
	// only to incremental events. Returning 2 when window is absent keeps SSR
	// hydrated markup consistent with the smallest-client default.
	const resolveLaneCount = (): number => {
		for (const [mq, cols] of LANE_BREAKPOINTS) {
			if (typeof window !== 'undefined' && window.matchMedia(mq).matches) {
				return cols;
			}
		}
		return LANE_BREAKPOINTS[LANE_BREAKPOINTS.length - 1][1];
	};

	let laneCount = resolveLaneCount();

	const syncLaneCount = () => {
		laneCount = resolveLaneCount();
	};

	const onLaneChange = (_event: MediaQueryListEvent) => {
		// Recompute holistically rather than trusting the single firing query —
		// shrinking the viewport flips a query to !matches, which the previous
		// "only when matches" guard ignored, freezing the count at the old peak.
		syncLaneCount();
	};

	onMount(() => {
		// Correct any drift between SSR/hydration and the real client width…
		syncLaneCount();
		for (const query of laneQueries) {
			query.addEventListener('change', onLaneChange);
		}
		window.addEventListener('resize', syncLaneCount);
	});

	onDestroy(() => {
		for (const query of laneQueries) {
			query.removeEventListener('change', onLaneChange);
		}
		window.removeEventListener('resize', syncLaneCount);
		if (searchTimer) clearTimeout(searchTimer);
	});

	let scopes: Record<'mine' | 'all', ReturnType<typeof createCreationScopeState>> = {
		mine: createCreationScopeState(),
		all: createCreationScopeState()
	};
	let appliedRevision = 0;
	let searchDraft = '';
	let filters: CreationListFilters = {
		search: '',
		task: '',
		publicationStatus: '',
		sort: 'newest'
	};
	let searchTimer: ReturnType<typeof setTimeout> | null = null;
	let selectionMode = false;
	let selectedIds = new Set<string>();
	let bulkBusy = false;

	let modalShow = false;
	let modalCreationId: string | null = null;

	$: state = scopes[scope];
	$: lanes = assignLanes(state.items, laneCount);

	const loadPage = async (targetScope: CreationScope, isFirst: boolean) => {
		const targetState = scopes[targetScope];
		const generation = beginCreationRequest(targetState);
		scopes = { ...scopes };
		try {
			const page =
				targetScope === 'all'
					? await listAdminCreations(localStorage.token, PAGE_SIZE, targetState.nextCursor)
					: await listCreations(localStorage.token, PAGE_SIZE, targetState.nextCursor, filters);
			applyCreationPage(targetState, generation, page, isFirst);
		} catch {
			applyCreationPage(targetState, generation, null, isFirst);
		}
		scopes = { ...scopes };
	};

	$: if (active) {
		const activeState = scopes[scope];
		if (activeState.stale && !activeState.loading) {
			void refreshActiveIfStale();
		} else if (!activeState.loaded && !activeState.loading && !activeState.error) {
			void loadPage(scope, true);
		}
	}
	$: if (revision > appliedRevision) {
		appliedRevision = revision;
		markCreationScopeStale(scopes.mine);
		if (scopes.all.loaded) {
			markCreationScopeStale(scopes.all);
		}
		scopes = { ...scopes };
	}

	const refreshActiveIfStale = async () => {
		const activeState = scopes[scope];
		if (!activeState.stale || activeState.loading) return;
		activeState.stale = false;
		activeState.items = [];
		activeState.nextCursor = null;
		activeState.loaded = false;
		scopes = { ...scopes };
		await loadPage(scope, true);
	};

	const loadMore = () => {
		const state = scopes[scope];
		if (state.loading || !state.nextCursor) return;
		void loadPage(scope, false);
	};

	const openDetails = (item: CreationSummary) => {
		modalCreationId = item.id;
		modalShow = true;
	};

	const reloadWithFilters = () => {
		const target = scopes.mine;
		target.requestGeneration += 1;
		target.items = [];
		target.nextCursor = null;
		target.loaded = false;
		target.loading = false;
		target.error = null;
		scopes = { ...scopes };
		selectedIds = new Set();
		if (active && scope === 'mine') void loadPage('mine', true);
	};

	const updateFilters = (patch: Partial<CreationListFilters>) => {
		filters = { ...filters, ...patch };
		reloadWithFilters();
	};

	const scheduleSearch = () => {
		if (searchTimer) clearTimeout(searchTimer);
		searchTimer = setTimeout(() => updateFilters({ search: searchDraft }), 350);
	};

	const toggleSelected = (item: CreationSummary) => {
		const next = new Set(selectedIds);
		if (next.has(item.id)) next.delete(item.id);
		else next.add(item.id);
		selectedIds = next;
	};

	const handleCardClick = (item: CreationSummary) => {
		if (selectionMode) toggleSelected(item);
		else openDetails(item);
	};

	const leaveSelectionMode = () => {
		selectionMode = false;
		selectedIds = new Set();
	};

	const downloadSelected = async () => {
		if (selectedIds.size === 0 || bulkBusy) return;
		bulkBusy = true;
		try {
			const selected = state.items.filter((item) => selectedIds.has(item.id) && item.content_url);
			await zipAndDownload(
				selected.map((item) => ({
					url: item.content_url as string,
					filename: (index: number, blob: Blob) =>
						`${String(index + 1).padStart(2, '0')}-${item.id}.${blobExtension(blob)}`
				})),
				`creations-${Date.now()}.zip`
			);
		} catch {
			toast.error($i18n.t('Failed to download selected creations'));
		} finally {
			bulkBusy = false;
		}
	};

	const removeSelected = async () => {
		if (
			selectedIds.size === 0 ||
			bulkBusy ||
			!window.confirm($i18n.t('Remove selected creations from your library?'))
		) {
			return;
		}
		bulkBusy = true;
		try {
			const response = await deleteCreations(localStorage.token, [...selectedIds]);
			for (const id of response.removed_ids) {
				for (const targetScope of ['mine', 'all'] as const) {
					if (scopes[targetScope].items.some((item) => item.id === id)) {
						removeCreationOptimistically(scopes[targetScope], id);
					}
				}
			}
			scopes = { ...scopes };
			leaveSelectionMode();
			toast.success($i18n.t('Selected creations removed'));
		} catch {
			toast.error($i18n.t('Failed to remove selected creations'));
		} finally {
			bulkBusy = false;
		}
	};

	const onModalUpdated = (detail: CreationDetail | AdminCreationDetail) => {
		for (const targetScope of ['mine', 'all'] as const) {
			const item = scopes[targetScope].items.find((candidate) => candidate.id === detail.id);
			if (item) {
				Object.assign(item, {
					caption: detail.caption,
					publication_status: detail.publication?.status ?? null,
					updated_at: detail.updated_at
				});
			}
		}
		scopes = { ...scopes };
	};

	const onModalRemoved = (creationId: string) => {
		for (const targetScope of ['mine', 'all'] as const) {
			try {
				removeCreationOptimistically(scopes[targetScope], creationId);
			} catch {
				// A scope may not be loaded or may not contain this owner's item.
			}
		}
		scopes = { ...scopes };
	};
</script>

<section class="flex h-full flex-col" aria-label={$i18n.t('Library')}>
	{#if scope === 'mine'}
		<div class="shrink-0 border-b border-gray-100 px-3 pb-3 dark:border-gray-850 sm:px-4">
			{#if selectionMode}
				<div
					class="flex min-h-11 flex-wrap items-center gap-2 rounded-2xl bg-gray-100 px-3 py-2 dark:bg-gray-850"
				>
					<p class="mr-auto text-sm font-medium text-gray-800 dark:text-gray-100">
						{$i18n.t('{{count}} selected', { count: selectedIds.size })}
					</p>
					<button
						type="button"
						class="min-h-11 rounded-xl px-3 text-sm text-gray-700 hover:bg-white dark:text-gray-200 dark:hover:bg-gray-800"
						disabled={selectedIds.size === 0 || bulkBusy}
						on:click={downloadSelected}>{$i18n.t('Download ZIP')}</button
					>
					<button
						type="button"
						class="min-h-11 rounded-xl px-3 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
						disabled={selectedIds.size === 0 || bulkBusy}
						on:click={removeSelected}>{$i18n.t('Remove')}</button
					>
					<button
						type="button"
						class="min-h-11 rounded-xl px-3 text-sm text-gray-600 hover:bg-white dark:text-gray-300 dark:hover:bg-gray-800"
						on:click={leaveSelectionMode}>{$i18n.t('Cancel')}</button
					>
				</div>
			{:else}
				<div class="grid grid-cols-2 gap-2 sm:flex sm:items-center">
					<label class="col-span-2 min-w-0 flex-1 sm:max-w-md">
						<span class="sr-only">{$i18n.t('Search creations')}</span>
						<input
							type="search"
							bind:value={searchDraft}
							on:input={scheduleSearch}
							placeholder={$i18n.t('Search prompts, notes, or models')}
							class="min-h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-900 outline-none transition focus:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
						/>
					</label>
					<Select
						value={filters.task}
						items={[
							{ value: '', label: $i18n.t('All types') },
							{ value: 'text-to-image', label: $i18n.t('Text to Image') },
							{ value: 'image-to-image', label: $i18n.t('Image to Image') }
						]}
						placeholder={$i18n.t('All types')}
						triggerClass="flex min-h-11 w-full min-w-0 items-center rounded-xl border border-gray-200 bg-white px-3 text-left text-sm text-gray-700 outline-none transition focus-visible:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 sm:w-auto sm:min-w-32"
						labelClass="block min-w-0 truncate"
						onChange={(task) => updateFilters({ task: task as CreationListFilters['task'] })}
					/>
					<Select
						value={filters.publicationStatus}
						items={[
							{ value: '', label: $i18n.t('All visibility') },
							{ value: 'published', label: $i18n.t('Published') },
							{ value: 'unpublished', label: $i18n.t('Not published') }
						]}
						placeholder={$i18n.t('All visibility')}
						triggerClass="flex min-h-11 w-full min-w-0 items-center rounded-xl border border-gray-200 bg-white px-3 text-left text-sm text-gray-700 outline-none transition focus-visible:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 sm:w-auto sm:min-w-32"
						labelClass="block min-w-0 truncate"
						onChange={(publicationStatus) =>
							updateFilters({
								publicationStatus: publicationStatus as CreationListFilters['publicationStatus']
							})}
					/>
					<Select
						value={filters.sort}
						items={[
							{ value: 'newest', label: $i18n.t('Newest first') },
							{ value: 'oldest', label: $i18n.t('Oldest first') }
						]}
						placeholder={$i18n.t('Newest first')}
						triggerClass="flex min-h-11 w-full min-w-0 items-center rounded-xl border border-gray-200 bg-white px-3 text-left text-sm text-gray-700 outline-none transition focus-visible:border-gray-400 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 sm:w-auto sm:min-w-32"
						labelClass="block min-w-0 truncate"
						onChange={(sort) => updateFilters({ sort: sort as CreationListFilters['sort'] })}
					/>
					<button
						type="button"
						class="min-h-11 rounded-xl border border-gray-200 px-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
						on:click={() => (selectionMode = true)}
					>
						{$i18n.t('Select')}
					</button>
				</div>
			{/if}
		</div>
	{/if}
	<div class="flex-1 min-h-0 overflow-y-auto">
		{#if state.loading && !state.loaded}
			<div class="flex items-center justify-center py-16">
				<Spinner className="size-6" />
			</div>
		{:else if state.error && state.items.length === 0}
			<div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
				<p class="text-sm text-red-500 dark:text-red-400">{$i18n.t('Load more failed')}</p>
				<button
					type="button"
					class="min-h-11 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-white dark:text-gray-900"
					on:click={() => loadPage(scope, true)}
				>
					{$i18n.t('Retry')}
				</button>
			</div>
		{:else if state.items.length === 0}
			<div
				class="flex flex-col items-center justify-center gap-3 py-16 text-center text-gray-500 dark:text-gray-400"
			>
				<Photo className="size-8" strokeWidth="1.5" />
				<p class="text-sm">{$i18n.t('Newly generated images will appear here.')}</p>
				<p class="text-xs">
					{$i18n.t('Creations recorded before this feature was enabled are not included.')}
				</p>
			</div>
		{:else}
			<div class="flex gap-2 px-3 sm:gap-3 sm:px-4 lg:gap-4">
				{#each lanes as lane, laneIndex (laneIndex)}
					<div class="flex min-w-0 flex-1 flex-col gap-2 sm:gap-3 lg:gap-4">
						{#each lane as item (item.id)}
							<article
								class="group relative w-full overflow-hidden rounded-xl border bg-white text-left transition dark:bg-gray-900/60 {selectedIds.has(
									item.id
								)
									? 'border-gray-950 ring-2 ring-gray-950/15 dark:border-white dark:ring-white/20'
									: 'border-gray-100 hover:border-gray-300 focus-within:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700'}"
							>
								<button
									type="button"
									class="block w-full overflow-hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400"
									on:click={() => handleCardClick(item)}
									aria-label={$i18n.t('View creation')}
									aria-pressed={selectionMode ? selectedIds.has(item.id) : undefined}
								>
									<div class="relative w-full overflow-hidden bg-gray-50 dark:bg-gray-800">
										{#if item.content_url}
											<img
												src={item.content_url}
												alt={item.caption ?? $i18n.t('Artwork')}
												loading="lazy"
												decoding="async"
												class="h-auto w-full transition duration-300 group-hover:scale-[1.01]"
											/>
										{:else}
											<div
												class="flex min-h-32 w-full items-center justify-center px-3 text-center text-xs text-gray-400 dark:text-gray-500"
											>
												{$i18n.t('Source file unavailable')}
											</div>
										{/if}
										{#if selectionMode}
											<span
												class="absolute right-2 top-2 flex size-8 items-center justify-center rounded-full border-2 text-sm font-semibold shadow-sm backdrop-blur {selectedIds.has(
													item.id
												)
													? 'border-gray-950 bg-gray-950 text-white dark:border-white dark:bg-white dark:text-gray-950'
													: 'border-white bg-black/25 text-transparent'}"
												aria-hidden="true"
											>
												✓
											</span>
										{/if}
									</div>
								</button>
							</article>
						{/each}
					</div>
				{/each}
			</div>

			{#if state.error && state.items.length > 0}
				<div class="flex flex-col items-center gap-2 py-5 text-center">
					<p class="text-sm text-red-500 dark:text-red-400">{$i18n.t('Load more failed')}</p>
					<button
						type="button"
						class="min-h-11 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white dark:bg-white dark:text-gray-900"
						on:click={loadMore}
					>
						{$i18n.t('Retry')}
					</button>
				</div>
			{:else if state.nextCursor}
				<div class="flex justify-center py-6">
					{#if state.loading}
						<Spinner className="size-5" />
					{:else}
						<Loader on:visible={loadMore} />
					{/if}
				</div>
			{/if}
		{/if}
	</div>
</section>

<CreationDetailsModal
	bind:show={modalShow}
	creationId={modalCreationId}
	{scope}
	canManage={scope === 'mine' || scope === 'all'}
	onUpdated={onModalUpdated}
	onRemoved={onModalRemoved}
	{onReuse}
/>
