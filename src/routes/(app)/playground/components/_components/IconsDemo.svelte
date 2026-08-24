<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// 用 import.meta.glob 批量收集 src/lib/components/icons 下的全部图标。
	// eager=false → 懒加载，按需解析，避免测试页首屏一次性把 180+ 图标全打进来。
	// as: 'component' → 拿到 Svelte 组件构造器。
	//
	// 返回值形如 { '/src/lib/components/icons/Check.svelte': () => Promise<Component> }
	const iconModules = import.meta.glob('$lib/components/icons/*.svelte', {
		query: '?component',
		import: 'default',
		eager: false
	});

	// 路径 → 文件名（如 'Check'），作为展示标签
	type IconEntry = {
		name: string; // Check
		load: () => Promise<any>; // 懒加载函数
	};

	let iconEntries: IconEntry[] = Object.entries(iconModules)
		.map(([path, load]) => ({
			name:
				path
					.split('/')
					.pop()
					?.replace(/\.svelte$/, '') ?? path,
			load: load as () => Promise<any>
		}))
		.sort((a, b) => a.name.localeCompare(b.name));

	// 搜索过滤
	let query = '';
	$: filtered = query
		? iconEntries.filter((e) => e.name.toLowerCase().includes(query.toLowerCase()))
		: iconEntries;

	// 点击复制组件 import 语句
	let copiedName = '';
	let copyTimer: ReturnType<typeof setTimeout>;
	const copyImport = async (name: string) => {
		try {
			await navigator.clipboard.writeText(
				`import ${name} from '$lib/components/icons/${name}.svelte';`
			);
			copiedName = name;
			clearTimeout(copyTimer);
			copyTimer = setTimeout(() => (copiedName = ''), 1500);
		} catch {
			// 剪贴板不可用时静默失败，不阻塞交互
		}
	};
</script>

<DemoCard
	title={$i18n.t('Icons')}
	desc={$i18n.t('Search icons by name') + ` · ${iconEntries.length}`}
>
	<div class="flex flex-col gap-2 w-full">
		<input
			class="w-full text-xs px-2.5 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-850 border border-gray-100 dark:border-gray-800 outline-none focus:border-gray-300 dark:focus:border-gray-700 transition text-gray-700 dark:text-gray-200"
			placeholder={$i18n.t('Search icons by name')}
			bind:value={query}
			aria-label={$i18n.t('Search icons by name')}
		/>

		{#if filtered.length === 0}
			<div class="text-[11px] text-gray-400 dark:text-gray-500 py-4 text-center">
				{$i18n.t('No results found')}
			</div>
		{:else}
			<div
				class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 max-h-72 overflow-y-auto p-0.5"
			>
				{#each filtered as entry (entry.name)}
					<button
						type="button"
						class="group flex flex-col items-center justify-center gap-1.5 rounded-lg border border-gray-100 dark:border-gray-850 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-850 hover:border-gray-200 dark:hover:border-gray-700 transition p-2.5 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-300 dark:focus:ring-blue-700"
						aria-label={copiedName === entry.name ? $i18n.t('Copied') : entry.name}
						on:click={() => copyImport(entry.name)}
					>
						<span
							class="text-gray-700 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition"
						>
							{#await entry.load()}
								<div class="size-5 animate-pulse bg-gray-100 dark:bg-gray-800 rounded"></div>
							{:then Component}
								<Component className="size-5" />
							{/await}
						</span>
						<span
							class="text-[10px] leading-tight text-gray-400 dark:text-gray-500 text-center break-all line-clamp-2 min-h-[1.5em]"
						>
							{entry.name}
						</span>
						{#if copiedName === entry.name}
							<span class="text-[9px] text-emerald-500 font-medium">{$i18n.t('Copied')}</span>
						{/if}
					</button>
				{/each}
			</div>
		{/if}
	</div>
</DemoCard>
