<script lang="ts">
	import { tick } from 'svelte';
	import CreditAccountsTab from '$lib/components/credits/admin/CreditAccountsTab.svelte';
	import CreditLedgerTab from '$lib/components/credits/admin/CreditLedgerTab.svelte';
	import CreditPricingTab from '$lib/components/credits/admin/CreditPricingTab.svelte';
	import CreditDimensionsTab from '$lib/components/credits/admin/CreditDimensionsTab.svelte';
	import CreditReconciliationTab from '$lib/components/credits/admin/CreditReconciliationTab.svelte';
	import CreditRedemptionTab from '$lib/components/credits/admin/CreditRedemptionTab.svelte';
	import { registerCreditTranslations } from '$lib/components/credits/credits-i18n';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();
	registerCreditTranslations(i18n);

	type CreditTab =
		| 'accounts'
		| 'ledger'
		| 'reconciliation'
		| 'redemption'
		| 'pricing'
		| 'dimensions';

	const tabs: Array<{ id: CreditTab; label: string }> = [
		{ id: 'accounts', label: 'credits.admin.accounts' },
		{ id: 'ledger', label: 'credits.ledger' },
		{ id: 'reconciliation', label: 'credits.admin.reconciliation' },
		{ id: 'redemption', label: 'credits.admin.redeemCodes' },
		{ id: 'pricing', label: 'credits.prices' },
		{ id: 'dimensions', label: 'credits.dimensions' }
	];

	let selectedTab: CreditTab = 'accounts';

	const handleTabKeydown = async (event: KeyboardEvent, index: number) => {
		let nextIndex: number | null = null;
		if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
		if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
		if (event.key === 'Home') nextIndex = 0;
		if (event.key === 'End') nextIndex = tabs.length - 1;
		if (nextIndex === null) return;
		event.preventDefault();
		selectedTab = tabs[nextIndex].id;
		await tick();
		document.getElementById(`credit-tab-${selectedTab}`)?.focus();
	};
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

	<div
		class="flex gap-1 overflow-x-auto border-b border-gray-100 dark:border-gray-800"
		role="tablist"
		aria-label={$i18n.t('credits.admin.management')}
	>
		{#each tabs as tab, index (tab.id)}
			<button
				class="whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition {selectedTab ===
				tab.id
					? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
					: 'border-transparent text-gray-500 hover:text-gray-900 dark:hover:text-gray-100'}"
				on:click={() => {
					selectedTab = tab.id;
				}}
				type="button"
				role="tab"
				aria-selected={selectedTab === tab.id}
				aria-controls={`credit-tab-panel-${tab.id}`}
				id={`credit-tab-${tab.id}`}
				tabindex={selectedTab === tab.id ? 0 : -1}
				on:keydown={(event) => handleTabKeydown(event, index)}
			>
				{$i18n.t(tab.label)}
			</button>
		{/each}
	</div>

	<div
		class="min-h-0 flex-1 overflow-y-auto pb-4"
		role="tabpanel"
		id={`credit-tab-panel-${selectedTab}`}
		aria-labelledby={`credit-tab-${selectedTab}`}
	>
		{#if selectedTab === 'accounts'}
			<CreditAccountsTab />
		{:else if selectedTab === 'ledger'}
			<CreditLedgerTab />
		{:else if selectedTab === 'reconciliation'}
			<CreditReconciliationTab />
		{:else if selectedTab === 'redemption'}
			<CreditRedemptionTab />
		{:else if selectedTab === 'pricing'}
			<CreditPricingTab />
		{:else if selectedTab === 'dimensions'}
			<CreditDimensionsTab />
		{/if}
	</div>
</div>
