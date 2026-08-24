<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import DropdownMenu from '$lib/components/common/DropdownMenu.svelte';
	import DemoCard from './DemoCard.svelte';
	const i18n = getContext<Writable<i18nType>>('i18n');

	let show = false;
</script>

<DemoCard
	title="Dropdown"
	desc={$i18n.t(
		'Portal dropdown container. trigger slot + content slot. bind:show, auto-flip/shift.'
	)}
>
	<div class="flex flex-col items-start gap-2">
		<div class="inline-block">
			<Dropdown bind:show align="end" side="bottom" sideOffset={6} closeOnOutsideClick={true}>
				<button
					class="px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition text-sm"
				>
					{$i18n.t('Menu')} ▾
				</button>
				<div slot="content">
					<DropdownMenu className="min-w-[170px]">
						<button
							class="block w-full text-left px-2 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
							on:click={() => (show = false)}
						>
							{$i18n.t('Edit')}
						</button>
						<button
							class="block w-full text-left px-2 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
							on:click={() => (show = false)}
						>
							{$i18n.t('Delete')}
						</button>
					</DropdownMenu>
				</div>
			</Dropdown>
		</div>
		<span class="text-[11px] text-gray-400">open = {show}</span>
	</div>
</DemoCard>
