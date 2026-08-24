<script lang="ts">
	import { onDestroy, onMount } from 'svelte';

	import { getAdminCreditAccounts, type CreditAccount } from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import AdjustCreditsModal from './AdjustCreditsModal.svelte';
	import RepairAccountModal from './RepairAccountModal.svelte';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();
	const pageSize = 25;

	let accounts: CreditAccount[] = [];
	let total = 0;
	let query = '';
	let page = 1;
	let loading = true;
	let error = '';
	let selectedAccount: CreditAccount | null = null;
	let showAdjustment = false;
	let showRepair = false;
	let searchTimer: ReturnType<typeof setTimeout>;
	let mounted = false;

	const loadAccounts = async () => {
		loading = true;
		error = '';
		try {
			const result = await getAdminCreditAccounts(localStorage.token, {
				query: query.trim() || undefined,
				skip: (page - 1) * pageSize,
				limit: pageSize
			});
			accounts = result.items;
			total = result.total;
		} catch (requestError) {
			accounts = [];
			total = 0;
			error = translateCreditApiError($i18n, requestError, 'credits.admin.accountsLoadError');
		} finally {
			loading = false;
		}
	};

	const handleSearch = () => {
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			if (page === 1) {
				loadAccounts();
			} else {
				page = 1;
			}
		}, 300);
	};

	const openAdjustment = (account: CreditAccount) => {
		selectedAccount = account;
		showAdjustment = true;
	};

	const openRepair = (account: CreditAccount) => {
		selectedAccount = account;
		showRepair = true;
	};

	$: if (mounted && page > 0) {
		loadAccounts();
	}

	onMount(() => {
		mounted = true;
	});
	onDestroy(() => clearTimeout(searchTimer));
</script>

<AdjustCreditsModal
	bind:show={showAdjustment}
	account={selectedAccount}
	onAdjusted={() => {
		loadAccounts();
	}}
/>

<RepairAccountModal
	bind:show={showRepair}
	account={selectedAccount}
	onRepaired={() => {
		loadAccounts();
	}}
/>

<div class="flex h-full flex-col gap-4">
	<div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
		<div>
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.accountsTitle')}
			</h2>
			<p class="mt-1 text-sm text-gray-500">
				{$i18n.t('credits.admin.accountsDescription')}
			</p>
		</div>
		<input
			class="w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden sm:max-w-xs dark:border-gray-700"
			bind:value={query}
			placeholder={$i18n.t('credits.admin.accountsSearch')}
			on:input={handleSearch}
		/>
	</div>

	{#if error}
		<div
			class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
		>
			{error}
			<button class="ml-2 underline" on:click={loadAccounts} type="button"
				>{$i18n.t('credits.common.retry')}</button
			>
		</div>
	{/if}

	{#if loading}
		<div class="flex flex-1 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if accounts.length === 0}
		<div
			class="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-700"
		>
			{$i18n.t('credits.admin.accountsEmpty')}
		</div>
	{:else}
		<div class="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
			<table class="w-full text-left text-sm">
				<thead class="border-b border-gray-100 text-xs text-gray-500 dark:border-gray-800">
					<tr>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.user')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.balance')}</th>
						<th class="px-4 py-3 font-medium"
							><span class="sr-only">{$i18n.t('credits.common.actions')}</span></th
						>
					</tr>
				</thead>
				<tbody>
					{#each accounts as account (account.user_id)}
						<tr class="border-b border-gray-50 last:border-0 dark:border-gray-850">
							<td class="px-4 py-3">
								<div class="font-medium dark:text-gray-100">
									{account.name ?? $i18n.t('credits.common.deletedUser')}
								</div>
								<div class="mt-0.5 text-xs text-gray-500">{account.email ?? account.user_id}</div>
							</td>
							<td class="px-4 py-3 font-medium tabular-nums dark:text-gray-100"
								>{account.balance}</td
							>
							<td class="px-4 py-3 text-right">
								<div class="flex flex-wrap justify-end gap-2">
									<button
										class="rounded-3xl bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
										on:click={() => openAdjustment(account)}
										type="button"
									>
										{$i18n.t('credits.admin.adjust')}
									</button>
									<button
										class="rounded-3xl border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
										on:click={() => openRepair(account)}
										type="button"
									>
										{$i18n.t('credits.admin.repair.button')}
									</button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		{#if total > pageSize}
			<div class="flex justify-end"><Pagination bind:page count={total} perPage={pageSize} /></div>
		{/if}
	{/if}
</div>
