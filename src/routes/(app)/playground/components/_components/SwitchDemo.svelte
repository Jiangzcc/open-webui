<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Switch from '$lib/components/common/Switch.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// state 是布尔，bind:state 双向
	let enabled = true;
</script>

<DemoCard
	title="Switch"
	desc={$i18n.t('Boolean toggle, bits-ui based. bind:state, on:change dispatches boolean.')}
>
	<div class="flex flex-col items-start gap-3">
		<label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
			<Switch
				bind:state={enabled}
				id="opt-1"
				ariaLabel="Enable feature"
				tooltip={true}
				on:change={(e) => console.log('change:', e.detail)}
			/>
			{$i18n.t('Enable feature')}
		</label>
		<span class="text-[11px] text-gray-400">state = {enabled}</span>
	</div>
</DemoCard>
