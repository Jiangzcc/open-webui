<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = false;
	let lastResult = '';
</script>

<DemoCard
	title="ConfirmDialog"
	desc={$i18n.t(
		'Confirm with markdown message + optional input. onConfirm prop, on:confirm event.'
	)}
>
	<button
		class="text-xs px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
		on:click={() => (show = true)}
	>
		{$i18n.t('Open Confirm')}
	</button>
	<ConfirmDialog
		bind:show
		title={$i18n.t('Delete file?')}
		message={$i18n.t('This action cannot be undone. Do you wish to continue?')}
		confirmLabel={$i18n.t('Delete')}
		cancelLabel={$i18n.t('Cancel')}
		onConfirm={async () => {
			lastResult = 'confirmed';
			console.log('confirmed');
		}}
		on:cancel={() => {
			lastResult = 'cancelled';
		}}
	/>
	{#if lastResult}
		<span class="text-[11px] text-gray-400">last: {lastResult}</span>
	{/if}
</DemoCard>
