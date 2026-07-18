<script lang="ts">
	import { createEventDispatcher, getContext, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import { getMyCredits } from '$lib/apis/credits';
	import { registerCreditTranslations } from '$lib/components/credits/credits-i18n';
	import ChartBar from '$lib/components/icons/ChartBar.svelte';

	import {
		idleCreditBalanceState,
		shouldRefreshCreditBalance,
		unavailableCreditBalanceState,
		type CreditBalanceState
	} from './credit-ledger-state';

	const i18n = getContext<Writable<I18n>>('i18n');
	registerCreditTranslations($i18n);

	export let dropdownOpen = false;
	export let refreshKey = 0;

	const dispatch = createEventDispatcher<{ openLedger: void }>();

	let balanceState: CreditBalanceState = idleCreditBalanceState();
	let wasOpen = false;
	let loadedRefreshKey = refreshKey;
	let requestController: AbortController | null = null;

	const refreshBalance = async () => {
		requestController?.abort();
		requestController = new AbortController();
		balanceState = { status: 'loading', balance: null };

		try {
			const { balance } = await getMyCredits(localStorage.token, requestController.signal);
			balanceState = { status: 'ready', balance };
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') return;
			balanceState = unavailableCreditBalanceState(balanceState);
		}
	};

	$: if (
		shouldRefreshCreditBalance(wasOpen, dropdownOpen) ||
		(dropdownOpen && refreshKey !== loadedRefreshKey)
	) {
		loadedRefreshKey = refreshKey;
		refreshBalance();
	}

	$: wasOpen = dropdownOpen;

	onDestroy(() => requestController?.abort());
</script>

<button
	class="flex w-full cursor-pointer select-none rounded-xl px-3 py-1.5 text-left transition hover:bg-gray-50 dark:hover:bg-gray-800"
	type="button"
	on:click={() => dispatch('openLedger')}
>
	<div class="mr-3 self-center">
		<ChartBar className="size-5" strokeWidth="1.5" />
	</div>
	<div class="flex min-w-0 flex-1 items-center justify-between gap-2">
		<div class="truncate">{$i18n.t('credits.balance')}</div>
		{#if balanceState.status === 'ready'}
			<div class="shrink-0 font-medium tabular-nums">{balanceState.balance}</div>
		{:else if balanceState.status === 'loading'}
			<div class="shrink-0 text-xs text-gray-500">{$i18n.t('credits.common.loading')}</div>
		{:else if balanceState.status === 'unavailable'}
			<div class="shrink-0 text-xs text-gray-500">{$i18n.t('credits.unavailable')}</div>
		{/if}
	</div>
</button>
