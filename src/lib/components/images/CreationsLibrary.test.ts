import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./CreationsLibrary.svelte', import.meta.url)),
	'utf-8'
);
const headerSource = readFileSync(
	fileURLToPath(new URL('../common/MediaGalleryHeader.svelte', import.meta.url)),
	'utf-8'
);

describe('CreationsLibrary source contract', () => {
	test('lazy loads original images and exposes details on touch', () => {
		expect(source).toContain('loading="lazy"');
		expect(source).toContain('decoding="async"');
		// 卡片点击通过 handleCardClick → openDetails 打开详情弹窗，不再有独立的 "Details" 按钮。
		expect(source).toContain('openDetails');
		expect(source).toContain('<Loader');
		// 独立 owner 标注已从卡片移除。
		expect(source).not.toContain("$i18n.t('Deleted user')");
	});

	test('keeps cards artwork-focused without a prompt overlay', () => {
		// 卡片重新设计后不再显示 prompt 预览浮层；prompt 仅在详情弹窗中展示。
		expect(source).not.toContain('{item.prompt_preview}');
		expect(source).not.toContain('line-clamp-2');
		// 悬浮透明度只服务视频预览，不重新引入 prompt 覆盖层。
		expect(source).toContain('group-hover:opacity-100');
		expect(source).not.toContain('from-black/70');
		expect(source).not.toContain('.prompt-overlay');
	});

	test('opens details on a single card click without a selection mode', () => {
		// 批量选择/ZIP/批量删除随「选择」按钮一并移除（重置取代之）；卡片点击只开详情。
		expect(source).toContain('on:click={() => openDetails(item)}');
		expect(source).not.toContain('handleCardClick');
		expect(source).not.toContain('selectionMode');
		expect(source).not.toContain('toggleSelected');
		expect(source).not.toContain('Download ZIP');
		expect(source).not.toContain('deleteCreations');
		expect(source).not.toContain("$i18n.t('Details')");
		expect(source).not.toContain('details-btn');
	});

	test('receives scope from its parent instead of rendering a scope switcher', () => {
		expect(source).toContain('export let scope: CreationScope');
		// The scope selector lives in the parent pill now; the library must not redraw it.
		expect(source).not.toContain("$i18n.t('My creations')");
		expect(source).not.toContain("$i18n.t('All creations')");
		expect(source).not.toContain('selectScope');
	});

	test('strips owner identity off the cards so it lives only in the detail modal', () => {
		// Owner name/email moved into CreationDetailsModal; the gallery card must
		// no longer render any owner attribution regardless of scope/role.
		expect(source).not.toContain("'owner' in item");
		expect(source).not.toContain('.owner.');
		expect(source).not.toContain("$i18n.t('Deleted user')");
		expect(source).not.toContain("$i18n.t('Email')");
	});

	test('declares the documented props', () => {
		expect(source).toContain('export let active');
		expect(source).toContain('export let scope');
		expect(source).toContain('export let revision');
		// 媒体类型并入类型筛选后不再有 mediaKind prop。
		expect(source).not.toContain('export let mediaKind');
		expect(source).not.toContain('export let onCreate');
	});

	test('uses the creations api and scope state helpers', () => {
		expect(source).toContain('listCreations');
		expect(source).toContain('listAdminCreations');
		expect(source).toContain('createCreationScopeState');
		expect(source).toContain('beginCreationRequest');
		expect(source).toContain('applyCreationPage');
	});

	test('lays cards out in a polished uniform crop grid', () => {
		expect(source).toContain('aspect-video');
		expect(source).toContain('object-cover');
		expect(source).toContain('overflow-hidden rounded-[14px] bg-gray-200/70');
		expect(source).toContain('active:scale-[0.99]');
		expect(source).toContain('group-hover:-translate-y-0.5');
		expect(source).toContain('group-hover:shadow-[');
		expect(source).toContain('group-hover:scale-[1.025]');
		expect(source).toContain('grid-cols-1');
		expect(source).toContain('sm:grid-cols-2');
		expect(source).toContain('md:grid-cols-3');
		expect(source).toContain('xl:grid-cols-4');
		expect(source).toContain('new Date(item.created_at * 1000).toLocaleDateString()');
		expect(source).toContain('const creationTitle = (item: CreationSummary) =>');
		// 视频磁贴播放按钮用 Play 图标组件，不用跨系统字形不一致的文本「▶」。
		expect(source).toContain('<Play className=');
		expect(source).not.toContain('▶');
		expect(source).not.toContain('assignLanes');
		expect(source).not.toContain('columns-2');
		expect(source).not.toContain('break-inside-avoid');
		expect(source).not.toContain('aspect-square');
	});

	test('autoplays video previews on hover-capable devices', () => {
		expect(source).toContain('playMutedPreview(previewVideos[id], hoverCapable)');
		expect(source).toContain("matchMedia('(hover: hover)')");
		expect(source).toContain('bind:this={previewVideos[item.id]}');
		expect(source).toContain('on:mouseenter={() => playPreview(item.id)}');
		expect(source).toContain('on:mouseleave={() => stopPreview(item.id)}');
	});

	test('keeps artwork as the card focus without model labels', () => {
		expect(source).not.toContain("$i18n.t('Unknown model')");
		expect(source).not.toContain('item.model_name ??');
	});

	test('opens the details modal lazily', () => {
		expect(source).toContain('CreationDetailsModal');
		expect(source).toContain('listCreations');
		expect(source).toContain('listAdminCreations');
	});

	test('invalidates Svelte state after helper mutations', () => {
		expect(source).toContain('scopes = { ...scopes };');
	});

	test('projects saved captions into every cached scope immediately', () => {
		expect(source).toContain(
			'const onModalUpdated = (detail: CreationDetail | AdminCreationDetail) => {'
		);
		expect(source).toContain("for (const targetScope of ['mine', 'all'] as const)");
		expect(source).toContain('caption: detail.caption');
		expect(source).toContain('updated_at: detail.updated_at');
	});

	test('consumes each generation revision once and refreshes stale state on activation', () => {
		expect(source).toContain('let appliedRevision = 0;');
		expect(source).toContain('revision > appliedRevision');
		expect(source).toContain('activeState.stale && !activeState.loading');
	});

	test('merges kind and task into one type filter with attribute filters', () => {
		// 类型筛选：图片/视频 → kind，创作方式 → task；
		// 时间/清晰度/比例走后端归一化列的等值筛选。
		// 重构后筛选配置单点化（RAW_FILTER_SELECTS），移动面板与桌面行共用同一份。
		expect(source).toContain('const selectTypeFilter = (value: string) => {');
		expect(source).toContain("if (value === 'image' || value === 'video')");
		expect(source).toContain('const RAW_FILTER_SELECTS: FilterSelectConfig[] = [');
		expect(source).toContain('onChange: selectTypeFilter');
		expect(source).toContain("updateFilters({ since: since as CreationListFilters['since'] })");
		expect(source).toContain(
			"updateFilters({ clarity: clarity as CreationListFilters['clarity'] })"
		);
		expect(source).toContain(
			"updateFilters({ aspectRatio: aspectRatio as CreationListFilters['aspectRatio'] })"
		);
		// 比例标签形如 16:9，不能过 i18n（冒号会被 namespace 分隔符误拆），原样渲染。
		expect(source).toContain(
			'...CREATION_ASPECT_RATIOS.map((ratio) => ({ value: ratio, label: ratio, raw: true }))'
		);
		expect(source).toContain('label: item.raw ? item.label : $i18n.t(item.label)');
		// 三处渲染都从同一配置源派生（移动面板 + 桌面高频项 + 高级项）。
		expect(source).toContain('{#each panelSelects as select (select.key)}');
		expect(source).toContain('{#each primaryDesktopSelects as select (select.key)}');
		expect(source).toContain('{#each advancedDesktopSelects as select (select.key)}');
		// 激活判定：各筛选取值点亮，排序偏离默认时点亮。
		expect(source).toContain('active: (filters) => Boolean(filters.clarity)');
		expect(source).toContain('active: (filters) => filters.sort !== DEFAULT_FILTERS.sort');
	});

	test('collapses the mobile toolbar into one row with a filter drawer', () => {
		// 用户拍板：移动端顶部堆叠太占空间。常驻只留一行（搜索为主 +
		// 排序 + 筛选入口），其余筛选与重置收进展开面板，徽标提示生效数。
		expect(source).toContain('flex items-center gap-2 md:hidden');
		expect(source).toContain('aria-expanded={mobileFiltersOpen}');
		expect(source).toContain('aria-controls="mobile-filter-panel"');
		expect(source).toContain('transition:slide={{ duration: 150 }}');
		expect(source).toContain('$: panelFilterCount =');
		// 面板内筛选撑满网格单元。
		expect(source).toContain('fullWidth');
		// 胶囊横滑行退场：移动端不再横滑，桌面端改为换行。
		expect(source).not.toContain('overflow-x-auto');
		expect(source).not.toContain('scrollbar-none');
	});

	test('adopts the vidu-style pill row with inline search and an end-of-list marker', () => {
		// 与发现页共用同一个标题/筛选玻璃容器，不再维护第二层伪标题栏。
		expect(source).toContain('<MediaGalleryHeader');
		expect(headerSource).toContain('backdrop-filter: blur(24px) saturate(165%) contrast(1.03)');
		expect(source).toContain('class="min-h-full bg-transparent"');
		expect(source).toContain('<div class="pb-2">');
		expect(source).not.toContain('sticky top-0 z-20 border-b');
		// 桌面端常显高频筛选，低频条件收进高级筛选区，搜索保持靠右。
		expect(source).toContain('hidden items-center gap-2 md:flex');
		expect(source).toContain('aria-controls="desktop-filter-panel"');
		expect(source).toContain('w-[min(18rem,28vw)] min-w-44');
		const desktopToolbar = source.slice(
			source.indexOf('<!-- 桌面端只保留高频条件'),
			source.indexOf('</div>', source.lastIndexOf('bind:value={searchDraft}')) + 6
		);
		expect(desktopToolbar).toContain('fullWidth');
		expect(desktopToolbar).toContain("select.key === 'type' ? 'w-40 shrink-0' : 'w-36 shrink-0'");
		// 移动面板的重置无可清除条件时禁用，避免「点了没反应」的假按钮。
		expect(source).toContain('disabled={!hasActiveFilters && !searchDraft}');
		// 列表底部给出「已加载全部内容」终态提示（vidu 同款）。
		expect(source).toContain("$i18n.t('All creations loaded.')");
	});

	test('resets every filter and keeps the desktop search box last in the toolbar', () => {
		expect(source).toContain('const resetFilters = () => {');
		expect(source).toContain('DEFAULT_FILTERS');
		// 搜索框双份渲染（移动行 + 桌面行）：桌面端那份排在桌面筛选胶囊行之后。
		expect(source.match(/bind:value=\{searchDraft\}/g)?.length).toBe(2);
		expect(source.lastIndexOf('bind:value={searchDraft}')).toBeGreaterThan(
			source.lastIndexOf('{#each primaryDesktopSelects as select (select.key)}')
		);
	});

	test('keeps the empty state honest about filters versus a fresh library', () => {
		expect(source).toContain('$: hasActiveFilters = Boolean(');
		expect(source).toContain("$i18n.t('No creations match the current filters.')");
		expect(source).toContain("$i18n.t('Newly generated images and videos will appear here.')");
		// 空态是行动邀请：无筛选给「开始创作」入口（跳图片页），有筛选给重置出路。
		expect(source).toContain("{$i18n.t('Start creating')}");
		expect(source).toContain("on:click={() => goto('/images')}");
		// 「启用此功能前生成的作品不计入在内」属装饰性文案，随页头一起精简。
		expect(source).not.toContain('Creations recorded before this feature');
	});

	test('does not auto-loop after an initial load failure', () => {
		expect(source).toContain('!activeState.loading && !activeState.error');
	});

	test('keeps loaded cards visible when pagination fails', () => {
		expect(source).toContain('state.error && state.items.length === 0');
		expect(source).toContain('state.error && state.items.length > 0');
	});

	test('keeps mobile touch targets while compacting pills on desktop', () => {
		const filterSelect = readFileSync(
			fileURLToPath(new URL('./LibraryFilterSelect.svelte', import.meta.url)),
			'utf-8'
		);
		// 768px 以下控件保持 44px 触控高度；桌面端收紧到 36px。
		expect(source).toContain('min-h-11');
		expect(filterSelect).toContain('min-h-11 shrink-0');
		expect(filterSelect).toContain('md:h-9 md:min-h-0');
		expect(filterSelect).toContain('flex w-full min-w-0 items-center justify-between gap-2');
	});

	test('removes a deleted owner item from both cached admin scopes', () => {
		expect(source).toContain("for (const targetScope of ['mine', 'all'] as const)");
		expect(source).toContain('removeCreationOptimistically(scopes[targetScope], creationId)');
		expect(source).not.toContain("if (scope === 'all')");
	});

	test('offers a non-hover retry affordance', () => {
		expect(source).toContain("$i18n.t('Retry')");
	});

	test('enables admin management from the global library detail', () => {
		expect(source).toContain("canManage={scope === 'mine' || scope === 'all'}");
	});

	test('uses the shared play icon instead of a text glyph on video tiles', () => {
		expect(source).toContain("import Play from '$lib/components/icons/Play.svelte'");
		expect(source).not.toContain('\u25b6');
	});

	test('gives toolbar toggles, reset and retry buttons press feedback', () => {
		// 与全应用按压语言统一：筛选、重置和重试按钮均提供微缩反馈。
		expect(source).toContain('active:scale-[0.98]');
		const filterSelect = readFileSync(
			fileURLToPath(new URL('./LibraryFilterSelect.svelte', import.meta.url)),
			'utf-8'
		);
		expect(filterSelect).toContain('active:scale-[0.98]');
	});
});
