<script lang="ts">
	import { tick } from 'svelte';
	import { mobile, showSidebar } from '$lib/stores';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { getI18nContext } from '$lib/i18n/context';

	type Selection = 'generate' | 'mine' | 'all';
	type Tab = { id: Selection; elementId: string; panelId: string; label: string };

	const i18n = getI18nContext();

	export let selection: Selection;
	export let isAdmin: boolean;
	export let pageLabel: string;
	export let tabs: readonly Tab[];
	export let onSelect: (selection: Selection) => void | Promise<void>;

	$: visibleTabs = tabs.filter((tab) => tab.id !== 'all' || isAdmin);

	const handleKeydown = async (event: KeyboardEvent) => {
		if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
		event.preventDefault();
		const index = visibleTabs.findIndex((tab) => tab.id === selection);
		if (index < 0) return;
		const direction = event.key === 'ArrowRight' ? 1 : -1;
		const next = visibleTabs[(index + direction + visibleTabs.length) % visibleTabs.length];
		await onSelect(next.id);
		await tick();
		document.getElementById(next.elementId)?.focus();
	};
</script>

{#snippet pageTabs()}
	<div
		class="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-gray-200/80 bg-white/80 p-1 shadow-lg shadow-black/10 backdrop-blur-xl dark:border-gray-700/80 dark:bg-gray-900/80 dark:shadow-black/30"
		role="tablist"
		tabindex="-1"
		aria-label={$i18n.t(pageLabel)}
		on:keydown={handleKeydown}
	>
		{#each visibleTabs as tab}
			<button
				id={tab.elementId}
				type="button"
				role="tab"
				aria-selected={selection === tab.id}
				aria-controls={tab.panelId}
				tabindex={selection === tab.id ? 0 : -1}
				class="min-h-11 shrink-0 whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-medium transition-all focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 sm:min-h-10 {selection ===
				tab.id
					? 'bg-gray-900 text-white shadow-sm dark:bg-white dark:text-gray-900'
					: 'text-gray-500 hover:bg-gray-100/80 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100'}"
				on:click={() => onSelect(tab.id)}
			>
				{$i18n.t(tab.label)}
			</button>
		{/each}
	</div>
{/snippet}

{#if $mobile}
	<nav
		class="relative z-40 flex h-14 shrink-0 items-center px-3 backdrop-blur-xl drag-region select-none"
	>
		<div class="relative z-10 flex flex-none items-center">
			<Tooltip
				content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
				interactive={true}
			>
				<button
					id="sidebar-toggle-button"
					type="button"
					class="flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-lg transition hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:hover:bg-gray-850"
					on:click={() => showSidebar.set(!$showSidebar)}
					aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
				>
					<SidebarIcon />
				</button>
			</Tooltip>
		</div>
		<div
			class="pointer-events-none absolute inset-y-0 left-0 right-0 flex items-center justify-center"
		>
			{@render pageTabs()}
		</div>
	</nav>
{:else}
	<div class="pointer-events-none absolute inset-x-0 top-0 z-30 flex justify-center px-3 pt-2">
		{@render pageTabs()}
	</div>
{/if}
