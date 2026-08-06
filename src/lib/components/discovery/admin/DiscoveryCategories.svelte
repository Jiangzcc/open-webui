<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		createAdminDiscoveryCategory,
		deleteAdminDiscoveryCategory,
		listAdminDiscoveryCategories,
		updateAdminDiscoveryCategory
	} from '$lib/apis/discovery';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import type { DiscoveryCategoryItem } from '$lib/utils/discovery';

	const i18n = getContext('i18n');
	let categories: DiscoveryCategoryItem[] = [];
	let loading = true;
	let savingId: string | null = null;
	let deletingId: string | null = null;
	let showCreate = false;
	let creating = false;
	let newCategory = { display_name: '', enabled: true, sort_order: 1000 };

	const sortCategories = (items: DiscoveryCategoryItem[]) =>
		items.sort((a, b) => a.sort_order - b.sort_order || a.id.localeCompare(b.id));

	const load = async () => {
		loading = true;
		try {
			categories = await listAdminDiscoveryCategories(localStorage.token);
		} catch {
			toast.error($i18n.t('Failed to load image categories'));
		} finally {
			loading = false;
		}
	};

	const save = async (category: DiscoveryCategoryItem) => {
		if (savingId || !category.display_name.trim()) return;
		savingId = category.id;
		try {
			const updated = await updateAdminDiscoveryCategory(localStorage.token, category.id, {
				display_name: category.display_name.trim(),
				enabled: category.enabled,
				sort_order: category.sort_order
			});
			categories = sortCategories(
				categories.map((item) => (item.id === updated.id ? updated : item))
			);
			toast.success($i18n.t('Image category saved'));
		} catch {
			toast.error($i18n.t('Failed to save image category'));
		} finally {
			savingId = null;
		}
	};

	const createCategory = async () => {
		if (creating || !newCategory.display_name.trim()) return;
		creating = true;
		try {
			const created = await createAdminDiscoveryCategory(localStorage.token, {
				...newCategory,
				display_name: newCategory.display_name.trim()
			});
			categories = sortCategories([...categories, created]);
			newCategory = { display_name: '', enabled: true, sort_order: 1000 };
			showCreate = false;
			toast.success($i18n.t('Image category created'));
		} catch {
			toast.error($i18n.t('Failed to create image category'));
		} finally {
			creating = false;
		}
	};

	const remove = async (category: DiscoveryCategoryItem) => {
		if (deletingId || category.id === 'other') return;
		if (
			!window.confirm($i18n.t('Delete image category {{name}}?', { name: category.display_name }))
		)
			return;
		deletingId = category.id;
		try {
			await deleteAdminDiscoveryCategory(localStorage.token, category.id);
			categories = categories.filter((item) => item.id !== category.id);
			toast.success($i18n.t('Image category deleted'));
		} catch (error) {
			const detail = (error as { detail?: string } | null)?.detail;
			toast.error(
				detail === 'category is in use'
					? $i18n.t('This category is used by published creations and cannot be deleted.')
					: $i18n.t('Failed to delete image category')
			);
		} finally {
			deletingId = null;
		}
	};

	onMount(load);
</script>

