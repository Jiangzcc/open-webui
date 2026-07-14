export const DEFAULT_PINNED_MENU_ITEMS = ['notes', 'workspace', 'images'];
export const PINNED_IMAGES_MENU_VERSION = 1;

type SidebarMenuSettings = {
	pinnedMenuItems?: string[];
	pinnedMenuItemsVersion?: number;
};

export const getPinnedImagesMenuMigration = (settings: SidebarMenuSettings) => {
	if (
		!Array.isArray(settings.pinnedMenuItems) ||
		settings.pinnedMenuItemsVersion === PINNED_IMAGES_MENU_VERSION
	) {
		return null;
	}

	return {
		pinnedMenuItems: settings.pinnedMenuItems.includes('images')
			? [...settings.pinnedMenuItems]
			: [...settings.pinnedMenuItems, 'images'],
		pinnedMenuItemsVersion: PINNED_IMAGES_MENU_VERSION
	};
};
