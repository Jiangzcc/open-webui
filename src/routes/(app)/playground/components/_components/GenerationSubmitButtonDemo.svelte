<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import GenerationSubmitButton from '$lib/components/common/GenerationSubmitButton.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let loading = false;
</script>

<DemoCard
	title="GenerationSubmitButton"
	desc={$i18n.t('Circular submit button (type=submit). loading swaps Sparkles for Spinner.')}
>
	<div class="flex items-center gap-3">
		<form
			on:submit={(e) => {
				e.preventDefault();
				loading = true;
				setTimeout(() => (loading = false), 1500);
			}}
		>
			<GenerationSubmitButton label={$i18n.t('Generate')} {loading} disabled={false} />
		</form>
		<span class="text-[11px] text-gray-400">
			{$i18n.t('Click to trigger')} loading
		</span>
	</div>
</DemoCard>
