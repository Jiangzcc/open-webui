<script lang="ts">
	import { goto } from '$app/navigation';
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';

	import {
		getDiscoveryPost,
		listDiscoveryCategories,
		listDiscoveryPosts,
		listFavoritePosts,
		setDiscoveryReaction
	} from '$lib/apis/discovery';
	import { showSidebar, WEBUI_NAME } from '$lib/stores';
	import {
		buildCreationDraft,
		storePendingCreationDraft,
		type ImageCreationDraft
	} from '$lib/utils/image-generation-batches';
	import { playMutedPreview, stopPreview as stopVideoPreview } from '$lib/utils/video-preview';
	import {
		applyDiscoveryPage,
		applyReactionState,
		beginDiscoveryRequest,
		createDiscoveryFeedState,
		type DiscoveryFeed,
		type DiscoveryCategory,
		type DiscoveryCategoryItem,
		type DiscoveryPostSummary,
		type ReactionKind,
		type ReactionState
	} from '$lib/utils/discovery';

	import Bookmark from '$lib/components/icons/Bookmark.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import MediaGalleryHeader from '$lib/components/common/MediaGalleryHeader.svelte';
	import MediaGallerySurface from '$lib/components/common/MediaGallerySurface.svelte';
	import MobileSidebarHeader from '$lib/components/common/MobileSidebarHeader.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import Play from '$lib/components/icons/Play.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import DiscoveryDetailsModal from './DiscoveryDetailsModal.svelte';

	const i18n = getContext<Writable<I18n>>('i18n');
	const PAGE_SIZE = 24;
	const SKELETON_IDS = Array.from({ length: 10 }, (_, index) => index);

	// Vidu 发现区的紧凑媒体墙为原型；本项目在不降低可点击性的前提下
	// 把间距放大到 8px、媒体圆角收敛到 12px，头像 16px、正文/计数 14px。
	// 瀑布流列数断点：移动 2 列、sm 3 列、lg 4 列。

	let activeFeed: DiscoveryFeed = 'latest';
	let activeCategory: DiscoveryCategory | null = null;
	let activeMediaKind: 'all' | 'image' | 'video' = 'all';
	let feeds = {
		featured: createDiscoveryFeedState(),
		latest: createDiscoveryFeedState(),
		popular: createDiscoveryFeedState(),
		favorites: createDiscoveryFeedState()
	};
	let detailsShow = false;
	let detailsPostId: string | null = null;
	let pendingReactions = new Set<string>();
	let pendingReuse = new Set<string>();
	let categories: DiscoveryCategoryItem[] = [
		{ id: 'other', display_name: $i18n.t('Other'), enabled: true, sort_order: 999 }
	];
	let masonryColumnCount = 2;
	let masonryWidth = 0;
	let contentElement: HTMLElement | null = null;
	let hoverCapable = false;
	// 注意用普通对象而非 Map：bind:this={previewVideos[item.id]} 编译为属性赋值，
	// Map 的话会写到实例属性而非条目，.get() 永远取不到。
	const previewVideos: Record<string, HTMLVideoElement | null> = {};

	$: state = feeds[activeFeed];
	$: feedNavigationItems = [
		{ value: 'featured', label: $i18n.t('Featured') },
		{ value: 'latest', label: $i18n.t('Latest') },
		{ value: 'popular', label: $i18n.t('Popular') },
		{ value: 'favorites', label: $i18n.t('My favorites') }
	];
	// vidu 瀑布流：最短列优先的均衡分布（列高尽量一致），而非轮转分列——
	// 轮转会造成某列明显偏长。用后端 aspect_ratio（无比例按 kind 兜底）在渲染前确定性估算卡片
	// 高度，布局稳定不闪动；无比例时按媒体类型兜底。
	$: masonryColumns = balanceMasonry(state.items, masonryColumnCount, masonryWidth);

	const CARD_COLUMN_GAP = 12;
	const FILTER_ACTIVE =
		'border border-[#5b6ee1]/25 bg-[#5b6ee1]/10 font-medium text-[#4051bd] shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] dark:border-[#8290ed]/30 dark:bg-[#5b6ee1]/20 dark:text-[#c4caff]';
	const FILTER_IDLE =
		'border border-transparent text-slate-500 hover:border-white/60 hover:bg-white/45 hover:text-slate-950 dark:text-slate-400 dark:hover:border-white/[0.06] dark:hover:bg-white/[0.06] dark:hover:text-slate-100';
	// 兜底比例（W/H）：图竖版 3:4、视频横版 16:9。
	const FALLBACK_ASPECT: Record<'image' | 'video', { width: number; height: number }> = {
		image: { width: 3, height: 4 },
		video: { width: 16, height: 9 }
	};

	// 后端归一化比例（"W:H"）解析；无比例（实测多为视频）按 kind 兜底。
	function aspectParts(item: DiscoveryPostSummary): { width: number; height: number } {
		const match = /^(\d+(?:\.\d+)?)[:x](\d+(?:\.\d+)?)$/.exec(item.aspect_ratio ?? '');
		if (match) {
			const width = Number(match[1]);
			const height = Number(match[2]);
			if (width > 0 && height > 0) return { width, height };
		}
		return FALLBACK_ASPECT[item.kind];
	}

	function parseAspect(item: DiscoveryPostSummary): number {
		const { width, height } = aspectParts(item);
		return height / width;
	}

	// 卡片容器强制比例（用户拍板 P1：前端兜底）：渲染高度与瀑布流估算完全一致，
	// 列高必然均衡且图片加载前后无重排（零 CLS）；无比例视频的海报按兜底比例裁切。
	function cardAspectRatioStyle(item: DiscoveryPostSummary): string {
		const { width, height } = aspectParts(item);
		return `aspect-ratio: ${width} / ${height};`;
	}

	function balanceMasonry(
		items: DiscoveryPostSummary[],
		columnCount: number,
		containerWidth: number
	): DiscoveryPostSummary[][] {
		const columnWidth =
			containerWidth > 0 ? (containerWidth - (columnCount - 1) * CARD_COLUMN_GAP) / columnCount : 0;
		const heights = new Array<number>(columnCount).fill(0);
		const columns: DiscoveryPostSummary[][] = Array.from({ length: columnCount }, () => []);
		for (const item of items) {
			let shortest = 0;
			for (let column = 1; column < columnCount; column++) {
				if (heights[column] < heights[shortest]) shortest = column;
			}
			columns[shortest].push(item);
			heights[shortest] +=
				(columnWidth > 0 ? columnWidth * parseAspect(item) : 0) + CARD_COLUMN_GAP;
		}
		return columns;
	}

	// vidu 交互：视频卡片 hover 自动静音播放，移出即停并回封面。
	// 仅在支持 hover 的指针设备上启用，触屏保持封面 + 播放角标。
	// reduced-motion 只关闭 CSS 缩放/渐变；用户主动悬浮仍应启动静音预览。
	const playPreview = (id: string) => {
		void playMutedPreview(previewVideos[id], hoverCapable);
	};

	const stopPreview = (id: string) => {
		stopVideoPreview(previewVideos[id]);
	};

	const loadPage = async (feed: DiscoveryFeed, first: boolean) => {
		const target = feeds[feed];
		const generation = beginDiscoveryRequest(target);
		feeds = { ...feeds };
		try {
			const page =
				feed === 'favorites'
					? await listFavoritePosts(
							localStorage.token,
							PAGE_SIZE,
							first ? null : target.nextCursor,
							activeCategory ?? undefined,
							activeMediaKind === 'all' ? undefined : activeMediaKind
						)
					: await listDiscoveryPosts(
							localStorage.token,
							feed,
							PAGE_SIZE,
							first ? null : target.nextCursor,
							activeCategory ?? undefined,
							activeMediaKind === 'all' ? undefined : activeMediaKind
						);
			applyDiscoveryPage(target, generation, page, first);
		} catch {
			applyDiscoveryPage(target, generation, null, first);
		} finally {
			feeds = { ...feeds };
		}
	};

	const resetFeeds = () => {
		feeds = {
			featured: createDiscoveryFeedState(),
			latest: createDiscoveryFeedState(),
			popular: createDiscoveryFeedState(),
			favorites: createDiscoveryFeedState()
		};
	};

	const selectCategory = (category: DiscoveryCategory | null) => {
		if (activeCategory === category) return;
		activeCategory = category;
		resetFeeds();
		void loadPage(activeFeed, true);
	};

	const selectMediaKind = (mediaKind: 'image' | 'video') => {
		// 无「全部」按钮：点击已选中的类型即取消，回到全部（vidu 单行子筛选的紧凑形态）。
		const next: 'all' | 'image' | 'video' = activeMediaKind === mediaKind ? 'all' : mediaKind;
		if (activeMediaKind === next) return;
		activeMediaKind = next;
		resetFeeds();
		void loadPage(activeFeed, true);
	};

	const selectFeed = (feed: DiscoveryFeed) => {
		activeFeed = feed;
		if (!feeds[feed].loaded && !feeds[feed].loading) void loadPage(feed, true);
	};

	onMount(() => {
		// 分类元数据与首屏信息流相互独立：并行加载，避免 categories 端点慢/挂起
		// 时阻塞 feed 首屏；categories 失败时回退到内置「Other」分类即可。
		void (async () => {
			const categoryPromise = listDiscoveryCategories(localStorage.token)
				.then((result) => {
					categories = result;
				})
				.catch(() => {
					// feed 仍可用内置回退分类。
				});
			await Promise.all([categoryPromise, loadPage('latest', true)]);
		})();

		const lgQuery = window.matchMedia('(min-width: 1024px)');
		const xlQuery = window.matchMedia('(min-width: 1280px)');
		const smQuery = window.matchMedia('(min-width: 640px)');
		const updateColumnCount = () => {
			masonryColumnCount = xlQuery.matches ? 5 : lgQuery.matches ? 4 : smQuery.matches ? 3 : 2;
		};
		updateColumnCount();
		lgQuery.addEventListener('change', updateColumnCount);
		xlQuery.addEventListener('change', updateColumnCount);
		smQuery.addEventListener('change', updateColumnCount);

		hoverCapable = window.matchMedia('(hover: hover)').matches;
		// 列宽随侧边栏开合/窗口缩放变化，用 ResizeObserver 跟踪以重算均衡布局。
		const resizeObserver = new ResizeObserver((entries) => {
			masonryWidth = entries[0]?.contentRect.width ?? 0;
		});
		if (contentElement) resizeObserver.observe(contentElement);
		return () => {
			lgQuery.removeEventListener('change', updateColumnCount);
			xlQuery.removeEventListener('change', updateColumnCount);
			smQuery.removeEventListener('change', updateColumnCount);
			resizeObserver.disconnect();
		};
	});

	const openDetails = (item: DiscoveryPostSummary) => {
		detailsPostId = item.id;
		detailsShow = true;
	};

	const reuseCreation = async (draft: ImageCreationDraft) => {
		try {
			storePendingCreationDraft(sessionStorage, draft);
			await goto('/images');
		} catch {
			toast.error($i18n.t('Failed to load creation settings'));
		}
	};

	// 卡片悬浮「做同款」（vidu 签名交互）：拉取详情后走与详情弹窗一致的复用链路。
	const reuseFromCard = async (item: DiscoveryPostSummary) => {
		if (pendingReuse.has(item.id)) return;
		pendingReuse.add(item.id);
		pendingReuse = new Set(pendingReuse);
		try {
			const detail = await getDiscoveryPost(localStorage.token, item.id);
			if (detail.kind === 'video') {
				localStorage.setItem(
					'video-creation-draft',
					JSON.stringify({
						task: detail.task,
						prompt: detail.prompt ?? '',
						model: detail.model_id,
						params: detail.params
					})
				);
				await goto('/videos');
				return;
			}
			await reuseCreation(
				buildCreationDraft({
					prompt: detail.prompt ?? '',
					model_id: detail.model_id,
					params: detail.params,
					content_url: detail.content_url,
					useAsReference: false
				})
			);
		} catch {
			toast.error($i18n.t('Failed to load creation settings'));
		} finally {
			pendingReuse.delete(item.id);
			pendingReuse = new Set(pendingReuse);
		}
	};

	const updateEveryCopy = (reaction: ReactionState) => {
		for (const feed of Object.values(feeds)) {
			const item = feed.items.find((candidate) => candidate.id === reaction.post_id);
			if (item) applyReactionState(item, reaction);
		}
		if (reaction.kind === 'favorite' && !reaction.active) {
			feeds.favorites.items = feeds.favorites.items.filter((item) => item.id !== reaction.post_id);
		}
		feeds = { ...feeds };
	};

	const toggleReaction = async (item: DiscoveryPostSummary, kind: ReactionKind) => {
		const key = `${item.id}:${kind}`;
		if (pendingReactions.has(key)) return;
		pendingReactions.add(key);
		pendingReactions = new Set(pendingReactions);
		const active = kind === 'like' ? !item.liked : !item.favorited;
		try {
			updateEveryCopy(await setDiscoveryReaction(localStorage.token, item.id, kind, active));
		} catch {
			toast.error($i18n.t('Interaction failed'));
		} finally {
			pendingReactions.delete(key);
			pendingReactions = new Set(pendingReactions);
		}
	};
