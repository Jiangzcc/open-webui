<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { getDiscoveryPost, setDiscoveryReaction } from '$lib/apis/discovery';
	import { copyToClipboard } from '$lib/utils';
	import { extractParamTags, type ParamTag } from '$lib/utils/creations-library';
	import { buildCreationDraft, type ImageCreationDraft } from '$lib/utils/image-generation-batches';
	import type { DiscoveryPostDetail, ReactionKind, ReactionState } from '$lib/utils/discovery';

	import Bookmark from '$lib/components/icons/Bookmark.svelte';
	import Clipboard from '$lib/components/icons/Clipboard.svelte';
	import Heart from '$lib/components/icons/Heart.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import ArtworkViewerShell from '$lib/components/images/ArtworkViewerShell.svelte';

	export let show = false;
	export let postId: string | null = null;
	export let onReaction: (reaction: ReactionState) => void = () => {};
	export let onReuse: (draft: ImageCreationDraft) => void = () => {};

	const i18n: any = getContext('i18n');

	let detail: DiscoveryPostDetail | null = null;
	let loading = false;
	let requestGeneration = 0;
	let reactionPending: ReactionKind | null = null;
	let previousPostId: string | null = null;
	let copyingPrompt = false;

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

	const reuseCreation = (useAsReference: boolean) => {
		if (!detail || (useAsReference && !detail.content_url)) return;
		onReuse(
			buildCreationDraft({
				prompt: detail.prompt ?? '',
				model_id: detail.model_id,
				params: detail.params,
				content_url: detail.content_url,
				useAsReference
			})
		);
		show = false;
	};

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
	const paramLabel = (key: ParamTag['key']) => PARAM_LABELS[key] ?? key;
	$: paramTags = detail ? extractParamTags(detail.params) : [];
</script>

<ArtworkViewerShell
	bind:show
	{loading}
	error={null}
	headerTitle={detail
		? detail.owner.deleted
			? $i18n.t('Deleted user')
			: (detail.owner.name ?? $i18n.t('Creator'))
		: ''}
	headerSubtitle={detail?.model_name ?? ''}
	mediaLabel={$i18n.t('Artwork')}
>
	<svelte:fragment slot="media">
		{#if detail}
			{#if detail.content_url}
				<img
					src={detail.content_url}
					alt={detail.title ?? detail.prompt ?? $i18n.t('Artwork')}
					class="max-h-[75dvh] max-w-full rounded-xl object-contain sm:rounded-2xl"
				/>
			{:else}
				<p class="text-sm text-gray-500">{$i18n.t('Source file unavailable')}</p>
			{/if}
		{/if}
	</svelte:fragment>

	<svelte:fragment slot="details">
		{#if detail}
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

			<div class="grid grid-cols-2 gap-2">
				{#if detail.prompt}
					<button
						type="button"
						class="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-gray-950 px-3 text-sm font-medium text-white transition hover:bg-gray-800 focus-visible:outline-2 focus-visible:outline-offset-2 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100 {detail.content_url
							? ''
							: 'col-span-2'}"
						on:click={() => reuseCreation(false)}
					>
						<Sparkles className="size-4" strokeWidth="1.8" />
						{$i18n.t('Create again')}
					</button>
				{/if}
				{#if detail.content_url}
					<button
						type="button"
						class="inline-flex min-h-11 items-center justify-center rounded-xl border border-gray-200 px-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800 {detail.prompt
							? ''
							: 'col-span-2'}"
						on:click={() => reuseCreation(true)}
					>
						{$i18n.t('Use as reference')}
					</button>
				{/if}
			</div>

			{#if detail.prompt}
				<section class="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
					<div class="mb-1 flex items-center justify-between gap-2">
						<h3 class="text-xs font-medium uppercase tracking-wide text-gray-500">
							{$i18n.t('Prompt')}
						</h3>
						<button
							type="button"
							class="inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg text-gray-400 transition hover:bg-gray-200/70 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-50 dark:hover:bg-gray-700 dark:hover:text-gray-200"
							disabled={copyingPrompt}
							on:click={copyPrompt}
							aria-label={$i18n.t('Copy')}
							title={$i18n.t('Copy')}
						>
							<Clipboard className="size-4" strokeWidth="2" />
						</button>
					</div>
					<div class="max-h-48 overflow-y-auto overscroll-contain pr-1">
						<p class="whitespace-pre-wrap break-words text-sm text-gray-800 dark:text-gray-100">
							{detail.prompt}
						</p>
					</div>
				</section>
			{:else}
				<p class="text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('The creator chose not to share the prompt.')}
				</p>
			{/if}

			{#if detail.negative_prompt}
				<p class="whitespace-pre-wrap break-words text-xs text-gray-500 dark:text-gray-400">
					<span class="font-medium">{$i18n.t('Negative Prompt')}: </span>{detail.negative_prompt}
				</p>
			{/if}

			<ul class="flex flex-wrap gap-1.5" aria-label={$i18n.t('Generation parameters')}>
				{#if detail.model_name || detail.model_id}
					<li
						class="inline-flex max-w-full items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
					>
						<span class="mr-1 font-medium text-gray-500 dark:text-gray-400"
							>{$i18n.t('Model')}:</span
						>
						<span class="min-w-0 break-words">{detail.model_name ?? detail.model_id}</span>
					</li>
				{/if}
				<li
					class="inline-flex max-w-full items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
				>
					<span class="mr-1 font-medium text-gray-500 dark:text-gray-400"
						>{$i18n.t('Creation type')}:</span
					>
					<span
						>{detail.task === 'image-to-image'
							? $i18n.t('Image to Image')
							: $i18n.t('Text to Image')}</span
					>
				</li>
				{#each paramTags as tag (tag.key)}
					<li
						class="inline-flex max-w-full items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200"
					>
						<span class="mr-1 font-medium text-gray-500 dark:text-gray-400"
							>{paramLabel(tag.key)}:</span
						>
						<span class="min-w-0 break-words">{tag.value}</span>
					</li>
				{/each}
			</ul>

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
					aria-label={$i18n.t('Like')}
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
					aria-label={$i18n.t('Favorite')}
					aria-pressed={detail.favorited}
				>
					<Bookmark className="size-4" strokeWidth="2" />
					{detail.favorite_count}
				</button>
			</div>
		{/if}
	</svelte:fragment>
</ArtworkViewerShell>
