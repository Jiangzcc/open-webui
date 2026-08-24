<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import DragGhost from '$lib/components/common/DragGhost.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// DragGhost: portal 到 body 的浮层，跟手指/指针走（x, y）。
	// onMount 会锁 body overflow；故只在"拖动中"渲染，松手即销毁恢复。
	let dragging = false;
	let x = 0;
	let y = 0;

	const start = () => {
		dragging = true;
	};
	const move = (e: PointerEvent) => {
		if (!dragging) return;
		x = e.clientX;
		y = e.clientY;
	};
	const end = () => {
		dragging = false;
		x = 0;
		y = 0;
	};
</script>

<svelte:window on:pointermove={move} on:pointerup={end} on:pointercancel={end} />

<DemoCard
	title="DragGhost"
	desc={$i18n.t(
		'Pointer-following ghost layer. Press and drag the box. Portal to body while active.'
	)}
>
	<div
		role="button"
		tabindex="0"
		class="w-24 h-16 rounded-xl bg-indigo-500 text-white flex items-center justify-center text-xs cursor-grab active:cursor-grabbing select-none touch-none focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700"
		on:pointerdown={start}
		on:keydown={(e) => e.key === 'Enter' && start()}
		aria-pressed={dragging}
	>
		{$i18n.t('Drag me')}
	</div>
</DemoCard>

{#if dragging}
	<!-- 锁定期间显示一个跟手的小卡片，作为被拖"幽灵" -->
	<DragGhost {x} {y}>
		<div
			class="px-3 py-2 rounded-lg bg-gray-900/90 text-white text-xs shadow-lg border border-white/10"
		>
			ghost 👻
		</div>
	</DragGhost>
{/if}
