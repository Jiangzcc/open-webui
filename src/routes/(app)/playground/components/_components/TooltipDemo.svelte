<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');
</script>

<DemoCard
	title="Tooltip"
	desc={$i18n.t('tippy.js tooltip. content runs through DOMPurify. touch=true on mobile.')}
>
	<div class="flex flex-wrap items-center gap-3">
		<Tooltip content={$i18n.t('Helpful hint')} placement="top">
			<span class="underline decoration-dotted cursor-help text-sm text-gray-700 dark:text-gray-200">
				{$i18n.t('Hover me')} (top)
			</span>
		</Tooltip>
		<Tooltip content={$i18n.t('Bottom placement')} placement="bottom">
			<span class="underline decoration-dotted cursor-help text-sm text-gray-700 dark:text-gray-200">
				{$i18n.t('Hover me')} (bottom)
			</span>
		</Tooltip>
		<Tooltip content="<b>Bold</b> &amp; <i>italic</i> HTML allowed" placement="top" allowHTML={true}>
			<span class="underline decoration-dotted cursor-help text-sm text-gray-700 dark:text-gray-200">
				{$i18n.t('Hover me')} (html)
			</span>
		</Tooltip>
	</div>
</DemoCard>
