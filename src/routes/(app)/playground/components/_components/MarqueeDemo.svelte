<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Marquee from '$lib/components/common/Marquee.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard
	title="Marquee"
	desc={$i18n.t(
		'Rotating words every duration ms, fly-in transition. Note: interval not cleared on destroy.'
	)}
>
	<div
		class="flex items-center h-6 px-3 rounded-lg bg-gray-50 dark:bg-gray-850 text-sm font-medium text-gray-700 dark:text-gray-200"
	>
		<Marquee
			className="text-sm"
			words={['New feature', 'Bug fixes', 'Release v1.0']}
			duration={3000}
		/>
	</div>
</DemoCard>
