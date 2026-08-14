<script lang="ts">
	import { vendorLogoUrl } from '$lib/utils/images-dropdown';

	/**
	 * Vendor brand logo with a graceful fallback.
	 *
	 * Logos live at /assets/vendors/<provider>.webp as 96×96 opaque webp.
	 * 27 of the fal catalog's providers ship an asset (alibaba, baai, baidu,
	 * black-forest-labs, bria, bytedance, deepseek, google, hidream, ideogram,
	 * kling, krea, ltx, luma, meituan, microsoft, minimax, nvidia, openai,
	 * pika, pixverse, recraft, stability, tencent, vidu, xai, zhipu). The
	 * six long-tail vendors without a logo (boogu, other, patina, phota,
	 * reve, rundiffusion) deliberately fall back here rather than shipping a
	 * letter-only placeholder, so a missing asset renders a gradient disc
	 * with the provider's first initial instead of a broken-image glyph —
	 * and keeps future catalog additions legible before their logo lands.
	 */
	export let provider: string;
	export let alt: string = '';
	export let className: string = 'size-4 shrink-0 rounded-sm';

	let failedProvider = '';

	$: initial = (provider || '?').trim().charAt(0).toUpperCase() || '?';
	$: src = provider ? vendorLogoUrl(provider) : '';
</script>

{#if provider && failedProvider !== provider}
	<img
		{src}
		{alt}
		class={className}
		loading="lazy"
		decoding="async"
		on:error={() => (failedProvider = provider)}
	/>
{:else}
	<span
		class="inline-flex items-center justify-center bg-gradient-to-br from-gray-300 to-gray-400 font-medium text-gray-600 dark:from-gray-600 dark:to-gray-700 dark:text-gray-200 {className}"
		aria-hidden="true">{initial}</span
	>
{/if}
