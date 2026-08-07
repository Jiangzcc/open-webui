<script lang="ts">
	// 演示卡片：统一外壳，左侧标签 + 右侧交互区
	// 这样新增/修改组件时，每个 demo 只需关心它自己。
	export let title = '';
	export let desc = '';
</script>

<div
	class="flex flex-col gap-2 rounded-xl border border-gray-100 dark:border-gray-850 p-3 bg-white dark:bg-gray-900 min-h-[7rem]"
>
	<div class="flex flex-col">
		<span class="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</span>
		{#if desc}
			<span class="text-[11px] leading-tight text-gray-400 dark:text-gray-500">{desc}</span>
		{/if}
	</div>
	<div class="flex-1 flex items-center gap-2 flex-wrap pt-1">
		<slot />
	</div>
</div>
