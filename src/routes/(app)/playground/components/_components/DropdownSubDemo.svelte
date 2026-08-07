<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import DropdownSub from '$lib/components/common/DropdownSub.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard
	title="DropdownSub"
	desc={$i18n.t('Nested submenu. Hover / Enter / ArrowRight to open. No show prop, self-managed.')}>
	<div class="w-full">
		<DropdownSub
			contentClass="rounded-2xl p-1 bg-white dark:bg-gray-850 shadow-lg border border-gray-100 dark:border-gray-800"
			maxWidth={200}
			sideOffset={8}
		>
			<button
				slot="trigger"
				class="block w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
			>
				{$i18n.t('More')} ▸
			</button>
			<button
				class="block w-full text-left px-2 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
			>
				{$i18n.t('Sub Item')} 1
			</button>
			<button
				class="block w-full text-left px-2 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
			>
				{$i18n.t('Sub Item')} 2
			</button>
		</DropdownSub>
	</div>
</DemoCard>
