<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Image from '$lib/components/common/Image.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// 用本地静态资源，不依赖后端：
	// - /favicon.png（仓库 static/favicon.png，同源相对路径）
	// - /assets/welcome.webp（仓库 static/assets/welcome.webp）
	// - data:image/svg+xml 内联图（安全，safeImageUrl 允许 data: 前缀）
	const inlineSvg =
		'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120"><rect width="200" height="120" fill="%234f46e5"/><text x="100" y="65" font-size="14" fill="white" text-anchor="middle">SVG</text></svg>';

	let dismissedCount = 0;
</script>

<DemoCard
	title="Image"
	desc={$i18n.t(
		'Image with preview + dismissible. Click to open ImagePreview (pan/zoom/download).'
	)}
>
	<div class="flex flex-wrap items-start gap-3 w-full">
		<div class="flex flex-col items-center gap-1">
			<Image src="/favicon.png" alt="favicon" imageClassName="w-20 h-20 object-contain" />
			<span class="text-[10px] text-gray-400">/favicon.png</span>
		</div>

		<div class="flex flex-col items-center gap-1">
			<Image src="/assets/welcome.webp" alt="welcome" imageClassName="w-28 rounded-lg" />
			<span class="text-[10px] text-gray-400">/assets/welcome.webp</span>
		</div>

		<div class="flex flex-col items-center gap-1">
			<Image src={inlineSvg} alt="inline svg" imageClassName="w-28 rounded-lg" />
			<span class="text-[10px] text-gray-400">data: SVG</span>
		</div>

		<div class="flex flex-col items-center gap-1">
			<Image
				src="/favicon.png"
				alt="dismissible"
				imageClassName="w-20 h-20 object-contain"
				dismissible
				onDismiss={() => (dismissedCount += 1)}
			/>
			<span class="text-[10px] text-gray-400">dismissed ×{dismissedCount}</span>
		</div>
	</div>
</DemoCard>
