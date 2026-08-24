<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import PanzoomContainer from '$lib/components/common/PanzoomContainer.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// PanzoomContainer 导出 reset() 供 bind:this 调用。
	// 需要父容器给定 height，否则高度坍缩无法交互。
	let panzoom: PanzoomContainer;
	const reset = () => panzoom?.reset();
</script>

<DemoCard
	title="PanzoomContainer"
	desc={$i18n.t(
		'Generic pan/zoom wrapper. Drag to pan, wheel to zoom. Reset button calls reset().'
	)}
>
	<div
		class="w-full h-52 rounded-lg overflow-hidden border border-gray-100 dark:border-gray-850 bg-gray-50 dark:bg-gray-900 relative"
	>
		<!-- 这里放任意可缩放内容，演示用一张大图 -->
		<PanzoomContainer
			className="flex h-full max-h-full justify-center items-center z-0"
			bind:this={panzoom}
		>
			<img
				src="/assets/welcome.webp"
				alt="panzoom target"
				class="h-full object-contain select-none pointer-events-none"
				draggable="false"
			/>
		</PanzoomContainer>

		<!-- 重置按钮浮在右上，支持键盘 + 触屏 -->
		<button
			type="button"
			class="absolute top-2 right-2 z-10 text-xs px-2 py-1 rounded-lg bg-white/90 dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-gray-800 transition focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700"
			on:click={reset}
		>
			{$i18n.t('Reset')}
		</button>
	</div>
</DemoCard>
