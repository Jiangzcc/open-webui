import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Discover.svelte', import.meta.url)), 'utf-8');
const detailsSource = readFileSync(
	fileURLToPath(new URL('./DiscoveryDetailsModal.svelte', import.meta.url)),
	'utf-8'
);

describe('Discover responsive shell', () => {
	test('reserves desktop space for the expanded application sidebar', () => {
		expect(source).toContain('$showSidebar');
		expect(source).toContain('md:max-w-[calc(100%-var(--sidebar-width))]');
		expect(source).toContain('transition-width');
	});

	test('provides the application sidebar toggle on mobile', () => {
		expect(source).toContain('{#if $mobile}');
		expect(source).toContain('id="sidebar-toggle-button"');
		expect(source).toContain('showSidebar.set(!$showSidebar)');
		expect(source).toContain('<SidebarIcon />');
		expect(source).toContain('aria-label={$showSidebar');
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
