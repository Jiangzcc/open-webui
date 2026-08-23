import i18next from 'i18next';
import { describe, expect, test, vi } from 'vitest';

import { registerPromptTagTranslations } from './prompt-tags-i18n';

describe('prompt tag translations', () => {
	test('registers each i18n instance only once', async () => {
		const instance = i18next.createInstance();
		await instance.init({ lng: 'en-US', fallbackLng: false });
		const addResourceBundle = vi.spyOn(instance, 'addResourceBundle');

		registerPromptTagTranslations(instance);
		registerPromptTagTranslations(instance);

		expect(addResourceBundle).toHaveBeenCalledTimes(2);
		expect(instance.t('promptTags.title')).toBe('Prompt Tags');
	});
});
