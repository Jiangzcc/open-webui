<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		listAdminDiscoveryCategories,
		listDiscoveryPosts,
		updateDiscoveryOperation
	} from '$lib/apis/discovery';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import type {
		DiscoveryCategory,
		DiscoveryCategoryItem,
		DiscoveryPostSummary
	} from '$lib/utils/discovery';

	const i18n = getContext('i18n');
	let categories: DiscoveryCategoryItem[] = [
		{ id: 'other', display_name: $i18n.t('Other'), enabled: true, sort_order: 999 }
	];
	let items: DiscoveryPostSummary[] = [];
	let loading = true;
	let nextCursor: string | null = null;
	let page = 1;
	let pageSize = 20;
	let pageCursors: Array<string | null> = [null];
	let search = '';
	let editing: DiscoveryPostSummary | null = null;
	let saving = false;
	let showPreview = false;
	let previewUrl = '';
	let previewAlt = '';

	$: visibleItems = items.filter((item) =>
		`${item.title ?? ''} ${item.prompt_preview ?? ''} ${item.owner.name ?? ''}`
			.toLowerCase()
			.includes(search.trim().toLowerCase())
	);

	const categoryLabel = (category: DiscoveryCategory) =>
		$i18n.t(categories.find((item) => item.id === category)?.display_name ?? 'Other');

	const loadCategories = async () => {
		try {
			categories = await listAdminDiscoveryCategories(localStorage.token);
		} catch {
			toast.error($i18n.t('Failed to load image categories'));
		}
	};

	const load = async (cursor: string | null = null) => {
		loading = true;
		try {
			const result = await listDiscoveryPosts(localStorage.token, 'latest', pageSize, cursor);
			items = result.items;
			nextCursor = result.next_cursor;
		} catch {
			toast.error($i18n.t('Failed to load discovery feed'));
		} finally {
			loading = false;
		}
	};

	const nextPage = async () => {
		if (!nextCursor || loading) return;
		pageCursors = [...pageCursors.slice(0, page), nextCursor];
		page += 1;
		await load(nextCursor);
	};

	const previousPage = async () => {
		if (page <= 1 || loading) return;
		page -= 1;
		await load(pageCursors[page - 1] ?? null);
	};

	const resetPagination = async () => {
		page = 1;
		pageCursors = [null];
		await load(null);
	};

	const openEditor = (item: DiscoveryPostSummary) => {
		editing = { ...item, owner: { ...item.owner } };
	};

	const openPreview = (item: DiscoveryPostSummary) => {
		if (!item.content_url) return;
		previewUrl = item.content_url;
		previewAlt = item.title ?? item.prompt_preview ?? $i18n.t('Artwork');
		showPreview = true;
	};

	const save = async () => {
		if (!editing || saving) return;
		saving = true;
		try {
			const result = await updateDiscoveryOperation(localStorage.token, editing.id, {
				category: editing.category,
				featured: editing.featured,
				featured_rank: editing.featured_rank
			});
			items = items.map((item) =>
				item.id === editing?.id
					? {
							...item,
							category: result.category,
							featured: result.featured,
							featured_rank: result.featured_rank
						}
					: item
			);
			editing = null;
			toast.success($i18n.t('Discovery settings saved'));
		} catch {
			toast.error($i18n.t('Failed to save discovery settings'));
		} finally {
			saving = false;
		}
	};

	onMount(() => {
		void loadCategories();
		void load();
	});
</script>

<svelte:window on:keydown={(event) => event.key === 'Escape' && !saving && (editing = null)} />

