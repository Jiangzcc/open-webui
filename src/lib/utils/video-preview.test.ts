import { describe, expect, test, vi } from 'vitest';

import { playMutedPreview, stopPreview } from './video-preview';

const createVideo = () => ({
	currentTime: 12,
	muted: false,
	pause: vi.fn(),
	play: vi.fn().mockResolvedValue(undefined)
});

describe('video preview', () => {
	test('plays a muted preview when hover is available', async () => {
		const video = createVideo();

		await expect(playMutedPreview(video, true)).resolves.toBe(true);
		expect(video.muted).toBe(true);
		expect(video.play).toHaveBeenCalledOnce();
	});

	test('does not start preview on a touch-only device', async () => {
		const video = createVideo();

		await expect(playMutedPreview(video, false)).resolves.toBe(false);
		expect(video.play).not.toHaveBeenCalled();
	});

	test('contains browser autoplay rejection without leaving an unhandled promise', async () => {
		const video = createVideo();
		video.play.mockRejectedValueOnce(new Error('blocked'));

		await expect(playMutedPreview(video, true)).resolves.toBe(false);
	});

	test('pauses and rewinds when the pointer leaves', () => {
		const video = createVideo();

		stopPreview(video);
		expect(video.pause).toHaveBeenCalledOnce();
		expect(video.currentTime).toBe(0);
	});

	test('accepts a missing video during teardown', () => {
		expect(() => stopPreview(null)).not.toThrow();
	});
});
