<script lang="ts">
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	export let loading = false;
	export let disabled = false;
	export let label: string;
</script>

<button
	type="submit"
	class="flex size-11 shrink-0 items-center justify-center rounded-full transition active:scale-90 sm:size-8 {disabled
		? 'cursor-not-allowed bg-gray-200 text-gray-500 dark:bg-gray-800 dark:text-gray-500'
		: 'bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-100'}"
	{disabled}
	aria-label={label}
>
	{#if loading}
		<Spinner className="size-4" />
	{:else}
		<Sparkles className="size-4" strokeWidth="2" />
	{/if}
</button>
