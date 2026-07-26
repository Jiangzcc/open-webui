export const DEFAULT_PINNED_MENU_ITEMS = ['notes', 'workspace', 'discover', 'images'];
export const PINNED_MEDIA_MENU_VERSION = 2;

type SidebarMenuSettings = {
	pinnedMenuItems?: string[];
	pinnedMenuItemsVersion?: number;
};

export const getPinnedMediaMenuMigration = (settings: SidebarMenuSettings) => {
	if (
		!Array.isArray(settings.pinnedMenuItems) ||
		settings.pinnedMenuItemsVersion === PINNED_MEDIA_MENU_VERSION
	) {
		return null;
	}

	const items = [...settings.pinnedMenuItems];
	if (!items.includes('images')) items.push('images');
	if (!items.includes('discover')) {
		const imagesIndex = items.indexOf('images');
		items.splice(imagesIndex < 0 ? items.length : imagesIndex, 0, 'discover');
	}
	return {
		pinnedMenuItems: items,
		pinnedMenuItemsVersion: PINNED_MEDIA_MENU_VERSION
	};
};
