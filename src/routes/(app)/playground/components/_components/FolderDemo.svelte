<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Folder from '$lib/components/common/Folder.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Folder: 可折叠的目录节点。
	// - collapsible 控制能否折叠（默认 true）
	// - onAdd 传入才显示 + 号新增按钮（需 onAddLabel 提示文案）
	// - localStorage 用 `${id}-folder-state` 持久化开合状态 → 演示用唯一 id
	// - dragAndDrop 支持拖入 JSON 文件（dispatch import/drop）
	let added = 0;
	const addOne = () => (added += 1);

	let lastEvent = '';
</script>

<DemoCard
	title="Folder"
	desc={$i18n.t('Collapsible folder node. + button (onAdd) dispatches import/drop on drag. State persisted to localStorage.')}
>
	<div class="w-full flex flex-col gap-1">
		<Folder
			id="pg-folder-collapsible"
			name={$i18n.t('Workspace') as any}
			collapsible
			onAddLabel={$i18n.t('New Folder')}
			onAdd={addOne}
		>
			<!-- 折叠展开后的内容插槽 -->
			<div class="ml-3 pl-2 border-l border-gray-100 dark:border-gray-850 flex flex-col gap-1 py-1">
				<span class="text-xs text-gray-500">item-1</span>
				<span class="text-xs text-gray-500">item-2</span>
				<span class="text-xs text-gray-500">item-3</span>
			</div>
		</Folder>

		<Folder
			id="pg-folder-static"
			name={$i18n.t('Pinned') as any}
			collapsible
			chevron
			dragAndDrop
			on:import={(e) => (lastEvent = 'import')}
			on:drop={(e) => (lastEvent = 'drop')}
		>
			<div class="ml-3 pl-2 border-l border-gray-100 dark:border-gray-850 text-xs text-gray-500 py-1">
				{$i18n.t('No items')}
			</div>
		</Folder>

		{#if added > 0}
			<p class="text-[11px] text-emerald-500">+ {$i18n.t('New Folder')} ×{added}</p>
		{/if}
		{#if lastEvent}
			<p class="text-[11px] text-gray-400">{$i18n.t('Dropped data is not valid JSON text or is empty. Ignoring drop event for this type of data.')} → {lastEvent}</p>
		{/if}
	</div>
</DemoCard>
