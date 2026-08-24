<script lang="ts">
	import type { CreationScope } from '$lib/utils/creations-library';
	import type { ImageCreationDraft } from '$lib/utils/image-generation-batches';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import CreationsLibrary from './CreationsLibrary.svelte';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();

	export let active: boolean;
	export let scope: CreationScope;
	export let revision: number;
	export let labelledBy: string;
	export let onReuse: (draft: ImageCreationDraft) => void;
	export let onStartCreating: () => void;
</script>

<div
	id="images-library-panel"
	role="tabpanel"
	aria-labelledby={labelledBy}
	class="min-h-0 flex-1 overflow-y-auto"
	hidden={!active}
>
	<div class="pt-4 sm:pt-18">
		<CreationsLibrary {active} {scope} {revision} {onReuse} mediaKind="image" />
	</div>
</div>

{#if active}
	<div
		class="pointer-events-none absolute inset-x-0 bottom-0 z-30 flex justify-center px-3 pb-4 sm:pb-5"
	>
		<button
			type="button"
			class="pointer-events-auto inline-flex min-h-11 items-center gap-2 rounded-full border border-gray-200/80 bg-white/85 px-5 text-sm font-medium text-gray-800 shadow-lg shadow-black/10 backdrop-blur-xl transition hover:bg-white hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-400 dark:border-gray-700/80 dark:bg-gray-900/85 dark:text-gray-100 dark:hover:bg-gray-900 dark:hover:text-white"
			on:click={onStartCreating}
		>
			<Sparkles className="size-4 shrink-0 text-gray-500 dark:text-gray-400" strokeWidth="1.5" />
			{$i18n.t('Start creating')}
		</button>
	</div>
{/if}
