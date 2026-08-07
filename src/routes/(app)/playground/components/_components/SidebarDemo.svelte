<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Sidebar from '$lib/components/common/Sidebar.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = true;
</script>

<DemoCard
	title="Sidebar"
	desc={$i18n.t('Slide-in sidebar from left/right. bind:show. Needs relative parent with height.')}>
	<div class="flex flex-col items-start gap-2 w-full">
		<button
			class="text-xs px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
			on:click={() => (show = !show)}
		>
			{show ? $i18n.t('Hide Sidebar') : $i18n.t('Show Sidebar')}
		</button>
		<!-- Sidebar 自身是 absolute，父容器必须 relative + 固定高度 -->
		<div class="relative h-40 w-full rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
			<Sidebar bind:show side="right" width="200px" duration={100}>
				<div class="p-3 text-sm text-gray-700 dark:text-gray-200">
					{$i18n.t('Sidebar content')}
				</div>
			</Sidebar>
			<div class="p-3 text-xs text-gray-400">{$i18n.t('Relative parent container')}</div>
		</div>
	</div>
</DemoCard>
