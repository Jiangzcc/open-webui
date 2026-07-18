import { WEBUI_API_BASE_URL } from '$lib/constants';

export type CreditApiError = {
	code: string;
	message: string;
	context: Record<string, unknown>;
};

export type CreditBalance = {
	balance: number;
};

export type ImageQuoteInput = {
	resource_id: string;
	action: 'text-to-image' | 'image-to-image';
	prompt: string;
	image?: string | string[] | null;
	dimensions: Record<string, string | number>;
};

export type PriceFactor = {
	key: string;
	value: string | number;
	multiplier: string;
};

export type ImageQuote = {
	balance: number;
	sufficient: boolean;
	exempt: boolean;
	configured: boolean;
	factors: PriceFactor[];
	charged_credits: number | null;
	error: string | null;
};

export type LedgerCursor = {
	created_at: number;
	id: string;
};

export type LedgerItem = {
	id: string;
	user_id: string;
	amount: number;
	balance_before: number;
	balance_after: number;
	entry_type: string;
	reason_code: string | null;
	note: string | null;
	user_name_snapshot: string | null;
	user_email_snapshot: string | null;
	operator_id: string | null;
	operator_name_snapshot: string | null;
	operator_email_snapshot: string | null;
	request_source: string;
	request_id: string;
	service_type: string | null;
	resource_id: string | null;
	action: string | null;
	usage_status: 'debited' | 'invoking' | 'succeeded' | 'failed' | 'unknown' | null;
	pricing_snapshot: Record<string, unknown> | null;
	metadata_snapshot: Record<string, unknown> | null;
	created_at: number;
};

export type Page<T> = {
	items: T[];
	next_cursor: LedgerCursor | null;
};

export type LedgerQuery = {
	category?: 'income' | 'consumption' | 'adjustment';
	since?: number;
	until?: number;
	cursor_created_at?: number;
	cursor_id?: string;
	limit?: number;
};

export type AdminLedgerQuery = {
	user_id?: string;
	entry_type?: 'consumption' | 'admin_adjustment' | 'system_adjustment';
	reason_code?: AdjustmentReason;
	service_type?: string;
	resource_id?: string;
	action?: string;
	since?: number;
	until?: number;
	cursor_created_at?: number;
	cursor_id?: string;
	limit?: number;
};

export type CreditAccountQuery = {
	query?: string;
	skip?: number;
	limit?: number;
};

export type CreditAccount = {
	user_id: string;
	name: string | null;
	email: string | null;
	balance: number;
};

export type CreditAccountsPage = {
	items: CreditAccount[];
	total: number;
};

export type AdjustmentReason =
	| 'offline_recharge'
	| 'promotion_gift'
	| 'manual_refund'
	| 'accounting_correction'
	| 'violation_deduction'
	| 'other';

export type CreditAdjustmentInput = {
	direction: 'increase' | 'decrease';
	amount: number;
	reason_code: AdjustmentReason;
	note?: string | null;
};

export type CreditAdjustment = {
	ledger_id: string;
	source: string;
	request_id: string;
};

export type PriceRule = {
	key: string;
	kind: 'exact_map' | 'numeric_tier' | 'unit_blocks' | 'quantity';
	[key: string]: unknown;
};

export type PriceRuleSet = {
	schema_version: 1;
	dimensions: PriceRule[];
};

export type CreditPriceInput = {
	service_type: string;
	resource_id: string;
	action: string;
	base_price: string;
	rules: PriceRuleSet;
	enabled?: boolean;
};

export type CreditPriceUpdate = {
	base_price?: string;
	rules?: PriceRuleSet;
	enabled?: boolean;
};

export type CreditPrice = {
	id: string;
	service_type: string;
	resource_id: string;
	action: string;
	base_price: string;
	rules: PriceRuleSet;
	enabled: boolean;
	updated_at: number;
};

export type CreditPriceQuery = {
	skip?: number;
	limit?: number;
};

export type CreditDimensions = {
	service_type: string;
	dimensions: Record<string, Array<{ key: string; rule_types: string[] }>>;
};

type QueryValue = string | number | boolean | null | undefined;
type Query = Record<string, QueryValue>;

type CreditRequest = {
	method: 'GET' | 'POST' | 'PUT' | 'DELETE';
	path: string;
	token: string;
	query?: Query;
	body?: object;
	signal?: AbortSignal;
};

const unavailableError = (): CreditApiError => ({
	code: 'credit_service_unavailable',
	message: 'Credit service is unavailable',
	context: {}
});

