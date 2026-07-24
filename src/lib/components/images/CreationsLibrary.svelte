<script lang="ts">
	import { getContext } from 'svelte';

	import { listAdminCreations, listCreations } from '$lib/apis/creations';
	import {
		applyCreationPage,
		assignLanes,
		beginCreationRequest,
		createCreationScopeState,
		markCreationScopeStale,
		removeCreationOptimistically,
		type AdminCreationDetail,
		type CreationDetail,
		type CreationScope,
		type CreationSummary
	} from '$lib/utils/creations-library';

	import { onDestroy, onMount } from 'svelte';

	import Loader from '$lib/components/common/Loader.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import CreationDetailsModal from './CreationDetailsModal.svelte';

	export let active = false;
	export let scope: CreationScope = 'mine';
	export let revision = 0;

	const i18n = getContext('i18n');

	const PAGE_SIZE = 20;

	// Lane breakpoints mirror the former columns-* ladder (2/3/4/5) so the
	// density curve is preserved; only the packing mechanic changes — from
	// browser-balanced CSS multicol to deterministic round-robin lanes that
	// never reshuffle existing items when a later page streams in.
	const LANE_BREAKPOINTS: ReadonlyArray<[string, number]> = [
		['(min-width: 1024px)', 5],
		['(min-width: 768px)', 4],
		['(min-width: 640px)', 3],
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
	});

	let scopes: Record<'mine' | 'all', ReturnType<typeof createCreationScopeState>> = {
		mine: createCreationScopeState(),
		all: createCreationScopeState()
	};
	let appliedRevision = 0;

	let modalShow = false;
	let modalCreationId: string | null = null;

	// Lightweight big-image preview, decoupled from the full details modal: a
	// tap on the photo opens this; the floating "details" chip opens the modal.
	let previewShow = false;
	let previewSrc = '';
	let previewAlt = '';

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
					: await listCreations(localStorage.token, PAGE_SIZE, targetState.nextCursor);
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

	const openPreview = (item: CreationSummary) => {
		if (!item.content_url) {
			// Nothing to enlarge — fall back to the details modal so the card
			// never feels like a dead tap when the underlying file is gone.
			openDetails(item);
			return;
		}
		previewSrc = item.content_url;
		previewAlt = item.caption ?? $i18n.t('Artwork');
		previewShow = true;
	};

	const onModalUpdated = (detail: CreationDetail | AdminCreationDetail) => {
		for (const targetScope of ['mine', 'all'] as const) {
			const item = scopes[targetScope].items.find((candidate) => candidate.id === detail.id);
			if (item) {
				Object.assign(item, {
					caption: detail.caption,
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
			<div class="flex gap-2 px-3 sm:px-4">
				{#each lanes as lane, laneIndex (laneIndex)}
					<div class="flex min-w-0 flex-1 flex-col gap-2">
						{#each lane as item (item.id)}
							<article
								class="group relative w-full overflow-hidden rounded-lg border border-gray-100 bg-white text-left transition hover:border-gray-200 focus-within:border-gray-200 dark:border-gray-800 dark:bg-gray-900/60 dark:hover:border-gray-700"
							>
								<button
									type="button"
									class="block w-full overflow-hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400"
									on:click={() => openPreview(item)}
									aria-label={$i18n.t('Preview')}
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
											{#if item.prompt_preview}
												<div
													class="prompt-overlay pointer-events-none absolute inset-x-0 bottom-0 translate-y-1 bg-gradient-to-t from-black/70 via-black/40 to-transparent px-2.5 py-2 pr-16 opacity-0 transition duration-200 ease-out group-hover:translate-y-0 group-hover:opacity-100"
												>
													<p class="line-clamp-2 text-xs leading-snug text-white/90">
														{item.prompt_preview}
													</p>
												</div>
											{/if}
										{:else}
											<div
												class="flex min-h-32 w-full items-center justify-center px-3 text-center text-xs text-gray-400 dark:text-gray-500"
											>
												{$i18n.t('Source file unavailable')}
											</div>
										{/if}
									</div>
								</button>
								<button
									type="button"
									class="details-btn absolute bottom-2 right-2 z-10 inline-flex min-h-8 items-center gap-1 rounded-full bg-black/35 px-2.5 text-xs font-medium text-white opacity-0 backdrop-blur-sm transition duration-200 ease-out hover:bg-black/55 focus-visible:opacity-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/80 group-hover:opacity-100"
									on:click={() => openDetails(item)}
								>
									{$i18n.t('Details')}
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
	canManage={scope === 'mine'}
	onUpdated={onModalUpdated}
	onRemoved={onModalRemoved}
/>

<ImagePreview bind:show={previewShow} src={previewSrc} alt={previewAlt} />

<style>
	/* Touch devices have no hover, so the prompt overlay would sit forever
	   invisible if we honoured the opacity-0 default. On hover-less clients we
	   pin it visible at a modest transparency so the prompt is legible without
	   swamping the artwork; pointer-events-none above lets taps reach the
	   preview button beneath it. The details chip dims to 0.7 on phones so it
	   stays reachable without competing with every thumbnail's composition. */
	@media (hover: none) {
		.prompt-overlay {
			opacity: 0.85;
			transform: translateY(0);
		}
		.details-btn {
			opacity: 0.7;
		}
	}
</style>
