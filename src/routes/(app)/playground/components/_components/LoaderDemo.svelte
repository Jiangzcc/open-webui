<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Loader from '$lib/components/common/Loader.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let triggerCount = 0;
	// 让 loader 始终在容器内可见，避免它撑满整页
</script>

<DemoCard
	title="Loader"
	desc={$i18n.t('IntersectionObserver: dispatches "visible" every 100ms while in viewport.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<div
			class="relative h-16 w-full overflow-y-auto rounded-lg border border-dashed border-gray-200 dark:border-gray-700"
		>
			<!-- 填充占位让 loader 在底部，滚动到底部才会触发 -->
			<div class="h-40 flex items-center justify-center text-[11px] text-gray-400">
				{$i18n.t('Scroll down inside this box')}
			</div>
			<Loader on:visible={() => (triggerCount += 1)}>
				<div class="py-1 text-center text-[11px] text-blue-500">
					↓ {$i18n.t('Load more')}
				</div>
			</Loader>
		</div>
		<span class="text-[11px] text-gray-400">
			{$i18n.t('visible fired')}: {triggerCount}
			{$i18n.t('times')}
		</span>
	</div>
</DemoCard>
