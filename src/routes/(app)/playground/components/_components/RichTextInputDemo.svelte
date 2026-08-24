<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import RichTextInput from '$lib/components/common/RichTextInput.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// RichTextInput 是 TipTap 富文本编辑器。
	// value: markdown 字符串（bind）；placeholder 仅提示。
	// 这里只做纯前端编辑，不开 image/file/collaboration 等需后端的能力。
	let value = `# 富文本编辑器

支持 **加粗**、*斜体*、\`行内代码\`，以及：

- 列表项 A
- 列表项 B
- [ ] 任务项

\`\`\`python
print("hello, world")
\`\`\``;
</script>

<DemoCard
	title="RichTextInput"
	desc={$i18n.t('TipTap rich-text editor. Markdown in/out. Formatting toolbar toggleable.')}
>
	<div class="w-full">
		<RichTextInput
			bind:value
			placeholder={$i18n.t('Type here...')}
			showFormattingToolbar
			className="input-prose min-h-[12rem] max-h-[24rem] overflow-y-auto"
		/>
		<details class="mt-2 text-[11px] text-gray-400">
			<summary class="cursor-pointer select-none">{$i18n.t('Source')} (markdown)</summary>
			<pre
				class="mt-1 whitespace-pre-wrap break-words bg-gray-50 dark:bg-gray-850 p-2 rounded">{value}</pre>
		</details>
	</div>
</DemoCard>
