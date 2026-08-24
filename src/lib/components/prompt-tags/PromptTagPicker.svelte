<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';

	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import {
		getPromptTagCatalog,
		type PromptTagPublicCatalog,
		type PromptTagMediaKind
	} from '$lib/apis/prompt_tags';
	const i18n = getContext<Writable<I18n>>('i18n');

	const dispatch = createEventDispatcher<{
		insert: { text: string; isNegative: boolean };
	}>();

	export let mediaKind: PromptTagMediaKind;
	export let modelId: string | null = null;
	/** 当前模型是否支持负面提示词；false 时隐藏负面标签，避免用户插入后
	 * 提交时被参数归一化静默丢弃（审查发现 #6）。 */
	export let negativeSupported: boolean = true;

	let show = false;
	let catalog: PromptTagPublicCatalog | null = null;
	let loading = false;
	let loadError = '';
	let search = '';
	let activeCategoryId = '';
	let lastLoadedKey = '';
	let abortController: AbortController | null = null;

	const isZh = () => ($i18n.language ?? 'en').toLowerCase().startsWith('zh');
	const label = (item: { label_zh: string; label_en: string }) =>
		isZh() ? item.label_zh : item.label_en;
	const categoryName = (item: { name_zh: string; name_en: string }) =>
		isZh() ? item.name_zh : item.name_en;

	const catalogKey = () => `${mediaKind}:${modelId ?? ''}`;

	// 模型切换后旧目录立即失效：下拉重新打开时按新的媒体/模型作用域拉取。
	let lastResetKey = '';
	$: if (catalogKey() !== lastResetKey) {
		lastResetKey = catalogKey();
		catalog = null;
	}

	async function loadCatalog(force = false) {
		const key = catalogKey();
		if (!force && key === lastLoadedKey && catalog) return;
		if (abortController) abortController.abort();
		abortController = new AbortController();
		loading = true;
		loadError = '';
		try {
			catalog = await getPromptTagCatalog(
				localStorage.token,
				mediaKind,
				modelId ?? undefined,
				abortController.signal
			);
			lastLoadedKey = key;
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') return;
			loadError = $i18n.t('promptTags.errors.unavailable');
		} finally {
			loading = false;
		}
	}

	function onOpenChange(open: boolean) {
		if (open) loadCatalog();
	}

	// 点击即插入并关闭：把标签文本交给页面追加到提示词输入框（负面标签进负向框）。
	// 选中即收起弹窗，与参数/模型弹窗的交互节奏一致。
	function insertTag(tag: { insert_text: string; is_negative: boolean }) {
		dispatch('insert', { text: tag.insert_text, isNegative: tag.is_negative });
		show = false;
	}

	function selectCategory(id: string) {
		activeCategoryId = id;
	}

	function handleCategoryKeydown(event: KeyboardEvent, index: number) {
		if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key))
			return;
		event.preventDefault();
		const ids = filteredCategories.map((category) => category.id);
		if (ids.length === 0) return;
		let next = index;
		if (event.key === 'Home') next = 0;
		else if (event.key === 'End') next = ids.length - 1;
		else if (event.key === 'ArrowDown' || event.key === 'ArrowRight')
			next = (index + 1) % ids.length;
		else next = (index - 1 + ids.length) % ids.length;
		selectCategory(ids[next]);
		requestAnimationFrame(() =>
			document.getElementById(`prompt-tag-category-${ids[next]}`)?.focus()
		);
	}

	$: filteredCategories = (() => {
		if (!catalog) return [];
		const q = search.trim().toLowerCase();
		return catalog.categories
			.map((cat) => ({
				...cat,
				tags: cat.tags.filter((tag) => {
					if (tag.is_negative && !negativeSupported) return false;
					if (!q) return true;
					// 按展示名搜索；同时匹配 insert_text，方便按实际内容找片段。
					return (
						tag.label_zh.toLowerCase().includes(q) ||
						tag.label_en.toLowerCase().includes(q) ||
						tag.insert_text.toLowerCase().includes(q)
					);
				})
			}))
			.filter((cat) => cat.tags.length > 0);
	})();

	$: if (
		filteredCategories.length > 0 &&
		!filteredCategories.some((category) => category.id === activeCategoryId)
	) {
		activeCategoryId = filteredCategories[0].id;
	}

	$: totalTags = catalog?.categories.reduce((sum, c) => sum + c.tags.length, 0) ?? 0;
</script>

<Dropdown
	bind:show
	side="top"
	align="start"
	contentRole="dialog"
	{onOpenChange}
	maxHeight="min(70dvh, 30rem)"
	contentClass="z-50 h-[min(70dvh,30rem)] w-[min(32rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-gray-200/90 bg-white/98 p-2 shadow-2xl backdrop-blur-xl sm:h-96 dark:border-gray-700 dark:bg-gray-900/98"
