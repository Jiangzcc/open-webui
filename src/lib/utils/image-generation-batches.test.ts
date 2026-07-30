import { describe, expect, test } from 'vitest';

import {
	buildCreationDraft,
	consumePendingCreationDraft,
	generationElapsedSeconds,
	isGenerationTaskTerminal,
	mergeGenerationTask,
	storePendingCreationDraft,
	taskToGenerationBatch,
	type ImageGenerationTask
} from './image-generation-batches';

const task = (overrides: Partial<ImageGenerationTask> = {}): ImageGenerationTask => ({
	id: 'task-1',
	status: 'queued',
	kind: 'text-to-image',
	prompt: 'quiet lake',
	model_id: 'fal/model',
	params: { aspect_ratio: '16:9', resolution: '2K', quality: 'high' },
	expected_count: 2,
	result: [],
	error_code: null,
	created_at: 1_000,
	started_at: null,
	completed_at: null,
	updated_at: 1_000,
	...overrides
});

describe('image generation batches', () => {
	test('maps a persisted task to a stable result batch', () => {
		expect(taskToGenerationBatch(task())).toMatchObject({
			id: 'task-1',
			status: 'queued',
			aspectRatio: '16:9',
			resolution: '2K',
			quality: 'high',
			expectedCount: 2
		});
	});

	test('updates one batch without flattening or reordering other batches', () => {
		const older = taskToGenerationBatch(task({ id: 'older', created_at: 500 }));
		const pending = taskToGenerationBatch(task());
		const completed = task({
			status: 'succeeded',
			result: [{ url: '/one.png' }, { url: '/two.png' }],
			completed_at: 4_000
		});

		const merged = mergeGenerationTask([pending, older], completed);
		expect(merged.map((batch) => batch.id)).toEqual(['task-1', 'older']);
		expect(merged[0].images).toHaveLength(2);
		expect(merged[1]).toBe(older);
	});

	test('prepends a recovered newer task and identifies terminal states', () => {
		const older = taskToGenerationBatch(task({ id: 'older', created_at: 500 }));
		const merged = mergeGenerationTask([older], task({ id: 'new', created_at: 2_000 }));
		expect(merged.map((batch) => batch.id)).toEqual(['new', 'older']);
		expect(isGenerationTaskTerminal('running')).toBe(false);
		expect(isGenerationTaskTerminal('succeeded')).toBe(true);
		expect(isGenerationTaskTerminal('failed')).toBe(true);
	});

	test('reports elapsed time from creation until now or completion', () => {
		const pending = taskToGenerationBatch(task());
		expect(generationElapsedSeconds(pending, 1_005_999)).toBe(5);
		expect(
			generationElapsedSeconds(taskToGenerationBatch(task({ completed_at: 1_008 })), 20_000)
		).toBe(8);
	});

	test('builds explicit recreate and use-as-reference drafts', () => {
		const common = {
			prompt: 'quiet lake',
			model_id: 'fal/model',
			params: { aspect_ratio: '3:2', size: '1536x1024', quality: 'medium' },
			content_url: '/image.png'
		};
		expect(buildCreationDraft(common)).toEqual({
			prompt: 'quiet lake',
			modelId: 'fal/model',
			aspectRatio: '3:2',
			resolution: '1536x1024',
			quality: 'medium',
			referenceImageUrl: null
		});
		expect(buildCreationDraft({ ...common, useAsReference: true }).referenceImageUrl).toBe(
			'/image.png'
		);
	});

	test('stores and consumes a cross-route creation draft exactly once', () => {
		const values = new Map<string, string>();
		const storage = {
			getItem: (key: string) => values.get(key) ?? null,
			setItem: (key: string, value: string) => values.set(key, value),
			removeItem: (key: string) => values.delete(key)
		};
		const draft = buildCreationDraft({
			prompt: 'quiet lake',
			model_id: 'public/model',
			params: { aspect_ratio: '16:9' },
			content_url: '/image.png',
			useAsReference: true
		});

		storePendingCreationDraft(storage, draft);
		expect(consumePendingCreationDraft(storage)).toEqual(draft);
		expect(consumePendingCreationDraft(storage)).toBeNull();
	});

	test('discards malformed cross-route drafts', () => {
		const values = new Map([['open-webui:pending-image-creation-draft', '{"prompt":1}']]);
		const storage = {
			getItem: (key: string) => values.get(key) ?? null,
			setItem: (key: string, value: string) => values.set(key, value),
			removeItem: (key: string) => values.delete(key)
		};

		expect(consumePendingCreationDraft(storage)).toBeNull();
		expect(values.size).toBe(0);
	});
});
