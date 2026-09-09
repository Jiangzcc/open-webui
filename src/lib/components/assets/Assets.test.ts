import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const read = (relative: string) =>
	readFileSync(fileURLToPath(new URL(relative, import.meta.url)), 'utf-8');

const route = read('../../../routes/(app)/assets/+page.svelte');
const page = read('./Assets.svelte');
const library = read('../images/CreationsLibrary.svelte');
const header = read('../common/MediaGalleryHeader.svelte');
const navigation = read('../common/MediaGalleryNavigation.svelte');
const surface = read('../common/MediaGallerySurface.svelte');
const api = read('../../apis/creations/index.ts');

describe('assets page', () => {
	test('mounts the assets component at /assets', () => {
		expect(route).toContain("import Assets from '$lib/components/assets/Assets.svelte'");
		expect(route).toContain('<Assets />');
	});

	test('uses the shared editorial page header without decorative copy', () => {
		expect(library).toContain('<MediaGalleryHeader');
		expect(header).toContain('<header');
		expect(header).toContain('<h1');
		expect(page).not.toContain('Every image and video');
		expect(page).not.toContain('aria-pressed={mediaKind ===');
		expect(page).toContain('<CreationsLibrary');
		expect(page).toContain('<MediaGallerySurface>');
		expect(surface).toContain('background-color: #f2f4f7');
		expect(surface).toContain('background-color: #0b0e14');
	});

	test('shows My creations to everyone while All creations stays admin-only', () => {
		// 「我的作品」所有用户可见；「全部作品」仅管理员追加（页签行不再包
		// {#if isAdmin}，普通用户也能看到自己的作品范围切换入口）。
		// 单页签（非管理员）在移动端没有切换功能，隐藏以省纵向空间（用户拍板）。
		expect(page).toContain("$: isAdmin = $user?.role === 'admin';");
		expect(page).toContain(
			'$: scopeOptions = isAdmin ? SCOPE_OPTIONS : SCOPE_OPTIONS.slice(0, 1);'
		);
		expect(page).not.toContain('{#if isAdmin}');
		expect(header).toContain('{#if items.length > 1}');
		expect(page).toContain("{ value: 'mine', label: 'My creations' }");
		expect(page).toContain("{ value: 'all', label: 'All creations' }");
		expect(library).toContain('<MediaGalleryHeader');
		expect(header).toContain('<MediaGalleryNavigation');
		expect(navigation).toContain('aria-selected={selected === item.value}');
	});

	test('centers the tool column with breathing room instead of hugging the edge', () => {
		// 与发现页同一版式：玻璃表面全宽，内部内容限宽 96rem 居中。
		expect(library).toContain('max-w-[96rem]');
		expect(header).toContain('mx-auto w-full max-w-[96rem] px-4 sm:px-6 lg:px-8');
		expect(page).not.toContain('mx-auto h-full w-full max-w-[96rem]');
		expect(page).toContain('headerItems={scopeNavigationItems}');
		expect(page).toContain("headerTitle={$i18n.t('Assets')}");
	});

	test('uses the shared editorial navigation separated from the workspace', () => {
		expect(header).toContain("? 'media-gallery-header--divided'");
		expect(header).toContain('backdrop-filter: blur(24px) saturate(165%) contrast(1.03)');
		expect(header).toContain('inset 0 1px 0 rgb(255 255 255 / 0.9)');
		expect(header).toContain('flex h-[52px] min-w-0 items-center');
		expect(header).toContain('@media (prefers-reduced-transparency: reduce)');
		expect(library).not.toContain('divider={false}');
		expect(library).toContain(
			"import MediaGalleryHeader from '$lib/components/common/MediaGalleryHeader.svelte'"
		);
		expect(library).toContain('onSelect={onHeaderSelect}');
		expect(navigation).toContain('after:h-0.5');
		expect(navigation).toContain('after:scale-x-100');
		expect(navigation).not.toContain('bg-gray-100 font-medium text-gray-950');
		expect(navigation).toContain("event.key !== 'ArrowLeft'");
	});

	test('reuses image creations through the pending draft and navigation', () => {
		// 与发现页一致：图片「再次创作」先写 sessionStorage 草稿再跳 /images；
		// 视频端由详情弹窗自行写 video-creation-draft 并跳 /videos。
		expect(page).toContain('storePendingCreationDraft(sessionStorage, draft)');
		expect(page).toContain("await goto('/images')");
	});

	test('renders the shared mobile sidebar header and sets the page title', () => {
		expect(page).toContain('<MobileSidebarHeader />');
		expect(page).toContain("{$i18n.t('Assets')} • {$WEBUI_NAME}");
	});

	test('keeps the library as the flexible scroll area of a fixed-height page', () => {
		expect(page).toContain('h-screen max-h-[100dvh]');
		expect(surface).toContain('min-h-0 min-w-0 flex-1 overflow-y-auto');
		expect(surface).toContain('scrollbar-gutter: stable');
	});

	test('library toolbar carries the normalized filter params through the API', () => {
		expect(library).toContain('const selectTypeFilter = (value: string) => {');
		expect(library).toContain('updateFilters({ since:');
		expect(library).toContain('updateFilters({ clarity:');
		expect(library).toContain('updateFilters({ aspectRatio:');
		// 时间窗口在请求时换算成 since 时间戳（窗口随请求时刻滚动）。
		expect(api).toContain('SINCE_WINDOW_SECONDS');
		expect(api).toContain("'since'");
		expect(api).toContain("params.set('clarity', filters.clarity)");
		expect(api).toContain("params.set('aspect_ratio', filters.aspectRatio)");
	});
});
