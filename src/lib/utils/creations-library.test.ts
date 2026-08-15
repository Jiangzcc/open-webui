import { describe, expect, test } from 'vitest';

import {
	applyCreationPage,
	assignLanes,
	beginCreationRequest,
	createCreationScopeState,
	extractParamTags,
	markCreationScopeStale,
	removeCreationOptimistically,
	restoreCreation
} from './creations-library';

const ids = (...xs: string[]) => xs.map((id) => ({ id }) as never);

describe('creations library state', () => {
	test('keeps mine and all scope cursors independent', () => {
		const mine = createCreationScopeState();
		const all = createCreationScopeState();
		expect(mine).not.toBe(all);
		expect(mine.nextCursor).toBeNull();
		expect(all.nextCursor).toBeNull();
	});

	test('clears existing items on first page and loads only the new page', () => {
		const state = createCreationScopeState([{ id: 'a' }, { id: 'b' }, { id: 'c' }] as never[]);
		const ok = applyCreationPage(
			state,
			beginCreationRequest(state),
			{ items: [{ id: 'b' }, { id: 'd' }] as never[], next_cursor: 'cur' },
			true
		);
		expect(ok).toBe(true);
		// isFirst=true 清空旧项后只保留新页面数据。
		expect(state.items.map((item) => item.id)).toEqual(['b', 'd']);
		expect(state.nextCursor).toBe('cur');
	});

	test('dedupes by id and preserves server order on subsequent page merge', () => {
		const state = createCreationScopeState([{ id: 'a' }, { id: 'b' }, { id: 'c' }] as never[]);
		state.loaded = true;
		const ok = applyCreationPage(
			state,
			beginCreationRequest(state),
			{ items: [{ id: 'b' }, { id: 'd' }] as never[], next_cursor: 'cur' },
			false
		);
		expect(ok).toBe(true);
		// isFirst=false 保留已有项，去重后追加新项。
		expect(state.items.map((item) => item.id)).toEqual(['a', 'b', 'c', 'd']);
		expect(state.nextCursor).toBe('cur');
	});

	test('ignores a response from an older request generation', () => {
		const state = createCreationScopeState();
		const first = beginCreationRequest(state);
		const second = beginCreationRequest(state);
		expect(applyCreationPage(state, first, { items: [], next_cursor: null }, true)).toBe(false);
		expect(applyCreationPage(state, second, { items: [], next_cursor: null }, true)).toBe(true);
	});

	test('marks loaded and clears loading after a successful first page', () => {
		const state = createCreationScopeState();
		const gen = beginCreationRequest(state);
		expect(state.loading).toBe(true);
		applyCreationPage(state, gen, { items: [{ id: 'x' }] as never[], next_cursor: null }, true);
		expect(state.loaded).toBe(true);
		expect(state.loading).toBe(false);
		expect(state.stale).toBe(false);
	});

	test('invalidates an in-flight page when new creations make it stale', () => {
		const state = createCreationScopeState();
		const oldGeneration = beginCreationRequest(state);

		markCreationScopeStale(state);

		expect(state.stale).toBe(true);
		expect(state.loading).toBe(false);
		expect(applyCreationPage(state, oldGeneration, { items: [], next_cursor: null }, true)).toBe(
			false
		);
	});

	test('restores an optimistically removed card at its original index', () => {
		const state = createCreationScopeState([{ id: 'a' }, { id: 'b' }, { id: 'c' }] as never[]);
		const removed = removeCreationOptimistically(state, 'b');
		expect(state.items.map((item) => item.id)).toEqual(['a', 'c']);
		expect(removed.item.id).toBe('b');
		expect(removed.index).toBe(1);
		restoreCreation(state, removed);
		expect(state.items.map((item) => item.id)).toEqual(['a', 'b', 'c']);
	});

	test('restore is a no-op when the item is already present', () => {
		const state = createCreationScopeState([{ id: 'a' }] as never[]);
		const removed = { item: { id: 'a' } as never, index: 0 };
		restoreCreation(state, removed);
		expect(state.items.map((item) => item.id)).toEqual(['a']);
	});

	test('sets error and clears loading on a failed page load', () => {
		const state = createCreationScopeState();
		const gen = beginCreationRequest(state);
		// simulate failure path: caller hands the same generation back marked as error
		applyCreationPage(state, gen, null, true);
		expect(state.loading).toBe(false);
		expect(state.error).toBeInstanceOf(Error);
	});

	test('append page keeps existing items and appends new ones without dupes', () => {
		const state = createCreationScopeState([{ id: 'a' }] as never[]);
		state.loaded = true;
		state.nextCursor = 'cur';
		const gen = beginCreationRequest(state);
		applyCreationPage(
			state,
			gen,
			{ items: [{ id: 'a' }, { id: 'b' }] as never[], next_cursor: null },
			false
		);
		expect(state.items.map((item) => item.id)).toEqual(['a', 'b']);
		expect(state.nextCursor).toBeNull();
	});
});

