<script lang="ts">
	import { getContext } from 'svelte';
	import CreditAccountsTab from '$lib/components/credits/admin/CreditAccountsTab.svelte';
	import CreditLedgerTab from '$lib/components/credits/admin/CreditLedgerTab.svelte';
	import CreditPricingTab from '$lib/components/credits/admin/CreditPricingTab.svelte';
	import CreditDimensionsTab from '$lib/components/credits/admin/CreditDimensionsTab.svelte';
	import CreditReconciliationTab from '$lib/components/credits/admin/CreditReconciliationTab.svelte';
	import { registerCreditTranslations } from '$lib/components/credits/credits-i18n';

	const i18n = getContext('i18n');
	registerCreditTranslations(i18n);

	type CreditTab = 'accounts' | 'ledger' | 'reconciliation' | 'pricing' | 'dimensions';

	const tabs: Array<{ id: CreditTab; label: string }> = [
		{ id: 'accounts', label: 'credits.admin.accounts' },
		{ id: 'ledger', label: 'credits.ledger' },
		{ id: 'reconciliation', label: 'credits.admin.reconciliation' },
		{ id: 'pricing', label: 'credits.prices' },
		{ id: 'dimensions', label: 'credits.dimensions' }
	];

	let selectedTab: CreditTab = 'accounts';
</script>

<svelte:head>
	<title>{$i18n.t('credits.admin.management')}</title>
</svelte:head>

<div class="flex h-full flex-col gap-5 px-4 py-3 lg:px-6">
	<div>
		<h1 class="text-xl font-medium dark:text-gray-100">{$i18n.t('credits.admin.management')}</h1>
		<p class="mt-1 text-sm text-gray-500">
			{$i18n.t('credits.admin.description')}
		</p>
	</div>

	<div class="flex gap-1 overflow-x-auto border-b border-gray-100 dark:border-gray-800">
		{#each tabs as tab (tab.id)}
			<button
				class="whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition {selectedTab ===
				tab.id
					? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
					: 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}"
				on:click={() => {
					selectedTab = tab.id;
				}}
				type="button"
			>
				{$i18n.t(tab.label)}
			</button>
		{/each}
	</div>

	<div class="min-h-0 flex-1 overflow-y-auto pb-4">
		{#if selectedTab === 'accounts'}
			<CreditAccountsTab />
		{:else if selectedTab === 'ledger'}
			<CreditLedgerTab />
		{:else if selectedTab === 'reconciliation'}
			<CreditReconciliationTab />
		{:else if selectedTab === 'pricing'}
			<CreditPricingTab />
		{:else if selectedTab === 'dimensions'}
			<CreditDimensionsTab />
		{/if}
	</div>
</div>
