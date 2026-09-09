<script lang="ts">
	import { tick } from 'svelte';

	export let items: ReadonlyArray<{ value: string; label: string }> = [];
	export let selected = '';
	export let ariaLabel = '';
	export let idPrefix = 'media-gallery-tab';
	export let className = '';
	export let onSelect: (value: string) => void = () => {};

	const selectAndFocus = async (value: string) => {
		onSelect(value);
		await tick();
		document.getElementById(`${idPrefix}-${value}`)?.focus();
	};

	const handleKeydown = (event: KeyboardEvent) => {
		if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
		const index = items.findIndex((item) => item.value === selected);
		if (index === -1) return;
		event.preventDefault();
		const direction = event.key === 'ArrowRight' ? 1 : -1;
		const next = items[(index + direction + items.length) % items.length];
		void selectAndFocus(next.value);
	};
</script>

<nav class="min-w-0 {className}" aria-label={ariaLabel}>
	<div
		class="flex min-h-11 items-center gap-0.5 overflow-x-auto scrollbar-none"
		role="tablist"
		tabindex="-1"
		on:keydown={handleKeydown}
	>
		{#each items as item (item.value)}
			<button
				type="button"
				role="tab"
				id={`${idPrefix}-${item.value}`}
				tabindex={selected === item.value ? 0 : -1}
				aria-selected={selected === item.value}
				class="relative min-h-11 shrink-0 whitespace-nowrap rounded-[10px] px-3 text-sm transition duration-200 after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:origin-center after:rounded-full after:transition-transform after:duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5b6ee1] active:scale-[0.98] sm:min-h-9 {selected ===
				item.value
					? 'font-semibold text-slate-950 after:scale-x-100 after:bg-[#5b6ee1] dark:text-slate-50'
					: 'text-slate-500 after:scale-x-0 after:bg-[#5b6ee1] hover:bg-white/45 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.06] dark:hover:text-slate-100'}"
				on:click={() => onSelect(item.value)}
			>
				{item.label}
			</button>
		{/each}
	</div>
</nav>
