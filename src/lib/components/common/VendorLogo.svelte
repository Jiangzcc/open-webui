<script lang="ts">
	import { vendorLogoUrl } from '$lib/utils/images-dropdown';

	/**
	 * Vendor brand logo with a graceful fallback.
	 *
	 * Many providers in the fal catalog (e.g. black-forest-labs, baidu, hidream,
	 * minimax, nvidia, recraft, reve, rundiffusion, stability, tencent, zhipu,
	 * …) have no static logo asset under /assets/vendors/. A raw <img> with a
	 * missing src shows a broken-image glyph, which reads as "no icon" in the
	 * selector. This component falls back to a gradient disc showing the first
	 * letter of the provider slug when the asset 404s or the provider is empty,
	 * so every model row renders a recognizable brand mark.
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
