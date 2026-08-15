import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(
	fileURLToPath(new URL('./CreationsLibrary.svelte', import.meta.url)),
	'utf-8'
);

describe('CreationsLibrary source contract', () => {
	test('lazy loads original images and exposes details on touch', () => {
		expect(source).toContain('loading="lazy"');
		expect(source).toContain('decoding="async"');
		// 卡片点击通过 handleCardClick → openDetails 打开详情弹窗，不再有独立的 "Details" 按钮。
		expect(source).toContain('openDetails');
		expect(source).toContain('<Loader');
		// 独立 owner 标注已从卡片移除。
		expect(source).not.toContain("$i18n.t('Deleted user')");
	});

	test('keeps cards artwork-focused without a prompt overlay', () => {
		// 卡片重新设计后不再显示 prompt 预览浮层；prompt 仅在详情弹窗中展示。
		expect(source).not.toContain('{item.prompt_preview}');
		expect(source).not.toContain('line-clamp-2');
		expect(source).not.toContain('group-hover:opacity-100');
		expect(source).not.toContain('from-black/70');
		expect(source).not.toContain('.prompt-overlay');
	});

	test('uses a single card click to open details or toggle selection', () => {
		// 卡片不再拆分为预览点击 + 详情按钮两个入口；
		// 单一 handleCardClick 根据选择模式决定打开详情或切换选中。
		expect(source).toContain('handleCardClick');
		expect(source).toContain('openDetails');
		expect(source).toContain('toggleSelected');
		expect(source).toContain('selectionMode');
		// 不再有独立的预览/详情按钮。
		expect(source).not.toContain("$i18n.t('Preview')");
		expect(source).not.toContain("$i18n.t('Details')");
		expect(source).not.toContain('details-btn');
	});

	test('receives scope from its parent instead of rendering a scope switcher', () => {
		expect(source).toContain('export let scope: CreationScope');
		// The scope selector lives in the parent pill now; the library must not redraw it.
		expect(source).not.toContain("$i18n.t('My creations')");
		expect(source).not.toContain("$i18n.t('All creations')");
		expect(source).not.toContain('selectScope');
	});

	test('strips owner identity off the cards so it lives only in the detail modal', () => {
		// Owner name/email moved into CreationDetailsModal; the gallery card must
		// no longer render any owner attribution regardless of scope/role.
		expect(source).not.toContain("'owner' in item");
		expect(source).not.toContain('.owner.');
		expect(source).not.toContain("$i18n.t('Deleted user')");
		expect(source).not.toContain("$i18n.t('Email')");
	});

	test('declares the documented props', () => {
		expect(source).toContain('export let active');
		expect(source).toContain('export let scope');
		expect(source).toContain('export let revision');
		expect(source).not.toContain('export let onCreate');
	});

	test('uses the creations api and scope state helpers', () => {
		expect(source).toContain('listCreations');
		expect(source).toContain('listAdminCreations');
		expect(source).toContain('createCreationScopeState');
		expect(source).toContain('beginCreationRequest');
		expect(source).toContain('applyCreationPage');
	});

	test('routes cards into deterministic round-robin lanes instead of CSS multicol', () => {
		// Deterministic lanes keep settled items pinned when later pages stream in;
		// CSS columns rebalance on insert and visibly shuffle existing cards.
		expect(source).toContain('assignLanes');
		expect(source).toContain('flex min-w-0 flex-1 flex-col gap-2');
		expect(source).toContain('h-auto w-full');
		expect(source).not.toContain('columns-2');
		expect(source).not.toContain('sm:columns-3');
		expect(source).not.toContain('lg:columns-5');
		expect(source).not.toContain('break-inside-avoid');
		expect(source).not.toContain('aspect-square');
		expect(source).not.toContain('object-cover');
	});

	test('keeps artwork as the card focus without model labels', () => {
		expect(source).not.toContain("$i18n.t('Unknown model')");
		expect(source).not.toContain('item.model_name ??');
	});

	test('opens the details modal lazily', () => {
		expect(source).toContain('CreationDetailsModal');
		expect(source).toContain('listCreations');
		expect(source).toContain('listAdminCreations');
	});

	test('invalidates Svelte state after helper mutations', () => {
		expect(source).toContain('scopes = { ...scopes };');
	});

	test('projects saved captions into every cached scope immediately', () => {
		expect(source).toContain(
			'const onModalUpdated = (detail: CreationDetail | AdminCreationDetail) => {'
		);
		expect(source).toContain("for (const targetScope of ['mine', 'all'] as const)");
		expect(source).toContain('caption: detail.caption');
		expect(source).toContain('updated_at: detail.updated_at');
	});

	test('consumes each generation revision once and refreshes stale state on activation', () => {
		expect(source).toContain('let appliedRevision = 0;');
		expect(source).toContain('revision > appliedRevision');
		expect(source).toContain('activeState.stale && !activeState.loading');
	});

	test('does not auto-loop after an initial load failure', () => {
		expect(source).toContain('!activeState.loading && !activeState.error');
	});

	test('keeps loaded cards visible when pagination fails', () => {
		expect(source).toContain('state.error && state.items.length === 0');
		expect(source).toContain('state.error && state.items.length > 0');
	});

	test('keeps touch-sized targets on the remaining retry buttons', () => {
		expect(source).not.toContain('min-h-9');
		expect(source).toContain('min-h-11');
	});

	test('removes a deleted owner item from both cached admin scopes', () => {
		expect(source).toContain("for (const targetScope of ['mine', 'all'] as const)");
		expect(source).toContain('removeCreationOptimistically(scopes[targetScope], creationId)');
		expect(source).not.toContain("if (scope === 'all')");
	});

	test('offers a non-hover retry affordance', () => {
		expect(source).toContain("$i18n.t('Retry')");
	});

	test('enables admin management from the global library detail', () => {
		expect(source).toContain("canManage={scope === 'mine' || scope === 'all'}");
	});
});
