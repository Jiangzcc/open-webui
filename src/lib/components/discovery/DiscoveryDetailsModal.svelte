<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { getDiscoveryPost, setDiscoveryReaction } from '$lib/apis/discovery';
	import type { DiscoveryPostDetail, ReactionKind, ReactionState } from '$lib/utils/discovery';

	import Bookmark from '$lib/components/icons/Bookmark.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	export let show = false;
	export let postId: string | null = null;
	export let onReaction: (reaction: ReactionState) => void = () => {};

	const i18n: any = getContext('i18n');

	let detail: DiscoveryPostDetail | null = null;
	let loading = false;
	let requestGeneration = 0;
	let reactionPending: ReactionKind | null = null;
	let previousPostId: string | null = null;

	const load = async (id: string) => {
		const generation = ++requestGeneration;
		loading = true;
		detail = null;
		try {
			const fetched = await getDiscoveryPost(localStorage.token, id);
			if (generation === requestGeneration && show && postId === id) detail = fetched;
		} catch {
			if (generation === requestGeneration) toast.error($i18n.t('Failed to load post'));
		} finally {
			if (generation === requestGeneration) loading = false;
		}
	};

	$: if (show && postId && postId !== previousPostId) {
		previousPostId = postId;
		void load(postId);
	}
	$: if (!show && previousPostId) {
		previousPostId = null;
		requestGeneration += 1;
	}

	const toggleReaction = async (kind: ReactionKind) => {
		if (!detail || reactionPending) return;
		reactionPending = kind;
		const active = kind === 'like' ? !detail.liked : !detail.favorited;
		try {
			const reaction = await setDiscoveryReaction(localStorage.token, detail.id, kind, active);
			detail = {
				...detail,
				like_count: reaction.like_count,
				favorite_count: reaction.favorite_count,
				liked: kind === 'like' ? reaction.active : detail.liked,
				favorited: kind === 'favorite' ? reaction.active : detail.favorited
			};
			onReaction(reaction);
		} catch {
			toast.error($i18n.t('Interaction failed'));
		} finally {
			reactionPending = null;
		}
	};
</script>

<Modal
	bind:show
	size="lg"
	containerClassName="p-2 sm:p-4 flex"
	className="overflow-hidden rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl !w-fit max-w-5xl max-h-[96dvh]"
>
	<div class="flex max-h-[96dvh] min-w-0 flex-col">
		<header class="flex shrink-0 items-center justify-between gap-3 px-3 py-2 sm:px-4">
			<div class="min-w-0">
				{#if detail}
					<p class="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
						{detail.owner.deleted
							? $i18n.t('Deleted user')
							: (detail.owner.name ?? $i18n.t('Creator'))}
					</p>
					{#if detail.model_name}
						<p class="truncate text-xs text-gray-500 dark:text-gray-400">{detail.model_name}</p>
					{/if}
				{/if}
			</div>
			<button
				type="button"
				class="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full text-gray-500 hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-offset-2 dark:hover:bg-gray-800"
				on:click={() => (show = false)}
				aria-label={$i18n.t('Close')}
			>
				<XMark className="size-5" strokeWidth="2" />
			</button>
		</header>

		{#if loading}
			<div class="flex min-h-72 items-center justify-center"><Spinner className="size-6" /></div>
		{:else if detail}
			<div class="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
				<div
					class="flex min-h-64 min-w-0 flex-1 items-center justify-center bg-stone-100 p-3 dark:bg-black/35 sm:p-5"
				>
					{#if detail.content_url}
						<img
							src={detail.content_url}
							alt={detail.title ?? detail.prompt ?? $i18n.t('Artwork')}
							class="max-h-[75dvh] max-w-full rounded-xl object-contain sm:rounded-2xl"
						/>
					{:else}
						<p class="text-sm text-gray-500">{$i18n.t('Source file unavailable')}</p>
					{/if}
				</div>

				<aside
					class="flex min-w-0 flex-col gap-4 border-t border-gray-100 p-4 lg:w-80 lg:shrink-0 lg:overflow-y-auto lg:border-l lg:border-t-0 dark:border-gray-800"
				>
					{#if detail.title || detail.description}
						<section>
							{#if detail.title}
								<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
									{detail.title}
								</h2>
							{/if}
							{#if detail.description}
								<p class="mt-1 whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-300">
									{detail.description}
								</p>
							{/if}
						</section>
					{/if}

					{#if detail.prompt}
						<section class="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
							<h3 class="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">
								{$i18n.t('Prompt')}
							</h3>
							<p class="whitespace-pre-wrap break-words text-sm text-gray-800 dark:text-gray-100">
								{detail.prompt}
							</p>
						</section>
					{:else}
						<p class="text-xs text-gray-500 dark:text-gray-400">
							{$i18n.t('The creator chose not to share the prompt.')}
						</p>
					{/if}

					<div
						class="mt-auto grid grid-cols-2 gap-2 border-t border-gray-100 pt-4 dark:border-gray-800"
					>
						<button
							type="button"
							class="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border transition {detail.liked
								? 'border-rose-200 bg-rose-50 text-rose-600 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300'
								: 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800'}"
							disabled={reactionPending !== null}
							on:click={() => toggleReaction('like')}
							aria-pressed={detail.liked}
						>
							<Heart className="size-4" strokeWidth="2" />
							{detail.like_count}
						</button>
						<button
							type="button"
							class="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border transition {detail.favorited
								? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300'
								: 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800'}"
							disabled={reactionPending !== null}
							on:click={() => toggleReaction('favorite')}
							aria-pressed={detail.favorited}
						>
							<Bookmark className="size-4" strokeWidth="2" />
							{detail.favorite_count}
						</button>
					</div>
				</aside>
			</div>
		{/if}
	</div>
</Modal>
