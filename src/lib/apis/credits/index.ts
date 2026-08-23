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

export type VideoQuoteInput = {
	resource_id: string;
	action: 'text-to-video' | 'image-to-video' | 'video-to-video';
	dimensions: Record<string, string | number>;
};

export type VideoQuote = ImageQuote;

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

export type AdminLedgerPage = {
	items: LedgerItem[];
	total: number;
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
	skip?: number;
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
	kind: 'exact_map' | 'numeric_tier' | 'unit_blocks' | 'proportional' | 'quantity';
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
	service_type?: string;
	resource_id?: string;
	action?: string;
	enabled?: boolean;
	skip?: number;
	limit?: number;
};

export type CreditPricePage = {
	items: CreditPrice[];
	total: number;
};

export type CreditDimensions = {
	service_type: string;
	dimensions: Record<string, Array<{ key: string; rule_types: string[] }>>;
};

export type ReconciliationStatus = 'failed' | 'unknown';

export type ReconciliationItem = {
	usage_id: string;
	user_id: string;
	user_name_snapshot: string | null;
	user_email_snapshot: string | null;
	status: ReconciliationStatus;
	charged_credits: number;
	resource_id: string;
	action: string;
	channel: string;
	execution_mode: 'mock' | 'fal' | null;
	error_code: string | null;
	error_summary: string | null;
	consumption_ledger_id: string | null;
	compensation_ledger_id: string | null;
	created_at: number;
	completed_at: number | null;
};

export type ReconciliationQuery = {
	status?: ReconciliationStatus;
	compensated?: boolean;
	user_id?: string;
	skip?: number;
	limit?: number;
};

export type ReconciliationPage = { items: ReconciliationItem[]; total: number };

export type CompensationResult = {
	ledger_id: string;
	created: boolean;
	amount: number;
};

export type CreditRedeemResult = {
	ledger_id: string;
	credited: number;
	balance: number;
	redeemed_at: number;
};

export type CreditRedeemBatch = {
	id: string;
	name: string;
	face_value: number;
	code_count: number;
	redeemed_count: number;
	voided_count: number;
	unused_count: number;
	available_count: number;
	expires_at: number | null;
	per_user_limit: number | null;
	voided_at: number | null;
	created_by_id: string;
	created_by_name_snapshot: string | null;
	created_at: number;
};

export type CreditRedeemBatchPage = {
	items: CreditRedeemBatch[];
	total: number;
};

export type CreditRedeemBatchInput = {
	name: string;
	face_value: number;
	quantity: number;
	expires_at: number | null;
	per_user_limit: number | null;
};

export type CreditRedeemBatchCreated = CreditRedeemBatch & {
	codes: string[];
};

export type CreditRedeemCodeStatus = 'available' | 'redeemed' | 'voided' | 'expired';

export type CreditRedeemCode = {
	id: string;
	code: string;
	hint: string;
	status: CreditRedeemCodeStatus;
	redeemed_by_user_id: string | null;
	redeemed_by_name_snapshot: string | null;
	redeemed_at: number | null;
	voided_at: number | null;
};

export type CreditRedeemCodePage = {
	items: CreditRedeemCode[];
	total: number;
};

export type CreditRedeemAudit = {
	id: string;
	action: 'generate' | 'redeem' | 'void_batch' | 'void_code';
	code_id: string | null;
	actor_id: string;
	actor_name_snapshot: string | null;
	request_source: 'web' | 'api' | 'api_key' | 'internal_admin';
	request_id: string;
	metadata: Record<string, unknown> | null;
	created_at: number;
};

export type CreditRedeemAuditPage = {
	items: CreditRedeemAudit[];
	total: number;
};

type QueryValue = string | number | boolean | null | undefined;
type Query = Record<string, QueryValue>;

