<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ToolCallDisplay from '$lib/components/common/ToolCallDisplay.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// ToolCallDisplay 三种状态由 attributes.done 决定：
	// - undefined（未开始）→ 灰色扳手
	// - 'false' 或非 'true'（执行中）→ Spinner + shimmer
	// - 'true'（完成）→ 绿色对勾，展开后显示 Input/Output
	// arguments/result/files/embeds 都是「被编码的字符串」（内部 decode + 多层 JSON.parse）。

	type Attrs = {
		type?: string;
		id?: string;
		name?: string;
		arguments?: string;
		result?: string;
		files?: string;
		embeds?: string;
		done?: string;
	};

	// 执行中：done='false'
	const executing: Attrs = {
		name: 'web_search',
		arguments: JSON.stringify({ query: 'Svelte 5 runes', max_results: 5 }),
		done: 'false'
	};

	// 已完成：done='true'，带 result（对象）+ files（含 data 图）
	const dataImg =
		'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"><rect width="120" height="80" fill="%2310b981"/><text x="60" y="48" text-anchor="middle" fill="white" font-size="12">chart</text></svg>';
	const done: Attrs = {
		name: 'generate_chart',
		arguments: JSON.stringify({ type: 'bar', data: [10, 20, 30] }),
		result: JSON.stringify({ status: 'ok', rows: 3 }),
		files: JSON.stringify([dataImg]),
		done: 'true'
	};

	// 已完成（纯文本结果）
	const doneText: Attrs = {
		name: 'get_weather',
		arguments: JSON.stringify({ city: '北京', unit: 'celsius' }),
		result: '北京 多云 23°C，湿度 45%',
		done: 'true'
	};
</script>

<DemoCard
	title="ToolCallDisplay"
	desc={$i18n.t('Tool-call row: executing (spinner) / done (check). Expand to see Input/Output. Mock data.')}
>
	<div class="w-full flex flex-col gap-1">
		<ToolCallDisplay id="pg-tcd-executing" attributes={executing} />
		<ToolCallDisplay id="pg-tcd-done" attributes={done} open />
		<ToolCallDisplay id="pg-tcd-done-text" attributes={doneText} />
	</div>
</DemoCard>
