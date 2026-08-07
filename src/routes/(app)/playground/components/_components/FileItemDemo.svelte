<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import FileItem from '$lib/components/common/FileItem.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// FileItem 不传 url/item 即为纯展示态：显示图标 + 名称 + 类型 + 大小。
	// 传 dismissible 才出叉号，dispatch('dismiss')。
	let dismissed: string[] = [];
</script>

<DemoCard
	title="FileItem"
	desc={$i18n.t('File/list row: icon + name + type + size. Optional dismiss button.')}
>
	<div class="flex flex-col gap-2 w-full">
		<FileItem
			name="welcome.webp"
			type="file"
			size={244000}
			colorClassName="bg-indigo-50 dark:bg-indigo-900/30"
			className="w-full"
			dismissible
			on:dismiss={() => dismissed.push('welcome.webp')}
		/>
		<FileItem
			name="README.md"
			type="note"
			size={5120}
			colorClassName="bg-emerald-50 dark:bg-emerald-900/30"
			className="w-full"
		/>
		<FileItem
			name="project-plan.doc"
			type="doc"
			size={81920}
			colorClassName="bg-amber-50 dark:bg-amber-900/30"
			className="w-full"
			small
		/>
		<FileItem
			name="My Collection"
			type="collection"
			size={0}
			colorClassName="bg-rose-50 dark:bg-rose-900/30"
			className="w-full"
		/>
		{#if dismissed.length > 0}
			<p class="text-[11px] text-gray-400">{$i18n.t('Dismissed')}: {dismissed.join(', ')}</p>
		{/if}
	</div>
</DemoCard>
