<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ChatList from '$lib/components/common/ChatList.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// ChatList: 纯展示用 showUserInfo=false，避免去后端拉用户头像/名字。
	// time_range 让列表自动按时间段分组（Today/Yesterday/...），dayjs calendar 计算。
	// 演示"加载更多"：onLoadMore 被调用时追加假数据。
	type Chat = {
		id: string;
		title: string;
		updated_at: number;
		time_range?: string;
	};

	// 用秒级时间戳，updated_at 单位为秒
	const now = Math.floor(Date.now() / 1000);
	let chatList: Chat[] = [
		{ id: 'c1', title: '前端组件展示页设计', updated_at: now - 360, time_range: 'Today' },
		{ id: 'c2', title: 'Svelte 5 runes 迁移', updated_at: now - 7200, time_range: 'Today' },
		{ id: 'c3', title: 'Open WebUI 二开规范', updated_at: now - 86400, time_range: 'Yesterday' },
		{ id: 'c4', title: '响应式布局自查清单', updated_at: now - 86400, time_range: 'Yesterday' }
	];

	let loading = false;
	let allLoaded = false;
	let clickLog = '';

	// 排序状态
	let orderBy: 'title' | 'updated_at' | 'user_name' | null = 'updated_at';
	let direction: 'asc' | 'desc' = 'desc';

	const loadMore = () => {
		if (loading || allLoaded) return;
		loading = true;
		setTimeout(() => {
			chatList = [
				...chatList,
				{
					id: 'c' + (chatList.length + 1),
					title: '历史会话 #' + (chatList.length + 1),
					updated_at: now - 172800,
					time_range: 'Last 7 Days'
				}
			];
			loading = false;
			if (chatList.length >= 6) allLoaded = true;
		}, 400);
	};

	const onChatClick = (id: string) => (clickLog = id);
	const onSort = (key: 'title' | 'updated_at' | 'user_name') => {
		if (orderBy === key) {
			direction = direction === 'asc' ? 'desc' : 'asc';
		} else {
			orderBy = key;
			direction = 'desc';
		}
		// 简单就地排序（纯前端 mock，不调后端）
		chatList = [...chatList].sort((a, b) => {
			let r = 0;
			if (key === 'title') r = a.title.localeCompare(b.title);
			else r = a.updated_at - b.updated_at;
			return direction === 'asc' ? r : -r;
		});
	};
</script>

<DemoCard
	title="ChatList"
	desc={$i18n.t(
		'Chat list with time grouping, sort headers, load-more. Uses mock data, no backend.'
	)}
>
	<div class="w-full">
		<ChatList
			{chatList}
			{loading}
			{allLoaded}
			showUserInfo={false}
			{orderBy}
			{direction}
			onLoadMore={loadMore}
			{onChatClick}
			onSort={onSort as any}
		/>
		{#if clickLog}
			<p class="text-[11px] text-gray-400 mt-2">{$i18n.t('Selected')}: {clickLog}</p>
		{/if}
	</div>
</DemoCard>
