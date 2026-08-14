<script lang="ts">
	import { getContext, onMount } from 'svelte';

	import type { SvelteComponent } from 'svelte';

	import Loader from '$lib/components/common/Loader.svelte';

	const i18n = getContext('i18n');
	type OperationsTab = 'discovery' | 'categories' | 'models' | 'providers';
	const tabs: Array<{ id: OperationsTab; label: string }> = [
		{ id: 'discovery', label: 'Discovery operations' },
		{ id: 'categories', label: 'Creation categories' },
		{ id: 'models', label: 'Model operations' },
		{ id: 'providers', label: 'Provider operations' }
	];
	let active: OperationsTab = 'discovery';

	const selectTab = (tab: OperationsTab, target: EventTarget | null) => {
		active = tab;
		if (target instanceof HTMLElement) {
			target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
		}
	};

	// 懒加载：首屏只加载默认 discovery tab，其余 tab 切换时按需动态导入，
	// 避免一次性加载 4 个重组件拖慢运营中心首屏 TTI。
	// 用 SvelteComponentAny 绕开 svelte 类型对动态导入默认导出的严格签名。
	type SvelteComponentAny = typeof SvelteComponent<any>;
	type LazyState = { component: SvelteComponentAny | null; loading: boolean; error: boolean };
	let discoveryState: LazyState = { component: null, loading: false, error: false };
	let categoriesState: LazyState = { component: null, loading: false, error: false };
	let modelsState: LazyState = { component: null, loading: false, error: false };
	let providersState: LazyState = { component: null, loading: false, error: false };

	const loaders: Record<OperationsTab, () => Promise<{ default: SvelteComponentAny }>> = {
		discovery: () => import('$lib/components/discovery/admin/DiscoveryOperations.svelte'),
		categories: () => import('$lib/components/discovery/admin/DiscoveryCategories.svelte'),
		models: () => import('$lib/components/model-ops/admin/ImageModelOperations.svelte'),
		providers: () => import('$lib/components/provider-ops/admin/ProviderOperations.svelte')
	};

	const stateFor = (tab: OperationsTab): LazyState => {
		if (tab === 'discovery') return discoveryState;
		if (tab === 'categories') return categoriesState;
		if (tab === 'models') return modelsState;
		return providersState;
	};

	const setState = (tab: OperationsTab, state: LazyState) => {
		if (tab === 'discovery') discoveryState = state;
		else if (tab === 'categories') categoriesState = state;
		else if (tab === 'models') modelsState = state;
		else providersState = state;
	};

	const ensureLoaded = (tab: OperationsTab) => {
		const state = stateFor(tab);
		if (state.component || state.loading) return;
		setState(tab, { ...state, loading: true, error: false });
		void loaders[tab]()
			.then((mod) => {
				setState(tab, { component: mod.default, loading: false, error: false });
			})
			.catch(() => {
				setState(tab, { component: null, loading: false, error: true });
			})
			.finally(() => {
				const current = stateFor(tab);
				if (current.loading) setState(tab, { ...current, loading: false });
			});
	};

	onMount(() => {
		// 默认 tab 预加载，保证首屏可见内容立即可用。
		ensureLoaded('discovery');
	});

	$: if (active) ensureLoaded(active);
</script>

<svelte:head>
	<title>{$i18n.t('Operations center')}</title>
</svelte:head>

<div class="flex h-full min-h-0 flex-col gap-5 px-4 py-3 lg:px-6">
	<div>
		<h1 class="text-xl font-medium dark:text-gray-100">{$i18n.t('Operations center')}</h1>
		<p class="mt-1 text-sm text-gray-500">
			{$i18n.t('Manage discovery content, creation categories and generation models.')}
		</p>
	</div>

	<div
		class="flex shrink-0 gap-1 overflow-x-auto border-b border-gray-100 dark:border-gray-800"
		role="tablist"
		aria-label={$i18n.t('Operations center')}
	>
		{#each tabs as tab (tab.id)}
			<button
				class="whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition {active ===
				tab.id
					? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
					: 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}"
				type="button"
				role="tab"
				aria-selected={active === tab.id}
				on:click={(event) => selectTab(tab.id, event.currentTarget)}
			>
				{$i18n.t(tab.label)}
			</button>
		{/each}
	</div>

	<div class="min-h-0 flex-1 overflow-y-auto pb-4">
		{#if active === 'discovery'}
			{#if discoveryState.component}
				<svelte:component this={discoveryState.component} />
			{:else if discoveryState.error}
				<div
					class="flex h-40 flex-col items-center justify-center gap-3 px-4 text-center"
					role="alert"
				>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Failed to load operations section')}
					</p>
					<button
						type="button"
						class="min-h-11 rounded-xl bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 focus:outline-hidden focus:ring-2 focus:ring-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700"
						on:click={() => ensureLoaded('discovery')}>{$i18n.t('Retry')}</button
					>
				</div>
			{:else}
				<div class="flex h-32 items-center justify-center text-sm text-gray-400 dark:text-gray-500">
					<Loader />
				</div>
			{/if}
		{:else if active === 'categories'}
			{#if categoriesState.component}
				<svelte:component this={categoriesState.component} />
			{:else if categoriesState.error}
				<div
					class="flex h-40 flex-col items-center justify-center gap-3 px-4 text-center"
					role="alert"
				>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Failed to load operations section')}
					</p>
					<button
						type="button"
						class="min-h-11 rounded-xl bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 focus:outline-hidden focus:ring-2 focus:ring-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700"
						on:click={() => ensureLoaded('categories')}>{$i18n.t('Retry')}</button
					>
				</div>
			{:else}
				<div class="flex h-32 items-center justify-center text-sm text-gray-400 dark:text-gray-500">
					<Loader />
				</div>
			{/if}
		{:else if active === 'models'}
			{#if modelsState.component}
				<svelte:component this={modelsState.component} />
			{:else if modelsState.error}
				<div
					class="flex h-40 flex-col items-center justify-center gap-3 px-4 text-center"
					role="alert"
				>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Failed to load operations section')}
					</p>
					<button
						type="button"
						class="min-h-11 rounded-xl bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 focus:outline-hidden focus:ring-2 focus:ring-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700"
						on:click={() => ensureLoaded('models')}>{$i18n.t('Retry')}</button
					>
				</div>
			{:else}
				<div class="flex h-32 items-center justify-center text-sm text-gray-400 dark:text-gray-500">
					<Loader />
				</div>
			{/if}
		{:else if active === 'providers'}
			{#if providersState.component}
				<svelte:component this={providersState.component} />
			{:else if providersState.error}
				<div
					class="flex h-40 flex-col items-center justify-center gap-3 px-4 text-center"
					role="alert"
				>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{$i18n.t('Failed to load operations section')}
					</p>
					<button
						type="button"
						class="min-h-11 rounded-xl bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 focus:outline-hidden focus:ring-2 focus:ring-gray-400 dark:bg-gray-800 dark:hover:bg-gray-700"
						on:click={() => ensureLoaded('providers')}>{$i18n.t('Retry')}</button
					>
				</div>
			{:else}
				<div class="flex h-32 items-center justify-center text-sm text-gray-400 dark:text-gray-500">
					<Loader />
				</div>
			{/if}
		{/if}
	</div>
</div>
