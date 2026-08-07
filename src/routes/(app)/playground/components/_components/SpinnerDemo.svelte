<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard title="Spinner" desc={$i18n.t('Loading spinner, size via className, color via text-*')}>
	<div class="flex items-center gap-4">
		<div class="flex flex-col items-center gap-1">
			<Spinner className="size-4 text-blue-500" />
			<span class="text-[11px] text-gray-400">size-4</span>
		</div>
		<div class="flex flex-col items-center gap-1">
			<Spinner className="size-6 text-gray-700 dark:text-gray-300" />
			<span class="text-[11px] text-gray-400">size-6</span>
		</div>
		<div class="flex flex-col items-center gap-1">
			<Spinner className="size-8 text-green-500" />
			<span class="text-[11px] text-gray-400">size-8</span>
		</div>
	</div>
</DemoCard>
