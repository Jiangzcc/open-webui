<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { user } from '$lib/stores';

	// DEV 门控（复盘 #12）：48 个演示组件只允许出现在开发构建中。
	// 生产构建里 import.meta.env.DEV 被静态替换为 false，下方分支恒为
	// goto+return，Demos 的动态 import 成为不可达代码而被 Rollup 消除，
	// 演示 chunk 不进入产物。管理员守卫同页生效。
	let Demos: typeof import('./Demos.svelte').default | null = null;

	onMount(async () => {
		if (!import.meta.env.DEV || $user?.role !== 'admin') {
			await goto('/', { replaceState: true });
			return;
		}
		Demos = (await import('./Demos.svelte')).default;
	});
</script>

{#if Demos}
	<Demos />
{/if}
