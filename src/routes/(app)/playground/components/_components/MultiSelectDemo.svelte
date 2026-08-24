<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import MultiSelect from '$lib/components/common/MultiSelect.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// value 必须是数组；on:change 无 payload，读 bind:value
	let selected: string[] = ['a'];
</script>

<DemoCard
	title="MultiSelect"
	desc={$i18n.t(
		'Multi-select dropdown. value is string[]. on:change has no payload, read bind:value.'
	)}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<MultiSelect
			bind:value={selected}
			options={[{ value: 'a', label: 'Apple' }, { value: 'b', label: 'Banana' }, 'cherry']}
			placeholder={$i18n.t('Pick many')}
			className="w-full h-9 flex items-center gap-2 rounded-lg px-3 text-sm bg-gray-50 dark:bg-gray-850 outline-hidden"
			on:change={() => console.log('changed', selected)}
		/>
		<span class="text-[11px] text-gray-400">value = [{selected.join(', ')}]</span>
	</div>
</DemoCard>
