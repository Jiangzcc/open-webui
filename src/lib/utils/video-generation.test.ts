import { describe, expect, test } from 'vitest';

import type { VideoAdvancedField, VideoModel } from '$lib/apis/videos';
import {
	firstVideoAdvancedError,
	normalizeVideoParamsForModel,
	videoAdvancedFieldError
} from './video-generation';

const model = {
	id: 'video-model',
	name: 'Video Model',
	provider: 'vendor',
	task: 'text-to-video',
	prompt_required: true,
	advanced_fields: [
		{ key: 'seed', kind: 'integer', min: 0 },
		{ key: 'negative_prompt', kind: 'text', max_length: 20 },
		{ key: 'prompt_enhancement', kind: 'option', options: ['auto', 'on', 'off'], default: 'auto' },
		{ key: 'loop', kind: 'boolean', default: false }
	]
} satisfies VideoModel;

describe('video advanced parameter normalization', () => {
	test('keeps only standard and declared advanced parameters', () => {
		expect(
			normalizeVideoParamsForModel(model, {
				duration: '5',
				seed: '0',
				negative_prompt: '  flicker  ',
				prompt_enhancement: 'off',
				loop: true,
				safety_tolerance: '6',
				multi_prompt: '[]'
			})
		).toEqual({
			duration: '5',
			seed: 0,
			negative_prompt: 'flicker',
			prompt_enhancement: 'off',
			loop: true
		});
	});

	test('uses declared defaults without leaking unsupported values', () => {
		expect(normalizeVideoParamsForModel(model, {})).toEqual({
			prompt_enhancement: 'auto',
			loop: false
		});
	});

	test('validates integer, range, enum and text constraints', () => {
		const seed = model.advanced_fields?.[0] as VideoAdvancedField;
		expect(videoAdvancedFieldError(seed, '1.5')?.key).toBe('Enter a whole number');
		expect(videoAdvancedFieldError(seed, '-1')).toEqual({ key: 'Minimum: {{value}}', value: 0 });
		expect(firstVideoAdvancedError(model, { prompt_enhancement: 'invalid' })?.field.key).toBe(
			'prompt_enhancement'
		);
		expect(firstVideoAdvancedError(model, { negative_prompt: 'x'.repeat(21) })?.error.key).toBe(
			'Text is too long'
		);
	});
});
