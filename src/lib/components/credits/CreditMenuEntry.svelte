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
	class="flex h-[1.6875rem] w-full cursor-pointer select-none items-center gap-2 rounded-xl px-2 text-left text-[13px] transition hover:bg-gray-50/40 dark:hover:bg-gray-800/40"
	type="button"
	on:click={() => dispatch('openLedger')}
>
	<div class="flex size-4.5 shrink-0 items-center justify-center self-center">
		<ChartBar className="size-3.5" strokeWidth="1.5" />
	</div>
	<div class="self-center min-w-0 flex-1 truncate">{$i18n.t('credits.balance')}</div>
	<div
		class="ml-auto shrink-0 text-[11px] leading-none text-gray-500 tabular-nums dark:text-gray-400"
	>
		{#if balanceState.status === 'ready'}
			{balanceState.balance}
		{:else if balanceState.status === 'loading'}
			{$i18n.t('credits.common.loading')}
		{:else if balanceState.status === 'unavailable'}
			{$i18n.t('credits.unavailable')}
		{/if}
	</div>
</button>
