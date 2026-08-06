<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import {
		listImageModelOperations,
		updateImageModelOperation,
		type ImageModelOperation
	} from '$lib/apis/image-model-ops';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');
	let items: ImageModelOperation[] = [];
	let loading = true;
	let search = '';
	let task = '';
	let statusFilter = '';
	let page = 1;
	let pageSize = 25;
	let editing: ImageModelOperation | null = null;
	let tagDraft = '';
	let saving = false;

	$: filteredItems = items.filter((item) => {
		const matchesTask = !task || item.task === task;
		const matchesSearch = `${item.name} ${item.provider} ${item.public_id} ${item.tags.join(' ')}`
			.toLowerCase()
			.includes(search.trim().toLowerCase());
		const matchesStatus =
			!statusFilter ||
			(statusFilter === 'recommended' && item.recommended) ||
			(statusFilter === 'disabled' && !item.enabled) ||
			(statusFilter === 'hidden' && !item.visible) ||
			(statusFilter === 'maintenance' && Boolean(item.maintenance_message));
		return matchesTask && matchesSearch && matchesStatus;
	});
	$: totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
	$: if (page > totalPages) page = totalPages;
	$: pageItems = filteredItems.slice((page - 1) * pageSize, page * pageSize);

	const resetPage = () => (page = 1);

	const load = async () => {
		loading = true;
		try {
			items = await listImageModelOperations(localStorage.token);
		} catch {
			toast.error($i18n.t('Failed to load image models'));
		} finally {
			loading = false;
		}
	};

	const openEditor = (item: ImageModelOperation) => {
		editing = { ...item, tags: [...item.tags] };
		tagDraft = item.tags.join(', ');
	};

	const save = async () => {
		if (!editing || saving) return;
		saving = true;
		try {
			const saved = await updateImageModelOperation(localStorage.token, editing.model_id, {
				visible: editing.visible,
				enabled: editing.enabled,
				recommended: editing.recommended,
				sort_order: editing.sort_order,
				tags: tagDraft
					.split(',')
					.map((tag) => tag.trim())
					.filter(Boolean),
				maintenance_message: editing.maintenance_message
			});
			items = items.map((item) => (item.model_id === saved.model_id ? saved : item));
			editing = null;
			toast.success($i18n.t('Model settings saved'));
		} catch {
			toast.error($i18n.t('Failed to save model settings'));
		} finally {
			saving = false;
		}
	};

	onMount(load);
</script>

<svelte:window on:keydown={(event) => event.key === 'Escape' && !saving && (editing = null)} />

