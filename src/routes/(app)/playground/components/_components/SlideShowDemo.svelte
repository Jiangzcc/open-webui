<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import SlideShow from '$lib/components/common/SlideShow.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// SlideShow 需要相对定位父容器 + 明确高度，自身用 absolute 撑满。
	// 这里给一个固定高的容器。
	const imageUrls = ['/assets/welcome.webp', '/favicon.png', '/assets/vendors/openai.webp'];
	// duration 用较短值方便演示轮播
	const duration = 2500;
</script>

<DemoCard
	title="SlideShow"
	desc={$i18n.t('Auto-rotating image slideshow. Needs relative parent + height.')}
>
	<div class="relative w-full h-40 rounded-xl overflow-hidden border border-gray-100 dark:border-gray-850">
		<SlideShow {imageUrls} {duration} />
	</div>
</DemoCard>
