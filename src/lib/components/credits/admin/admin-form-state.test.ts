import { describe, expect, test } from 'vitest';

import {
	addExactMapEntry,
	createAdjustmentForm,
	removeExactMapEntry,
	toCreditAdjustmentInput,
	updateExactMapEntryKey,
	updateExactMapEntryMultiplier,
	validateAdjustmentForm,
	validatePriceForm
} from './admin-form-state';

describe('admin credit form state', () => {
	test('requires a positive integer adjustment amount', () => {
		const form = createAdjustmentForm();

		expect(validateAdjustmentForm({ ...form, amount: '0' }).amount).toBe(
			'credits.validation.positiveWholeNumber'
		);
		expect(validateAdjustmentForm({ ...form, amount: '2.5' }).amount).toBe(
			'credits.validation.positiveWholeNumber'
		);
	});

	test('requires a note only for the other adjustment reason', () => {
		const form = {
			...createAdjustmentForm(),
			reasonCode: 'other' as const,
			amount: '12',
			note: '   '
		};

		expect(validateAdjustmentForm(form).note).toBe('credits.validation.explainAdjustment');
		expect(toCreditAdjustmentInput({ ...form, note: ' manual correction ' })).toEqual({
			direction: 'increase',
			amount: 12,
			reason_code: 'other',
			note: 'manual correction'
		});
	});

	test('keeps fixed-reason notes out of the adjustment request', () => {
		expect(
			toCreditAdjustmentInput({
				...createAdjustmentForm(),
				amount: '8',
				reasonCode: 'promotion_gift',
				note: 'not submitted'
			})
		).toEqual({ direction: 'increase', amount: 8, reason_code: 'promotion_gift' });
	});

	test('updates one exact-map multiplier without losing other mappings', () => {
		const rule = {
			key: 'aspect_ratio',
			kind: 'exact_map' as const,
			values: { default: '1', '1:1': '1', '16:9': '1.5' }
		};

		expect(updateExactMapEntryMultiplier(rule, '16:9', '2')).toEqual({
			...rule,
			values: { default: '1', '1:1': '1', '16:9': '2' }
		});
		expect(rule.values).toEqual({ default: '1', '1:1': '1', '16:9': '1.5' });
	});

	test('renames one exact-map entry without mutating or overwriting mappings', () => {
		const rule = {
			key: 'aspect_ratio',
			kind: 'exact_map' as const,
			values: { default: '1', '1:1': '1', '16:9': '1.5' }
		};
		const originalValues = rule.values;

		expect(updateExactMapEntryKey(rule, '1:1', '4:3')).toEqual({
			...rule,
			values: { default: '1', '4:3': '1', '16:9': '1.5' }
		});
		expect(updateExactMapEntryKey(rule, '1:1', '16:9')).toBe(rule);
		expect(updateExactMapEntryKey(rule, '1:1', ' 16:9 ')).toBe(rule);
		expect(rule.values).toBe(originalValues);
		expect(rule.values).toEqual({ default: '1', '1:1': '1', '16:9': '1.5' });
	});

	test('adds and removes exact-map entries while preserving the default mapping', () => {
		const rule = {
			key: 'aspect_ratio',
			kind: 'exact_map' as const,
			values: { default: '1', '1:1': '1' }
		};
		const added = addExactMapEntry(rule);

		expect(added).toEqual({ ...rule, values: { default: '1', '1:1': '1', '': '1' } });
		expect(addExactMapEntry(added)).toBe(added);
		const whitespaceEntry = { ...rule, values: { ...rule.values, '   ': '1' } };
		expect(addExactMapEntry(whitespaceEntry)).toBe(whitespaceEntry);
		expect(removeExactMapEntry(rule, '1:1')).toEqual({ ...rule, values: { default: '1' } });
		expect(removeExactMapEntry(rule, 'default')).toBe(rule);
		expect(rule.values).toEqual({ default: '1', '1:1': '1' });
	});

	test('rejects blank exact-map keys and invalid multipliers', () => {
		const base = {
			serviceType: 'image',
			resourceId: 'model-a',
			action: 'text-to-image',
			basePrice: '10'
		};

		for (const values of [
			{ default: '1', '': '1' },
			{ default: '1', '   ': '1' },
			{ default: '1', '16:9': '1', ' 16:9 ': '2' },
			{ default: '1', '16:9': '' },
			{ default: '1', '16:9': '0' },
			{ default: '1', '16:9': '-1' }
		]) {
			expect(
				validatePriceForm({
					...base,
					dimensions: [{ key: 'aspect_ratio', kind: 'exact_map', values }]
				}).dimensions
			).toBe('credits.validation.validMultipliers');
		}
	});

	test('accepts multiple supported dimension rules together', () => {
		expect(
			validatePriceForm({
				serviceType: 'image',
				resourceId: 'model-a',
				action: 'text-to-image',
				basePrice: '1.5',
				dimensions: [
					{ key: 'size', kind: 'exact_map', values: { default: '1' } },
					{ key: 'pixel_count', kind: 'proportional', unit_size: '1000000' },
					{ key: 'image_count', kind: 'quantity' }
				]
			})
		).toEqual({});
	});

	test('validates every supported rule kind and exact-map default coverage', () => {
		const base = {
			serviceType: 'image',
			resourceId: 'model-a',
			action: 'text-to-image',
			basePrice: '1.5'
		};

		expect(
			validatePriceForm({
				...base,
				dimensions: [{ key: 'size', kind: 'exact_map', values: { '1024x1024': '1' } }]
			}).dimensions
		).toBe('credits.validation.validMultipliers');
		expect(
			validatePriceForm({
				...base,
				dimensions: [{ key: 'pixel_count', kind: 'proportional', unit_size: '1000000' }]
			})
		).toEqual({});
		expect(
			validatePriceForm({
				...base,
				dimensions: [{ key: 'pixel_count', kind: 'proportional', unit_size: '0' }]
			}).dimensions
		).toBe('credits.validation.validMultipliers');
		expect(
			validatePriceForm({
				...base,
				dimensions: [
					{ key: 'steps', kind: 'unit_blocks', block_size: '5', multiplier_per_block: '1.2' }
				]
			})
		).toEqual({});
		expect(
			validatePriceForm({
				...base,
				dimensions: [
					{ key: 'steps', kind: 'unit_blocks', block_size: '0', multiplier_per_block: '1.2' }
				]
			}).dimensions
		).toBe('credits.validation.validMultipliers');
	});

	test('rejects invalid base prices and duplicate supported dimension keys', () => {
		expect(
			validatePriceForm({
				serviceType: 'image',
				resourceId: 'model-a',
				action: 'text-to-image',
				basePrice: '0',
				dimensions: []
			}).basePrice
		).toBe('credits.validation.positivePrice');

		expect(
			validatePriceForm({
				serviceType: 'image',
				resourceId: 'model-a',
				action: 'text-to-image',
				basePrice: '1.5',
				dimensions: [
					{ key: 'size', kind: 'exact_map', values: { '1024x1024': '1' } },
					{ key: 'size', kind: 'quantity' }
				]
			}).dimensions
		).toBe('credits.validation.uniqueDimensions');
	});
});
