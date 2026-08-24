<script lang="ts">
	import GenerationPageNavigation from '$lib/components/common/GenerationPageNavigation.svelte';

	export let selection: 'generate' | 'mine' | 'all';
	export let isAdmin: boolean;
	export let onSelect: (selection: 'generate' | 'mine' | 'all') => void;

	const tabs = [
		{
			id: 'generate',
			elementId: 'images-generate-tab',
			panelId: 'images-generate-panel',
			label: 'Create art'
		},
		{
			id: 'mine',
			elementId: 'images-library-tab',
			panelId: 'images-library-panel',
			label: 'My creations'
		},
		{
			id: 'all',
			elementId: 'images-admin-tab',
			panelId: 'images-library-panel',
			label: 'All creations'
		}
	] as const;
</script>

<GenerationPageNavigation pageLabel="Images" {tabs} {selection} {isAdmin} {onSelect} />
