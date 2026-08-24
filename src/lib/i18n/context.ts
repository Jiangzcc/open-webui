import type { i18n as I18n } from 'i18next';
import { getContext } from 'svelte';
import type { Writable } from 'svelte/store';

export const getI18nContext = () => getContext<Writable<I18n>>('i18n');
