<script lang="ts">
	import { listAdminCreations, listCreations } from '$lib/apis/creations';
	import {
		applyCreationPage,
		beginCreationRequest,
		createCreationScopeState,
		markCreationScopeStale,
		removeCreationOptimistically,
		CREATION_ASPECT_RATIOS,
		type AdminCreationDetail,
		type CreationDetail,
		type CreationListFilters,
		type CreationScope,
		type CreationSummary
	} from '$lib/utils/creations-library';
	import type { ImageCreationDraft } from '$lib/utils/image-generation-batches';
	import { getI18nContext } from '$lib/i18n/context';
	import { playMutedPreview, stopPreview as stopVideoPreview } from '$lib/utils/video-preview';

	import { onDestroy, onMount } from 'svelte';
	import { slide } from 'svelte/transition';

	import { goto } from '$app/navigation';

	import Loader from '$lib/components/common/Loader.svelte';
	import MediaGalleryHeader from '$lib/components/common/MediaGalleryHeader.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ArrowPath from '$lib/components/icons/ArrowPath.svelte';
	import AdjustmentsHorizontal from '$lib/components/icons/AdjustmentsHorizontal.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Play from '$lib/components/icons/Play.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import CreationDetailsModal from './CreationDetailsModal.svelte';
	import LibraryFilterSelect, { IDLE_PILL, ACTIVE_PILL } from './LibraryFilterSelect.svelte';

	export let active = false;
	export let scope: CreationScope = 'mine';
	export let revision = 0;
	export let onReuse: (draft: ImageCreationDraft) => void = () => {};
	export let headerTitle = '';
	export let headerItems: ReadonlyArray<{ value: string; label: string }> = [];
	export let headerSelected = '';
	export let headerAriaLabel = '';
	export let headerIdPrefix = 'asset-scope-tab';
	export let onHeaderSelect: (value: string) => void = () => {};

	const i18n = getI18nContext();

	const PAGE_SIZE = 20;
	const SKELETON_IDS = Array.from({ length: 10 }, (_, index) => index);

	onDestroy(() => {
		if (searchTimer) clearTimeout(searchTimer);
	});

	let scopes: Record<'mine' | 'all', ReturnType<typeof createCreationScopeState>> = {
		mine: createCreationScopeState(),
		all: createCreationScopeState()
	};
	let appliedRevision = 0;
	let searchDraft = '';
	const DEFAULT_FILTERS: CreationListFilters = {
		kind: '',
		search: '',
		task: '',
		publicationStatus: '',
		sort: 'newest',
		since: '',
		clarity: '',
		aspectRatio: ''
	};
	let filters: CreationListFilters = { ...DEFAULT_FILTERS };
	let searchTimer: ReturnType<typeof setTimeout> | null = null;

	let modalShow = false;
	let modalCreationId: string | null = null;
	let hoverCapable = false;
	const previewVideos: Record<string, HTMLVideoElement | null> = {};

	const playPreview = (id: string) => {
		void playMutedPreview(previewVideos[id], hoverCapable);
	};

	const stopPreview = (id: string) => {
		stopVideoPreview(previewVideos[id]);
	};

	onMount(() => {
		const hoverQuery = window.matchMedia('(hover: hover)');
		const updateHoverCapability = () => (hoverCapable = hoverQuery.matches);
		updateHoverCapability();
		hoverQuery.addEventListener('change', updateHoverCapability);
		return () => hoverQuery.removeEventListener('change', updateHoverCapability);
	});

	$: state = scopes[scope];

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

	const creationTitle = (item: CreationSummary) =>
		item.caption?.trim() || item.prompt_preview?.trim() || item.model_name?.trim() || item.id;

	const reloadWithFilters = () => {
		const target = scopes.mine;
		target.requestGeneration += 1;
		target.items = [];
		target.nextCursor = null;
		target.loaded = false;
		target.loading = false;
		target.error = null;
		scopes = { ...scopes };
		if (active && scope === 'mine') void loadPage('mine', true);
	};

	const updateFilters = (patch: Partial<CreationListFilters>) => {
		filters = { ...filters, ...patch };
		reloadWithFilters();
	};

	const resetFilters = () => {
		searchDraft = '';
		updateFilters({ ...DEFAULT_FILTERS, search: '' });
	};

	const scheduleSearch = () => {
		if (searchTimer) clearTimeout(searchTimer);
		searchTimer = setTimeout(() => updateFilters({ search: searchDraft }), 350);
	};

	// 类型筛选合并 kind 与创作方式：图片/视频命中 kind，具体任务命中 task。
	const selectTypeFilter = (value: string) => {
		if (value === 'image' || value === 'video') {
			updateFilters({ kind: value, task: '' });
		} else if (value) {
			updateFilters({ kind: '', task: value as CreationListFilters['task'] });
		} else {
			updateFilters({ kind: '', task: '' });
		}
	};

	// 筛选下拉的单一配置源：移动端面板与桌面端胶囊行共用同一份定义，
	// 两处渲染只差 fullWidth 与容器（重构消除原先 ~190 行的双份模板）。
	// label 带 raw 的项（2K/4K/比例）不过 i18n：冒号会被 namespace 分隔符误拆。
	type FilterSelectConfig = {
		key: string;
		mobile: 'row' | 'panel';
		value: (filters: CreationListFilters) => string;
		active: (filters: CreationListFilters) => boolean;
		items: Array<{ value: string; label: string; raw?: boolean }>;
		placeholder: string;
		onChange: (value: string) => void;
	};

	const RAW_FILTER_SELECTS: FilterSelectConfig[] = [
		{
			key: 'type',
			mobile: 'panel',
			value: (filters) => filters.task || filters.kind || '',
			active: (filters) => Boolean(filters.task || filters.kind),
			items: [
				{ value: '', label: 'All types' },
				{ value: 'image', label: 'Images' },
				{ value: 'video', label: 'Videos' },
				{ value: 'text-to-image', label: 'Text to Image' },
				{ value: 'image-to-image', label: 'Image to Image' },
				{ value: 'text-to-video', label: 'Text to Video' },
				{ value: 'image-to-video', label: 'Image to Video' },
				{ value: 'video-to-video', label: 'Video to Video' }
			],
			placeholder: 'All types',
			onChange: selectTypeFilter
		},
		{
			key: 'since',
			mobile: 'panel',
			value: (filters) => filters.since ?? '',
			active: (filters) => Boolean(filters.since),
			items: [
				{ value: '', label: 'All time' },
				{ value: '24h', label: 'Last 24 hours' },
				{ value: '7d', label: 'Last 7 days' },
				{ value: '30d', label: 'Last 30 days' }
			],
			placeholder: 'All time',
			onChange: (since) => updateFilters({ since: since as CreationListFilters['since'] })
		},
		{
			key: 'clarity',
			mobile: 'panel',
			value: (filters) => filters.clarity ?? '',
			active: (filters) => Boolean(filters.clarity),
			items: [
				{ value: '', label: 'All clarity' },
				{ value: 'sd', label: 'SD' },
				{ value: 'hd', label: 'HD' },
				{ value: 'fhd', label: 'Full HD' },
				{ value: '2k', label: '2K', raw: true },
				{ value: '4k', label: '4K', raw: true }
			],
			placeholder: 'All clarity',
			onChange: (clarity) => updateFilters({ clarity: clarity as CreationListFilters['clarity'] })
		},
		{
			key: 'aspectRatio',
			mobile: 'panel',
			value: (filters) => filters.aspectRatio ?? '',
			active: (filters) => Boolean(filters.aspectRatio),
			items: [
				{ value: '', label: 'All aspect ratios' },
				...CREATION_ASPECT_RATIOS.map((ratio) => ({ value: ratio, label: ratio, raw: true }))
			],
			placeholder: 'All aspect ratios',
			onChange: (aspectRatio) =>
				updateFilters({ aspectRatio: aspectRatio as CreationListFilters['aspectRatio'] })
		},
		{
			key: 'publicationStatus',
			mobile: 'panel',
			value: (filters) => filters.publicationStatus ?? '',
			active: (filters) => Boolean(filters.publicationStatus),
			items: [
				{ value: '', label: 'All visibility' },
				{ value: 'published', label: 'Published' },
				{ value: 'unpublished', label: 'Not published' }
			],
			placeholder: 'All visibility',
			onChange: (publicationStatus) =>
				updateFilters({
					publicationStatus: publicationStatus as CreationListFilters['publicationStatus']
				})
		},
		{
			key: 'sort',
			mobile: 'row',
			value: (filters) => filters.sort ?? '',
			active: (filters) => filters.sort !== DEFAULT_FILTERS.sort,
			items: [
				{ value: 'newest', label: 'Newest first' },
				{ value: 'oldest', label: 'Oldest first' }
			],
			placeholder: 'Newest first',
			onChange: (sort) => updateFilters({ sort: sort as CreationListFilters['sort'] })
		}
	];

	// label/placeholder 走 i18n 响应式解析（语言切换时整组重建），值与激活态从 filters 派生。
	$: filterSelects = RAW_FILTER_SELECTS.map((config) => ({
		...config,
		value: config.value(filters),
		active: config.active(filters),
		placeholder: $i18n.t(config.placeholder),
		items: config.items.map((item) => ({
			value: item.value,
			label: item.raw ? item.label : $i18n.t(item.label)
		}))
	}));
	$: panelSelects = filterSelects.filter((config) => config.mobile === 'panel');
	$: rowSortSelect = filterSelects.find((config) => config.mobile === 'row');
	$: primaryDesktopSelects = filterSelects.filter(
		(config) => config.key === 'type' || config.key === 'since'
	);
	$: advancedDesktopSelects = filterSelects.filter(
		(config) => config.key !== 'type' && config.key !== 'since'
	);

	// 空态区分「库里还没有作品」与「筛选条件过滤掉了所有作品」，
	// 后者提示文案才有意义，前者应该引导去创作。
	$: hasActiveFilters = Boolean(
		filters.kind ||
		filters.task ||
		filters.since ||
		filters.clarity ||
		filters.aspectRatio ||
		filters.publicationStatus ||
		filters.search
	);

	// 移动端筛选收纳：工具行常驻 搜索/排序/筛选入口，其余筛选进展开面板，
	// 让作品网格尽快出现（用户拍板：顶部堆叠太占空间）。
	let mobileFiltersOpen = false;
	let desktopFiltersOpen = false;

	// 收纳进面板的筛选不可见，用计数徽标提示面板里生效了几项
	// （排序除外——它在移动端工具行内常驻可见）。
	$: panelFilterCount =
		(filters.kind || filters.task ? 1 : 0) +
		(filters.since ? 1 : 0) +
		(filters.clarity ? 1 : 0) +
		(filters.aspectRatio ? 1 : 0) +
		(filters.publicationStatus ? 1 : 0);
	$: advancedFilterCount =
		(filters.clarity ? 1 : 0) +
		(filters.aspectRatio ? 1 : 0) +
		(filters.publicationStatus ? 1 : 0) +
		(filters.sort !== DEFAULT_FILTERS.sort ? 1 : 0);

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

