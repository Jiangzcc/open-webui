import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Images.svelte', import.meta.url)), 'utf-8');

describe('fal.ai image settings', () => {
	test('keeps fal.ai available for generation and editing after upstream settings refactors', () => {
		expect(source.match(/<option value="fal">/g)).toHaveLength(2);
		expect(source).toContain("config?.IMAGE_GENERATION_ENGINE === 'fal'");
		expect(source).toContain("config?.IMAGE_EDIT_ENGINE === 'fal'");

		const generationEngineChain = source.indexOf(
			"{#if config?.IMAGE_GENERATION_ENGINE === 'openai'}"
		);
		const generationFalBranch = source.indexOf(
			"{:else if config?.IMAGE_GENERATION_ENGINE === 'fal'}"
		);
		const editSection = source.indexOf("<AdminSettingSection title={$i18n.t('Edit Image')}>");
		expect(generationFalBranch).toBeGreaterThan(generationEngineChain);
		expect(generationFalBranch).toBeLessThan(editSection);

		const editEngineChain = source.indexOf("{#if config?.IMAGE_EDIT_ENGINE === 'openai'}");
		const editFalBranch = source.indexOf("{:else if config?.IMAGE_EDIT_ENGINE === 'fal'}");
		expect(editFalBranch).toBeGreaterThan(editEngineChain);
	});

	test('binds both fal.ai endpoint and credential pairs', () => {
		for (const field of [
			'config.FAL_API_BASE_URL',
			'config.FAL_API_KEY',
			'config.IMAGES_EDIT_FAL_API_BASE_URL',
			'config.IMAGES_EDIT_FAL_API_KEY'
		]) {
			expect(source).toContain(`bind:value={${field}}`);
		}
		expect(source.match(/fal\.ai API Key is required\./g).length).toBeGreaterThanOrEqual(2);
	});
});
