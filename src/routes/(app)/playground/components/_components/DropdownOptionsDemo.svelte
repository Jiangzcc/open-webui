<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import DropdownOptions from '$lib/components/common/DropdownOptions.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let value = 'new';
</script>

<DemoCard
	title="DropdownOptions"
	desc={$i18n.t('Select wrapper with ChevronDown. Default items: New / Top. bind:value, onChange.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<DropdownOptions
			bind:value
			items={[
				{ value: 'new', label: $i18n.t('New') },
				{ value: 'top', label: $i18n.t('Top') }
			]}
			placeholder={$i18n.t('Sort by')}
			align="center"
			className="flex h-8 items-center gap-1.5 rounded-xl bg-gray-50 dark:bg-gray-850 px-2 text-[13px] hover:bg-gray-100 dark:hover:bg-gray-800 transition"
			onChange={(v) => console.log('sort:', v)}
		/>
		<span class="text-[11px] text-gray-400">value = {value}</span>
	</div>
</DemoCard>
