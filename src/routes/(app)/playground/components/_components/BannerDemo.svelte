<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Banner from '$lib/components/common/Banner.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Banner: 顶部横幅，content 走 markdown（marked + DOMPurify）。
	// type: info/success/warning/error，决定配色 chip。
	// url 存在时整条可点击跳转（这里用 # 避免真跳走）。
	// dismissed=true 父控制隐藏；点叉号 dispatch('dismiss', id)。
	const now = Math.floor(Date.now() / 1000);
	let dismissedIds: string[] = [];

	const banners = [
		{
			id: 'b-info',
			type: 'info',
			title: 'Info',
			content: '这是一条 **信息** 横幅，支持 Markdown。',
			url: '',
			dismissible: true,
			timestamp: now
		},
		{
			id: 'b-success',
			type: 'success',
			title: 'OK',
			content: '操作**成功**完成。',
			url: '',
			dismissible: true,
			timestamp: now
		},
		{
			id: 'b-warning',
			type: 'warning',
			title: 'Warn',
			content: '请注意：该功能为*演示*用途。',
			url: '',
			dismissible: true,
			timestamp: now
		},
		{
			id: 'b-error',
			type: 'error',
			title: 'Error',
			content: '发生错误，请检查后重试。',
			url: '',
			dismissible: true,
			timestamp: now
		},
		{
			id: 'b-link',
			type: 'info',
			title: 'Link',
			content: '带链接的横幅，点击可跳转。',
			url: '#section-overlays',
			dismissible: true,
			timestamp: now
		}
	];

	$: visible = banners.filter((b) => !dismissedIds.includes(b.id));
</script>

<DemoCard
	title="Banner"
	desc={$i18n.t(
		'Top banner with type chip (info/success/warning/error). Markdown content. Dismissible.'
	)}
>
	<div class="w-full flex flex-col gap-2">
		{#if visible.length === 0}
			<p class="text-xs text-gray-400 py-2">{$i18n.t('No results found')}</p>
		{:else}
			{#each visible as banner (banner.id)}
				<Banner
					{banner}
					dismissed={false}
					className="mx-0 px-2 rounded-lg"
					on:dismiss={(e) => (dismissedIds = [...dismissedIds, e.detail])}
				/>
			{/each}
		{/if}
		{#if dismissedIds.length > 0}
			<button
				type="button"
				class="self-start text-[11px] text-blue-500 hover:underline"
				on:click={() => (dismissedIds = [])}
			>
				{$i18n.t('Restore')} ({dismissedIds.length})
			</button>
		{/if}
	</div>
</DemoCard>
