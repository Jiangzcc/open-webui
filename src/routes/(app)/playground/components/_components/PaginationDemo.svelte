<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	// page 是当前页码，count 是总条目数（非页数），perPage 每页条数
	let page = 1;
	const count = 120;
	const perPage = 20;
</script>

<DemoCard
	title="Pagination"
	desc={$i18n.t('bits-ui pagination. bind:page (page number), count (total items), perPage.')}
>
	<div class="flex flex-col items-center gap-2 w-full">
		<Pagination bind:page {count} {perPage} />
		<span class="text-[11px] text-gray-400">
			{$i18n.t('Page')}: {page} / {Math.ceil(count / perPage)}
		</span>
	</div>
</DemoCard>
