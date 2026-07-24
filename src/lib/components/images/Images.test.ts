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

	test('quotes the selected or default model before a prompt is entered', () => {
		expect(source).toContain('const CREDIT_QUOTE_PLACEHOLDER_PROMPT =');
		expect(source).toContain('prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT');
		expect(source).not.toContain('quotePrompt: string');
		expect(source).toContain('$: selectedModelConfig =');
		expect(source).toContain('models.find((model) => model.isDefault) ?? models[0] ?? null');
		expect(source).toContain('buildImageQuoteInput(\n\t\tselectedAspectRatio,');
		expect(source).toContain('\n\t\treferenceImages\n\t)');
		expect(source).toContain('$: if (loaded && quoteInput) {');
	});

	test('uses a generic localized error instead of stringifying submission API errors', () => {
		const submitHandlerStart = source.indexOf('const submitHandler = async () => {');
		const submitHandlerEnd = source.indexOf('\n\tonMount', submitHandlerStart);
		const submitHandler = source.slice(submitHandlerStart, submitHandlerEnd);

		expect(submitHandler).toContain('toast.error(imageGenerationErrorMessage(error))');
		expect(submitHandler).not.toContain('toast.error(`${error}`)');
	});

	test('places the credit quote directly before the submit button on the right', () => {
		const toolbarStart = source.indexOf(
			'<div class="mt-2 flex h-8 items-center justify-between gap-2">'
		);
		const toolbarEnd = source.indexOf('</form>', toolbarStart);
		const toolbar = source.slice(toolbarStart, toolbarEnd);

		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeGreaterThan(
			toolbar.indexOf('bind:this={imageOptionsElement}')
		);
		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeLessThan(
			toolbar.indexOf('type="submit"')
		);
	});

	test('does not render loading text while the credit quote is pending', () => {
		const badgeSource = readFileSync(
			fileURLToPath(new URL('../credits/ImageCreditQuoteBadge.svelte', import.meta.url)),
			'utf-8'
		);

		expect(badgeSource).not.toContain("$i18n.t('credits.common.loading')");
	});

	test('uses accessible generate and library tabs without unmounting page state', () => {
		expect(source).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(source).toContain('role="tablist"');
		expect(source).toContain('role="tab"');
		expect(source).toContain('aria-selected={selection ===');
		expect(source).toContain('on:keydown={handleTabKeydown}');
		expect(source).toContain('aria-labelledby="images-generate-tab"');
		expect(source).toContain(
			"aria-labelledby={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}"
		);
		expect(source).toContain('id="images-library-panel"');
		expect(source).toContain("hidden={view !== 'library'}");
		expect(source).not.toContain('{#if canUseImages}');
	});

	test('lifts the three-segment pill out of flow so the library tops out', () => {
		expect(source).toContain('pointer-events-none absolute inset-x-0');
		expect(source).toContain('pointer-events-auto');
		expect(source).toContain("$i18n.t('My creations')");
		expect(source).toContain('{#if isAdmin}');
		expect(source).toContain('id="images-admin-tab"');
		expect(source).toContain("$i18n.t('All creations')");
		expect(source).toContain("selectSelection('all')");
	});

	test('lets the library scroller hug the viewport edge', () => {
		const panelStart = source.indexOf('id="images-library-panel"');
		const panelDecl = source.slice(panelStart, panelStart + 280);
		expect(panelDecl).toContain('overflow-y-auto');
		expect(panelDecl).not.toContain('px-3');
		expect(panelDecl).not.toContain('md:px-6');
	});

	test('styles image tabs as a centered floating pill while preserving accessibility', () => {
		expect(source).toContain('rounded-full border border-gray-200/80');
		expect(source).toContain('bg-white/80');
		expect(source).toContain('backdrop-blur-xl');
		expect(source).toContain('shadow-lg shadow-black/10');
		expect(source).toContain('aria-selected={selection ===');
		expect(source).toContain('on:keydown={handleTabKeydown}');
	});

	test('derives view and library scope from the unified selection', () => {
		expect(source).toContain("$: view = selection === 'generate' ? 'generate' : 'library';");
		expect(source).toContain("$: libraryScope = selection === 'all' ? 'all' : 'mine';");
		expect(source).toMatch(/hidden=\{view !== 'generate'\}|hidden=\{view === 'library'\}/);
	});

	test('increments library revision after a successful generation', () => {
		const success = source.slice(
			source.indexOf('generatedImages = ['),
			source.indexOf('} catch', source.indexOf('generatedImages = ['))
		);
		expect(success).toContain('libraryRevision += 1;');
	});

	test('drops the canUseImagesPage import and reactive gate', () => {
		expect(source).not.toContain('canUseImagesPage');
		expect(source).not.toContain('$: canUseImages =');
		expect(source).not.toContain("$i18n.t('Image generation is not available')");
	});
});
