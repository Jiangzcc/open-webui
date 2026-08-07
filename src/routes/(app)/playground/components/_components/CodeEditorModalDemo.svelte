<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import CodeEditorModal from '$lib/components/common/CodeEditorModal.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// CodeEditorModal 用 Svelte 5 runes ($props + $bindable)。
	// show/value 可 bind；内部包 CodeEditor + Drawer（右侧抽屉）。
	let show = false;
	let value = `// 在抽屉里编辑这段代码
const sum = (a, b) => a + b;
console.log(sum(1, 2));`;

	const open = () => (show = true);
	const onSave = (e: any) => {
		// 保存回调
	};
</script>

<DemoCard
	title="CodeEditorModal"
	desc={$i18n.t('Code editor in a side Drawer. bind:show / bind:value. Svelte 5 runes API.')}
>
	<button
		type="button"
		class="text-xs px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 transition focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700"
		on:click={open}
	>
		{$i18n.t('Open Code Editor')}
	</button>
</DemoCard>

<CodeEditorModal bind:show bind:value lang="javascript" {onSave} />
