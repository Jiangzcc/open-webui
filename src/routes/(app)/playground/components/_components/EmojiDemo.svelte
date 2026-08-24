<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Emoji from '$lib/components/common/Emoji.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Emoji: 传 shortCode（如 'slight_smile'），从 shortCodesToEmojis store 查 hex 文件名。
	// store 由静态 json 初始化，无需后端。
	const codes = [
		'slight_smile',
		'heart',
		'thumbsup',
		'tada',
		'rocket',
		'fire',
		'100',
		'thinking',
		'wave',
		'star2',
		'zzz',
		'eyes',
		'art',
		'cpu',
		'gear',
		'books',
		'bulb',
		'mag'
	];
</script>

<DemoCard title="Emoji" desc={$i18n.t('Short-code → SVG emoji. From static assets, no backend.')}>
	<div class="flex flex-wrap gap-3 w-full">
		{#each codes as code (code)}
			<div class="flex flex-col items-center gap-1">
				<Emoji shortCode={code} className="size-7" />
				<span class="text-[9px] text-gray-400">{code}</span>
			</div>
		{/each}
	</div>
</DemoCard>