<section class="min-h-full bg-transparent" aria-label={$i18n.t('Library')}>
	<MediaGalleryHeader
		title={headerTitle}
		items={headerItems}
		selected={headerSelected}
		ariaLabel={headerAriaLabel}
		idPrefix={headerIdPrefix}
		onSelect={onHeaderSelect}
	>
		{#if scope === 'mine'}
			<!-- vidu 风格工具行：裸筛选胶囊（无容器框），激活的筛选点亮为深色胶囊。
		     移动端压成一行（搜索为主 + 排序/筛选入口），其余筛选收纳进展开面板；
		     桌面端完整一行：胶囊换行、搜索靠右。 -->
			<div class="pb-2">
				<!-- 移动端单行工具（用户拍板：顶部堆叠太占空间）：搜索为主，
				 排序与筛选入口收在右侧；桌面端隐藏，走下方完整工具行。 -->
				<div class="flex items-center gap-2 md:hidden">
					<label
						class="flex min-h-11 min-w-0 flex-1 items-center gap-2 rounded-[10px] border border-slate-200/75 bg-white/45 px-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition focus-within:border-[#5b6ee1]/45 focus-within:bg-white/75 focus-within:ring-2 focus-within:ring-[#5b6ee1]/15 dark:border-white/[0.09] dark:bg-white/[0.055] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] dark:focus-within:border-[#8290ed]/45 dark:focus-within:bg-white/[0.08]"
					>
						<Search className="size-4 shrink-0 text-gray-400 dark:text-white/50" strokeWidth="2" />
						<span class="sr-only">{$i18n.t('Search creations')}</span>
						<input
							type="search"
							bind:value={searchDraft}
							on:input={scheduleSearch}
							placeholder={$i18n.t('Search prompts, notes, or models')}
							class="h-full w-full min-w-0 bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-white dark:placeholder:text-white/40"
						/>
					</label>
					{#if rowSortSelect}
						<LibraryFilterSelect
							value={rowSortSelect.value}
							items={rowSortSelect.items}
							placeholder={rowSortSelect.placeholder}
							active={rowSortSelect.active}
							onChange={rowSortSelect.onChange}
						/>
					{/if}
					<button
						type="button"
						class="flex min-h-11 shrink-0 items-center gap-2 rounded-[10px] px-3.5 py-2 text-sm font-normal transition active:scale-[0.98] {mobileFiltersOpen ||
						panelFilterCount > 0
							? ACTIVE_PILL
							: IDLE_PILL}"
						aria-expanded={mobileFiltersOpen}
						aria-controls="mobile-filter-panel"
						aria-label={$i18n.t('Filters')}
						on:click={() => (mobileFiltersOpen = !mobileFiltersOpen)}
					>
						<AdjustmentsHorizontal className="size-4 shrink-0" strokeWidth="2" />
						{#if panelFilterCount > 0}
							<span
								class="flex h-5 min-w-5 items-center justify-center rounded-md bg-[#5b6ee1] px-1 text-[10px] font-medium text-white"
							>
								{panelFilterCount}
							</span>
						{/if}
					</button>
				</div>

				<!-- 移动端筛选面板：其余筛选与重置收纳于此，展开才占空间。 -->
				{#if mobileFiltersOpen}
					<div
						id="mobile-filter-panel"
						class="grid grid-cols-2 gap-2 pt-2 md:hidden"
						transition:slide={{ duration: 150 }}
					>
						{#each panelSelects as select (select.key)}
							<LibraryFilterSelect
								fullWidth
								value={select.value}
								items={select.items}
								placeholder={select.placeholder}
								active={select.active}
								onChange={select.onChange}
							/>
						{/each}
						<button
							type="button"
							class="flex min-h-11 w-full items-center justify-center gap-2 rounded-[10px] border border-slate-200/75 bg-white/30 text-sm font-normal text-slate-500 transition active:scale-[0.98] hover:bg-white/70 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#5b6ee1] disabled:pointer-events-none disabled:opacity-40 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-400 dark:hover:bg-white/[0.08]"
							disabled={!hasActiveFilters && !searchDraft}
							on:click={resetFilters}
						>
							<ArrowPath className="size-3.5" strokeWidth="2" />
							{$i18n.t('Reset')}
						</button>
					</div>
				{/if}

				<!-- 桌面端只保留高频条件，其他条件收进同一层级的高级筛选区。 -->
				<div class="hidden items-center gap-2 md:flex">
					{#each primaryDesktopSelects as select (select.key)}
						<div class={select.key === 'type' ? 'w-40 shrink-0' : 'w-36 shrink-0'}>
							<LibraryFilterSelect
								fullWidth
								value={select.value}
								items={select.items}
								placeholder={select.placeholder}
								active={select.active}
								onChange={select.onChange}
							/>
						</div>
					{/each}
					<button
						type="button"
						class="flex h-9 shrink-0 items-center gap-2 rounded-[10px] px-3.5 text-sm transition active:scale-[0.98] {desktopFiltersOpen ||
						advancedFilterCount > 0
							? ACTIVE_PILL
							: IDLE_PILL}"
						aria-expanded={desktopFiltersOpen}
						aria-controls="desktop-filter-panel"
						on:click={() => (desktopFiltersOpen = !desktopFiltersOpen)}
					>
						<AdjustmentsHorizontal className="size-4 shrink-0" strokeWidth="2" />
						{$i18n.t('Filters')}
						{#if advancedFilterCount > 0}
							<span
								class="flex h-5 min-w-5 items-center justify-center rounded-md bg-[#5b6ee1] px-1 text-[10px] font-medium text-white"
							>
								{advancedFilterCount}
							</span>
						{/if}
					</button>
					{#if hasActiveFilters || searchDraft}
						<button
							type="button"
							class="flex h-9 shrink-0 items-center gap-1.5 rounded-[10px] px-2.5 text-sm text-slate-500 transition hover:bg-white/45 hover:text-slate-900 active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#5b6ee1] dark:text-slate-400 dark:hover:bg-white/[0.06] dark:hover:text-slate-100"
							on:click={resetFilters}
						>
							<ArrowPath className="size-3.5" strokeWidth="2" />
							{$i18n.t('Reset')}
						</button>
					{/if}
					<div class="min-w-4 flex-1"></div>
					<label
						class="flex h-9 w-[min(18rem,28vw)] min-w-44 items-center gap-2 rounded-[10px] border border-slate-200/75 bg-white/45 px-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] transition focus-within:border-[#5b6ee1]/45 focus-within:bg-white/75 focus-within:ring-2 focus-within:ring-[#5b6ee1]/15 dark:border-white/[0.09] dark:bg-white/[0.055] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] dark:focus-within:border-[#8290ed]/45 dark:focus-within:bg-white/[0.08]"
					>
						<Search
							className="size-4 shrink-0 text-slate-400 dark:text-slate-500"
							strokeWidth="2"
						/>
						<span class="sr-only">{$i18n.t('Search creations')}</span>
						<input
							type="search"
							bind:value={searchDraft}
							on:input={scheduleSearch}
							placeholder={$i18n.t('Search prompts, notes, or models')}
							class="h-full w-full min-w-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
						/>
					</label>
				</div>

				{#if desktopFiltersOpen}
					<div
						id="desktop-filter-panel"
						class="mt-2 hidden grid-cols-2 gap-2 rounded-[14px] border border-white/65 bg-white/55 p-2 shadow-[0_16px_34px_-24px_rgba(66,79,111,0.45),inset_0_1px_0_rgba(255,255,255,0.82)] backdrop-blur-xl md:grid md:grid-cols-4 dark:border-white/[0.08] dark:bg-[#111722]/75 dark:shadow-[0_18px_38px_-24px_rgba(1,4,12,0.9),inset_0_1px_0_rgba(255,255,255,0.07)]"
					>
						{#each advancedDesktopSelects as select (select.key)}
							<LibraryFilterSelect
								fullWidth
								value={select.value}
								items={select.items}
								placeholder={select.placeholder}
								active={select.active}
								onChange={select.onChange}
							/>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</MediaGalleryHeader>
	<div class="min-h-0" aria-live="polite">
		{#if state.loading && !state.loaded}
			<!-- 首次加载骨架屏：与图片页生成中占位一致的 animate-pulse shimmer -->
			<div
				class="mx-auto grid w-full max-w-[96rem] grid-cols-1 gap-x-4 gap-y-7 px-4 py-5 sm:grid-cols-2 sm:px-6 md:grid-cols-3 lg:px-8 xl:grid-cols-4"
				aria-hidden="true"
			>
				{#each SKELETON_IDS as index (index)}
					<div
						class="aspect-video overflow-hidden rounded-[14px] bg-gray-200/70 dark:bg-white/[0.06]"
					>
						<div
							class="h-full w-full animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.02]"
						></div>
					</div>
				{/each}
			</div>
		{:else if state.error && state.items.length === 0}
			<div class="flex flex-col items-center justify-center gap-3 px-4 py-16 text-center">
				<p class="text-sm text-red-500 dark:text-red-400">{$i18n.t('Load more failed')}</p>
				<button
					type="button"
					class="min-h-11 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition active:scale-[0.98] dark:bg-white dark:text-gray-950"
					on:click={() => loadPage(scope, true)}
				>
					{$i18n.t('Retry')}
				</button>
			</div>
		{:else if state.items.length === 0}
			<div class="px-4 py-6 sm:px-6 lg:px-8">
				<div
					class="flex min-h-64 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-gray-200 bg-gray-50 text-center dark:border-white/10 dark:bg-white/[0.03]"
				>
					<Photo className="size-8 text-gray-400 dark:text-white/40" strokeWidth="1.5" />
					<p class="px-4 text-sm text-gray-500 dark:text-white/60">
						{hasActiveFilters
							? $i18n.t('No creations match the current filters.')
							: $i18n.t('Newly generated images and videos will appear here.')}
					</p>
					<!-- 空态是行动邀请：无筛选时引导去创作，有筛选时给一条重置出路。 -->
					{#if hasActiveFilters}
						<button
							type="button"
							class="min-h-11 rounded-lg px-4 text-sm font-medium text-gray-600 transition hover:bg-gray-100 active:scale-[0.98] dark:text-white/70 dark:hover:bg-white/10"
							on:click={resetFilters}
						>
							{$i18n.t('Reset')}
						</button>
					{:else}
						<button
							type="button"
							class="min-h-11 rounded-lg bg-gray-900 px-4 text-sm font-medium text-white transition hover:bg-gray-800 active:scale-[0.98] dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100"
							on:click={() => goto('/images')}
						>
							{$i18n.t('Start creating')}
						</button>
					{/if}
				</div>
			</div>
		{:else}
			<!-- vidu 参考网格：等高 16:9 裁切磁贴（object-cover）+ 下方 meta 行，
			     移动端单列、桌面端最多四列，替代自然比例瀑布流 lanes。 -->
			<div
				class="mx-auto grid w-full max-w-[96rem] grid-cols-1 gap-x-4 gap-y-7 px-4 py-5 sm:grid-cols-2 sm:px-6 md:grid-cols-3 lg:px-8 xl:grid-cols-4"
			>
				{#each state.items as item, itemIndex (item.id)}
					<article
						class="gallery-reveal group relative w-full"
						style={`--gallery-index: ${Math.min(itemIndex, 12)}`}
						on:mouseenter={() => playPreview(item.id)}
						on:mouseleave={() => stopPreview(item.id)}
					>
						<button
							type="button"
							class="block w-full overflow-hidden rounded-[14px] bg-slate-200/70 ring-1 ring-slate-900/[0.045] transition-[transform,box-shadow] duration-300 ease-out focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5b6ee1] active:scale-[0.99] group-hover:-translate-y-0.5 group-hover:shadow-[0_18px_38px_-22px_rgba(66,79,111,0.42)] dark:bg-white/[0.055] dark:ring-white/[0.075] dark:focus-visible:outline-[#8290ed] dark:group-hover:shadow-[0_20px_40px_-24px_rgba(1,4,12,0.92)]"
							on:click={() => openDetails(item)}
							aria-label={$i18n.t('View creation')}
						>
							<div class="relative w-full overflow-hidden">
								{#if item.content_url}
									<img
										src={item.kind === 'video'
											? (item.poster_url ?? item.content_url)
											: item.content_url}
										alt={item.caption ?? $i18n.t('Artwork')}
										loading="lazy"
										decoding="async"
										class="aspect-video w-full object-cover transition duration-500 ease-out group-hover:scale-[1.025] motion-reduce:transition-none"
									/>
									{#if item.kind === 'video'}
										<video
											bind:this={previewVideos[item.id]}
											src={item.content_url}
											muted
											playsinline
											preload="metadata"
											aria-hidden="true"
											class="pointer-events-none absolute inset-0 aspect-video h-full w-full object-cover opacity-0 transition duration-300 group-hover:opacity-100 motion-reduce:transition-none"
										></video>
										<span class="absolute inset-0 flex items-center justify-center bg-black/10"
											><span
												class="flex size-10 items-center justify-center rounded-full bg-black/65 text-white transition duration-200 group-hover:scale-90 group-hover:opacity-0"
												><Play className="size-4" strokeWidth="2" /></span
											></span
										>
										{#if item.duration_seconds}<span
												class="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 text-[10px] text-white"
												>{item.duration_seconds}s</span
											>{/if}
									{/if}
								{:else}
									<div
										class="flex aspect-video w-full items-center justify-center px-3 text-center text-xs text-gray-400 dark:text-white/50"
									>
										{$i18n.t('Source file unavailable')}
									</div>
								{/if}
							</div>
						</button>
						<div class="mt-2.5 min-w-0 px-0.5">
							<p class="truncate text-sm font-medium text-slate-800 dark:text-slate-100/90">
								{creationTitle(item)}
							</p>
							<div class="mt-0.5 flex min-w-0 items-center justify-between gap-2 text-xs">
								<p class="min-w-0 truncate text-slate-400 dark:text-slate-500">
									{new Date(item.created_at * 1000).toLocaleDateString()}
									{#if item.model_name}<span aria-hidden="true"> / </span>{item.model_name}{/if}
								</p>
								{#if item.publication_status === 'published'}
									<span class="shrink-0 font-medium text-[#5b6ee1] dark:text-[#aeb8ff]">
										{$i18n.t('Published')}
									</span>
								{/if}
							</div>
						</div>
					</article>
				{/each}
			</div>

			{#if state.error && state.items.length > 0}
				<div class="flex flex-col items-center gap-2 px-4 py-5 text-center">
					<p class="text-sm text-red-500 dark:text-red-400">{$i18n.t('Load more failed')}</p>
					<button
						type="button"
						class="min-h-11 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white transition active:scale-[0.98] dark:bg-white dark:text-gray-950"
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

			{#if !state.nextCursor && !state.loading}
				<p class="py-6 text-center text-xs text-gray-400 dark:text-white/40">
					{$i18n.t('All creations loaded.')}
				</p>
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

<style>
	@media (prefers-reduced-motion: no-preference) {
		.gallery-reveal {
			animation: gallery-reveal 420ms cubic-bezier(0.16, 1, 0.3, 1) both;
			animation-delay: calc(var(--gallery-index) * 38ms);
		}
	}

	@keyframes gallery-reveal {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
