import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Discover.svelte', import.meta.url)), 'utf-8');
const navigationSource = readFileSync(
	fileURLToPath(new URL('../common/MediaGalleryNavigation.svelte', import.meta.url)),
	'utf-8'
);
const headerSource = readFileSync(
	fileURLToPath(new URL('../common/MediaGalleryHeader.svelte', import.meta.url)),
	'utf-8'
);
const surfaceSource = readFileSync(
	fileURLToPath(new URL('../common/MediaGallerySurface.svelte', import.meta.url)),
	'utf-8'
);
const detailsSource = readFileSync(
	fileURLToPath(new URL('./DiscoveryDetailsModal.svelte', import.meta.url)),
	'utf-8'
);
const viewerShellSource = readFileSync(
	fileURLToPath(new URL('../images/ArtworkViewerShell.svelte', import.meta.url)),
	'utf-8'
);

describe('Discover responsive shell', () => {
	test('reserves desktop space for the expanded application sidebar', () => {
		expect(source).toContain('$showSidebar');
		expect(source).toContain('md:max-w-[calc(100%-var(--sidebar-width))]');
		expect(source).toContain('transition-width');
	});

	test('uses the shared mobile sidebar header like the assets page', () => {
		// 移动端顶部栏与资产页统一走 MobileSidebarHeader（含侧栏开关与 aria 标签）。
		expect(source).toContain('<MobileSidebarHeader />');
		expect(source).not.toContain('id="sidebar-toggle-button"');
	});

	test('matches the assets page horizontal spacing and sticky navigation convention', () => {
		expect(headerSource).toContain('sticky top-0 z-20');
		expect(headerSource).toContain('max-w-[96rem] px-4 sm:px-6 lg:px-8');
		expect(surfaceSource).toContain('scrollbar-gutter: stable');
		expect(source).toContain('px-4 pb-12 pt-5 sm:px-6 lg:px-8');
		expect(source).not.toContain('sm:pt-8');
	});
});

