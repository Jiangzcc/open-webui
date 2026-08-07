<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import AccessButton from '$lib/components/common/AccessButton.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard title="AccessButton" desc={$i18n.t('Small access entry button with lock icon. Forwards on:click.')}>
	<div class="flex flex-col items-start gap-2">
		<AccessButton className="" disabled={false} on:click={() => console.log('access')} />
		<AccessButton className="" disabled={true} on:click={() => console.log('access')} />
	</div>
</DemoCard>
