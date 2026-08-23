<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import {
		getAdminPromptTagCatalog,
		createPromptTagCategory,
		updatePromptTagCategory,
		deletePromptTagCategory,
		createPromptTag,
		updatePromptTag,
		deletePromptTag,
		exportPromptTags,
		importPromptTags,
		type PromptTagCategoryItem,
		type PromptTagItem,
		type PromptTagMediaKind
	} from '$lib/apis/prompt_tags';
	import { registerPromptTagTranslations } from '$lib/components/prompt-tags/prompt-tags-i18n';
	import { trapFocus } from '$lib/actions/focusTrap';
	import { toast } from 'svelte-sonner';

	const i18n = getContext<Writable<I18n>>('i18n');

	let loading = true;
	let categories: PromptTagCategoryItem[] = [];
	let tags: PromptTagItem[] = [];
	let filterCategoryId = '';
	let search = '';

	/* ---------- category modal ---------- */
	let categoryModalOpen = false;
	let categoryEditing: PromptTagCategoryItem | null = null;
	let categoryForm = { slug: '', name_zh: '', name_en: '', enabled: true, sort_order: 1000 };
	let saving = false;

	/* ---------- tag modal ---------- */
	let tagModalOpen = false;
	let tagEditing: PromptTagItem | null = null;
	let tagForm = {
		slug: '',
		category_id: '',
		label_zh: '',
		label_en: '',
		insert_text: '',
		is_negative: false,
		media_kinds: ['image', 'video'] as PromptTagMediaKind[],
		enabled: true,
		sort_order: 1000
	};

	/* ---------- import ---------- */
	let importModalOpen = false;
	let importText = '';
	let importDryRun = true;
	let importUpsert = false;
	let importResult: {
		categories_created: number;
		categories_updated: number;
		tags_created: number;
		tags_updated: number;
	} | null = null;

	const isZh = () => ($i18n.language ?? 'en').toLowerCase().startsWith('zh');
	const catName = (c: PromptTagCategoryItem) => (isZh() ? c.name_zh : c.name_en);
	const tagLabel = (t: PromptTagItem) => (isZh() ? t.label_zh : t.label_en);

	async function loadCatalog() {
		loading = true;
		try {
			const data = await getAdminPromptTagCatalog(localStorage.token);
			categories = [...data.categories];
			tags = [...data.tags];
		} catch {
			toast.error($i18n.t('promptTags.errors.unavailable'));
		} finally {
			loading = false;
		}
	}

	$: tagName = (id: string) => categories.find((c) => c.id === id);

	$: filteredTags = tags.filter((t) => {
		if (filterCategoryId && t.category_id !== filterCategoryId) return false;
		if (search.trim()) {
			const q = search.trim().toLowerCase();
			return (
				t.label_zh.toLowerCase().includes(q) ||
				t.label_en.toLowerCase().includes(q) ||
				t.slug.toLowerCase().includes(q) ||
				t.insert_text.toLowerCase().includes(q)
			);
		}
		return true;
	});

	/* ---------- category CRUD ---------- */
	function openCreateCategory() {
		categoryEditing = null;
		categoryForm = { slug: '', name_zh: '', name_en: '', enabled: true, sort_order: 1000 };
		categoryModalOpen = true;
	}

	function openEditCategory(c: PromptTagCategoryItem) {
		categoryEditing = c;
		categoryForm = {
			slug: c.slug,
			name_zh: c.name_zh,
			name_en: c.name_en,
			enabled: c.enabled,
			sort_order: c.sort_order
		};
		categoryModalOpen = true;
	}

	async function saveCategory() {
		if (!categoryForm.slug.trim() || !categoryForm.name_zh.trim() || !categoryForm.name_en.trim())
			return;
		saving = true;
		try {
			if (categoryEditing) {
				await updatePromptTagCategory(localStorage.token, categoryEditing.id, categoryForm);
			} else {
				await createPromptTagCategory(localStorage.token, categoryForm);
			}
			categoryModalOpen = false;
			await loadCatalog();
			toast.success($i18n.t('promptTags.admin.saved'));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		} finally {
			saving = false;
		}
	}

	async function removeCategory(c: PromptTagCategoryItem) {
		const hasTags = tags.some((t) => t.category_id === c.id);
		if (hasTags && !confirm($i18n.t('promptTags.admin.confirmDeleteCategory'))) return;
		if (!hasTags && !confirm($i18n.t('promptTags.admin.deleteConfirm'))) return;
		try {
			await deletePromptTagCategory(localStorage.token, c.id, hasTags);
			await loadCatalog();
			toast.success($i18n.t('promptTags.admin.deleted'));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		}
	}

	/* ---------- tag CRUD ---------- */
	function openCreateTag() {
		if (categories.length === 0) {
			toast.error($i18n.t('promptTags.admin.noCategory'));
			return;
		}
		tagEditing = null;
		tagForm = {
			slug: '',
			category_id: filterCategoryId || categories[0].id,
			label_zh: '',
			label_en: '',
			insert_text: '',
			is_negative: false,
			media_kinds: ['image', 'video'],
			enabled: true,
			sort_order: 1000
		};
		tagModalOpen = true;
	}

	function openEditTag(t: PromptTagItem) {
		tagEditing = t;
		tagForm = {
			slug: t.slug,
			category_id: t.category_id,
			label_zh: t.label_zh,
			label_en: t.label_en,
			insert_text: t.insert_text,
			is_negative: t.is_negative,
			media_kinds: [...t.media_kinds],
			enabled: t.enabled,
			sort_order: t.sort_order
		};
		tagModalOpen = true;
	}

	async function saveTag() {
		if (
			!tagForm.slug.trim() ||
			!tagForm.label_zh.trim() ||
			!tagForm.label_en.trim() ||
			!tagForm.insert_text.trim()
		)
			return;
		saving = true;
		try {
			if (tagEditing) {
				await updatePromptTag(localStorage.token, tagEditing.id, tagForm);
			} else {
				await createPromptTag(localStorage.token, tagForm);
			}
			tagModalOpen = false;
			await loadCatalog();
			toast.success($i18n.t('promptTags.admin.saved'));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		} finally {
			saving = false;
		}
	}

	async function removeTag(t: PromptTagItem) {
		if (!confirm($i18n.t('promptTags.admin.deleteConfirm'))) return;
		try {
			await deletePromptTag(localStorage.token, t.id);
			await loadCatalog();
			toast.success($i18n.t('promptTags.admin.deleted'));
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		}
	}

	/* ---------- import / export ---------- */
	async function handleExport() {
		try {
			const doc = await exportPromptTags(localStorage.token);
			const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `prompt-tags-${Date.now()}.json`;
			a.click();
			URL.revokeObjectURL(url);
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		}
	}

	function openImport() {
		importText = '';
		importDryRun = true;
		importUpsert = false;
		importResult = null;
		importModalOpen = true;
	}

	async function handleImport() {
		if (!importText.trim()) return;
		saving = true;
		try {
			const doc = JSON.parse(importText);
			const result = await importPromptTags(localStorage.token, doc, {
				dryRun: importDryRun,
				upsert: importUpsert
			});
			importResult = result;
			if (!importDryRun) {
				await loadCatalog();
				toast.success($i18n.t('promptTags.admin.saved'));
			}
		} catch (e) {
			toast.error(e instanceof Error ? e.message : $i18n.t('promptTags.errors.requestFailed'));
		} finally {
			saving = false;
		}
	}

	function toggleMediaKind(kind: PromptTagMediaKind) {
		const set = new Set(tagForm.media_kinds);
		if (set.has(kind)) set.delete(kind);
		else set.add(kind);
		tagForm.media_kinds = [...set] as PromptTagMediaKind[];
		if (tagForm.media_kinds.length === 0) tagForm.media_kinds = ['image', 'video'];
	}

	// 组件挂载后拉取标签库；缺少这一步页面会一直停在 loading 转圈。
	onMount(() => {
		registerPromptTagTranslations($i18n);
		void loadCatalog();
	});