const isRecord = (value: unknown): value is Record<string, unknown> =>
	typeof value === 'object' && value !== null && !Array.isArray(value);

const parseCreditApiError = (value: unknown): CreditApiError => {
	if (
		isRecord(value) &&
		typeof value.code === 'string' &&
		typeof value.message === 'string' &&
		isRecord(value.context)
	) {
		return {
			code: value.code,
			message: value.message,
			context: { ...value.context }
		};
	}

	return unavailableError();
};

const parseJson = async (response: Response): Promise<unknown> => {
	try {
		return await response.json();
	} catch {
		return null;
	}
};

const buildUrl = (path: string, query?: Query) => {
	if (!query) {
		return `${WEBUI_API_BASE_URL}/credits${path}`;
	}

	const searchParams = new URLSearchParams();
	for (const [key, value] of Object.entries(query)) {
		if (value !== undefined && value !== null) {
			searchParams.set(key, String(value));
		}
	}

	const serializedQuery = searchParams.toString();
	return `${WEBUI_API_BASE_URL}/credits${path}${serializedQuery ? `?${serializedQuery}` : ''}`;
};

const requestCredits = async <T>({
	method,
	path,
	token,
	query,
	body,
	signal
}: CreditRequest): Promise<T> => {
	let response: Response;
	try {
		response = await fetch(buildUrl(path, query), {
			method,
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`
			},
			...(body ? { body: JSON.stringify(body) } : {}),
			...(signal ? { signal } : {})
		});
	} catch (error) {
		if (error instanceof DOMException && error.name === 'AbortError') {
			throw error;
		}
		throw unavailableError();
	}

	const payload = await parseJson(response);
	if (!response.ok) {
		throw parseCreditApiError(payload);
	}

	return payload as T;
};

export const getMyCredits = (token: string, signal?: AbortSignal) =>
	requestCredits<CreditBalance>({ method: 'GET', path: '/me', token, signal });

export const quoteImageCredits = (token: string, input: ImageQuoteInput, signal?: AbortSignal) =>
	requestCredits<ImageQuote>({ method: 'POST', path: '/quotes/image', token, body: input, signal });

export const getMyCreditLedger = (token: string, query: LedgerQuery, signal?: AbortSignal) =>
	requestCredits<Page<LedgerItem>>({ method: 'GET', path: '/me/ledger', token, query, signal });

export const getAdminCreditAccounts = (
	token: string,
	query: CreditAccountQuery = {},
	signal?: AbortSignal
) =>
	requestCredits<CreditAccountsPage>({
		method: 'GET',
		path: '/admin/accounts',
		token,
		query,
		signal
	});

export const adjustCreditAccount = (
	token: string,
	userId: string,
	input: CreditAdjustmentInput,
	signal?: AbortSignal
) =>
	requestCredits<CreditAdjustment>({
		method: 'POST',
		path: `/admin/accounts/${encodeURIComponent(userId)}/adjustments`,
		token,
		body: input,
		signal
	});

export const getAdminCreditLedger = (
	token: string,
	query: AdminLedgerQuery,
	signal?: AbortSignal
) =>
	requestCredits<Page<LedgerItem>>({ method: 'GET', path: '/admin/ledger', token, query, signal });

export const getCreditPrices = (
	token: string,
	query: CreditPriceQuery = {},
	signal?: AbortSignal
) => requestCredits<CreditPrice[]>({ method: 'GET', path: '/admin/prices', token, query, signal });

export const createCreditPrice = (token: string, input: CreditPriceInput, signal?: AbortSignal) =>
	requestCredits<CreditPrice>({
		method: 'POST',
		path: '/admin/prices',
		token,
		body: input,
		signal
	});

export const updateCreditPrice = (
	token: string,
	priceId: string,
	input: CreditPriceUpdate,
	signal?: AbortSignal
) =>
	requestCredits<CreditPrice>({
		method: 'PUT',
		path: `/admin/prices/${encodeURIComponent(priceId)}`,
		token,
		body: input,
		signal
	});

export const deleteCreditPrice = (token: string, priceId: string, signal?: AbortSignal) =>
	requestCredits<{ id: string }>({
		method: 'DELETE',
		path: `/admin/prices/${encodeURIComponent(priceId)}`,
		token,
		signal
	});

export const getAdminCreditDimensions = (
	token: string,
	serviceType: string,
	signal?: AbortSignal
) =>
	requestCredits<CreditDimensions>({
		method: 'GET',
		path: `/admin/dimensions/${encodeURIComponent(serviceType)}`,
		token,
		signal
	});
