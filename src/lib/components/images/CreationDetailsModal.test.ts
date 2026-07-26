import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./CreationDetailsModal.svelte', import.meta.url)),
	'utf-8'
);

describe('CreationDetailsModal source contract', () => {
	test('declares the documented props', () => {
		expect(source).toContain('export let show');
		expect(source).toContain('export let creationId');
		expect(source).toContain('export let scope');
		expect(source).toContain('export let canManage');
		expect(source).toContain('export let onUpdated');
		expect(source).toContain('export let onRemoved');
	});

	test('loads detail lazily and caches by scope:id', () => {
		expect(source).toContain('getCreation');
		expect(source).toContain('getAdminCreation');
		expect(source).toContain('cacheKey');
		expect(source).toContain('${targetScope}:${sid}');
	});

	test('ignores detail responses superseded by a newer selection', () => {
		expect(source).toContain('let detailRequestGeneration = 0;');
		expect(source).toContain('generation !== detailRequestGeneration');
	});

	test('opens the result image in the existing preview and download surface', () => {
		expect(source).toContain('openPreview(detail.content_url as string');
		expect(source).toContain('<ImagePreview');
	});

	test('does not let a completed mutation close or overwrite a newer detail', () => {
		expect(source).toContain('const sid = creationId;');
		expect(source).toContain('creationId === sid && scope === requestedScope');
	});

	test('cancels pending detail only when an opened modal transitions closed', () => {
		expect(source).toContain('let wasShown = false;');
		expect(source).toContain('wasShown = true;');
		expect(source).toContain('$: if (!show && wasShown)');
	});

	test('collapses admin owner identity into a header badge with hover email', () => {
		// Per the redesign, owner name/email left the aside and moved into a
		// compact header badge; the email reveals on hover/focus rather than
		// occupying a permanent paragraph that crowds every reader's first frame.
		expect(source).toContain('isAdminScope()');
		expect(source).toContain("'owner' in detail");
		expect(source).toContain('detail.owner.name');
		expect(source).toContain('detail.owner.email');
		expect(source).toContain('href={`mailto:');
		expect(source).toContain('group-hover/admn:block');
		// The standalone "Owner:" / "Email:" labelling paragraphs are gone.
		expect(source).not.toContain("$i18n.t('Owner')");
		expect(source).not.toContain("$i18n.t('Email')");
	});

	test('renders ordered references with missing placeholders', () => {
		expect(source).toContain("$i18n.t('Reference images')");
		expect(source).toContain("$i18n.t('Reference image unavailable')");
		expect(source).toContain('loading="lazy"');
		expect(source).toContain('decoding="async"');
	});

	test('shows the prompt inline and renders parameters as labelled chips', () => {
		// The accordion/disclosure was retired: the prompt now stands as a
		// permanent section, and params render as a chip cloud sourced from the
		// curated extractor rather than a raw JSON dump.
		expect(source).toContain('<h3');
		expect(source).toContain("$i18n.t('Prompt')");
		expect(source).toContain('{detail.prompt}');
		expect(source).toContain('extractParamTags');
		expect(source).toContain('paramLabel');
		expect(source).toContain('flex flex-wrap gap-1.5');
		expect(source).not.toContain('{JSON.stringify(detail.params)}');
		expect(source).not.toContain('expandedDetails');
		expect(source).not.toContain("$i18n.t('Prompt & Parameters')");
	});

	test('surfaces the model as a chip and hides operational metadata', () => {
		// The model name joins the param chip cloud under a "Model:" label so the
		// reader sees one unified attribute strip. The debug-grade bookkeeping
		// fields — task enum, source channel, batch-id prefix — were retired from
		// the product surface; pin their absence so nobody revives that clutter.
		expect(source).toContain("$i18n.t('Model')");
		expect(source).toContain('{detail.model_name ?? detail.model_id}');
		expect(source).not.toContain('{detail.task}');
		expect(source).not.toContain('{detail.source}');
		expect(source).not.toContain('detail.batch_id');
	});

	test('uses an artwork-first responsive gallery layout', () => {
		expect(source).toContain('max-w-5xl');
		// Flex row on desktop lets the artwork column shrink to the image's
		// natural width instead of greedily filling 1fr, so the modal wraps the
		// picture rather than parking it in a grey void.
		expect(source).toContain('lg:flex-row');
		expect(source).toContain('lg:w-[22rem]');
		expect(source).toContain("aria-label={$i18n.t('Artwork')}");
		expect(source).toContain('<aside');
		expect(source).toContain('lg:overflow-y-auto');
		expect(source).toContain('object-contain');
		expect(source).not.toContain('max-h-[40vh]');
	});

	test('keeps notes and generation metadata in the secondary panel', () => {
		expect(source).toContain('<aside');
		expect(source).toContain("$i18n.t('Prompt')");
		// The artwork region precedes the secondary aside so the picture leads.
		expect(source.indexOf("aria-label={$i18n.t('Artwork')}")).toBeLessThan(
			source.indexOf('<aside')
		);
		// Caption was demoted to an inline "add a note" affordance — the old
		// standalone labelled section is gone.
		expect(source).not.toContain("$i18n.t('Caption')");
		expect(source).toContain("$i18n.t('Add a note')");
	});

	test('gates caption save and remove behind canManage', () => {
		expect(source).toContain('{#if canManage}');
		expect(source).toContain("$i18n.t('Save')");
		expect(source).toContain("$i18n.t('Remove from library')");
	});

	test('demotes caption to a single-line inline input footprint', () => {
		// Caption is incidental, not structural: it earns a one-row text input
		// rather than a multi-row textarea, freeing vertical room for the art.
		expect(source).toContain('type="text"');
		expect(source).toContain('bind:value={captionDraft}');
		expect(source).toContain('bind:value={publicationDescription}');
		expect(source).not.toContain('<textarea bind:value={captionDraft}');
		expect(source).not.toContain('"Save caption"');
	});

	test('collapses caption behind an inline add-note trigger', () => {
		// D1 affordance: a dormant "add a note" (or the existing caption text)
		// button expands the editor in place — no permanent labelled section.
		expect(source).toContain('captionEditing');
		expect(source).toContain("$i18n.t('Add a note')");
		expect(source).toContain('cancelCaptionEdit');
	});

	test('lifts the prompt into a featured card with a copy affordance', () => {
		// The prompt earns a tinted card with a capped scroll height (stable
		// modal stature regardless of prompt length) and a one-tap copy button.
		expect(source).toContain('copyPrompt');
		expect(source).toContain('copyToClipboard');
		expect(source).toContain('<Clipboard');
		expect(source).toContain("$i18n.t('Copy')");
		expect(source).toContain('max-h-48');
	});

	test('retires the generic title in favour of a subtitle header', () => {
		// The vacuous "Creation details" heading is gone; the header now carries
		// a contextual "when · model" subtitle and the close control.
		expect(source).not.toContain("$i18n.t('Creation details')");
		expect(source).toContain('headerSubtitle');
		expect(source).toContain('formatDate');
	});

	test('confirms removal with a non-restorable warning', () => {
		expect(source).toContain("$i18n.t('Remove this creation from your library?')");
		expect(source).toContain(
			"'This will not delete images in chats, but it cannot be restored to the library in this version.'"
		);
	});

	test('uses updateCreation and deleteCreation from the api', () => {
		expect(source).toContain('updateCreation');
		expect(source).toContain('deleteCreation');
	});
});
