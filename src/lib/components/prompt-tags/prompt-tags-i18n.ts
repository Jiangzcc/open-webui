import type { i18n as I18n } from 'i18next';
import { get, type Readable } from 'svelte/store';

type PromptTagI18n = I18n | Readable<I18n>;

// Images/Videos each mount a picker and an editor. Registering the same
// resource bundles from every instance emits repeated `added` events on the
// shared i18n store, causing needless page-wide updates during mount.
const registeredI18n = new WeakSet<object>();

const zh = {
	promptTags: {
		title: '提示词标签',
		picker: {
			label: '标签',
			search: '搜索标签',
			categories: '标签分类',
			empty: '暂无可用标签',
			noResults: '未找到匹配标签',
			negative: '负面',
			selected: '已选',
			inserted: '已插入',
			removed: '已移除',
			removeChip: '点击移除',
			removeChipWithLabel: '移除标签 {{label}}',
			hint: '点击插入标签；输入框中的标签块可点击整块移除，提交时自动替换为实际提示词'
		},
		admin: {
			management: '提示词标签库',
			categories: '分类',
			tags: '标签',
			createCategory: '新建分类',
			createTag: '新建标签',
			editTag: '编辑标签',
			editCategory: '编辑分类',
			deleteConfirm: '确定删除？此操作不可撤销。',
			deleteCascadeHint: '删除分类将同时删除其下所有标签',
			slug: '标识',
			nameZh: '中文名称',
			nameEn: '英文名称',
			labelZh: '中文标签',
			labelEn: '英文标签',
			insertText: '插入文本',
			category: '分类',
			isNegative: '负面词',
			mediaKinds: '适用类型',
			modelRefs: '限定模型',
			enabled: '启用',
			sortOrder: '排序',
			importTitle: '导入标签库',
			exportTitle: '导出标签库',
			importResult: '导入结果',
			categoriesCreated: '新增分类',
			categoriesUpdated: '更新分类',
			tagsCreated: '新增标签',
			tagsUpdated: '更新标签',
			dryRun: '试运行',
			upsert: '覆盖同名',
			saved: '已保存',
			deleted: '已删除',
			confirmDeleteCategory: '该分类下仍有标签，是否一并删除？',
			noCategory: '请先创建分类',
			all: '全部',
			cancel: '取消',
			close: '关闭',
			importPlaceholder: '在此粘贴导出的 JSON…'
		},
		errors: {
			unavailable: '标签服务暂不可用',
			requestFailed: '请求失败',
			notFound: '未找到',
			conflict: '标识冲突',
			notEmpty: '分类下仍有标签'
		}
	}
};

const en: typeof zh = {
	promptTags: {
		title: 'Prompt Tags',
		picker: {
			label: 'Tags',
			search: 'Search tags',
			categories: 'Tag categories',
			empty: 'No tags available',
			noResults: 'No matching tags',
			negative: 'Negative',
			selected: 'Selected',
			inserted: 'Inserted',
			removed: 'Removed',
			removeChip: 'Click to remove',
			removeChipWithLabel: 'Remove tag {{label}}',
			hint: 'Click a tag to insert it; click a tag chip in the prompt to remove it. Tags are replaced with the real prompt on submit'
		},
		admin: {
			management: 'Prompt Tag Library',
			categories: 'Categories',
			tags: 'Tags',
			createCategory: 'New Category',
			createTag: 'New Tag',
			editTag: 'Edit Tag',
			editCategory: 'Edit Category',
			deleteConfirm: 'Are you sure? This cannot be undone.',
			deleteCascadeHint: 'Deleting a category also deletes all its tags',
			slug: 'Slug',
			nameZh: 'Chinese Name',
			nameEn: 'English Name',
			labelZh: 'Chinese Label',
			labelEn: 'English Label',
			insertText: 'Insert Text',
			category: 'Category',
			isNegative: 'Negative',
			mediaKinds: 'Media Types',
			modelRefs: 'Model Restrictions',
			enabled: 'Enabled',
			sortOrder: 'Sort Order',
			importTitle: 'Import Library',
			exportTitle: 'Export Library',
			importResult: 'Import Result',
			categoriesCreated: 'Categories Created',
			categoriesUpdated: 'Categories Updated',
			tagsCreated: 'Tags Created',
			tagsUpdated: 'Tags Updated',
			dryRun: 'Dry Run',
			upsert: 'Upsert',
			saved: 'Saved',
			deleted: 'Deleted',
			confirmDeleteCategory: 'This category still has tags. Delete them too?',
			noCategory: 'Create a category first',
			all: 'All',
			cancel: 'Cancel',
			close: 'Close',
			importPlaceholder: 'Paste exported JSON here…'
		},
		errors: {
			unavailable: 'Prompt tag service is unavailable',
			requestFailed: 'Request failed',
			notFound: 'Not found',
			conflict: 'Slug conflict',
			notEmpty: 'Category is not empty'
		}
	}
};

export const registerPromptTagTranslations = (contextI18n: PromptTagI18n) => {
	const i18n = 'addResourceBundle' in contextI18n ? contextI18n : get(contextI18n);
	if (registeredI18n.has(i18n)) return;
	registeredI18n.add(i18n);
	i18n.addResourceBundle('zh-CN', 'translation', zh, true, false);
	i18n.addResourceBundle('en-US', 'translation', en, true, false);
};
