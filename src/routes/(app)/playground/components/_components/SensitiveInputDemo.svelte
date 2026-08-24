<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let apiKey = '';
</script>

<DemoCard
	title="SensitiveInput"
	desc={$i18n.t('Password input with show/hide. variant: plain | settings. type: text | password.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<div class="w-full">
			<SensitiveInput
				bind:value={apiKey}
				type="password"
				placeholder={$i18n.t('API Key')}
				required={true}
				variant="settings"
				autocomplete="off"
				outerClassName="flex flex-1"
			/>
		</div>
		<span class="text-[11px] text-gray-400">{$i18n.t('Value')}: {apiKey ? '••••' : '—'}</span>
	</div>
</DemoCard>
