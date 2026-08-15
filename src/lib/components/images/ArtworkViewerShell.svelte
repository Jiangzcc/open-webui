<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	export let show = false;
	export let loading = false;
	export let error: string | null = null;
	export let headerTitle = '';
	export let headerSubtitle = '';
	export let mediaLabel = '';
	export let detailsClassName = 'lg:w-80';

	const i18n = getContext<Writable<I18n>>('i18n');
</script>

<Modal
	bind:show
	size="lg"
	containerClassName="p-0 sm:p-3 flex"
	className="overflow-hidden bg-white/98 dark:bg-gray-900/98 backdrop-blur-xl !w-full sm:!w-fit sm:max-w-5xl h-[100dvh] sm:h-auto sm:max-h-[94dvh] rounded-none sm:rounded-3xl shadow-2xl shadow-black/15 dark:shadow-black/40"
>
	<div class="flex h-full max-h-[100dvh] min-w-0 flex-col sm:max-h-[94dvh]">
		<header
			class="flex min-h-14 shrink-0 items-center justify-between gap-3 border-b border-gray-100 px-4 dark:border-gray-800 sm:px-5"
		>
			<div class="min-w-0">
				{#if headerTitle}
					<p class="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{headerTitle}</p>
				{/if}
				{#if headerSubtitle}
					<p class="truncate text-xs text-gray-500 dark:text-gray-400">{headerSubtitle}</p>
				{/if}
			</div>
			<button
				type="button"
				class="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-full text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100"
				on:click={() => (show = false)}
				aria-label={$i18n.t('Close')}
			>
				<XMark className="size-5" strokeWidth="2" />
			</button>
		</header>

		{#if loading}
			<div class="flex min-h-72 flex-1 items-center justify-center">
				<Spinner className="size-6" />
			</div>
		{:else if error}
			<div class="flex min-h-72 flex-1 items-center justify-center px-5 text-center">
				<p class="text-sm text-red-500 dark:text-red-400">{error}</p>
			</div>
		{:else}
			<div class="flex min-h-0 flex-1 flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
				<section
					class="flex min-h-64 min-w-0 flex-1 items-center justify-center bg-stone-100 p-3 dark:bg-black/35 sm:p-5"
					aria-label={mediaLabel || $i18n.t('Artwork')}
				>
					<slot name="media" />
				</section>

				<aside
					class="flex min-w-0 flex-col gap-4 border-t border-gray-100 p-4 lg:shrink-0 lg:overflow-y-auto lg:border-l lg:border-t-0 dark:border-gray-800 sm:p-5 {detailsClassName}"
				>
					<slot name="details" />
				</aside>
			</div>
		{/if}
	</div>
</Modal>
