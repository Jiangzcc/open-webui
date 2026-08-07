<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import SettingsSelect from '$lib/components/common/SettingsSelect.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let theme = 'light';
</script>

<DemoCard
	title="SettingsSelect"
	desc={$i18n.t('Native <select> for settings pages. Provide <option> via slot. No custom arrow.')}>
	<div class="flex flex-col items-start gap-2 w-full">
		<SettingsSelect
			bind:value={theme}
			placeholder={$i18n.t('Sort by')}
			className="w-full max-w-full"
		>
			<option value="light">{$i18n.t('Light')}</option>
			<option value="dark">{$i18n.t('Dark')}</option>
			<option value="system">{$i18n.t('System')}</option>
		</SettingsSelect>
		<span class="text-[11px] text-gray-400">value = {theme}</span>
	</div>
</DemoCard>
