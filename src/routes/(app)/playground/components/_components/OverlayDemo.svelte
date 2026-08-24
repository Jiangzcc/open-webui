<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Overlay from '$lib/components/common/Overlay.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = false;
</script>

<DemoCard
	title="Overlay"
	desc={$i18n.t('Absolute blur overlay over a relative parent. Needs positioned parent + height.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<button
			class="text-xs px-2.5 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
			on:click={() => (show = !show)}
		>
			{show ? $i18n.t('Hide Overlay') : $i18n.t('Show Overlay')}
		</button>
		<div
			class="relative h-28 w-full rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden"
		>
			<Overlay {show} content={$i18n.t('Loading')} opacity={1}>
				<div class="p-3 text-xs text-gray-500">
					{$i18n.t('Underlying content here.')}
				</div>
			</Overlay>
		</div>
	</div>
</DemoCard>