<div class="flex h-full min-h-0 flex-col gap-4">
	<header class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-end">
		<div class="grid gap-2 sm:grid-cols-[minmax(14rem,1fr)_7rem] lg:w-[28rem]">
			<input
				class="min-h-10 w-full rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
				bind:value={search}
				placeholder={$i18n.t('Search creations')}
			/>
			<select
				class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
				bind:value={pageSize}
				on:change={resetPagination}
				aria-label={$i18n.t('Items per page')}
			>
				<option value={20}>20 / {$i18n.t('page')}</option>
				<option value={50}>50 / {$i18n.t('page')}</option>
				<option value={100}>100 / {$i18n.t('page')}</option>
			</select>
		</div>
	</header>

	{#if loading}
		<div class="flex min-h-64 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if visibleItems.length === 0}
		<div
			class="flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800"
		>
			{$i18n.t('No published creations found')}
		</div>
	{:else}
		<div class="min-h-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
			<div
				class="hidden grid-cols-[minmax(16rem,1fr)_8rem_9rem_5rem] gap-3 border-b border-gray-200 bg-gray-50/70 px-4 py-2 text-xs font-medium text-gray-500 dark:border-gray-800 dark:bg-gray-900/40 md:grid"
			>
				<div>{$i18n.t('Creation')}</div>
				<div>{$i18n.t('Category')}</div>
				<div>{$i18n.t('Curation')}</div>
				<div class="text-right">{$i18n.t('Action')}</div>
			</div>
			<div class="max-h-[min(62vh,44rem)] overflow-y-auto overscroll-contain">
				{#each visibleItems as item (item.id)}
					<article
						class="grid grid-cols-[5rem_minmax(0,1fr)_auto] items-center gap-3 border-b border-gray-100 px-3 py-2 last:border-b-0 dark:border-gray-800/70 md:grid-cols-[6rem_minmax(12rem,1fr)_8rem_9rem_5rem] md:px-4"
					>
						{#if item.content_url}
							<button
								class="h-16 w-20 overflow-hidden rounded-lg bg-gray-100 ring-offset-2 transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 dark:bg-gray-800 md:w-24"
								type="button"
								on:click={() => openPreview(item)}
								aria-label={$i18n.t('Preview artwork')}
							>
								<img
									class="h-full w-full object-cover"
									src={item.content_url}
									alt={item.title ?? $i18n.t('Artwork')}
								/>
							</button>
						{:else}
							<div class="h-16 w-20 rounded-lg bg-gray-100 dark:bg-gray-800 md:w-24"></div>
						{/if}
						<div class="min-w-0">
							<div class="truncate text-sm font-medium dark:text-gray-100">
								{item.title ?? item.prompt_preview ?? $i18n.t('Untitled')}
							</div>
							<div class="mt-0.5 truncate text-xs text-gray-500">
								{item.owner.name ?? item.owner.user_id}
							</div>
							<div class="mt-1 flex flex-wrap gap-1 text-[11px] md:hidden">
								<span
									class="rounded-md bg-gray-100 px-1.5 py-0.5 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
									>{categoryLabel(item.category)}</span
								>
								{#if item.featured}<span
										class="rounded-md bg-amber-50 px-1.5 py-0.5 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
										>{$i18n.t('Featured')} · {item.featured_rank}</span
									>{/if}
							</div>
						</div>
						<div class="hidden text-xs text-gray-500 md:block">{categoryLabel(item.category)}</div>
						<div class="hidden items-center gap-1 text-xs md:flex">
							{#if item.featured}<span
									class="rounded-md bg-amber-50 px-1.5 py-0.5 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
									>{$i18n.t('Featured')}</span
								><span class="text-gray-500"># {item.featured_rank}</span>{:else}<span
									class="text-gray-400">{$i18n.t('Not featured')}</span
								>{/if}
						</div>
						<button
							class="min-h-9 rounded-lg border border-gray-200 px-3 text-xs font-medium transition hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800 md:justify-self-end"
							type="button"
							on:click={() => openEditor(item)}>{$i18n.t('Edit')}</button
						>
					</article>
				{/each}
			</div>
		</div>
	{/if}

	{#if !loading && (items.length > 0 || page > 1)}
		<nav class="flex items-center justify-between gap-3 pb-4" aria-label={$i18n.t('Pagination')}>
			<button
				class="min-h-10 rounded-xl border border-gray-200 px-4 text-sm disabled:opacity-40 dark:border-gray-700"
				type="button"
				disabled={page <= 1 || loading}
				on:click={previousPage}>{$i18n.t('Previous')}</button
			>
			<span class="text-sm tabular-nums text-gray-500">{$i18n.t('Page {{page}}', { page })}</span>
			<button
				class="min-h-10 rounded-xl border border-gray-200 px-4 text-sm disabled:opacity-40 dark:border-gray-700"
				type="button"
				disabled={!nextCursor || loading}
				on:click={nextPage}>{$i18n.t('Next')}</button
			>
		</nav>
	{/if}
</div>

{#if editing}
	<div
		class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 backdrop-blur-[2px] sm:items-center sm:p-4"
		role="presentation"
		on:click={(event) => event.currentTarget === event.target && !saving && (editing = null)}
	>
		<section
			class="max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl dark:bg-gray-900 sm:max-w-lg sm:rounded-3xl sm:p-6"
			role="dialog"
			aria-modal="true"
			aria-labelledby="discovery-operation-title"
		>
			<div class="flex items-start justify-between gap-4">
				<div class="flex min-w-0 items-center gap-3">
					<div class="size-14 shrink-0 overflow-hidden rounded-xl bg-gray-100 dark:bg-gray-800">
						{#if editing.content_url}<img
								class="h-full w-full object-cover"
								src={editing.content_url}
								alt=""
							/>{/if}
					</div>
					<div class="min-w-0">
						<h2
							id="discovery-operation-title"
							class="truncate text-lg font-medium dark:text-gray-100"
						>
							{editing.title ?? editing.prompt_preview ?? $i18n.t('Untitled')}
						</h2>
						<p class="mt-1 truncate text-xs text-gray-500">
							{editing.owner.name ?? editing.owner.user_id}
						</p>
					</div>
				</div>
				<button
					class="min-h-10 rounded-xl px-3 text-sm text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
					type="button"
					disabled={saving}
					on:click={() => (editing = null)}
					aria-label={$i18n.t('Close')}>✕</button
				>
			</div>

			<div class="mt-5 grid gap-4">
				<label class="grid gap-1.5 text-sm"
					><span class="font-medium">{$i18n.t('Category')}</span><select
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						bind:value={editing.category}
						>{#each categories as category}<option value={category.id}
								>{$i18n.t(category.display_name)}{category.enabled
									? ''
									: ` · ${$i18n.t('Disabled')}`}</option
							>{/each}</select
					></label
				>
				<label
					class="flex min-h-12 items-center gap-3 rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700"
					><input type="checkbox" bind:checked={editing.featured} /><span
						><span class="block font-medium">{$i18n.t('Featured')}</span><span
							class="text-xs text-gray-500">{$i18n.t('Show in the featured feed')}</span
						></span
					></label
				>
				<label class="grid gap-1.5 text-sm"
					><span class="font-medium">{$i18n.t('Featured rank')}</span><span
						class="text-xs text-gray-500"
						>{$i18n.t('Smaller numbers appear first in the featured feed.')}</span
					><input
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						type="number"
						min="0"
						max="10000"
						bind:value={editing.featured_rank}
					/></label
				>
			</div>

			<div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
				<button
					class="min-h-11 rounded-xl border border-gray-200 px-5 text-sm dark:border-gray-700"
					type="button"
					disabled={saving}
					on:click={() => (editing = null)}>{$i18n.t('Cancel')}</button
				>
				<button
					class="min-h-11 rounded-xl bg-gray-900 px-5 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-gray-900"
					type="button"
					disabled={saving}
					on:click={save}>{saving ? $i18n.t('Saving') : $i18n.t('Save')}</button
				>
			</div>
		</section>
	</div>
{/if}

<ImagePreview bind:show={showPreview} src={previewUrl} alt={previewAlt} />