<div class="flex h-full min-h-0 flex-col gap-4">
	<header class="flex justify-end">
		<div class="text-sm tabular-nums text-gray-500">
			{$i18n.t('{{count}} models', { count: filteredItems.length })}
		</div>
	</header>

	<div class="grid gap-2 sm:grid-cols-2 xl:grid-cols-[minmax(16rem,1fr)_12rem_12rem_7rem]">
		<input
			class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm outline-none focus:border-gray-400 dark:border-gray-700 dark:focus:border-gray-500 sm:col-span-2 xl:col-span-1"
			bind:value={search}
			on:input={resetPage}
			placeholder={$i18n.t('Search models')}
		/>
		<select
			class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			bind:value={task}
			on:change={resetPage}
		>
			<option value="">{$i18n.t('All tasks')}</option>
			<option value="text-to-image">{$i18n.t('Text to image')}</option>
			<option value="image-to-image">{$i18n.t('Image to image')}</option>
		</select>
		<select
			class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			bind:value={statusFilter}
			on:change={resetPage}
		>
			<option value="">{$i18n.t('All statuses')}</option>
			<option value="recommended">{$i18n.t('Recommended')}</option>
			<option value="disabled">{$i18n.t('Disabled')}</option>
			<option value="hidden">{$i18n.t('Hidden')}</option>
			<option value="maintenance">{$i18n.t('With maintenance message')}</option>
		</select>
		<select
			class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			bind:value={pageSize}
			on:change={resetPage}
			aria-label={$i18n.t('Rows per page')}
		>
			<option value={25}>25 / {$i18n.t('page')}</option>
			<option value={50}>50 / {$i18n.t('page')}</option>
			<option value={100}>100 / {$i18n.t('page')}</option>
		</select>
	</div>

	{#if loading}
		<div class="flex min-h-64 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if pageItems.length === 0}
		<div
			class="flex min-h-48 items-center justify-center rounded-2xl border border-dashed border-gray-200 text-sm text-gray-500 dark:border-gray-800"
		>
			{$i18n.t('No matching models')}
		</div>
	{:else}
		<div class="min-h-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
			<div
				class="hidden grid-cols-[minmax(16rem,1fr)_7rem_9rem_11rem_5rem] gap-3 border-b border-gray-200 bg-gray-50/70 px-4 py-2 text-xs font-medium text-gray-500 dark:border-gray-800 dark:bg-gray-900/40 md:grid"
			>
				<div>{$i18n.t('Model')}</div>
				<div>{$i18n.t('Task')}</div>
				<div>{$i18n.t('Status')}</div>
				<div>{$i18n.t('Operations')}</div>
				<div class="text-right">{$i18n.t('Action')}</div>
			</div>
			<div class="max-h-[min(62vh,44rem)] overflow-y-auto overscroll-contain">
				{#each pageItems as item (item.model_id)}
					<article
						class="grid gap-2 border-b border-gray-100 px-3 py-3 last:border-b-0 dark:border-gray-800/70 md:grid-cols-[minmax(16rem,1fr)_7rem_9rem_11rem_5rem] md:items-center md:gap-3 md:px-4 md:py-2.5"
					>
						<div class="min-w-0">
							<div class="truncate text-sm font-medium dark:text-gray-100">{item.name}</div>
							<div class="truncate text-xs text-gray-500">{item.provider} · {item.public_id}</div>
						</div>
						<div class="text-xs text-gray-500">
							{item.task === 'text-to-image' ? $i18n.t('Text to image') : $i18n.t('Image to image')}
						</div>
						<div class="flex flex-wrap gap-1 text-[11px]">
							{#if !item.visible}<span
									class="whitespace-nowrap rounded-md bg-gray-100 px-1.5 py-0.5 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
									>{$i18n.t('Hidden')}</span
								>{/if}
							{#if !item.enabled}<span
									class="whitespace-nowrap rounded-md bg-red-50 px-1.5 py-0.5 text-red-700 dark:bg-red-950/40 dark:text-red-300"
									>{$i18n.t('Disabled')}</span
								>{/if}
							{#if item.visible && item.enabled}<span
									class="whitespace-nowrap rounded-md bg-emerald-50 px-1.5 py-0.5 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
									>{$i18n.t('Available')}</span
								>{/if}
						</div>
						<div class="flex min-w-0 flex-wrap items-center gap-1 text-[11px]">
							{#if item.recommended}<span
									class="whitespace-nowrap rounded-md bg-amber-50 px-1.5 py-0.5 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
									>{$i18n.t('Recommended')}</span
								>{/if}
							<span class="whitespace-nowrap text-gray-500"># {item.sort_order}</span>
							{#if item.tags.length}<span class="max-w-24 truncate text-gray-500"
									>{item.tags.join(' · ')}</span
								>{/if}
							{#if item.maintenance_message}<span class="whitespace-nowrap text-orange-600 dark:text-orange-400"
									>{$i18n.t('Maintenance')}</span
								>{/if}
						</div>
						<button
							class="min-h-9 justify-self-start rounded-lg border border-gray-200 px-3 text-xs font-medium transition hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800 md:justify-self-end"
							type="button"
							on:click={() => openEditor(item)}>{$i18n.t('Edit')}</button
						>
					</article>
				{/each}
			</div>
		</div>

		<nav class="flex items-center justify-between gap-3" aria-label={$i18n.t('Pagination')}>
			<button
				class="min-h-10 rounded-xl border border-gray-200 px-4 text-sm disabled:opacity-40 dark:border-gray-700"
				type="button"
				disabled={page <= 1}
				on:click={() => (page -= 1)}>{$i18n.t('Previous')}</button
			>
			<span class="text-sm tabular-nums text-gray-500">{page} / {totalPages}</span>
			<button
				class="min-h-10 rounded-xl border border-gray-200 px-4 text-sm disabled:opacity-40 dark:border-gray-700"
				type="button"
				disabled={page >= totalPages}
				on:click={() => (page += 1)}>{$i18n.t('Next')}</button
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
			class="max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 shadow-2xl dark:bg-gray-900 sm:max-w-xl sm:rounded-3xl sm:p-6"
			role="dialog"
			aria-modal="true"
			aria-labelledby="model-operation-title"
		>
			<div class="flex items-start justify-between gap-4">
				<div class="min-w-0">
					<h2 id="model-operation-title" class="truncate text-lg font-medium dark:text-gray-100">
						{editing.name}
					</h2>
					<p class="mt-1 break-all text-xs text-gray-500">
						{editing.provider} · {editing.public_id}
					</p>
				</div>
				<button
					class="min-h-10 rounded-xl px-3 text-sm text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
					type="button"
					disabled={saving}
					on:click={() => (editing = null)}
					aria-label={$i18n.t('Close')}>✕</button
				>
			</div>

			<div class="mt-5 grid gap-3 sm:grid-cols-3">
				<label
					class="flex min-h-12 items-center gap-3 rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700"
					><input type="checkbox" bind:checked={editing.visible} /><span
						><span class="block font-medium">{$i18n.t('Visible')}</span><span
							class="text-xs text-gray-500">{$i18n.t('Shown in selector')}</span
						></span
					></label
				>
				<label
					class="flex min-h-12 items-center gap-3 rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700"
					><input type="checkbox" bind:checked={editing.enabled} /><span
						><span class="block font-medium">{$i18n.t('Enabled')}</span><span
							class="text-xs text-gray-500">{$i18n.t('Can be selected')}</span
						></span
					></label
				>
				<label
					class="flex min-h-12 items-center gap-3 rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700"
					><input type="checkbox" bind:checked={editing.recommended} /><span
						><span class="block font-medium">{$i18n.t('Recommended')}</span><span
							class="text-xs text-gray-500">{$i18n.t('Appears before regular models')}</span
						></span
					></label
				>
			</div>

			<div class="mt-4 grid gap-4">
				<label class="grid gap-1.5 text-sm"
					><span class="font-medium">{$i18n.t('Sort order')}</span><span
						class="text-xs text-gray-500"
						>{$i18n.t('Smaller numbers appear first within the same recommendation group.')}</span
					><input
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						type="number"
						min="0"
						max="100000"
						bind:value={editing.sort_order}
					/></label
				>
				<label class="grid gap-1.5 text-sm"
					><span class="font-medium">{$i18n.t('Tags')}</span><span class="text-xs text-gray-500"
						>{$i18n.t('Shown below the model name; separate multiple tags with commas.')}</span
					><input
						class="min-h-11 rounded-xl border border-gray-200 bg-transparent px-3 dark:border-gray-700"
						bind:value={tagDraft}
						placeholder={$i18n.t('Tags separated by commas')}
					/></label
				>
				<label class="grid gap-1.5 text-sm"
					><span class="font-medium">{$i18n.t('Maintenance message')}</span><span
						class="text-xs text-gray-500"
						>{$i18n.t(
							'Shown to users in the model selector. Disabled models cannot be selected.'
						)}</span
					><textarea
						class="min-h-24 resize-y rounded-xl border border-gray-200 bg-transparent px-3 py-2 dark:border-gray-700"
						bind:value={editing.maintenance_message}
						placeholder={$i18n.t('Maintenance message')}
					></textarea></label
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
