<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Collapsible from '$lib/components/common/Collapsible.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let open = true;
</script>

<DemoCard
	title="Collapsible"
	desc={$i18n.t('Fold/unfold container. bind:open. title → button; null title → slot + pointerup.')}
>
	<div class="w-full">
		<Collapsible
			bind:open
			title={$i18n.t('Reasoning') as any}
			onChange={(s: boolean) => console.log('open:', s)}
		>
			<svelte:fragment slot="content">
				<div class="p-2 text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('Folded content lives here.')}
				</div>
			</svelte:fragment>
		</Collapsible>
	</div>
</DemoCard>
