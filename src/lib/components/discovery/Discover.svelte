<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { listDiscoveryPosts, listFavoritePosts, setDiscoveryReaction } from '$lib/apis/discovery';
	import { mobile, showSidebar, WEBUI_NAME } from '$lib/stores';
	import {
		applyDiscoveryPage,
		applyReactionState,
		beginDiscoveryRequest,
		createDiscoveryFeedState,
		type DiscoveryFeed,
		type DiscoveryPostSummary,
		type ReactionKind,
		type ReactionState
	} from '$lib/utils/discovery';

	import Bookmark from '$lib/components/icons/Bookmark.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import DiscoveryDetailsModal from './DiscoveryDetailsModal.svelte';

	const i18n: any = getContext('i18n');
	const PAGE_SIZE = 24;

	let activeFeed: DiscoveryFeed = 'latest';
	let feeds = {
		latest: createDiscoveryFeedState(),
		popular: createDiscoveryFeedState(),
		favorites: createDiscoveryFeedState()
	};
	let detailsShow = false;
	let detailsPostId: string | null = null;
	let pendingReactions = new Set<string>();

	$: state = feeds[activeFeed];

	const loadPage = async (feed: DiscoveryFeed, first: boolean) => {
		const target = feeds[feed];
		const generation = beginDiscoveryRequest(target);
		feeds = { ...feeds };
		try {
			const page =
				feed === 'favorites'
					? await listFavoritePosts(localStorage.token, PAGE_SIZE, first ? null : target.nextCursor)
					: await listDiscoveryPosts(
							localStorage.token,
							feed,
							PAGE_SIZE,
							first ? null : target.nextCursor
						);
			applyDiscoveryPage(target, generation, page, first);
		} catch {
			applyDiscoveryPage(target, generation, null, first);
		} finally {
			feeds = { ...feeds };
		}
	};

	const selectFeed = (feed: DiscoveryFeed) => {
		activeFeed = feed;
		if (!feeds[feed].loaded && !feeds[feed].loading) void loadPage(feed, true);
	};

	onMount(() => void loadPage('latest', true));

	const openDetails = (item: DiscoveryPostSummary) => {
		detailsPostId = item.id;
		detailsShow = true;
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
						class="flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-lg transition hover:bg-gray-100 dark:hover:bg-gray-850"
						on:click={() => showSidebar.set(!$showSidebar)}
						aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
					>
						<div class="self-center">
							<SidebarIcon />
						</div>
					</button>
				</Tooltip>
			</div>
		</nav>
	{/if}

	<div class="min-h-0 min-w-0 flex-1 overflow-y-auto bg-stone-50/60 dark:bg-gray-950">
		<div class="mx-auto w-full max-w-[96rem] px-3 pb-10 pt-4 sm:px-5 sm:pt-8 lg:px-8">
			<header class="mb-5 flex flex-col gap-4 sm:mb-7 sm:flex-row sm:items-end sm:justify-between">
				<div>
					<p class="mb-1 text-xs font-medium uppercase tracking-[0.22em] text-gray-400">
						{$i18n.t('Community creations')}
					</p>
					<h1
						class="text-3xl font-semibold tracking-tight text-gray-950 dark:text-white sm:text-4xl"
					>
						{$i18n.t('Discover')}
					</h1>
					<p class="mt-2 max-w-xl text-sm leading-6 text-gray-500 dark:text-gray-400">
						{$i18n.t('Find inspiration in images shared by the community.')}
					</p>
				</div>

				<div
					class="grid min-h-11 grid-cols-3 rounded-full border border-gray-200/80 bg-white/80 p-1 shadow-sm backdrop-blur dark:border-gray-800 dark:bg-gray-900/80"
					role="tablist"
					aria-label={$i18n.t('Discovery feed')}
				>
					{#each [['latest', $i18n.t('Latest')], ['popular', $i18n.t('Popular')], ['favorites', $i18n.t('My favorites')]] as tab}
						<button
							type="button"
							class="min-h-9 rounded-full px-3 text-xs font-medium transition sm:px-4 {activeFeed ===
							tab[0]
								? 'bg-gray-950 text-white shadow-sm dark:bg-white dark:text-gray-950'
								: 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'}"
							on:click={() => selectFeed(tab[0] as DiscoveryFeed)}
							role="tab"
							aria-selected={activeFeed === tab[0]}
						>
							{tab[1]}
						</button>
					{/each}
				</div>
			</header>

			<div role="tabpanel" aria-label={$i18n.t('Discovery feed')}>
				{#if state.loading && !state.loaded}
					<div class="flex min-h-64 items-center justify-center">
						<Spinner className="size-6" />
					</div>
				{:else if state.error && state.items.length === 0}
					<div class="flex min-h-64 flex-col items-center justify-center gap-3 text-center">
						<p class="text-sm text-red-500">{$i18n.t('Failed to load discovery feed')}</p>
						<button
							type="button"
							class="min-h-11 rounded-xl bg-gray-950 px-4 text-sm font-medium text-white dark:bg-white dark:text-gray-950"
							on:click={() => loadPage(activeFeed, true)}>{$i18n.t('Retry')}</button
						>
					</div>
				{:else if state.items.length === 0}
					<div
						class="flex min-h-64 flex-col items-center justify-center gap-3 rounded-3xl border border-dashed border-gray-200 bg-white/50 text-center dark:border-gray-800 dark:bg-gray-900/30"
					>
						<Photo className="size-8 text-gray-400" strokeWidth="1.5" />
						<p class="text-sm text-gray-600 dark:text-gray-300">
							{activeFeed === 'favorites'
								? $i18n.t('Your favorite creations will appear here.')
								: $i18n.t('No creations have been shared yet.')}
						</p>
					</div>
				{:else}
					<div class="columns-2 gap-2 sm:columns-3 sm:gap-3 lg:columns-4 xl:columns-5">
						{#each state.items as item (item.id)}
							<article
								class="group mb-2 break-inside-avoid overflow-hidden rounded-2xl border border-gray-200/70 bg-white shadow-[0_1px_0_rgba(0,0,0,0.02)] transition duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/5 sm:mb-3 dark:border-gray-800 dark:bg-gray-900 dark:hover:shadow-black/25"
							>
								<button
									type="button"
									class="block w-full overflow-hidden bg-stone-100 text-left focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-gray-800"
									on:click={() => openDetails(item)}
									aria-label={item.title ?? $i18n.t('View creation')}
								>
									{#if item.content_url}
										<img
											src={item.content_url}
											alt={item.title ?? item.prompt_preview ?? $i18n.t('Artwork')}
											loading="lazy"
											decoding="async"
											class="h-auto w-full transition duration-500 group-hover:scale-[1.015]"
										/>
									{:else}
										<div
											class="flex min-h-36 items-center justify-center p-4 text-xs text-gray-400"
										>
											{$i18n.t('Source file unavailable')}
										</div>
									{/if}
								</button>

								<div class="p-2.5 sm:p-3">
									{#if item.title}
										<h2 class="line-clamp-2 text-sm font-medium text-gray-900 dark:text-gray-100">
											{item.title}
										</h2>
									{/if}
									<div class="mt-1.5 flex min-w-0 items-center justify-between gap-2">
										<div class="flex min-w-0 items-center gap-1.5">
											{#if item.owner.profile_image_url}
												<img
													src={item.owner.profile_image_url}
													alt=""
													class="size-5 shrink-0 rounded-full object-cover"
												/>
											{/if}
											<span class="truncate text-xs text-gray-500 dark:text-gray-400">
												{item.owner.deleted
													? $i18n.t('Deleted user')
													: (item.owner.name ?? $i18n.t('Creator'))}
											</span>
										</div>

										<div class="flex shrink-0 items-center gap-0.5">
											<button
												type="button"
												class="inline-flex min-h-9 min-w-9 items-center justify-center gap-1 rounded-full px-1.5 text-xs transition {item.liked
													? 'text-rose-600 dark:text-rose-300'
													: 'text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200'}"
												disabled={pendingReactions.has(`${item.id}:like`)}
												on:click={() => toggleReaction(item, 'like')}
												aria-label={$i18n.t('Like')}
												aria-pressed={item.liked}
											>
												<Heart className="size-4" strokeWidth="2" />
												{item.like_count}
											</button>
											<button
												type="button"
												class="inline-flex min-h-9 min-w-9 items-center justify-center gap-1 rounded-full px-1.5 text-xs transition {item.favorited
													? 'text-amber-700 dark:text-amber-300'
													: 'text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200'}"
												disabled={pendingReactions.has(`${item.id}:favorite`)}
												on:click={() => toggleReaction(item, 'favorite')}
												aria-label={$i18n.t('Favorite')}
												aria-pressed={item.favorited}
											>
												<Bookmark className="size-4" strokeWidth="2" />
												{item.favorite_count}
											</button>
										</div>
									</div>
								</div>
							</article>
						{/each}
					</div>

					{#if state.nextCursor}
						<div class="flex justify-center py-8">
							{#if state.loading}
								<Spinner className="size-5" />
							{:else}
								<Loader on:visible={() => loadPage(activeFeed, false)} />
							{/if}
						</div>
					{/if}
				{/if}
			</div>
		</div>
	</div>
</div>

<DiscoveryDetailsModal
	bind:show={detailsShow}
	postId={detailsPostId}
	onReaction={updateEveryCopy}
/>
