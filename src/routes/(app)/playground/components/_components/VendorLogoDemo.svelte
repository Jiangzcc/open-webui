<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import VendorLogo from '$lib/components/common/VendorLogo.svelte';
	import DemoCard from './DemoCard.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// 有静态 logo 的厂商（/assets/vendors/<provider>.webp 存在）
	const withLogo = ['openai', 'google', 'bytedance', 'xai', 'qwen', 'bfl', 'kling'];
	// 无静态 logo → 走首字母渐变回退
	const noLogo = ['stability', 'minimax', 'recraft', 'tencent', 'nvidia', 'zhipu'];
</script>

<DemoCard
	title="VendorLogo"
	desc={$i18n.t('Provider logo with graceful fallback to gradient initial disc on 404.')}
>
	<div class="flex flex-col gap-3 w-full">
		<div class="flex flex-wrap gap-3">
			{#each withLogo as p (p)}
				<div class="flex flex-col items-center gap-1">
					<VendorLogo provider={p} className="size-8 rounded-md" />
					<span class="text-[9px] text-gray-400">{p}</span>
				</div>
			{/each}
		</div>
		<div class="flex flex-wrap gap-3">
			{#each noLogo as p (p)}
				<div class="flex flex-col items-center gap-1">
					<VendorLogo provider={p} className="size-8 rounded-md" />
					<span class="text-[9px] text-gray-400">{p}</span>
				</div>
			{/each}
		</div>
	</div>
</DemoCard>
