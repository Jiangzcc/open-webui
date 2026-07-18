<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import { registerCreditTranslations } from './credits-i18n';
	import type { ImageQuoteState } from './quote-state';

	export let quoteState: ImageQuoteState = { status: 'loading' };

	const i18n = getContext<Writable<I18n>>('i18n');
	registerCreditTranslations($i18n);

	$: status = quoteState.status;
	$: chargedCredits = quoteState.chargedCredits;
</script>

<div
	class="min-w-0 text-xs font-medium text-gray-500 dark:text-gray-400"
	data-credit-quote-status={status}
	aria-live="polite"
>
	{#if status === 'ready'}
		<span class="sm:hidden">{chargedCredits} {$i18n.t('credits.common.unit')}</span>
		<span class="hidden sm:inline"
			>{$i18n.t('credits.quote')}: {chargedCredits} {$i18n.t('credits.common.unit')}</span
		>
		<span class="sr-only">{$i18n.t('credits.quote')}</span>
	{:else if status === 'insufficient'}
		<span class="text-red-600 dark:text-red-400">{$i18n.t('credits.insufficient')}</span>
	{:else if status === 'unconfigured'}
		<span>{$i18n.t('credits.unconfigured')}</span>
	{:else if status === 'error'}
		<span>{$i18n.t('credits.unavailable')}</span>
	{:else if status === 'exempt'}
		<span class="text-emerald-600 dark:text-emerald-400">{$i18n.t('credits.exempt')}</span>
	{/if}
</div>
