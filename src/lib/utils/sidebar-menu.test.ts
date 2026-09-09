import { describe, expect, test } from 'vitest';

import {
	DEFAULT_PINNED_MENU_ITEMS,
	PINNED_MEDIA_MENU_VERSION,
	getPinnedMediaMenuMigration
} from './sidebar-menu';

describe('sidebar menu settings', () => {
	test('includes Assets between Discover and Images in the default pinned menu', () => {
		expect(DEFAULT_PINNED_MENU_ITEMS).toEqual([
			'notes',
			'workspace',
			'discover',
			'assets',
			'images',
			'videos'
		]);
	});

	test('inserts Assets above Images for legacy users', () => {
		expect(
			getPinnedMediaMenuMigration({
				pinnedMenuItems: ['notes', 'workspace', 'discover', 'images', 'videos']
			})
		).toEqual({
			pinnedMenuItems: ['notes', 'workspace', 'discover', 'assets', 'images', 'videos'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
	});

	test('adds new entries without restoring an explicitly unpinned Images item', () => {
		const settings = { pinnedMenuItems: ['workspace', 'calendar'] };

		expect(getPinnedMediaMenuMigration(settings)).toEqual({
			pinnedMenuItems: ['workspace', 'calendar', 'discover', 'assets', 'videos'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
		expect(settings).toEqual({ pinnedMenuItems: ['workspace', 'calendar'] });
	});

	test('marks legacy settings that already contain Images without duplicating it', () => {
		expect(getPinnedMediaMenuMigration({ pinnedMenuItems: ['images', 'notes'] })).toEqual({
			pinnedMenuItems: ['discover', 'assets', 'images', 'notes', 'videos'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
	});

	test('does not re-add entries a version 3 user explicitly unpinned', () => {
		// v3 用户已迁移过 videos/discover：升级到 v4 只插入 assets，
		// 取消固定的 videos 不得被顺带恢复。
		expect(
			getPinnedMediaMenuMigration({
				pinnedMenuItems: ['notes', 'workspace', 'discover', 'images'],
				pinnedMenuItemsVersion: 3
			})
		).toEqual({
			pinnedMenuItems: ['notes', 'workspace', 'discover', 'assets', 'images'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
	});

	test('falls back to appending Assets when both Images and Videos are unpinned', () => {
		expect(
			getPinnedMediaMenuMigration({
				pinnedMenuItems: ['notes', 'workspace', 'discover'],
				pinnedMenuItemsVersion: 3
			})
		).toEqual({
			pinnedMenuItems: ['notes', 'workspace', 'discover', 'assets'],
			pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
		});
	});

	test('does not re-add Assets after the migration so users can unpin it', () => {
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
