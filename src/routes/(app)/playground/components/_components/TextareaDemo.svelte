<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Textarea from '$lib/components/common/Textarea.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let text = '';
</script>

<DemoCard
	title="Textarea"
	desc={$i18n.t('Auto-growing textarea. bind:value, onInput/onBlur. field-sizing:content.')}>
	<div class="flex flex-col items-start gap-2 w-full">
		<Textarea
			bind:value={text}
			placeholder={$i18n.t('Type here...')}
			rows={2}
			className="w-full rounded-lg px-3 py-2 text-sm bg-gray-50 dark:bg-gray-850 outline-hidden"
			onInput={(e) => console.log('input', e)}
		/>
		<span class="text-[11px] text-gray-400">{$i18n.t('Value')}: {text || '—'}</span>
	</div>
</DemoCard>
