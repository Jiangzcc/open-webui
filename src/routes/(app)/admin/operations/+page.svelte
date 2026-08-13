<script lang="ts">
	import { getContext } from 'svelte';

	import DiscoveryOperations from '$lib/components/discovery/admin/DiscoveryOperations.svelte';
	import DiscoveryCategories from '$lib/components/discovery/admin/DiscoveryCategories.svelte';
	import ImageModelOperations from '$lib/components/model-ops/admin/ImageModelOperations.svelte';
	import ProviderOperations from '$lib/components/provider-ops/admin/ProviderOperations.svelte';

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
			<DiscoveryOperations />
		{:else if active === 'categories'}
			<DiscoveryCategories />
		{:else if active === 'models'}
			<ImageModelOperations />
		{:else if active === 'providers'}
			<ProviderOperations />
		{/if}
	</div>
</div>
