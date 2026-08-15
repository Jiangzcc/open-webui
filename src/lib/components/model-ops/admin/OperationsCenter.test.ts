import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const readSource = (path: string) =>
	readFileSync(fileURLToPath(new URL(path, import.meta.url)), 'utf-8');

const adminLayout = readSource('../../../../routes/(app)/admin/+layout.svelte');
const operationsPage = readSource('../../../../routes/(app)/admin/operations/+page.svelte');
const discoveryOperations = readSource('../../discovery/admin/DiscoveryOperations.svelte');
const discoveryCategories = readSource('../../discovery/admin/DiscoveryCategories.svelte');
const creditReconciliation = readSource('../../credits/admin/CreditReconciliationTab.svelte');
const modelOperations = readSource('./ImageModelOperations.svelte');

describe('operations center', () => {
	test('combines discovery and image models after credit management', () => {
		// 页面已改为懒加载动态导入 + <svelte:component> 模式，
		// 断言动态导入路径而非静态组件标签。
		expect(operationsPage).toContain(
			"import('$lib/components/discovery/admin/DiscoveryOperations.svelte')"
		);
		expect(operationsPage).toContain(
			"import('$lib/components/discovery/admin/DiscoveryCategories.svelte')"
		);
		expect(operationsPage).toContain(
			"import('$lib/components/model-ops/admin/ImageModelOperations.svelte')"
		);
		expect(operationsPage).toContain('svelte:component this=');
		expect(operationsPage).toContain(
			'<h1 class="text-xl font-medium dark:text-gray-100">{$i18n.t(\'Operations center\')}</h1>'
		);
		expect(operationsPage).toContain('border-b-2 px-3 py-2 text-sm font-medium');
		expect(adminLayout).not.toContain('href="/admin/discovery"');
		expect(adminLayout).not.toContain('href="/admin/image-models"');
		expect(adminLayout.indexOf('href="/admin/credits"')).toBeLessThan(
			adminLayout.indexOf('href="/admin/operations"')
		);
	});

	test('provides maintainable discovery category names, visibility and order', () => {
		expect(discoveryCategories).toContain('listAdminDiscoveryCategories');
		expect(discoveryCategories).toContain('createAdminDiscoveryCategory');
		expect(discoveryCategories).toContain('deleteAdminDiscoveryCategory');
		expect(discoveryCategories).toContain('updateAdminDiscoveryCategory');
		expect(discoveryCategories).toContain('bind:value={category.display_name}');
		expect(discoveryCategories).toContain('bind:checked={category.enabled}');
		expect(discoveryCategories).toContain('bind:value={category.sort_order}');
		expect(discoveryCategories).toContain("category.id === 'other'");
		expect(discoveryCategories).toContain("disabled={category.id === 'other'}");
	});

	test('paginates credit reconciliation cases on the server', () => {
		expect(creditReconciliation).toContain('skip: (page - 1) * pageSize');
		expect(creditReconciliation).toContain('limit: pageSize');
		expect(creditReconciliation).toContain(
			'<Pagination bind:page count={total} perPage={pageSize} />'
		);
	});

	test('paginates discovery operations instead of appending an endless list', () => {
		expect(discoveryOperations).toContain('let pageSize = 20;');
		expect(discoveryOperations).toContain('const nextPage = async () =>');
		expect(discoveryOperations).toContain('const previousPage = async () =>');
		expect(discoveryOperations).toContain('max-h-[min(62vh,44rem)]');
		expect(discoveryOperations).toContain('role="dialog"');
		expect(discoveryOperations).toContain("$i18n.t('Preview artwork')");
		expect(discoveryOperations).toContain('<ImagePreview bind:show={showPreview}');
		expect(discoveryOperations).not.toContain("$i18n.t('Load more')");
	});

	test('keeps the model list dense and opens one editor at a time', () => {
		expect(modelOperations).toContain('let pageSize = 25;');
		expect(modelOperations).toContain('max-h-[min(62vh,44rem)]');
		expect(modelOperations).toContain('role="dialog"');
		expect(modelOperations).toContain('item.media_kind');
		expect(modelOperations).toContain('value="video"');
		expect(modelOperations).toContain("'text-to-video'");
	});

	test('treats categories and discovery operations as image and video features', () => {
		expect(operationsPage).toContain("label: 'Creation categories'");
		expect(discoveryCategories).toContain("$i18n.t('Add creation category')");
		expect(discoveryOperations).toContain('mediaKind');
		expect(discoveryOperations).toContain('<video');
	});
});