</script>

<svelte:head>
	<title>{$i18n.t('Discover')} • {$WEBUI_NAME}</title>
</svelte:head>

<div
	class="relative flex h-screen max-h-[100dvh] w-full max-w-full min-w-0 flex-col transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''}"
>
	<MobileSidebarHeader />

	<MediaGallerySurface>
		<MediaGalleryHeader
			title={$i18n.t('Discover')}
			items={feedNavigationItems}
			selected={activeFeed}
			ariaLabel={$i18n.t('Discovery feed')}
			idPrefix="discovery-feed-tab"
			onSelect={(value) => selectFeed(value as DiscoveryFeed)}
		>
			<div
				class="flex min-h-11 items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none sm:min-h-9"
				aria-label={$i18n.t('Filters')}
			>
				{#each [['image', 'Images'], ['video', 'Videos']] as option}
					<button
						type="button"
						class="min-h-11 shrink-0 whitespace-nowrap rounded-[10px] px-3.5 text-sm transition duration-200 active:scale-[0.98] sm:min-h-9 {activeMediaKind ===
						option[0]
							? FILTER_ACTIVE
							: FILTER_IDLE}"
						aria-pressed={activeMediaKind === option[0]}
						on:click={() => selectMediaKind(option[0] as 'image' | 'video')}
					>
						{$i18n.t(option[1])}
					</button>
				{/each}
				<span class="mx-1 h-4 w-px shrink-0 bg-slate-300/70 dark:bg-white/10" aria-hidden="true"
				></span>
				<button
					type="button"
					class="min-h-11 shrink-0 whitespace-nowrap rounded-[10px] px-3.5 text-sm transition duration-200 active:scale-[0.98] sm:min-h-9 {activeCategory ===
					null
						? FILTER_ACTIVE
						: FILTER_IDLE}"
					aria-pressed={activeCategory === null}
					on:click={() => selectCategory(null)}
				>
					{$i18n.t('All')}
				</button>
				{#each categories as category (category.id)}
					<button
						type="button"
						class="min-h-11 shrink-0 whitespace-nowrap rounded-[10px] px-3.5 text-sm transition duration-200 active:scale-[0.98] sm:min-h-9 {activeCategory ===
						category.id
							? FILTER_ACTIVE
							: FILTER_IDLE}"
						aria-pressed={activeCategory === category.id}
						on:click={() => selectCategory(category.id)}
					>
						{$i18n.t(category.display_name)}
					</button>
				{/each}
			</div>
		</MediaGalleryHeader>

		<div
			bind:this={contentElement}
			class="mx-auto w-full max-w-[96rem] px-4 pb-12 pt-5 sm:px-6 lg:px-8"
		>
			<div role="tabpanel" aria-label={$i18n.t('Discovery feed')} aria-live="polite">
				{#if state.loading && !state.loaded}
					<!-- 首次加载骨架屏：animate-pulse shimmer，避免长时间空 Spinners 带来"卡住"观感。 -->
					<div
						class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
						aria-hidden="true"
					>
						{#each SKELETON_IDS as index (index)}
							<div
								class="aspect-[3/4] overflow-hidden rounded-[14px] bg-gray-200/70 dark:bg-white/[0.06]"
							>
								<div
									class="h-full w-full animate-pulse bg-gradient-to-br from-transparent via-black/[0.03] to-transparent dark:via-white/[0.03]"
								></div>
							</div>
						{/each}
					</div>
				{:else if state.error && state.items.length === 0}
					<div class="flex min-h-64 flex-col items-center justify-center gap-3 text-center">
						<p class="text-sm text-red-500 dark:text-red-400">
							{$i18n.t('Failed to load discovery feed')}
						</p>
						<button
							type="button"
							class="min-h-11 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white transition hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
							on:click={() => loadPage(activeFeed, true)}>{$i18n.t('Retry')}</button
						>
					</div>
				{:else if state.items.length === 0}
					<div
						class="flex min-h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-200 bg-gray-50 text-center dark:border-white/10 dark:bg-white/[0.02]"
					>
						<Photo className="size-8 text-gray-400 dark:text-white/40" strokeWidth="1.5" />
						<p class="text-sm text-gray-500 dark:text-white/60">
							{activeFeed === 'favorites'
								? $i18n.t('Your favorite creations will appear here.')
								: $i18n.t('No creations have been shared yet.')}
						</p>
					</div>
				{:else}
					<div class="flex items-start gap-3">
						{#each masonryColumns as column, columnIndex (columnIndex)}
							<div class="flex min-w-0 flex-1 flex-col gap-3">
								{#each column as item, itemIndex (item.id)}
									<!-- vidu 式纯图卡：无框、无边线装饰，图片即卡片，卡片高度只有图片本身。
									     标题/分类/精选信息收进详情弹窗；作者与计数、做同款全部浮在图片上。 -->
									<article
										class="gallery-reveal group min-w-0"
										style={`--gallery-index: ${Math.min(columnIndex + itemIndex * masonryColumnCount, 12)}`}
										on:mouseenter={() => playPreview(item.id)}
										on:mouseleave={() => stopPreview(item.id)}
									>
										<div
											class="relative overflow-hidden rounded-[14px] bg-slate-200/70 ring-1 ring-slate-900/[0.045] transition-[transform,box-shadow] duration-300 ease-out group-hover:-translate-y-0.5 group-hover:shadow-[0_18px_38px_-22px_rgba(66,79,111,0.42)] dark:bg-white/[0.055] dark:ring-white/[0.075] dark:group-hover:shadow-[0_20px_40px_-24px_rgba(1,4,12,0.92)]"
										>
											<button
												type="button"
												class="block w-full text-left focus-visible:outline-2 focus-visible:outline-offset-2"
												on:click={() => openDetails(item)}
												aria-label={item.title ?? $i18n.t('View creation')}
											>
												{#if item.content_url}
													<div class="relative" style={cardAspectRatioStyle(item)}>
														<img
															src={item.kind === 'video'
																? (item.poster_url ?? item.content_url)
																: item.content_url}
															alt={item.title ?? item.prompt_preview ?? $i18n.t('Artwork')}
															loading="lazy"
															decoding="async"
															class="h-full w-full object-cover transition duration-500 ease-out group-hover:scale-[1.025] motion-reduce:transition-none"
														/>
														{#if item.kind === 'video'}
															<!-- vidu 交互：hover 时静音自动播放，移出即停并回封面。 -->
															<video
																bind:this={previewVideos[item.id]}
																src={item.content_url}
																muted
																playsinline
																preload="metadata"
																aria-hidden="true"
																class="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-0 transition duration-300 group-hover:opacity-100"
															></video>
															<span
																class="absolute inset-0 flex items-center justify-center bg-black/10 transition group-hover:opacity-0"
																><span
																	class="flex size-10 items-center justify-center rounded-full bg-black/65 text-white shadow"
																	><Play className="size-4" strokeWidth="2" /></span
																></span
															>
															{#if item.duration_seconds}<span
																	class="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 text-[10px] text-white"
																	>{item.duration_seconds}s</span
																>{/if}
														{/if}
													</div>
												{:else}
													<div
														class="flex min-h-36 items-center justify-center p-4 text-xs text-gray-400 dark:text-white/40"
													>
														{$i18n.t('Source file unavailable')}
													</div>
												{/if}
											</button>

											<!-- vidu 交互：作者与计数浮在图片底部（渐变遮罩），默认隐藏、
											     hover 卡片浮现——绝对定位不占卡片高度，纯图墙更紧凑。
											     触屏无 hover 即隐藏（用户拍板），点赞/收藏走详情弹窗。 -->
											<button
												type="button"
												class="pointer-events-none absolute right-2 top-2 z-10 min-h-9 -translate-y-1 rounded-lg bg-black/55 px-3 text-xs font-medium text-white opacity-0 backdrop-blur-md transition duration-200 hover:bg-black/70 focus-visible:outline-2 focus-visible:outline-offset-2 group-focus-within:pointer-events-auto group-focus-within:translate-y-0 group-focus-within:opacity-100 group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100 motion-reduce:transition-none disabled:opacity-50"
												disabled={pendingReuse.has(item.id)}
												on:click={() => reuseFromCard(item)}
											>
												{$i18n.t('Make similar')}
											</button>

											<div
												class="pointer-events-none absolute inset-x-0 bottom-0 z-10 flex items-center justify-between gap-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-2 pb-1.5 pt-7 opacity-0 transition group-focus-within:opacity-100 group-hover:opacity-100 motion-reduce:transition-none"
											>
												<div class="flex min-w-0 items-center gap-1.5">
													{#if item.owner.profile_image_url}
														<img
															src={item.owner.profile_image_url}
															alt=""
															class="size-4 shrink-0 rounded-full object-cover"
														/>
													{/if}
													<span class="truncate text-sm text-white/80">
														{item.owner.deleted
															? $i18n.t('Deleted user')
															: (item.owner.name ?? $i18n.t('Creator'))}
													</span>
												</div>

												<div class="flex shrink-0 items-center gap-0.5">
													<button
														type="button"
														class="pointer-events-none inline-flex min-h-9 min-w-9 items-center justify-center gap-1 rounded-full px-1 text-sm transition group-focus-within:pointer-events-auto group-hover:pointer-events-auto motion-reduce:transition-none active:scale-90 {item.liked
															? 'text-rose-300'
															: 'text-white/70 hover:bg-white/10 hover:text-white'}"
														disabled={pendingReactions.has(`${item.id}:like`)}
														on:click={() => toggleReaction(item, 'like')}
														aria-label={$i18n.t('Like')}
														aria-pressed={item.liked}
													>
														<Heart className="size-3.5" strokeWidth="2" />
														{item.like_count}
													</button>
													<button
														type="button"
														class="pointer-events-none inline-flex min-h-9 min-w-9 items-center justify-center gap-1 rounded-full px-1 text-sm transition group-focus-within:pointer-events-auto group-hover:pointer-events-auto motion-reduce:transition-none active:scale-90 {item.favorited
															? 'text-amber-200'
															: 'text-white/70 hover:bg-white/10 hover:text-white'}"
														disabled={pendingReactions.has(`${item.id}:favorite`)}
														on:click={() => toggleReaction(item, 'favorite')}
														aria-label={$i18n.t('Favorite')}
														aria-pressed={item.favorited}
													>
														<Bookmark className="size-3.5" strokeWidth="2" />
														{item.favorite_count}
													</button>
												</div>
											</div>
										</div>
									</article>
								{/each}
							</div>
						{/each}
					</div>

					{#if state.nextCursor}
						<div class="flex justify-center py-8">
							{#if state.loading}
								<Spinner className="size-5 text-gray-900 dark:text-white" />
							{:else}
								<Loader on:visible={() => loadPage(activeFeed, false)} />
							{/if}
						</div>
					{/if}
					{#if !state.nextCursor && !state.loading && state.loaded}
						<p class="py-8 text-center text-xs text-gray-400 dark:text-white/40">
							{$i18n.t('All creations loaded.')}
						</p>
					{/if}
				{/if}
			</div>
		</div>
	</MediaGallerySurface>
</div>

<DiscoveryDetailsModal
	bind:show={detailsShow}
	postId={detailsPostId}
	onReaction={updateEveryCopy}
	onReuse={reuseCreation}
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