<section class="flex min-h-0 flex-col gap-4">
	<div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
		<p class="max-w-3xl text-sm text-gray-500">
			{$i18n.t('Manage category names, visibility and order. Categories in use cannot be deleted.')}
		</p>
		<button
			class="min-h-10 shrink-0 rounded-lg bg-gray-900 px-4 text-sm font-medium text-white dark:bg-white dark:text-gray-900"
			type="button"
			on:click={() => (showCreate = true)}
		>
			{$i18n.t('Add image category')}
		</button>
	</div>

	{#if loading}
		<div class="flex min-h-48 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if categories.length === 0}
		<div
			class="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800"
		>
			{$i18n.t('No image categories found')}
		</div>
	{:else}
		<div class="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">
			<div
				class="hidden grid-cols-[minmax(10rem,1fr)_10rem_10rem_9rem] gap-4 border-b border-gray-200 bg-gray-50/70 px-4 py-2 text-xs font-medium text-gray-500 dark:border-gray-800 dark:bg-gray-900/40 md:grid"
			>
				<div>{$i18n.t('Category name')}</div>
				<div>{$i18n.t('Identifier')}</div>
				<div>{$i18n.t('Status and order')}</div>
				<div class="text-right">{$i18n.t('Action')}</div>
			</div>

			{#each categories as category (category.id)}
				<div
					class="grid gap-3 border-b border-gray-100 p-3 last:border-b-0 dark:border-gray-800/70 md:grid-cols-[minmax(10rem,1fr)_10rem_10rem_9rem] md:items-center md:px-4"
				>
					<label class="grid gap-1 text-xs text-gray-500">
						<span class="md:hidden">{$i18n.t('Category name')}</span>
						<input
							class="min-h-10 rounded-lg border border-gray-200 bg-transparent px-3 text-sm text-gray-900 dark:border-gray-700 dark:text-gray-100"
							maxlength="64"
							bind:value={category.display_name}
						/>
					</label>
					<div>
						<div class="text-xs text-gray-500 md:hidden">{$i18n.t('Identifier')}</div>
						<code class="text-xs text-gray-500">{category.id}</code>
					</div>
					<div class="flex items-center gap-3">
						<label class="flex min-h-10 items-center gap-2 text-sm">
							<input
								type="checkbox"
								bind:checked={category.enabled}
								disabled={category.id === 'other'}
							/>
							<span>{$i18n.t('Enabled')}</span>
						</label>
						<input
							class="min-h-10 w-20 rounded-lg border border-gray-200 bg-transparent px-2 text-sm tabular-nums dark:border-gray-700"
							type="number"
							min="0"
							max="10000"
							bind:value={category.sort_order}
							aria-label={$i18n.t('Sort order')}
						/>
					</div>
					<div class="grid grid-cols-2 gap-2 md:justify-self-end">
						<button
							class="min-h-10 rounded-lg border border-gray-200 px-3 text-sm font-medium transition hover:bg-gray-50 disabled:opacity-50 dark:border-gray-700 dark:hover:bg-gray-800"
							type="button"
							disabled={savingId !== null || deletingId !== null || !category.display_name.trim()}
							on:click={() => save(category)}
						>
							{savingId === category.id ? $i18n.t('Saving') : $i18n.t('Save')}
						</button>
						<button
							class="min-h-10 rounded-lg px-3 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-40 dark:text-red-400 dark:hover:bg-red-950/30"
							type="button"
							disabled={category.id === 'other' || savingId !== null || deletingId !== null}
							title={category.id === 'other'
								? $i18n.t('The default category cannot be deleted')
								: ''}
							on:click={() => remove(category)}
						>
							{deletingId === category.id ? $i18n.t('Deleting') : $i18n.t('Delete')}
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</section>

{#if showCreate}
	<div
		class="fixed inset-0 z-[100] flex items-end justify-center bg-black/40 p-0 backdrop-blur-[2px] sm:items-center sm:p-4"
		role="presentation"
		on:click={(event) => event.currentTarget === event.target && !creating && (showCreate = false)}
	>
		<section
			class="w-full rounded-t-3xl bg-white p-5 shadow-2xl dark:bg-gray-900 sm:max-w-md sm:rounded-3xl sm:p-6"
			role="dialog"
			aria-modal="true"
			aria-labelledby="create-category-title"
		>
			<h2 id="create-category-title" class="text-lg font-medium dark:text-gray-100">
				{$i18n.t('Add image category')}
			</h2>
			<div class="mt-5 grid gap-4">
				<label class="grid gap-1.5 text-sm">
					<span class="font-medium">{$i18n.t('Category name')}</span>
					<input
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						maxlength="64"
						bind:value={newCategory.display_name}
					/>
				</label>
				<label class="grid gap-1.5 text-sm">
					<span class="font-medium">{$i18n.t('Sort order')}</span>
					<input
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						type="number"
						min="0"
						max="10000"
						bind:value={newCategory.sort_order}
					/>
				</label>
				<label class="flex min-h-11 items-center gap-2 text-sm">
					<input type="checkbox" bind:checked={newCategory.enabled} />
					<span>{$i18n.t('Enabled')}</span>
				</label>
			</div>
			<div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
				<button
					class="min-h-11 rounded-xl border border-gray-200 px-5 text-sm dark:border-gray-700"
					type="button"
					disabled={creating}
					on:click={() => (showCreate = false)}>{$i18n.t('Cancel')}</button
				>
				<button
					class="min-h-11 rounded-xl bg-gray-900 px-5 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-gray-900"
					type="button"
					disabled={creating || !newCategory.display_name.trim()}
					on:click={createCategory}
				>
					{creating ? $i18n.t('Creating') : $i18n.t('Create')}
				</button>
			</div>
		</section>
	</div>
{/if}
