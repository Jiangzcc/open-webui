import { describe, expect, test } from 'vitest';

import {
	DEFAULT_PINNED_MENU_ITEMS,
	PINNED_IMAGES_MENU_VERSION,
	getPinnedImagesMenuMigration
} from './sidebar-menu';

describe('sidebar menu settings', () => {
	test('includes Images in the default pinned menu', () => {
		expect(DEFAULT_PINNED_MENU_ITEMS).toEqual(['notes', 'workspace', 'images']);
	});

	test('adds Images once to existing legacy pinned settings', () => {
		const settings = { pinnedMenuItems: ['workspace', 'calendar'] };

		expect(getPinnedImagesMenuMigration(settings)).toEqual({
			pinnedMenuItems: ['workspace', 'calendar', 'images'],
			pinnedMenuItemsVersion: PINNED_IMAGES_MENU_VERSION
		});
		expect(settings).toEqual({ pinnedMenuItems: ['workspace', 'calendar'] });
	});

	test('marks legacy settings that already contain Images without duplicating it', () => {
		expect(getPinnedImagesMenuMigration({ pinnedMenuItems: ['images', 'notes'] })).toEqual({
			pinnedMenuItems: ['images', 'notes'],
			pinnedMenuItemsVersion: PINNED_IMAGES_MENU_VERSION
		});
	});

	test('does not re-add Images after the migration so users can unpin it', () => {
		expect(
			getPinnedImagesMenuMigration({
				pinnedMenuItems: ['workspace'],
				pinnedMenuItemsVersion: PINNED_IMAGES_MENU_VERSION
			})
		).toBeNull();
	});

	test('uses defaults instead of persisting a migration for users without pinned settings', () => {
		expect(getPinnedImagesMenuMigration({})).toBeNull();
	});
});
