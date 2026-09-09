<script context="module" lang="ts">
	// 胶囊底色常量导出：移动端「筛选」入口按钮（非 Select）要复用同款样式。
	export const IDLE_PILL =
		'border border-slate-200/75 bg-white/45 text-slate-600 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] hover:border-slate-300/80 hover:bg-white/75 hover:text-slate-950 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#5b6ee1] dark:border-white/[0.09] dark:bg-white/[0.055] dark:text-slate-300 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] dark:hover:bg-white/[0.09] dark:hover:text-white dark:focus-visible:outline-[#8290ed]';
	export const ACTIVE_PILL =
		'border border-[#5b6ee1]/30 bg-[#5b6ee1]/10 font-medium text-[#4051bd] shadow-[inset_0_1px_0_rgba(255,255,255,0.7)] hover:bg-[#5b6ee1]/15 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#5b6ee1] dark:border-[#8290ed]/35 dark:bg-[#5b6ee1]/20 dark:text-[#b9c1ff] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] dark:hover:bg-[#5b6ee1]/28 dark:focus-visible:outline-[#8290ed]';
</script>

<script lang="ts">
	import Select from '$lib/components/common/Select.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';

	export let value = '';
	export let items: Array<{ value: string; label: string }> = [];
	export let placeholder = '';
	// 激活的筛选点亮成反色胶囊，让「当前生效的查询」一眼可读。
	export let active = false;
	export let onChange: (value: string) => void = () => {};
	// 资产筛选统一撑满所属网格单元，避免胶囊只包住文字形成零碎悬空。
	export let fullWidth = false;

	// vidu 参数：32px 高、微填充底、圆角 8px、14px/400、内距 8×12；
	// 移动端抬高到 44px 保证触控；深浅主题按应用映射。
</script>

<Select
	{value}
	{items}
	{placeholder}
	{onChange}
	triggerClass="flex min-h-11 shrink-0 items-center gap-2 whitespace-nowrap rounded-[10px] px-3.5 py-2 text-sm font-normal transition active:scale-[0.98] md:h-9 md:min-h-0 {fullWidth
		? 'w-full'
		: ''} {active ? ACTIVE_PILL : IDLE_PILL}"
>
	<span
		slot="trigger"
		let:selectedLabel
		let:open
		class="flex w-full min-w-0 items-center justify-between gap-2"
	>
		<span class="min-w-0 truncate">{selectedLabel}</span>
		<ChevronDown
			className="size-3.5 shrink-0 opacity-60 transition-transform {open ? 'rotate-180' : ''}"
		/>
	</span>
</Select>