describe('Vidu-style discovery layout', () => {
	test('follows the application theme on both light and dark canvases', () => {
		// 浅色画布和偏冷深色画布都保留，不强制恒定深色。
		expect(source).toContain('<MediaGallerySurface>');
		expect(surfaceSource).toContain('background-color: #f2f4f7');
		expect(surfaceSource).toContain('background-color: #0b0e14');
		expect(source).not.toContain('bg-[#020b13]');
	});

	test('renders feed and filter rows as vidu text tabs in a single sub-row', () => {
		expect(source).toContain('<MediaGalleryHeader');
		expect(headerSource).toContain('<MediaGalleryNavigation');
		expect(navigationSource).toContain('role="tablist"');
		expect(source).not.toContain('rounded-full border border-gray-200/80 bg-white/80');
		// 主 tab 与资产页共用安静型导航，二级分类复用同一套低对比状态面。
		expect(navigationSource).toContain('gap-0.5 overflow-x-auto scrollbar-none');
		expect(navigationSource).toContain('after:h-0.5');
		expect(navigationSource).toContain('after:scale-x-100');
		expect(source).toContain(
			'min-h-11 items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none sm:min-h-9'
		);
		expect(source).toContain('min-h-11 shrink-0 whitespace-nowrap rounded-[10px]');
		expect(source).toContain('sm:min-h-9');
		expect(source).toContain('bg-[#5b6ee1]/10 font-medium text-[#4051bd]');
		// 媒体类型与分类合并进单行子筛选（竖分隔线分组），媒体类型点击已选项取消回到全部。
		expect(source).toContain('h-4 w-px shrink-0 bg-slate-300/70 dark:bg-white/10');
		expect(source).toContain(
			"const next: 'all' | 'image' | 'video' = activeMediaKind === mediaKind ? 'all' : mediaKind;"
		);
	});

	test('uses media-only masonry cards with metadata revealed on interaction', () => {
		expect(source).toContain('flex items-start gap-3');
		expect(source).toContain('flex min-w-0 flex-1 flex-col gap-3');
		expect(source).toContain('relative overflow-hidden rounded-[14px]');
		expect(source).toContain('grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5');
		expect(source).not.toContain('<h2');
		expect(source).not.toContain('item.featured');
		expect(source).not.toContain('item.title ?? item.owner.name');
		expect(source).not.toContain("item.kind === 'video' ? $i18n.t('Video')");
		expect(source).toContain("aria-label={$i18n.t('Like')}");
		expect(source).toContain("aria-label={$i18n.t('Favorite')}");
		expect(source).toContain("aria-label={item.title ?? $i18n.t('View creation')}");
		// 头像 16px、正文/计数 14px、图标 14px（vidu 实测）。
		expect(source).toContain('size-4 shrink-0 rounded-full object-cover');
		expect(source).toContain('class="truncate text-sm text-white/80"');
		// 做同款保留在媒体表面，作者与互动信息只在悬浮或键盘聚焦时出现。
		expect(source).toContain('absolute right-2 top-2 z-10 min-h-9');
		expect(source).not.toContain('max-h-0 overflow-hidden');
	});

	test('balances the masonry by placing each item into the shortest column', () => {
		// 轮转分列会造成列高不齐（用户实测反馈）；vidu 是最短列优先的均衡布局，
		// 用后端 aspect_ratio 在渲染前确定性估算卡片高度，避免渲染后重排闪动。
		expect(source).toContain('function balanceMasonry(');
		expect(source).toContain('if (heights[column] < heights[shortest]) shortest = column;');
		expect(source).toContain('function parseAspect(');
		expect(source).toContain('new ResizeObserver(');
		expect(source).not.toContain('% masonryColumnCount');
		// P1 定稿（拍板：前端兜底）：容器强制比例 + object-cover，渲染高度与估算
		// 完全一致——列高必然均衡、零 CLS；无比例视频的海报按兜底比例裁切。
		expect(source).toContain('function cardAspectRatioStyle(');
		expect(source).toContain('style={cardAspectRatioStyle(item)}');
		expect(source).toContain('class="h-full w-full object-cover transition');
	});

	test('offers the vidu make-same hover action straight from the card', () => {
		expect(source).toContain("$i18n.t('Make similar')");
		expect(source).toContain('getDiscoveryPost(localStorage.token, item.id)');
		expect(source).toContain('buildCreationDraft(');
		expect(source).toContain("'video-creation-draft'");
		// 仅 hover/focus 可见且不拦截触屏点击：pointer-events 默认关闭。
		expect(source).toContain('pointer-events-none');
		expect(source).toContain('group-hover:pointer-events-auto');
	});

	test('reveals the floating footer on hover only and autoplays video previews', () => {
		// vidu 交互：信息栏浮层默认隐藏、hover 卡片浮现，键盘焦点（focus-within）可唤出；
		// 触屏不常显（用户拍板），点赞/收藏走详情弹窗。
		expect(source).toContain(
			'pointer-events-none absolute inset-x-0 bottom-0 z-10 flex items-center justify-between gap-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-2 pb-1.5 pt-7 opacity-0 transition group-focus-within:opacity-100 group-hover:opacity-100'
		);
		expect(source).not.toContain('pointer-coarse:opacity-100');
		expect(source).not.toContain('pointer-coarse:pointer-events-auto');
		// 视频卡片 hover 自动静音播放，移出即停；仅 hover 设备启用。
		expect(source).toContain('const playPreview = (id: string) => {');
		expect(source).toContain("matchMedia('(hover: hover)')");
		expect(source).toContain('muted');
		expect(source).toContain('playsinline');
	});

	test('lets the details modal follow the application theme', () => {
		// 恒定深色画布已废弃（用户拍板改主题跟随），forceDark 机制随之移除。
		expect(source).not.toContain('forceDark');
		expect(detailsSource).not.toContain('forceDark');
		expect(viewerShellSource).not.toContain('forceDark');
	});
});

