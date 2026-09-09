export const DEFAULT_PINNED_MENU_ITEMS = [
	'notes',
	'workspace',
	'discover',
	'assets',
	'images',
	'videos'
];
export const PINNED_MEDIA_MENU_VERSION = 4;

type SidebarMenuSettings = {
	pinnedMenuItems?: string[];
	pinnedMenuItemsVersion?: number;
};

// v3 及更早版本的迁移：补齐 videos 与 discover（这两个入口首次上线时的动作）。
const applyLegacyMediaMigration = (items: string[]) => {
	if (!items.includes('videos')) items.push('videos');
	if (!items.includes('discover')) {
		const imagesIndex = items.indexOf('images');
		const videosIndex = items.indexOf('videos');
		items.splice(
			imagesIndex >= 0 ? imagesIndex : videosIndex >= 0 ? videosIndex : items.length,
			0,
			'discover'
		);
	}
};

// v4 迁移：在图片、视频上方插入资产入口。只新增 assets，绝不顺带恢复用户
// 主动取消固定的其他菜单项；已包含 assets（如未来版本回退再升级）时保持不动。
const applyAssetsMigration = (items: string[]) => {
	if (items.includes('assets')) return;
	const imagesIndex = items.indexOf('images');
	const videosIndex = items.indexOf('videos');
	items.splice(
		imagesIndex >= 0 ? imagesIndex : videosIndex >= 0 ? videosIndex : items.length,
		0,
		'assets'
	);
};

export const getPinnedMediaMenuMigration = (settings: SidebarMenuSettings) => {
	if (
		!Array.isArray(settings.pinnedMenuItems) ||
		settings.pinnedMenuItemsVersion === PINNED_MEDIA_MENU_VERSION
	) {
		return null;
	}

	const items = [...settings.pinnedMenuItems];
	// v3 用户已迁移过 videos/discover，重新补齐等于恢复他们主动取消固定的项，
	// 因此旧迁移只对更早版本（含从未迁移的 undefined）执行。
	if ((settings.pinnedMenuItemsVersion ?? 0) < 3) {
		applyLegacyMediaMigration(items);
	}
	applyAssetsMigration(items);
	return {
		pinnedMenuItems: items,
		pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
	};
};
