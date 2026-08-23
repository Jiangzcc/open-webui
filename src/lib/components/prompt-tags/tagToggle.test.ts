import { describe, expect, test } from 'vitest';

import { appendPromptText } from './tagToggle';

describe('appendPromptText', () => {
	test('appends a snippet as a comma-separated segment', () => {
		expect(appendPromptText('a quiet street', 'cinematic lighting')).toBe(
			'a quiet street, cinematic lighting'
		);
	});

	test('puts the snippet alone into an empty box', () => {
		expect(appendPromptText('   ', 'cinematic lighting')).toBe('cinematic lighting');
	});

	test('trims existing text and ignores empty snippets', () => {
		expect(appendPromptText('a street ,  ', 'rain')).toBe('a street, rain');
		expect(appendPromptText('a street', '   ')).toBe('a street');
	});
});
