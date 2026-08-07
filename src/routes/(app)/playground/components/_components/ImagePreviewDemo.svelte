<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// ImagePreview 是全屏浮层：bind:show 控制开关，点图触发。
	// 注意它本身只渲染遮罩 + 图片，不放触发器，触发由父组件负责。
	let show = false;
	const open = () => (show = true);
</script>

<DemoCard
	title="ImagePreview"
	desc={$i18n.t('Full-screen image viewer. Pan/zoom/download. ESC or backdrop closes.')}
>
	<div class="flex flex-wrap items-start gap-3 w-full">
		<button
			type="button"
			class="flex flex-col items-center gap-1 group focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700 rounded-lg"
			on:click={open}
		>
			<img
				src="/assets/welcome.webp"
				alt="welcome"
				class="w-28 rounded-lg cursor-zoom-in object-cover transition group-hover:opacity-90"
			/>
			<span class="text-[10px] text-gray-400">{$i18n.t('Click to preview')}</span>
		</button>

		<button
			type="button"
			class="flex flex-col items-center gap-1 group focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700 rounded-lg"
			on:click={() => (show = true)}
		>
			<img
				src="/favicon.png"
				alt="favicon"
				class="w-20 h-20 object-contain cursor-zoom-in transition group-hover:opacity-90"
			/>
			<span class="text-[10px] text-gray-400">{$i18n.t('Click to preview')}</span>
		</button>
	</div>
</DemoCard>

<ImagePreview bind:show src="/assets/welcome.webp" alt="welcome" />
