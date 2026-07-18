import type { AdjustmentReason, CreditAdjustmentInput, PriceRule } from '$lib/apis/credits';

export type AdjustmentForm = {
	direction: 'increase' | 'decrease';
	amount: string;
	reasonCode: AdjustmentReason;
	note: string;
};

export type PriceForm = {
	serviceType: string;
	resourceId: string;
	action: string;
	basePrice: string;
	dimensions: PriceRule[];
};

export type FormErrors = Partial<Record<keyof AdjustmentForm | keyof PriceForm, string>>;

export const creditValidationKeys = {
	positiveWholeNumber: 'credits.validation.positiveWholeNumber',
	explainAdjustment: 'credits.validation.explainAdjustment',
	serviceType: 'credits.validation.serviceType',
	resourceId: 'credits.validation.resourceId',
	action: 'credits.validation.action',
	positivePrice: 'credits.validation.positivePrice',
	uniqueDimensions: 'credits.validation.uniqueDimensions',
	validMultipliers: 'credits.validation.validMultipliers'
} as const;

const MAX_ADJUSTMENT = 1_000_000_000;
const positiveDecimal = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

const isRecord = (value: unknown): value is Record<string, unknown> =>
	typeof value === 'object' && value !== null && !Array.isArray(value);

export const isPositiveDecimal = (value: unknown) =>
	typeof value === 'string' && positiveDecimal.test(value) && Number(value) > 0;

export const createAdjustmentForm = (): AdjustmentForm => ({
	direction: 'increase',
	amount: '',
	reasonCode: 'promotion_gift',
	note: ''
});

export const validateAdjustmentForm = (form: AdjustmentForm): FormErrors => {
	const errors: FormErrors = {};
	const amount = Number(form.amount);

	if (!Number.isSafeInteger(amount) || amount < 1 || amount > MAX_ADJUSTMENT) {
		errors.amount = creditValidationKeys.positiveWholeNumber;
	}

	if (form.reasonCode === 'other' && !form.note.trim()) {
		errors.note = creditValidationKeys.explainAdjustment;
	}

	return errors;
};

export const toCreditAdjustmentInput = (form: AdjustmentForm): CreditAdjustmentInput => {
	const input: CreditAdjustmentInput = {
		direction: form.direction,
		amount: Number(form.amount),
		reason_code: form.reasonCode
	};

	if (form.reasonCode === 'other') {
		return { ...input, note: form.note.trim() };
	}

	return input;
};

const isValidRule = (rule: PriceRule) => {
	if (!rule.key.trim()) {
		return false;
	}

	if (rule.kind === 'exact_map') {
		return (
			isRecord(rule.values) &&
			Object.prototype.hasOwnProperty.call(rule.values, 'default') &&
			Object.keys(rule.values).length > 0 &&
			Object.values(rule.values).every(isPositiveDecimal)
		);
	}

	if (rule.kind === 'numeric_tier') {
		return (
			Array.isArray(rule.tiers) &&
			rule.tiers.length > 0 &&
			rule.tiers.every(
				(tier) =>
					isRecord(tier) &&
					isPositiveDecimal(String(tier.max)) &&
					isPositiveDecimal(String(tier.multiplier))
			)
		);
	}

	if (rule.kind === 'unit_blocks') {
		return (
			isPositiveDecimal(String(rule.block_size)) &&
			isPositiveDecimal(String(rule.multiplier_per_block))
		);
	}

	return rule.kind === 'quantity';
};

export const validatePriceForm = (form: PriceForm): FormErrors => {
	const errors: FormErrors = {};

	if (!form.serviceType.trim()) {
		errors.serviceType = creditValidationKeys.serviceType;
	}
	if (!form.resourceId.trim()) {
		errors.resourceId = creditValidationKeys.resourceId;
	}
	if (!form.action.trim()) {
		errors.action = creditValidationKeys.action;
	}
	if (!isPositiveDecimal(form.basePrice)) {
		errors.basePrice = creditValidationKeys.positivePrice;
	}

	const keys = form.dimensions.map((rule) => rule.key.trim());
	if (new Set(keys).size !== keys.length) {
		errors.dimensions = creditValidationKeys.uniqueDimensions;
	} else if (!form.dimensions.every(isValidRule)) {
		errors.dimensions = creditValidationKeys.validMultipliers;
	}

	return errors;
};