describe('assignLanes deterministic slot routing', () => {
	test('round-robins items across lanes so growth stays balanced', () => {
		const lanes = assignLanes(ids('a', 'b', 'c', 'd', 'e'), 3);
		expect(lanes.map((lane) => lane.map((item) => (item as { id: string }).id))).toEqual([
			['a', 'd'],
			['b', 'e'],
			['c']
		]);
	});

	test('returns the requested number of lanes even when fed fewer items', () => {
		const lanes = assignLanes(ids('a'), 4);
		expect(lanes).toHaveLength(4);
		expect(lanes.map((lane) => lane.map((item) => (item as { id: string }).id))).toEqual([
			['a'],
			[],
			[],
			[]
		]);
	});

	test('produces an empty lane matrix for an empty feed', () => {
		expect(
			assignLanes([], 3).map((lane) => lane.map((item) => (item as { id: string }).id))
		).toEqual([[], [], []]);
	});

	test('never reshuffles settled items when a later page is appended', () => {
		// Page 1 settles 4 items into 3 lanes.
		const firstBatch = ids('a', 'b', 'c', 'd');
		const settled = assignLanes(firstBatch, 3);

		// Later page adds 3 more items; rebuild from the combined feed.
		const combined = assignLanes([...firstBatch, ...ids('e', 'f', 'g')], 3);

		// Every originally-settled item must occupy the same lane index AND
		// the same intra-lane ordinal as before — the hallmark of stability.
		settled.forEach((lane, laneIdx) => {
			lane.forEach((item, ord) => {
				expect(combined[laneIdx][ord]).toBe(item);
			});
		});
	});
});

describe('extractParamTags curated chips', () => {
	test('returns nothing for null, undefined, or empty params', () => {
		expect(extractParamTags(null)).toEqual([]);
		expect(extractParamTags(undefined)).toEqual([]);
		expect(extractParamTags({})).toEqual([]);
	});

	test('maps whitelisted keys to localized labels in a stable order', () => {
		// Insert deliberately OUT OF ORDER to prove ordering follows the map,
		// not the input object's enumeration order.
		const tags = extractParamTags({
			quality: 'hd',
			resolution: '1024x1024',
			steps: 30,
			style: 'photoreal'
		});
		expect(tags.map((tag) => tag.key)).toEqual(['resolution', 'quality', 'steps', 'style']);
		expect(tags.map((tag) => tag.value)).toEqual(['1024x1024', 'hd', '30', 'photoreal']);
	});

	test('drops unknown keys, blanks, booleans, and nested objects', () => {
		// Unknown whitelist-or-not junk must vanish; truthy-looking empties
		// (whitespace-only string) drop alongside genuine falsy blanks.
		const tags = extractParamTags({
			system_prompt: 'ignored essay', // curated-away verbose prose
			enable_safety_checker: true, // operational toggle, not surfaced
			nonsense_field: 'whatever',
			background: '   ',
			image_count: 0,
			seed: '',
			output_format: 'png',
			nested: { deeply: 'buried' }
		});
		expect(tags.map((tag) => tag.key)).toEqual(['output_format']);
		expect(tags[0]?.value).toBe('png');
	});

	test('coerces numbers and trims surrounding whitespace on string values', () => {
		const tags = extractParamTags({
			guidance_scale: 7.5,
			strength: 0.65,
			seed: 0,
			aspect_ratio: '  16:9  '
		});
		// aspect_ratio precedes guidance_scale in the curated map.
		expect(tags.map((tag) => tag.value)).toEqual(['16:9', '7.5', '0.65', '0']);
	});

	test('keeps curated video controls while excluding provider internals', () => {
		const tags = extractParamTags({
			prompt_enhancement: 'off',
			motion_amplitude: 'large',
			fps: '50',
			output_quality: 'high',
			retake_mode: 'replace_video',
			safety_tolerance: '6',
			multi_prompt: [{ prompt: 'hidden' }]
		});

		expect(tags.map((tag) => tag.key)).toEqual([
			'prompt_enhancement',
			'motion_amplitude',
			'fps',
			'output_quality',
			'retake_mode'
		]);
	});
});
