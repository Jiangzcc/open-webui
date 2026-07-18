import { describe, expect, test } from 'vitest';

import {
	createAdjustmentForm,
	toCreditAdjustmentInput,
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

	test('accepts multiple supported dimension rules together', () => {
		expect(
			validatePriceForm({
				serviceType: 'image',
				resourceId: 'model-a',
				action: 'text-to-image',
				basePrice: '1.5',
				dimensions: [
					{ key: 'size', kind: 'exact_map', values: { default: '1' } },
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
