<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import SVGPanZoom from '$lib/components/common/SVGPanZoom.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// SVGPanZoom: svg(原始字符串,会经 DOMPurify 消毒)+ content(源码文本,用于复制/下载)。
	// 仅当 content 非空时才显示 下载/重置/复制 按钮组。
	// 这里给一个简单 Mermaid 风格的 SVG 流程图，content 与 svg 一致。
	const sampleSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 160" width="100%" height="100%">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6366f1"/>
    </marker>
  </defs>
  <rect x="10" y="50" width="80" height="60" rx="8" fill="#eef2ff" stroke="#6366f1" stroke-width="2"/>
  <text x="50" y="84" text-anchor="middle" font-size="12" fill="#4338ca">Input</text>
  <line x1="90" y1="80" x2="130" y2="80" stroke="#6366f1" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="130" y="50" width="80" height="60" rx="8" fill="#6366f1"/>
  <text x="170" y="84" text-anchor="middle" font-size="12" fill="white">Process</text>
  <line x1="210" y1="80" x2="250" y2="80" stroke="#6366f1" stroke-width="2" marker-end="url(#arrow)"/>
  <rect x="250" y="50" width="60" height="60" rx="8" fill="#eef2ff" stroke="#6366f1" stroke-width="2"/>
  <text x="280" y="84" text-anchor="middle" font-size="12" fill="#4338ca">Out</text>
</svg>`;
</script>

<DemoCard
	title="SVGPanZoom"
	desc={$i18n.t('Sanitized SVG with pan/zoom. Buttons: download SVG, reset, copy source.')}
>
	<!-- 需要 height 才能撑起交互区 -->
	<div class="w-full h-52">
		<SVGPanZoom
			className="w-full h-full rounded-lg border border-gray-100 dark:border-gray-850"
			svg={sampleSvg}
			content={sampleSvg}
		/>
	</div>
</DemoCard>
