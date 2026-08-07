<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import FullHeightIframe from '$lib/components/common/FullHeightIframe.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// FullHeightIframe 的 src 自动判别 URL 还是原始 HTML：
	// - 以 http(s):// 或 // 开头 → iframe src（外部地址）
	// - 其它 → 当作原始 HTML，走 srcdoc（会注入 CSP、处理依赖）
	// 这里用原始 HTML 演示，不依赖外网。allowSameOrigin=false（默认），沙箱安全。
	const rawHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{font-family:system-ui,sans-serif;margin:0;padding:1.5rem;background:linear-gradient(135deg,#eef2ff,#faf5ff);color:#1e293b}h3{margin:0 0 .5rem}p{margin:0;color:#64748b;font-size:14px}</style></head><body><h3>📄 Iframe 内容</h3><p>这是由 FullHeightIframe 注入的原始 HTML，自动沙箱化并同步高度。</p></body></html>`;

	// 第二个例子：相对 URL（同源静态页）—— /static/favicon 同源，用 about: 占位避免真外网
	// 这里直接也用 rawHtml 变体演示不同高度
	let altHtml = rawHtml;
</script>

<DemoCard
	title="FullHeightIframe"
	desc={$i18n.t('Iframe that auto-detects URL vs raw HTML, sandboxed, height-synced via postMessage.')}
>
	<div class="flex flex-col gap-3 w-full">
		<FullHeightIframe
			src={rawHtml}
			title="demo html"
			initialHeight={160}
			iframeClassName="w-full rounded-lg border border-gray-100 dark:border-gray-850"
		/>

		<FullHeightIframe
			src={altHtml.replace('Iframe 内容', '另一段内容').replace('#eef2ff,#faf5ff', '#ecfeff,#fef3c7')}
			title="demo html 2"
			initialHeight={120}
			iframeClassName="w-full rounded-lg border border-gray-100 dark:border-gray-850"
		/>
	</div>
</DemoCard>