</script>

<svelte:head>
	<title>{$i18n.t('promptTags.admin.management')}</title>
</svelte:head>

<div class="mx-auto max-w-4xl p-4 sm:p-6">
	<div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
				{$i18n.t('promptTags.admin.management')}
			</h1>
			<p class="mt-1 text-sm text-gray-500">
				{categories.length}
				{$i18n.t('promptTags.admin.categories')} · {tags.length}
				{$i18n.t('promptTags.admin.tags')}
			</p>
		</div>
		<div class="flex flex-wrap gap-2">
			<button
				type="button"
				class="inline-flex min-h-9 items-center rounded-xl border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850"
				on:click={openImport}
			>
				{$i18n.t('promptTags.admin.importTitle')}
			</button>
			<button
				type="button"
				class="inline-flex min-h-9 items-center rounded-xl border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850"
				on:click={handleExport}
			>
				{$i18n.t('promptTags.admin.exportTitle')}
			</button>
			<button
				type="button"
				class="inline-flex min-h-9 items-center rounded-xl border border-gray-200 bg-white px-3 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-850"
				on:click={openCreateCategory}
			>
				{$i18n.t('promptTags.admin.createCategory')}
			</button>
			<button
				type="button"
				class="inline-flex min-h-9 items-center rounded-xl bg-gray-900 px-3 text-sm font-medium text-white transition hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
				on:click={openCreateTag}
			>
				{$i18n.t('promptTags.admin.createTag')}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-16 text-gray-400">
			<svg class="size-6 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4z" />
			</svg>
		</div>
	{:else}
		<!-- categories -->
		<section class="mb-8">
			<h2
				class="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
			>
				{$i18n.t('promptTags.admin.categories')}
			</h2>
			<div class="grid gap-2 sm:grid-cols-2">
				{#each categories as c (c.id)}
					<div
						class="flex items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white p-3 dark:border-gray-800 dark:bg-gray-900"
					>
						<div class="min-w-0">
							<div class="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
								{catName(c)}
							</div>
							<div class="truncate text-xs text-gray-400">
								{c.slug} · {tags.filter((t) => t.category_id === c.id).length}
								{$i18n.t('promptTags.admin.tags')}
							</div>
						</div>
						<div class="flex shrink-0 items-center gap-1">
							<span
								class="rounded px-1.5 py-0.5 text-[10px] font-medium {c.enabled
									? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
									: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}"
							>
								{c.enabled ? '✓' : '✗'}
							</span>
							<button
								type="button"
								class="flex size-7 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200"
								on:click={() => openEditCategory(c)}
								aria-label={$i18n.t('promptTags.admin.editCategory')}
							>
								<svg
									class="size-4"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="1.8"
									aria-hidden="true"
									><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path
										d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
									/></svg
								>
							</button>
							<button
								type="button"
								class="flex size-7 items-center justify-center rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950 dark:hover:text-red-400"
								on:click={() => removeCategory(c)}
								aria-label={$i18n.t('promptTags.admin.delete')}
							>
								<svg
									class="size-4"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="1.8"
									aria-hidden="true"
									><path
										d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
									/></svg
								>
							</button>
						</div>
					</div>
				{:else}
					<p class="col-span-2 py-6 text-center text-sm text-gray-400">
						{$i18n.t('promptTags.picker.empty')}
					</p>
				{/each}
			</div>
		</section>

		<!-- tags -->
		<section>
			<div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
				<h2 class="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
					{$i18n.t('promptTags.admin.tags')}
				</h2>
				<div class="flex flex-wrap gap-2">
					<select
						bind:value={filterCategoryId}
						class="min-h-9 rounded-xl border border-gray-200 bg-white px-3 text-sm dark:border-gray-700 dark:bg-gray-900"
					>
						<option value=""
							>{$i18n.t('promptTags.admin.categories')}: {$i18n.t('promptTags.admin.all')}</option
						>
						{#each categories as c (c.id)}
							<option value={c.id}>{catName(c)}</option>
						{/each}
					</select>
					<input
						type="search"
						bind:value={search}
						class="min-h-9 flex-1 rounded-xl border border-gray-200 bg-white px-3 text-sm dark:border-gray-700 dark:bg-gray-900"
						placeholder={$i18n.t('promptTags.picker.search')}
					/>
				</div>
			</div>

			<div class="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
				<table class="w-full text-left text-sm">
					<thead
						class="border-b border-gray-100 bg-gray-50 text-xs text-gray-500 dark:border-gray-800 dark:bg-gray-900/50"
					>
						<tr>
							<th class="whitespace-nowrap px-3 py-2.5 font-medium"
								>{$i18n.t('promptTags.admin.labelZh')}</th
							>
							<th class="whitespace-nowrap px-3 py-2.5 font-medium"
								>{$i18n.t('promptTags.admin.insertText')}</th
							>
							<th class="hidden whitespace-nowrap px-3 py-2.5 font-medium sm:table-cell"
								>{$i18n.t('promptTags.admin.category')}</th
							>
							<th class="hidden whitespace-nowrap px-3 py-2.5 font-medium md:table-cell"
								>{$i18n.t('promptTags.admin.isNegative')}</th
							>
							<th class="whitespace-nowrap px-3 py-2.5 font-medium text-right">—</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredTags as t (t.id)}
							<tr class="border-b border-gray-50 last:border-0 dark:border-gray-850">
								<td class="px-3 py-2.5">
									<div class="font-medium text-gray-900 dark:text-gray-100">{tagLabel(t)}</div>
									<div class="text-xs text-gray-400">{t.slug}</div>
								</td>
								<td
									class="max-w-[12rem] truncate px-3 py-2.5 text-gray-600 dark:text-gray-300"
									title={t.insert_text}
								>
									{t.insert_text}
								</td>
								<td class="hidden px-3 py-2.5 text-gray-600 dark:text-gray-300 sm:table-cell">
									{tagName(t.category_id) ? catName(tagName(t.category_id)!) : '—'}
								</td>
								<td class="hidden px-3 py-2.5 md:table-cell">
									{#if t.is_negative}
										<span
											class="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-900 dark:text-amber-300"
											>{$i18n.t('promptTags.admin.isNegative')}</span
										>
									{/if}
								</td>
								<td class="whitespace-nowrap px-3 py-2.5 text-right">
									<button
										type="button"
										class="mr-1 inline-flex size-7 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200"
										on:click={() => openEditTag(t)}
										aria-label={$i18n.t('promptTags.admin.editTag')}
									>
										<svg
											class="size-4"
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											stroke-width="1.8"
											aria-hidden="true"
											><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path
												d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
											/></svg
										>
									</button>
									<button
										type="button"
										class="inline-flex size-7 items-center justify-center rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950 dark:hover:text-red-400"
										on:click={() => removeTag(t)}
										aria-label={$i18n.t('promptTags.admin.delete')}
									>
										<svg
											class="size-4"
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											stroke-width="1.8"
											aria-hidden="true"
											><path
												d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
											/></svg
										>
									</button>
								</td>
							</tr>
						{:else}
							<tr>
								<td colspan="5" class="px-3 py-8 text-center text-gray-400"
									>{$i18n.t('promptTags.picker.empty')}</td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>
	{/if}
</div>

<!-- category modal -->
{#if categoryModalOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
		on:click|self={() => (categoryModalOpen = false)}
		role="dialog"
		aria-modal="true"
		use:trapFocus
	>
		<div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl dark:bg-gray-900">
			<h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
				{categoryEditing
					? $i18n.t('promptTags.admin.editCategory')
					: $i18n.t('promptTags.admin.createCategory')}
			</h2>
			<form on:submit|preventDefault={saveCategory} class="space-y-3">
				<div>
					<label class="mb-1 block text-xs font-medium text-gray-500" for="cat-slug"
						>{$i18n.t('promptTags.admin.slug')}</label
					>
					<input
						id="cat-slug"
						bind:value={categoryForm.slug}
						class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
						disabled={!!categoryEditing}
					/>
				</div>
				<div>
					<label class="mb-1 block text-xs font-medium text-gray-500" for="cat-zh"
						>{$i18n.t('promptTags.admin.nameZh')}</label
					>
					<input
						id="cat-zh"
						bind:value={categoryForm.name_zh}
						class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
					/>
				</div>
				<div>
					<label class="mb-1 block text-xs font-medium text-gray-500" for="cat-en"
						>{$i18n.t('promptTags.admin.nameEn')}</label
					>
					<input
						id="cat-en"
						bind:value={categoryForm.name_en}
						class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
					/>
				</div>
				<div class="flex gap-3">
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" bind:checked={categoryForm.enabled} />
						{$i18n.t('promptTags.admin.enabled')}
					</label>
					<label class="flex items-center gap-2 text-sm">
						{$i18n.t('promptTags.admin.sortOrder')}
						<input
							type="number"
							bind:value={categoryForm.sort_order}
							class="min-h-9 w-20 rounded-xl border border-gray-200 px-2 text-sm dark:border-gray-700 dark:bg-gray-950"
						/>
					</label>
				</div>
				<div class="flex justify-end gap-2 pt-2">
					<button
						type="button"
						class="min-h-9 rounded-xl px-4 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
						on:click={() => (categoryModalOpen = false)}
						>{$i18n.t('promptTags.admin.cancel')}</button
					>
					<button
						type="submit"
						class="min-h-9 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
						disabled={saving}
					>
						{$i18n.t('promptTags.admin.save')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- tag modal -->
{#if tagModalOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
		on:click|self={() => (tagModalOpen = false)}
		role="dialog"
		aria-modal="true"
		use:trapFocus
	>
		<div
			class="max-h-[85dvh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5 shadow-xl dark:bg-gray-900"
		>
			<h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
				{tagEditing ? $i18n.t('promptTags.admin.editTag') : $i18n.t('promptTags.admin.createTag')}
			</h2>
			<form on:submit|preventDefault={saveTag} class="space-y-3">
				<div class="grid gap-3 sm:grid-cols-2">
					<div>
						<label class="mb-1 block text-xs font-medium text-gray-500" for="tag-slug"
							>{$i18n.t('promptTags.admin.slug')}</label
						>
						<input
							id="tag-slug"
							bind:value={tagForm.slug}
							class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
							disabled={!!tagEditing}
						/>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium text-gray-500" for="tag-cat"
							>{$i18n.t('promptTags.admin.category')}</label
						>
						<select
							id="tag-cat"
							bind:value={tagForm.category_id}
							class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
						>
							{#each categories as c (c.id)}
								<option value={c.id}>{catName(c)}</option>
							{/each}
						</select>
					</div>
				</div>
				<div class="grid gap-3 sm:grid-cols-2">
					<div>
						<label class="mb-1 block text-xs font-medium text-gray-500" for="tag-zh"
							>{$i18n.t('promptTags.admin.labelZh')}</label
						>
						<input
							id="tag-zh"
							bind:value={tagForm.label_zh}
							class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
						/>
					</div>
					<div>
						<label class="mb-1 block text-xs font-medium text-gray-500" for="tag-en"
							>{$i18n.t('promptTags.admin.labelEn')}</label
						>
						<input
							id="tag-en"
							bind:value={tagForm.label_en}
							class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
						/>
					</div>
				</div>
				<div>
					<label class="mb-1 block text-xs font-medium text-gray-500" for="tag-insert"
						>{$i18n.t('promptTags.admin.insertText')}</label
					>
					<input
						id="tag-insert"
						bind:value={tagForm.insert_text}
						class="min-h-9 w-full rounded-xl border border-gray-200 px-3 text-sm dark:border-gray-700 dark:bg-gray-950"
					/>
				</div>
				<div class="flex flex-wrap items-center gap-4">
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" bind:checked={tagForm.is_negative} />
						{$i18n.t('promptTags.admin.isNegative')}
					</label>
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" bind:checked={tagForm.enabled} />
						{$i18n.t('promptTags.admin.enabled')}
					</label>
					<div class="flex items-center gap-2 text-sm">
						{$i18n.t('promptTags.admin.mediaKinds')}:
						{#each ['image', 'video'] as kind (kind)}
							<label class="flex items-center gap-1">
								<input
									type="checkbox"
									checked={tagForm.media_kinds.includes(kind as PromptTagMediaKind)}
									on:change={() => toggleMediaKind(kind as PromptTagMediaKind)}
								/>
								{kind}
							</label>
						{/each}
					</div>
					<label class="flex items-center gap-2 text-sm">
						{$i18n.t('promptTags.admin.sortOrder')}
						<input
							type="number"
							bind:value={tagForm.sort_order}
							class="min-h-9 w-20 rounded-xl border border-gray-200 px-2 text-sm dark:border-gray-700 dark:bg-gray-950"
						/>
					</label>
				</div>
				<div class="flex justify-end gap-2 pt-2">
					<button
						type="button"
						class="min-h-9 rounded-xl px-4 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
						on:click={() => (tagModalOpen = false)}>{$i18n.t('promptTags.admin.cancel')}</button
					>
					<button
						type="submit"
						class="min-h-9 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
						disabled={saving}
					>
						{$i18n.t('promptTags.admin.save')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- import modal -->
{#if importModalOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
		on:click|self={() => (importModalOpen = false)}
		role="dialog"
		aria-modal="true"
		use:trapFocus
	>
		<div
			class="max-h-[85dvh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5 shadow-xl dark:bg-gray-900"
		>
			<h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
				{$i18n.t('promptTags.admin.importTitle')}
			</h2>
			<div class="space-y-3">
				<textarea
					bind:value={importText}
					class="min-h-32 w-full rounded-xl border border-gray-200 p-3 font-mono text-xs dark:border-gray-700 dark:bg-gray-950"
					placeholder={$i18n.t('promptTags.admin.importPlaceholder')}
				></textarea>
				<div class="flex flex-wrap gap-4">
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" bind:checked={importDryRun} />
						{$i18n.t('promptTags.admin.dryRun')}
					</label>
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" bind:checked={importUpsert} />
						{$i18n.t('promptTags.admin.upsert')}
					</label>
				</div>
				{#if importResult}
					<div class="rounded-xl bg-gray-50 p-3 text-sm dark:bg-gray-850">
						<div class="font-medium text-gray-700 dark:text-gray-300">
							{$i18n.t('promptTags.admin.importResult')}
						</div>
						<div class="mt-1 text-xs text-gray-500">
							{$i18n.t('promptTags.admin.categoriesCreated')}: {importResult.categories_created} ·
							{$i18n.t('promptTags.admin.categoriesUpdated')}: {importResult.categories_updated} ·
							{$i18n.t('promptTags.admin.tagsCreated')}: {importResult.tags_created} ·
							{$i18n.t('promptTags.admin.tagsUpdated')}: {importResult.tags_updated}
						</div>
					</div>
				{/if}
				<div class="flex justify-end gap-2">
					<button
						type="button"
						class="min-h-9 rounded-xl px-4 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
						on:click={() => (importModalOpen = false)}>{$i18n.t('promptTags.admin.close')}</button
					>
					<button
						type="button"
						class="min-h-9 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
						disabled={saving || !importText.trim()}
						on:click={handleImport}
					>
						{importDryRun ? $i18n.t('promptTags.admin.dryRun') : $i18n.t('promptTags.admin.import')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
