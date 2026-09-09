<script lang="ts">
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';

	import { showSidebar, user, WEBUI_NAME } from '$lib/stores';
	import {
		storePendingCreationDraft,
		type ImageCreationDraft
	} from '$lib/utils/image-generation-batches';
	import type { CreationScope } from '$lib/utils/creations-library';

	import CreationsLibrary from '$lib/components/images/CreationsLibrary.svelte';
	import MediaGallerySurface from '$lib/components/common/MediaGallerySurface.svelte';
	import MobileSidebarHeader from '$lib/components/common/MobileSidebarHeader.svelte';

	const i18n = getContext<Writable<I18n>>('i18n');

	// 「我的作品」所有用户可见；「全部作品」仅管理员可见。
	const SCOPE_OPTIONS: ReadonlyArray<{ value: CreationScope; label: string }> = [
		{ value: 'mine', label: 'My creations' },
		{ value: 'all', label: 'All creations' }
	];

	let scope: CreationScope = 'mine';

	$: isAdmin = $user?.role === 'admin';
	$: scopeOptions = isAdmin ? SCOPE_OPTIONS : SCOPE_OPTIONS.slice(0, 1);
	$: scopeNavigationItems = scopeOptions.map((option) => ({
		value: option.value,
		label: $i18n.t(option.label)
	}));

	// 图片「再次创作」需要回到图片页表单：与发现页一致，先把草稿放进
	// sessionStorage 再跳转，由图片页挂载时消费；视频创作由详情弹窗自行写
	// video-creation-draft 并跳 /videos，不经过这个回调。
	const reuseImageCreation = async (draft: ImageCreationDraft) => {
		try {
			storePendingCreationDraft(sessionStorage, draft);
			await goto('/images');
		} catch {
			toast.error($i18n.t('Failed to load creation settings'));
		}
	};
</script>

<svelte:head>
	<title>{$i18n.t('Assets')} • {$WEBUI_NAME}</title>
</svelte:head>

<div
	class="relative flex h-screen max-h-[100dvh] w-full max-w-full min-w-0 flex-col transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''}"
>
	<MobileSidebarHeader />

	<MediaGallerySurface>
		<CreationsLibrary
			active
			{scope}
			headerTitle={$i18n.t('Assets')}
			headerItems={scopeNavigationItems}
			headerSelected={scope}
			headerAriaLabel={$i18n.t('Asset scope')}
			headerIdPrefix="asset-scope-tab"
			onHeaderSelect={(value) => (scope = value as CreationScope)}
			onReuse={reuseImageCreation}
		/>
	</MediaGallerySurface>
</div>
