import { describe, expect, test } from 'vitest';

import {
	DEFAULT_PINNED_MENU_ITEMS,
	PINNED_MEDIA_MENU_VERSION,
	getPinnedMediaMenuMigration
} from './sidebar-menu';

describe('sidebar menu settings', () => {
	test('includes Images in the default pinned menu', () => {
		expect(DEFAULT_PINNED_MENU_ITEMS).toEqual(['notes', 'workspace', 'discover', 'images']);
	});

	test('adds Images once to existing legacy pinned settings', () => {
		const settings = { pinnedMenuItems: ['workspace', 'calendar'] };

		expect(getPinnedMediaMenuMigration(settings)).toEqual({
			pinnedMenuItems: ['workspace', 'calendar', 'discover', 'images'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
		expect(settings).toEqual({ pinnedMenuItems: ['workspace', 'calendar'] });
	});

	test('marks legacy settings that already contain Images without duplicating it', () => {
		expect(getPinnedMediaMenuMigration({ pinnedMenuItems: ['images', 'notes'] })).toEqual({
			pinnedMenuItems: ['discover', 'images', 'notes'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
	});

	test('does not re-add Images after the migration so users can unpin it', () => {
		expect(
			getPinnedMediaMenuMigration({
				pinnedMenuItems: ['workspace'],
				pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
			})
		).toBeNull();
	});

	test('uses defaults instead of persisting a migration for users without pinned settings', () => {
		expect(getPinnedMediaMenuMigration({})).toBeNull();
	});
});
