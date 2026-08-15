import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ProviderOverview = {
	provider: string;
	window_start_at: number;
	window_end_at: number;
	invocation_count: number;
	success_count: number;
	failed_count: number;
	active_count: number;
	average_duration_ms: number | null;
	provider_request_count: number;
	matched_provider_request_count: number;
	billing_event_count: number;
	matched_billing_event_count: number;
	exact_costs: Record<string, string>;
	matched_exact_costs: Record<string, string>;
	last_sync_status: 'running' | 'succeeded' | 'failed' | null;
	last_synced_at: number | null;
};

export type ProviderModelSummary = {
	provider: string;
	provider_model_id: string;
	media_kind: 'image' | 'video';
	request_count: number;
	success_count: number;
	failed_count: number;
	cancelled_count: number;
	unknown_count: number;
	active_count: number;
	average_execution_duration_ms: number | null;
	last_invocation_at: number;
};

export type ProviderBillingEvent = {
	provider: string;
	provider_request_id: string;
	provider_model_id: string;
	event_timestamp: string;
	api_key_id: string | null;
	output_units: string | null;
	unit_price: string | null;
	percent_discount: string | null;
	cost_subtotal: string;
	cost_discount: string;
	cost_total: string;
	cost_nano_usd: string;
	currency: string;
	matched_invocation: boolean;
	synced_at: number;
};

export type ProviderAnalytics = {
	provider: string;
	provider_model_id: string;
	timeframe: string;
	bucket_start: string;
	metrics: Record<string, number>;
	synced_at: number;
};

export type ProviderSyncResult = {
	id: string;
	provider: string;
	status: 'running' | 'succeeded' | 'failed';
	resources: Array<'pricing' | 'requests' | 'billing_events' | 'usage' | 'analytics'>;
	counts: Record<string, number> | null;
	error_code: string | null;
	window_start_at: number;
	window_end_at: number;
	started_at: number;
	completed_at: number | null;
};

const request = async <T>(path: string, token: string, init?: RequestInit): Promise<T> => {
	const response = await fetch(`${WEBUI_API_BASE_URL}/provider-ops${path}`, {
		...init,
		headers: {
			Accept: 'application/json',
			...(init?.body ? { 'Content-Type': 'application/json' } : {}),
			authorization: `Bearer ${token}`,
			...(init?.headers ?? {})
		}
	});
	if (!response.ok) throw await response.json().catch(() => null);
	// 204 No Content 无响应体，直接返回 undefined。
	if (response.status === 204) return undefined as T;
	return (await response.json()) as T;
};

const query = (provider: string, windowHours: number, limit?: number) => {
	const params = new URLSearchParams({ provider, window_hours: String(windowHours) });
	if (limit !== undefined) params.set('limit', String(limit));
	return params.toString();
};

export const getProviderOverview = (token: string, provider: string, windowHours: number) =>
	request<ProviderOverview>(`/admin/overview?${query(provider, windowHours)}`, token);

export const listProviderModelSummary = (token: string, provider: string, windowHours: number) =>
	request<{ items: ProviderModelSummary[] }>(
		`/admin/model-summary?${query(provider, windowHours)}`,
		token
	).then((response) => response.items);

export const listProviderBillingEvents = (
	token: string,
	provider: string,
	windowHours: number,
	limit = 100
) =>
	request<{ items: ProviderBillingEvent[] }>(
		`/admin/billing-events?${query(provider, windowHours, limit)}`,
		token
	).then((response) => response.items);

export const listProviderAnalytics = (
	token: string,
	provider: string,
	windowHours: number,
	limit = 500
) =>
	request<{ items: ProviderAnalytics[] }>(
		`/admin/analytics?${query(provider, windowHours, limit)}`,
		token
	).then((response) => response.items);

export const syncFalProvider = (token: string, windowHours: number, timeframe: string) =>
	request<ProviderSyncResult>('/admin/providers/fal/sync', token, {
		method: 'POST',
		body: JSON.stringify({
			resources: ['pricing', 'requests', 'billing_events', 'usage', 'analytics'],
			window_hours: windowHours,
			timeframe: timeframe
		})
	});