type CreditRequest = {
	method: 'GET' | 'POST' | 'PUT' | 'DELETE';
	path: string;
	token: string;
	query?: Query;
	body?: object;
	headers?: Record<string, string>;
	cache?: RequestCache;
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
	if (isRecord(value) && 'detail' in value) {
		return parseCreditApiError(value.detail);
	}
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
	// FastAPI HTTPException detail 形态：{code, reason?}（限流、修复校验等）。
	// 缺少该分支时这类错误全部回退成 credit_service_unavailable，限流/校验
	// 失败会被误报成基础设施故障。reason 放入 context 与 CreditError 的
	// context.reason 约定一致（如 redeem_expiry_not_future）。
	if (isRecord(value) && typeof value.code === 'string') {
		const reason = typeof value.reason === 'string' ? value.reason : '';
		return {
			code: value.code,
			message: reason,
			context: reason ? { reason } : {}
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
	headers,
	cache,
	signal
}: CreditRequest): Promise<T> => {
	let response: Response;
	try {
		response = await fetch(buildUrl(path, query), {
			method,
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`,
				...headers
			},
			...(cache ? { cache } : {}),
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

export const quoteVideoCredits = (token: string, input: VideoQuoteInput, signal?: AbortSignal) =>
	requestCredits<VideoQuote>({ method: 'POST', path: '/quotes/video', token, body: input, signal });

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

export type CreditAccountRepairInput = {
	incident_id: string;
	expected_balance: number;
	note: string;
	backup_confirmed: boolean;
};

export type CreditAccountRepairResult = {
	ledger_id: string;
	balance_before: number;
	balance_after: number;
	request_id: string;
};

export const repairCreditAccount = (
	token: string,
	userId: string,
	input: CreditAccountRepairInput,
	signal?: AbortSignal
) =>
	requestCredits<CreditAccountRepairResult>({
		method: 'POST',
		path: `/admin/accounts/${encodeURIComponent(userId)}/repair`,
		token,
		body: input,
		signal
	});

export const getAdminCreditLedger = (
	token: string,
	query: AdminLedgerQuery,
	signal?: AbortSignal
) =>
	requestCredits<AdminLedgerPage>({
		method: 'GET',
		path: '/admin/ledger',
		token,
		query,
		signal
	});

export const getCreditPrices = (
	token: string,
	query: CreditPriceQuery = {},
	signal?: AbortSignal
) =>
	requestCredits<CreditPricePage>({
		method: 'GET',
		path: '/admin/prices',
		token,
		query,
		signal
	});

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

export const getCreditReconciliationCases = (
	token: string,
	query: ReconciliationQuery = {},
	signal?: AbortSignal
) =>
	requestCredits<ReconciliationPage>({
		method: 'GET',
		path: '/admin/reconciliation',
		token,
		query,
		signal
	});

export const compensateCreditReconciliationCase = (
	token: string,
	usageId: string,
	note?: string,
	signal?: AbortSignal
) =>
	requestCredits<CompensationResult>({
		method: 'POST',
		path: `/admin/reconciliation/${encodeURIComponent(usageId)}/compensate`,
		token,
		body: { note: note?.trim() || null },
		signal
	});

export const redeemCreditCode = (token: string, code: string, signal?: AbortSignal) =>
	requestCredits<CreditRedeemResult>({
		method: 'POST',
		path: '/redeem',
		token,
		headers: { 'X-Credit-Redeem-Code': code },
		cache: 'no-store',
		signal
	});

export const getCreditRedeemBatches = (
	token: string,
	query: { skip?: number; limit?: number } = {},
	signal?: AbortSignal
) =>
	requestCredits<CreditRedeemBatchPage>({
		method: 'GET',
		path: '/admin/redeem-batches',
		token,
		query,
		signal
	});

export const createCreditRedeemBatch = (
	token: string,
	input: CreditRedeemBatchInput,
	signal?: AbortSignal
) =>
	requestCredits<CreditRedeemBatchCreated>({
		method: 'POST',
		path: '/admin/redeem-batches',
		token,
		body: input,
		cache: 'no-store',
		signal
	});

export const getCreditRedeemCodes = (
	token: string,
	batchId: string,
	query: { skip?: number; limit?: number } = {},
	signal?: AbortSignal
) =>
	requestCredits<CreditRedeemCodePage>({
		method: 'GET',
		path: `/admin/redeem-batches/${encodeURIComponent(batchId)}/codes`,
		token,
		query,
		signal
	});

export const getCreditRedeemAudit = (
	token: string,
	batchId: string,
	query: { skip?: number; limit?: number } = {},
	signal?: AbortSignal
) =>
	requestCredits<CreditRedeemAuditPage>({
		method: 'GET',
		path: `/admin/redeem-batches/${encodeURIComponent(batchId)}/audit`,
		token,
		query,
		signal
	});

export const voidCreditRedeemBatch = (token: string, batchId: string, signal?: AbortSignal) =>
	requestCredits<{ voided_count: number }>({
		method: 'POST',
		path: `/admin/redeem-batches/${encodeURIComponent(batchId)}/void`,
		token,
		signal
	});

export const voidCreditRedeemCode = (
	token: string,
	batchId: string,
	codeId: string,
	signal?: AbortSignal
) =>
	requestCredits<{ voided: boolean }>({
		method: 'POST',
		path: `/admin/redeem-batches/${encodeURIComponent(batchId)}/codes/${encodeURIComponent(codeId)}/void`,
		token,
		signal
	});
