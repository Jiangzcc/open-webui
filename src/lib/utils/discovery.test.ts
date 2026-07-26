import { describe, expect, test } from 'vitest';

import { applyDiscoveryPage, beginDiscoveryRequest, createDiscoveryFeedState } from './discovery';

const post = (id: string) => ({
	id,
	title: null,
	description: null,
	content_url: `/content/${id}`,
	availability: 'available' as const,
	mime_type: 'image/png',
	prompt_preview: null,
	model_name: null,
	owner: { user_id: 'u1', name: 'Author', profile_image_url: null, deleted: false },
	like_count: 0,
	favorite_count: 0,
	liked: false,
	favorited: false,
	published_at: 10
});

describe('discovery feed state', () => {
	test('deduplicates appended pages and keeps the newest cursor', () => {
		const state = createDiscoveryFeedState([post('p1')]);
		const generation = beginDiscoveryRequest(state);

		expect(
			applyDiscoveryPage(
				state,
				generation,
				{ items: [post('p1'), post('p2')], next_cursor: 'next' },
				false
			)
		).toBe(true);
		expect(state.items.map((item) => item.id)).toEqual(['p1', 'p2']);
		expect(state.nextCursor).toBe('next');
	});

	test('ignores stale responses after a newer request starts', () => {
		const state = createDiscoveryFeedState();
		const stale = beginDiscoveryRequest(state);
		beginDiscoveryRequest(state);

		expect(applyDiscoveryPage(state, stale, { items: [post('p1')], next_cursor: null }, true)).toBe(
			false
		);
		expect(state.items).toEqual([]);
	});
});
