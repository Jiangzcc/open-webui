<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Drawer from '$lib/components/common/Drawer.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = false;
</script>

<DemoCard
	title="Drawer"
	desc={$i18n.t('Bottom-sheet drawer. bind:show. Esc / backdrop click closes. Mobile-friendly.')}>
	<button
		class="text-xs px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
		on:click={() => (show = true)}
	>
		{$i18n.t('Open Drawer')}
	</button>
	<Drawer bind:show={show} onClose={() => console.log('closed')}>
		<div class="p-4">
			<h3 class="text-lg font-medium mb-2 text-gray-900 dark:text-gray-100">
				{$i18n.t('Drawer')}
			</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t('Slides up from the bottom.')}
			</p>
			<button
				class="px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition text-sm"
				on:click={() => (show = false)}
			>
				{$i18n.t('Close')}
			</button>
		</div>
	</Drawer>
</DemoCard>
