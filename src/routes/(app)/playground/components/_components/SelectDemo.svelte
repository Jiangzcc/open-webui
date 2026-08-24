<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Select from '$lib/components/common/Select.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// Select 是底层组件：trigger slot + 默认 slot（需调用 selectItem 才能选中）
	let value = 'a';
	const items = [
		{ value: 'a', label: 'Apple' },
		{ value: 'b', label: 'Banana' },
		{ value: 'c', label: 'Cherry' }
	];
</script>

<DemoCard
	title="Select"
	desc={$i18n.t('Custom dropdown base: trigger + content slots. Call selectItem(item) to select.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<div class="w-full">
			<Select
				bind:value
				{items}
				placeholder={$i18n.t('Pick one')}
				onChange={(v) => console.log('picked', v)}
				triggerClass="relative w-full flex items-center h-9 px-3 rounded-lg bg-gray-50 dark:bg-gray-850 text-sm outline-hidden"
				contentClass="min-w-[170px]"
				align="start"
				side="bottom"
			>
				<svelte:fragment slot="trigger" let:selectedLabel>
					<span class="truncate">{selectedLabel}</span>
				</svelte:fragment>
				<svelte:fragment let:selectItem>
					{#each items as item}
						<button
							class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 {value ===
							item.value
								? 'text-gray-900 dark:text-gray-100'
								: 'text-gray-500 dark:text-gray-400'}"
							type="button"
							on:click={() => selectItem(item)}
						>
							{item.label}
						</button>
					{/each}
				</svelte:fragment>
			</Select>
		</div>
		<span class="text-[11px] text-gray-400">value = {value}</span>
	</div>
</DemoCard>
