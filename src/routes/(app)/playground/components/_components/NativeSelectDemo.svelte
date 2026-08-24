<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import NativeSelect from '$lib/components/common/NativeSelect.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let value = 'a';
</script>

<DemoCard
	title="NativeSelect"
	desc={$i18n.t(
		'Thin native <select> + custom arrow. options array or slot. bind:value, on:change.'
	)}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<NativeSelect
			bind:value
			placeholder={$i18n.t('Pick one')}
			className="w-full rounded-lg py-2 px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-hidden"
			options={[{ value: 'a', label: 'Apple' }, { value: 'b', label: 'Banana' }, 'cherry']}
			on:change={() => console.log('changed')}
		/>
		<span class="text-[11px] text-gray-400">value = {value}</span>
	</div>
</DemoCard>
