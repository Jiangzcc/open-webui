import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Images.svelte', import.meta.url)), 'utf-8');

describe('images page controls', () => {
	test('shows the model selector beside the image options in the composer', () => {
		const composerStart = source.indexOf(
			'<div class="mt-2 flex h-8 items-center justify-between gap-2">'
		);
		const composerEnd = source.indexOf('</form>', composerStart);
		const composer = source.slice(composerStart, composerEnd);

		expect(composer).toContain('bind:this={modelSelectorElement}');
		expect(composer.indexOf('bind:this={modelSelectorElement}')).toBeLessThan(
			composer.indexOf('bind:this={imageOptionsElement}')
		);
	});

	test('uses concise option headings and omits generation mode helper text', () => {
		expect(source).toContain("$i18n.t('Ratio')");
		expect(source).toContain("$i18n.t('Resolution')");
		expect(source).toContain("$i18n.t('Quantity')");
		expect(source).not.toContain("$i18n.t('Select aspect ratio')");
		expect(source).not.toContain(': modeLabel}');
	});

	test('uses auto without ratio or resolution icons in the selected options', () => {
		const composerStart = source.indexOf(
			'<div class="mt-2 flex h-8 items-center justify-between gap-2">'
		);
		const composerEnd = source.indexOf('</form>', composerStart);
		const composer = source.slice(composerStart, composerEnd);

		expect(source).toContain("ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio");
		expect(composer).not.toMatch(/getAspectRatioPreviewClass\(\s*selectedAspectRatio\s*\)/);
		expect(composer).not.toContain('getAspectRatioPreviewStyle(selectedAspectRatio)');
		expect(source).not.toContain('<ArrowsPointingOut');
		expect(source).not.toContain('<Grid');
	});

	test('uses compact illustrative ratio thumbnails instead of exact large ratios', () => {
		expect(source).toContain('const previewSize = 20;');
		expect(source).toContain('const minimumPreviewSize = 12;');
		expect(source).toContain('Math.max(minimumPreviewSize');
	});

	test('shows only the model name in the trigger but keeps the provider in popup options', () => {
		expect(source).toContain('getImageModelDisplayName');
		expect(source).toContain('getImageModelDisplayName(selectedModelConfig)');
		expect(source).toContain('<span class="truncate">{model.name ?? model.id}</span>');
		expect(source).not.toContain('getImageModelDisplayName(model)');
	});

	test('keeps only the mobile sidebar toggle in the page header', () => {
		const navStart = source.indexOf('<nav ');
		const navEnd = source.indexOf('</nav>', navStart);
		const nav = source.slice(navStart, navEnd);

		expect(nav).toContain('SidebarIcon');
		expect(nav).not.toContain("$i18n.t('Images')");
		expect(nav).not.toContain('bind:this={modelSelectorElement}');
	});
});
