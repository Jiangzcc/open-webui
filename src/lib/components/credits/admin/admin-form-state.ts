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

type ExactMapRule = PriceRule & {
	kind: 'exact_map';
	values: Record<string, string>;
};

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

export const hasBlankExactMapEntry = (rule: ExactMapRule): boolean =>
	Object.keys(rule.values).some((key) => !key.trim());

export const addExactMapEntry = (rule: ExactMapRule): ExactMapRule =>
	hasBlankExactMapEntry(rule) ? rule : { ...rule, values: { ...rule.values, '': '1' } };

export const updateExactMapEntryKey = (
	rule: ExactMapRule,
	currentKey: string,
	nextKey: string
): ExactMapRule => {
	const normalizedNextKey = nextKey.trim();
	const normalizedKeyExists = Object.keys(rule.values).some(
		(key) => key !== currentKey && key.trim() === normalizedNextKey
	);
	if (
		currentKey === 'default' ||
		currentKey === nextKey ||
		!Object.prototype.hasOwnProperty.call(rule.values, currentKey) ||
		normalizedKeyExists
	) {
		return rule;
	}

	const values = Object.fromEntries(
		Object.entries(rule.values).map(([key, multiplier]) =>
			key === currentKey ? [nextKey, multiplier] : [key, multiplier]
		)
	);
	return { ...rule, values };
};

export const updateExactMapEntryMultiplier = (
	rule: ExactMapRule,
	key: string,
	multiplier: string
): ExactMapRule =>
	Object.prototype.hasOwnProperty.call(rule.values, key)
		? { ...rule, values: { ...rule.values, [key]: multiplier } }
		: rule;

export const removeExactMapEntry = (rule: ExactMapRule, key: string): ExactMapRule => {
	if (key === 'default' || !Object.prototype.hasOwnProperty.call(rule.values, key)) return rule;
	return {
		...rule,
		values: Object.fromEntries(Object.entries(rule.values).filter(([entryKey]) => entryKey !== key))
	};
};

const isValidRule = (rule: PriceRule) => {
	if (!rule.key.trim()) {
		return false;
	}

	if (rule.kind === 'exact_map') {
		const valueKeys = isRecord(rule.values) ? Object.keys(rule.values) : [];
		const normalizedValueKeys = valueKeys.map((key) => key.trim());
		return (
			isRecord(rule.values) &&
			Object.prototype.hasOwnProperty.call(rule.values, 'default') &&
			valueKeys.length > 0 &&
			normalizedValueKeys.every(Boolean) &&
			new Set(normalizedValueKeys).size === normalizedValueKeys.length &&
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
	if (rule.kind === 'proportional') {
		return isPositiveDecimal(String(rule.unit_size));
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
