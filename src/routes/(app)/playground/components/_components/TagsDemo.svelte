<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Tags from '$lib/components/common/Tags.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let tags = [{ name: 'open-webui' }, { name: 'svelte' }];
	const suggestionTags = ['important', 'draft', 'review', 'bug', 'feature'];
</script>

<DemoCard
	title="Tags"
	desc={$i18n.t('Tag input with autocomplete. on:add / on:delete. Enter or space to add.')}
>
	<div class="flex flex-col items-start gap-2 w-full">
		<div class="w-full p-2 rounded-lg border border-gray-200 dark:border-gray-800">
			<Tags
				{tags}
				{suggestionTags}
				disabled={false}
				on:add={(e) => {
					console.log('add:', e.detail);
					tags = [...tags, { name: e.detail }];
				}}
				on:delete={(e) => {
					console.log('delete:', e.detail);
					tags = tags.filter((t) => t.name !== e.detail);
				}}
			/>
		</div>
		<span class="text-[11px] text-gray-400">
			{$i18n.t('Tags')}: {tags.map((t) => t.name).join(', ') || '—'}
		</span>
	</div>
</DemoCard>
