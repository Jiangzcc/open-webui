<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import CodeEditor from '$lib/components/common/CodeEditor.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// CodeEditor 基于 CodeMirror，id 必填且全页唯一。
	// value 双向；lang 影响语法高亮（language-data 按需加载）。
	// 注意：Ctrl+Shift+F 会触发后端 Python 格式化 API，演示里不引导用户按该快捷键。
	let value = `def greet(name: str) -> str:
    return f"hello, {name}"


if __name__ == "__main__":
    print(greet("world"))`;

	let saved = '';
	const onSave = (e: any) => (saved = typeof e === 'string' ? e : JSON.stringify(e));
	const onChange = (e: any) => {};
</script>

<DemoCard
	title="CodeEditor"
	desc={$i18n.t('CodeMirror editor. Multi-language highlight. Save callback on Ctrl/Cmd+S.')}
>
	<div class="w-full">
		<CodeEditor
			id="pg-code-editor-demo"
			lang="python"
			bind:value
			{onSave}
			{onChange}
			className="text-xs"
		/>
		{#if saved}
			<p class="mt-2 text-[11px] text-emerald-500">{$i18n.t('Saved')} ✓</p>
		{/if}
	</div>
</DemoCard>
