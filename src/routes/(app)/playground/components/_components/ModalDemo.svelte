<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Modal from '$lib/components/common/Modal.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = false;
</script>

<DemoCard
	title="Modal"
	desc={$i18n.t('Centered modal with focus-trap. bind:show. Escape / backdrop click to close.')}
>
	<button
		class="text-xs px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
		on:click={() => (show = true)}
	>
		{$i18n.t('Open Modal')}
	</button>
	<Modal bind:show size="md" className="bg-white dark:bg-gray-900 rounded-3xl">
		<div class="p-6">
			<h3 class="text-lg font-medium mb-2 text-gray-900 dark:text-gray-100">
				{$i18n.t('Modal Title')}
			</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
				{$i18n.t('Modal content goes here.')}
			</p>
			<button
				class="mt-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition text-sm"
				on:click={() => (show = false)}
			>
				{$i18n.t('Close')}
			</button>
		</div>
	</Modal>
</DemoCard>
