<script lang="ts">
	import { mobile, showSidebar } from '$lib/stores';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();
</script>

<!-- 移动端页面顶部栏：仅承载侧栏开关（与发现页的内联实现一致）。
     桌面端不渲染——侧栏常驻，页面内容直接从顶部开始。 -->
{#if $mobile}
	<nav class="relative z-40 shrink-0 px-3 pb-2 pt-2 backdrop-blur-xl drag-region select-none">
		<div class="flex flex-none items-center">
			<Tooltip
				content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
				interactive={true}
			>
				<button
					id="sidebar-toggle-button"
					type="button"
					class="flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-lg transition hover:bg-gray-100 dark:hover:bg-gray-850"
					on:click={() => showSidebar.set(!$showSidebar)}
					aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
				>
					<div class="self-center">
						<SidebarIcon />
					</div>
				</button>
			</Tooltip>
		</div>
	</nav>
{/if}
