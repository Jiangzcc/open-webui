<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Selector from '$lib/components/common/Selector.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// Selector 是基于 Select 的"选模型"成品组件，内置搜索 + 打勾
	let value = 'mango';
</script>

<DemoCard
	title="Selector"
	desc={$i18n.t(
		'Select-based picker with built-in search + checkmark. Default placeholder = Select a model.'
	)}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<div class="w-full">
			<Selector
				bind:value
				placeholder={$i18n.t('Select a model')}
				searchEnabled={true}
				searchPlaceholder={$i18n.t('Search a model')}
			/>
		</div>
		<span class="text-[11px] text-gray-400">value = {value}</span>
	</div>
</DemoCard>
