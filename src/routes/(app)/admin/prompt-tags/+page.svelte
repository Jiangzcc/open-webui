<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	onMount(() => {
		const query = new URLSearchParams($page.url.search);
		query.set('tab', 'promptTags');
		void goto(`/admin/operations?${query.toString()}`, { replaceState: true });
	});
</script>
