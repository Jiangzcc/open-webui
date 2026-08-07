<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// 注意：state 是 'unchecked' | 'checked' 字符串，不是布尔
	let state = 'unchecked';
</script>

<DemoCard
	title="Checkbox"
	desc={$i18n.t("state is 'unchecked'/'checked' string, not boolean. indeterminate for half-check.")}
>
	<div class="flex flex-col items-start gap-3">
		<label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
			<Checkbox
				bind:state
				indeterminate={false}
				ariaLabel="Agree to terms"
				on:change={(e) => console.log('change:', e.detail)}
			/>
			{$i18n.t('Toggle')}
		</label>
		<span class="text-[11px] text-gray-400">state = {state}</span>

		<label class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-200">
			<!-- 半选演示：indeterminate 常驻 -->
			<Checkbox state="unchecked" indeterminate={true} ariaLabel="Half" />
			{$i18n.t('Indeterminate')}
		</label>
	</div>
</DemoCard>
