import { describe, expect, test } from 'vitest';

import {
	createImageCustomSizeState,
	updateImageCustomSizeState,
	type ImageCustomSizeContext,
	type ImageCustomSizeState
} from './image-generation-custom-size-state';

const ratioContext = (
	aspectRatio: ImageCustomSizeContext['aspectRatio'] = '16:9',
	ratioSize = '1024x576',
	multipleOf?: number
): ImageCustomSizeContext => ({ aspectRatio, ratioSize, multipleOf });

const enabledState = (overrides: Partial<ImageCustomSizeState> = {}): ImageCustomSizeState => ({
	enabled: true,
	aspectRatioLocked: true,
	width: 1024,
	height: 576,
	...overrides
});

describe('image custom size state', () => {
	test('starts disabled with the aspect ratio lock ready', () => {
		expect(createImageCustomSizeState()).toEqual({
			enabled: false,
			aspectRatioLocked: true,
			width: null,
			height: null
		});
	});

	test('enables with the selected ratio baseline and disables without discarding dimensions', () => {
		const enabled = updateImageCustomSizeState(
			createImageCustomSizeState(),
			{ type: 'set-enabled', enabled: true },
			ratioContext()
		);
		expect(enabled).toEqual(enabledState());
		expect(
			updateImageCustomSizeState(enabled, { type: 'set-enabled', enabled: false }, ratioContext())
		).toEqual({ ...enabled, enabled: false });
	});

	test('relocks existing dimensions when custom size is re-enabled', () => {
		const state = enabledState({
			enabled: false,
			aspectRatioLocked: false,
			width: 800,
			height: 900
		});
		expect(
			updateImageCustomSizeState(state, { type: 'set-enabled', enabled: true }, ratioContext('4:3'))
		).toEqual(enabledState({ width: 800, height: 600 }));
	});

	test('updates the companion dimension while locked and honors size alignment', () => {
		const context = ratioContext('16:9', '1024x576', 32);
		expect(
			updateImageCustomSizeState(
				enabledState(),
				{ type: 'set-dimension', dimension: 'width', value: 800 },
				context
			)
		).toEqual(enabledState({ width: 800, height: 448 }));
		expect(
			updateImageCustomSizeState(
				enabledState(),
				{ type: 'set-dimension', dimension: 'height', value: 640 },
				context
			)
		).toEqual(enabledState({ width: 1152, height: 640 }));
	});

	test('lets dimensions change independently while unlocked or disabled', () => {
		const unlocked = enabledState({ aspectRatioLocked: false });
		expect(
			updateImageCustomSizeState(
				unlocked,
				{ type: 'set-dimension', dimension: 'width', value: 700 },
				ratioContext()
			)
		).toEqual({ ...unlocked, width: 700 });
		const disabled = enabledState({ enabled: false });
		expect(
			updateImageCustomSizeState(
				disabled,
				{ type: 'set-dimension', dimension: 'height', value: 700 },
				ratioContext()
			)
		).toEqual({ ...disabled, height: 700 });
		expect(
			updateImageCustomSizeState(
				disabled,
				{ type: 'set-dimensions', width: 1536, height: 1024 },
				ratioContext()
			)
		).toEqual({ ...disabled, width: 1536, height: 1024 });
	});

	test('clears or keeps invalid source input without inventing a companion value', () => {
		const state = enabledState();
		expect(
			updateImageCustomSizeState(
				state,
				{ type: 'set-dimension', dimension: 'width', value: null },
				ratioContext()
			)
		).toEqual({ ...state, width: null });
		expect(
			updateImageCustomSizeState(
				state,
				{ type: 'set-dimension', dimension: 'width', value: -1 },
				ratioContext()
			)
		).toEqual({ ...state, width: -1 });
	});

	test('toggles the lock and realigns from width, height, or the ratio baseline', () => {
		const unlocked = updateImageCustomSizeState(
			enabledState(),
			{ type: 'toggle-aspect-ratio-lock' },
			ratioContext()
		);
		expect(unlocked.aspectRatioLocked).toBe(false);
		expect(
			updateImageCustomSizeState(
				{ ...unlocked, width: 900, height: 600 },
				{ type: 'toggle-aspect-ratio-lock' },
				ratioContext('1:1', '1024x1024')
			)
		).toEqual(enabledState({ width: 900, height: 900 }));
		expect(
			updateImageCustomSizeState(
				enabledState({ aspectRatioLocked: false, width: null, height: 600 }),
				{ type: 'toggle-aspect-ratio-lock' },
				ratioContext('4:3', '1024x768')
			)
		).toEqual(enabledState({ width: 800, height: 600 }));
		expect(
			updateImageCustomSizeState(
				enabledState({ aspectRatioLocked: false, width: null, height: null }),
				{ type: 'toggle-aspect-ratio-lock' },
				ratioContext()
			)
		).toEqual(enabledState());
	});

	test('switches locked custom dimensions with the selected ratio', () => {
		expect(
			updateImageCustomSizeState(
				enabledState(),
				{ type: 'select-aspect-ratio' },
				ratioContext('4:3', '1024x768')
			)
		).toEqual(enabledState({ height: 768 }));
		expect(
			updateImageCustomSizeState(
				enabledState(),
				{ type: 'select-aspect-ratio' },
				{ aspectRatio: '3:2' }
			)
		).toEqual(enabledState({ height: 683 }));
	});

	test('does not synchronize a selected ratio while disabled or unlocked', () => {
		for (const state of [
			enabledState({ enabled: false }),
			enabledState({ aspectRatioLocked: false })
		]) {
			expect(
				updateImageCustomSizeState(
					state,
					{ type: 'select-aspect-ratio' },
					ratioContext('4:3', '1024x768')
				)
			).toBe(state);
		}
	});

	test('uses the current dimensions as the lock ratio for Auto', () => {
		const state = enabledState({ width: 800, height: 400 });
		expect(
			updateImageCustomSizeState(
				state,
				{ type: 'set-dimension', dimension: 'width', value: 600 },
				{ aspectRatio: 'auto' }
			)
		).toEqual(enabledState({ width: 600, height: 300 }));
	});

	test('uses a concrete fallback when Auto has no numeric custom dimensions yet', () => {
		expect(
			updateImageCustomSizeState(
				createImageCustomSizeState(),
				{ type: 'set-enabled', enabled: true },
				{ aspectRatio: 'auto', ratioSize: 'auto', fallbackSize: '1024x1024' }
			)
		).toEqual(enabledState({ height: 1024 }));
	});

	test('keeps incomplete dimensions when no usable lock ratio exists', () => {
		const auto = { aspectRatio: 'auto' } as const;
		expect(
			updateImageCustomSizeState(
				enabledState({ width: 800, height: null }),
				{ type: 'set-dimension', dimension: 'width', value: 600 },
				auto
			)
		).toEqual(enabledState({ width: 600, height: null }));
		expect(
			updateImageCustomSizeState(
				enabledState({ aspectRatioLocked: false, width: 800, height: null }),
				{ type: 'toggle-aspect-ratio-lock' },
				{ aspectRatio: '0:1' as ImageCustomSizeContext['aspectRatio'] }
			)
		).toEqual(enabledState({ width: 800, height: null }));
		expect(
			updateImageCustomSizeState(
				enabledState({ aspectRatioLocked: false, width: null, height: 600 }),
				{ type: 'toggle-aspect-ratio-lock' },
				auto
			)
		).toEqual(enabledState({ width: null, height: 600 }));
		expect(
			updateImageCustomSizeState(
				createImageCustomSizeState(),
				{ type: 'set-enabled', enabled: true },
				auto
			)
		).toEqual(enabledState({ width: null, height: null }));
	});
});
