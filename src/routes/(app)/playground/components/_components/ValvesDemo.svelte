<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import Valves from '$lib/components/common/Valves.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// Valves 用 JSON Schema 描述字段（valvesSpec），valves 存值（bind）。
	// 支持类型：string / boolean / enum(select) / multiselect / password / map。
	// dispatch('change') 在任意字段变更时触发。
	const valvesSpec = {
		title: 'Demo Valves',
		properties: {
			api_key: {
				type: 'string',
				format: 'password',
				title: 'API Key',
				description: '用于鉴权，密码框隐藏'
			},
			model: {
				type: 'string',
				enum: ['gpt-4o', 'claude-3.5', 'gemini-1.5'],
				title: 'Model',
				description: '下拉选择模型'
			},
			enabled: {
				type: 'boolean',
				title: 'Enabled',
				default: true
			},
			tools: {
				type: 'array',
				title: 'Tools',
				input: {
					type: 'multiselect',
					options: [
						{ value: 'search', label: 'Search' },
						{ value: 'code', label: 'Code Interpreter' },
						{ value: 'vision', label: 'Vision' }
					]
				}
			},
			params: {
				type: 'object',
				title: 'Params',
				description: '键值对映射'
			}
		},
		required: ['api_key', 'model']
	};
	// Upstream Valves.svelte is still JavaScript and infers its default-null prop too narrowly.
	const valvesProps: Record<string, unknown> = { valvesSpec };

	let valves: Record<string, any> = {
		api_key: 'demo',
		model: 'gpt-4o',
		enabled: true,
		tools: ['search', 'vision'],
		params: { temperature: 0.7 }
	};

	let changeCount = 0;
</script>

<DemoCard
	title="Valves"
	desc={$i18n.t('JSON-Schema-driven form. password/enum/multiselect/boolean/map. dispatch change.')}
>
	<div class="w-full flex flex-col gap-2">
		<Valves {...valvesProps} bind:valves on:change={() => (changeCount += 1)} />
		<details class="text-[11px] text-gray-400">
			<summary class="cursor-pointer select-none"
				>{$i18n.t('Source')} (valves) · {$i18n.t('Changes')}: {changeCount}</summary
			>
			<pre
				class="mt-1 whitespace-pre-wrap break-words bg-gray-50 dark:bg-gray-850 p-2 rounded">{JSON.stringify(
					valves,
					null,
					2
				)}</pre>
		</details>
	</div>
</DemoCard>
