<script lang="ts">
	import GenerationPageNavigation from '$lib/components/common/GenerationPageNavigation.svelte';

	export let selection: 'generate' | 'mine' | 'all';
	export let isAdmin: boolean;
	export let onSelect: (selection: 'generate' | 'mine' | 'all') => void;

	const tabs = [
		{
			id: 'generate',
			elementId: 'videos-tab-generate',
			panelId: 'videos-generate-panel',
			label: 'Create art'
		},
		{
			id: 'mine',
			elementId: 'videos-tab-mine',
			panelId: 'videos-library-panel',
			label: 'My creations'
		},
		{
			id: 'all',
			elementId: 'videos-tab-all',
			panelId: 'videos-library-panel',
			label: 'All creations'
		}
	] as const;
</script>

<GenerationPageNavigation pageLabel="Videos" {tabs} {selection} {isAdmin} {onSelect} />
