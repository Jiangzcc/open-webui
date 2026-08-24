<script context="module" lang="ts">
	export type SelectableModel = {
		id: string;
		name: string;
		provider?: string | null;
		recommended?: boolean;
		tags?: string[];
		maintenance?: string | null;
		enabled?: boolean;
		raw: unknown;
	};
</script>

<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import Dropdown from './Dropdown.svelte';
	import VendorLogo from './VendorLogo.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';

	/**
	 * 二开共享：图片页与视频页的「模型选择器」弹窗。
	 *
	 * 两个页面原本各自内联了一份结构几乎相同的 Dropdown（厂商列 + 模型列 + 选项行），
	 * 但触发按钮高度、间距、字体粗细和弹出层样式都有细微出入。抽到此处后，两页共用
	 * 同一份触发器与弹出层，仅通过 props 注入数据、通过 `extras` 具名槽渲染各自的
	 * 额外徽标（图片页：参考图支持 / 代理慢启动 / 基础价；视频页：预计积分）。
	 *
	 * 字段名差异（图片页 camelCase，视频页 snake_case）由各页在构造 SelectableModel 时
	 * 归一化，组件内部只依赖归一化后的字段，不耦合任一页的具体模型类型。
	 */
	/** 双向绑定的展开状态（与 Dropdown 的外部点击关闭联动）。 */
	export let show = false;
	/** 触发按钮显示的模型名（由页面计算：加载中 / 短名 / 默认模型）。 */
	export let label: string;
	/** 触发按钮前导厂商 Logo 的 provider slug；为空时回退 Photo 图标。 */
	export let provider: string | null | undefined = null;
	/** 厂商列条目（页面已排序，`other` 已后置）。 */
	export let vendors: string[] = [];
	export let selectedVendor = '';
	/** 当前选中厂商下的模型（页面已过滤后传入）。 */
	export let models: SelectableModel[] = [];
	export let selectedId = '';
	export let onSelectVendor: (vendor: string) => void = () => {};
	export let onSelectModel: (model: SelectableModel) => void = () => {};
	/** 弹出模型选择对话框的无障碍标签。 */
	export let listboxLabel = '';

	const i18n = getContext<Writable<I18n>>('i18n');
</script>

<Dropdown
	bind:show
	side="top"
	align="start"
	contentRole="dialog"
	maxHeight="min(55dvh, 24rem)"
	contentClass="z-50 h-[min(55dvh,24rem)] w-[min(32rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-gray-200/90 bg-white/98 p-2 shadow-2xl backdrop-blur-xl sm:h-80 sm:min-w-[22rem] dark:border-gray-700 dark:bg-gray-900/98"
>
	<button
		type="button"
		class="inline-flex h-11 min-w-0 max-w-full items-center gap-2 overflow-hidden rounded-[10px] bg-gray-100 px-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 sm:h-8 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
		aria-expanded={show}
		aria-haspopup="dialog"
		aria-label={listboxLabel || $i18n.t('Select model')}
	>
		{#if provider}
			<VendorLogo {provider} className="size-4 shrink-0 rounded-sm" />
		{:else}
			<Photo className="size-4 shrink-0" strokeWidth="2" />
		{/if}
		<span class="truncate">{label}</span>
		<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">⌄</span>
	</button>

	<!-- 高度单源：外层 Dropdown 定高，内层 h-full 撑满，避免双高度差裁切底部 -->
	<div
		slot="content"
		class="flex h-full min-h-0 min-w-0 flex-row gap-2"
		role="dialog"
		aria-label={listboxLabel || $i18n.t('Models')}
	>
		<!-- 厂商列（左/上） -->
		<ul
			class="flex min-h-0 w-28 shrink-0 flex-col gap-1 overflow-y-auto overflow-x-hidden overscroll-contain border-r border-gray-100 pr-1 dark:border-gray-800 sm:w-40 sm:pr-1"
			aria-label={$i18n.t('Brands')}
		>
			{#each vendors as vendor}
				<li class="snap-start">
					<button
						type="button"
						class="flex min-h-11 min-w-0 w-full shrink-0 items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition sm:min-h-0 {selectedVendor ===
						vendor
							? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
							: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
						on:click={() => onSelectVendor(vendor)}
						aria-pressed={selectedVendor === vendor}
					>
						<VendorLogo provider={vendor} alt={vendor} className="size-4 shrink-0 rounded-sm" />
						<span class="min-w-0 truncate capitalize">{vendor}</span>
					</button>
				</li>
			{/each}
		</ul>
		<!-- 模型列（右/下） -->
		<ul
			class="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain sm:h-full"
			aria-label={$i18n.t('Models')}
		>
			{#each models as model}
				<li>
					<button
						type="button"
						class="flex min-h-11 w-full items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition sm:min-h-0 {selectedId ===
						model.id
							? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
							: model.enabled === false
								? 'cursor-not-allowed text-gray-400 dark:text-gray-600'
								: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
						on:click={() => model.enabled !== false && onSelectModel(model)}
						disabled={model.enabled === false}
						aria-pressed={selectedId === model.id}
					>
						{#if model.provider}
							<VendorLogo provider={model.provider} className="size-4 shrink-0 rounded-sm" />
						{/if}
						<span class="min-w-0 flex-1 text-left">
							<span class="flex min-w-0 items-center gap-1.5">
								<span class="truncate">{model.name}</span>
								{#if model.recommended}
									<span
										class="shrink-0 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
										>{$i18n.t('Recommended')}</span
									>
								{/if}
							</span>
							{#if model.tags?.length}
								<span class="mt-0.5 block truncate text-[11px] text-gray-400"
									>{model.tags.join(' · ')}</span
								>
							{/if}
							{#if model.maintenance}
								<span
									class="mt-0.5 block line-clamp-2 text-[11px] text-orange-600 dark:text-orange-400"
									>{model.maintenance}</span
								>
							{/if}
						</span>
						<slot name="extras" {model} />
					</button>
				</li>
			{/each}
		</ul>
	</div>
</Dropdown>
