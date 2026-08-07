<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Badge from '$lib/components/common/Badge.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard title="Badge" desc={$i18n.t('Status tags: info / success / warning / error / muted.')}>
	<div class="flex flex-col items-start gap-2">
		<div class="flex flex-wrap gap-1.5">
			<Badge type="info" content="Info" />
			<Badge type="success" content="Success" />
			<Badge type="warning" content="Warning" />
			<Badge type="error" content="Error" />
			<Badge type="muted" content="Muted" />
		</div>
		<span class="text-[11px] text-gray-400">{$i18n.t('type → color, content → text')}</span>
	</div>
</DemoCard>
