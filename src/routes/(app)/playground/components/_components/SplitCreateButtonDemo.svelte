<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import SplitCreateButton from '$lib/components/common/SplitCreateButton.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// 注意：actions 中 id 后缀决定图标（-new / -import / -export / -import-link）
	// primaryAction 取 id 以 "-new" 结尾的项
	const singleActions = [{ id: 'doc-new', label: 'New Doc', onClick: () => console.log('new') }];

	const multiActions = [
		{ id: 'doc-new', label: 'New Doc', onClick: () => console.log('new') },
		{ id: 'doc-import', label: 'Import', onClick: () => console.log('import') },
		{ id: 'doc-export', label: 'Export', href: '#export' }
	];
</script>

<DemoCard
	title="SplitCreateButton"
	desc={$i18n.t('Single action → button; multiple → primary + dropdown. id suffix picks the icon.')}
>
	<div class="flex flex-col items-start gap-2">
		<div class="flex flex-col gap-1">
			<span class="text-[11px] text-gray-400">{$i18n.t('Single action')}:</span>
			<SplitCreateButton label="Create" actions={singleActions} />
		</div>
		<div class="flex flex-col gap-1">
			<span class="text-[11px] text-gray-400">{$i18n.t('Multiple actions')}:</span>
			<SplitCreateButton label="Create" actions={multiActions} />
		</div>
	</div>
</DemoCard>