>
	<button
		type="button"
		class="inline-flex h-11 items-center gap-1.5 rounded-[10px] bg-gray-100 px-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 sm:h-8 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
		aria-expanded={show}
		aria-haspopup="dialog"
		aria-label={$i18n.t('promptTags.picker.label')}
	>
		<svg
			class="size-4 shrink-0"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="1.8"
			aria-hidden="true"
			><path
				d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"
			/><circle cx="7" cy="7" r="1.5" fill="currentColor" stroke="none" /></svg
		>
		<span class="hidden sm:inline">{$i18n.t('promptTags.picker.label')}</span>
	</button>

	<!-- 高度单源：外层 Dropdown 定高，内层 h-full 撑满，杜绝双高度差导致底部裁切 -->
	<div
		slot="content"
		class="flex h-full min-h-0 min-w-0 flex-col"
	>
		<!-- search -->
		<div class="px-1 pb-2 pt-1">
			<input
				type="search"
				bind:value={search}
				class="min-h-11 w-full rounded-xl border border-gray-200 bg-gray-50 px-3 text-sm outline-hidden focus:border-gray-400 focus:ring-2 focus:ring-gray-200 sm:min-h-9 dark:border-gray-700 dark:bg-gray-950 dark:focus:border-gray-500 dark:focus:ring-gray-800"
				placeholder={$i18n.t('promptTags.picker.search')}
				aria-label={$i18n.t('promptTags.picker.search')}
			/>
		</div>

		{#if loading}
			<div class="flex flex-1 items-center justify-center text-sm text-gray-400">
				<svg class="size-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
					/>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4z" />
				</svg>
			</div>
		{:else if loadError}
			<p class="flex-1 py-8 text-center text-sm text-red-500" role="alert">{loadError}</p>
		{:else if !catalog || totalTags === 0}
			<p class="flex-1 py-8 text-center text-sm text-gray-400">
				{$i18n.t('promptTags.picker.empty')}
			</p>
		{:else if filteredCategories.length === 0}
			<p class="flex-1 py-8 text-center text-sm text-gray-400">
				{$i18n.t('promptTags.picker.noResults')}
			</p>
		{:else}
			<div class="flex min-h-0 flex-1 flex-row gap-2">
				<!-- 分类列（左） -->
				<ul
					class="flex min-h-0 w-28 shrink-0 flex-col gap-1 overflow-y-auto overscroll-contain border-r border-gray-100 pr-1 dark:border-gray-800 sm:w-36"
					role="listbox"
					aria-label={$i18n.t('promptTags.picker.categories')}
				>
					{#each filteredCategories as category, index (category.id)}
						<li>
							<button
								type="button"
								id={`prompt-tag-category-${category.id}`}
								class="flex min-h-11 w-full items-center justify-between gap-1 rounded-xl px-2 py-1.5 text-left text-sm transition sm:min-h-9 {activeCategoryId ===
								category.id
									? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
									: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
								role="option"
								aria-selected={activeCategoryId === category.id}
								tabindex={activeCategoryId === category.id ? 0 : -1}
								on:keydown={(event) => handleCategoryKeydown(event, index)}
								on:click={() => selectCategory(category.id)}
							>
								<span class="min-w-0 truncate">{categoryName(category)}</span>
							</button>
						</li>
					{/each}
				</ul>

				<!-- 标签列（右）：点击即插入实际提示词文本 -->
				<div class="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain">
					{#each filteredCategories as category (category.id)}
						{#if category.id === activeCategoryId}
							<div class="flex flex-wrap gap-1.5">
								{#each category.tags as tag (tag.id)}
									<button
										type="button"
										class="inline-flex min-h-11 items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-700 transition select-none hover:bg-gray-100 sm:min-h-8 dark:border-gray-700 dark:bg-gray-850 dark:text-gray-300 dark:hover:bg-gray-800 {tag.is_negative
											? 'ring-1 ring-amber-200 dark:ring-amber-800'
											: ''}"
										title={tag.insert_text}
										on:click={() => insertTag(tag)}
									>
										{label(tag)}
										{#if tag.is_negative}
											<span
												class="rounded bg-amber-100 px-1 text-[10px] font-semibold text-amber-700 dark:bg-amber-900 dark:text-amber-300"
												>{$i18n.t('promptTags.picker.negative')}</span
											>
										{/if}
									</button>
								{/each}
							</div>
						{/if}
					{/each}
				</div>
			</div>
		{/if}
	</div>
</Dropdown>