describe('Discovery creation reuse', () => {
	test('hands an ephemeral draft to the Images page', () => {
		expect(source).toContain('storePendingCreationDraft(sessionStorage, draft)');
		expect(source).toContain("await goto('/images')");
		expect(source).toContain('onReuse={reuseCreation}');
	});

	test('exposes creation actions, prompt copy, and generation metadata', () => {
		expect(detailsSource).toContain("$i18n.t('Create again')");
		expect(detailsSource).toContain("$i18n.t('Use as reference')");
		expect(detailsSource).not.toContain("$i18n.t('Download')");
		expect(detailsSource).toContain('copyToClipboard(detail.prompt)');
		expect(detailsSource).toContain('detail.model_name ?? detail.model_id');
		expect(detailsSource).toContain('extractParamTags(detail.params)');
	});

	test('keeps reactions at the bottom while constraining long prompts and balancing reuse actions', () => {
		const likeAction = detailsSource.indexOf("toggleReaction('like')");
		const promptContent = detailsSource.indexOf("$i18n.t('Prompt')");

		expect(likeAction).toBeGreaterThan(-1);
		expect(likeAction).toBeGreaterThan(promptContent);
		expect(detailsSource).toContain('max-h-48 overflow-y-auto overscroll-contain pr-1');
		expect(detailsSource).toContain("aria-label={$i18n.t('Like')}");
		expect(detailsSource).toContain("aria-label={$i18n.t('Favorite')}");
		expect(detailsSource).toContain(
			"{detail.content_url\n\t\t\t\t\t\t\t? ''\n\t\t\t\t\t\t\t: 'col-span-2'}"
		);
		expect(detailsSource).toContain(
			"{detail.prompt\n\t\t\t\t\t\t\t? ''\n\t\t\t\t\t\t\t: 'col-span-2'}"
		);
		expect(detailsSource).toContain('mt-auto grid grid-cols-2');
	});
});

describe('Discover interaction polish', () => {
	test('removes overlay motion without forcing every overlay to stay visible', () => {
		// reduced-motion 只关闭动画；不应该把所有卡片操作常驻，否则作品墙会被重复按钮淹没。
		expect(source).toContain('motion-reduce:transition-none');
		expect(source).not.toContain('motion-reduce:opacity-100');
		expect(source).not.toContain('motion-reduce:pointer-events-auto');
		expect(source).not.toContain("matchMedia('(prefers-reduced-motion: reduce)')");
	});

	test('allows explicit hover video preview while disabling visual transitions under reduced motion', () => {
		expect(source).toContain('playMutedPreview(previewVideos[id], hoverCapable)');
		expect(source).not.toContain('|| reducedMotion');
		expect(source).toContain('group-hover:scale-[1.025] motion-reduce:transition-none');
	});

	test('announces the end of the feed like the assets page', () => {
		// 资产页同款终态：nextCursor 耗尽且非加载中时提示已加载全部。
		expect(source).toContain('{#if !state.nextCursor && !state.loading && state.loaded}');
		expect(source).toContain("$i18n.t('All creations loaded.')");
	});

	test('gives overlay buttons and tabs tactile press feedback', () => {
		// 分类状态块、共享导航与点赞/收藏图标都有按压反馈。
		expect(source).toContain('active:scale-[0.98]');
		expect(source).toContain('active:scale-90');
		expect(navigationSource).toContain('active:scale-[0.98]');
	});

	test('replaces the play text glyph with the shared icon component', () => {
		// 文本字符 ▶ 在不同平台渲染尺寸/基线不一致，统一走图标组件。
		expect(source).toContain("import Play from '$lib/components/icons/Play.svelte'");
		expect(source).not.toContain('\u25b6');
	});

	test('labels every task kind in the details modal and shows load failures inline', () => {
		// 视频任务此前被三元误标成「文生图」；加载失败此前只 toast、弹窗本身空白。
		expect(detailsSource).toContain('TASK_LABELS');
		expect(detailsSource).toContain("'text-to-video': $i18n.t('Text to Video')");
		expect(detailsSource).toContain("'video-to-video': $i18n.t('Video to Video')");
		expect(detailsSource).not.toContain("? $i18n.t('Image to Image')");
		expect(detailsSource).toContain('loadError = true');
		expect(detailsSource).toContain("error={loadError ? $i18n.t('Failed to load post') : null}");
	});

	test('gives details modal buttons the same press feedback as the assets modal', () => {
		expect(detailsSource).toContain('active:scale-[0.98]');
		expect(detailsSource).toContain('active:scale-90');
	});
});
