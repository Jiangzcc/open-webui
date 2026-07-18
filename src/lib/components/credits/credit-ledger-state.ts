import type { LedgerCursor, LedgerQuery } from '$lib/apis/credits';

export type CreditBalanceState =
	| { status: 'idle' | 'loading'; balance: number | null }
	| { status: 'ready'; balance: number }
	| { status: 'unavailable'; balance: null };

const DAY_MS = 24 * 60 * 60 * 1000;
const MAX_LEDGER_AGE_MS = 365 * DAY_MS;

export const LEDGER_PAGE_SIZE = 5;

const toDateInputValue = (date: Date) => date.toISOString().slice(0, 10);

export const idleCreditBalanceState = (): CreditBalanceState => ({
	status: 'idle',
	balance: null
});

export const unavailableCreditBalanceState = (_state: CreditBalanceState): CreditBalanceState => ({
	status: 'unavailable',
	balance: null
});

export const shouldRefreshCreditBalance = (wasOpen: boolean, isOpen: boolean) => isOpen && !wasOpen;

export const oneYearAgoDate = (now = new Date()) =>
	toDateInputValue(new Date(now.getTime() - MAX_LEDGER_AGE_MS));

export const todayDate = (now = new Date()) => toDateInputValue(now);

export const toUnixTimestamp = (
	value: string,
	now = new Date(),
	boundary: 'start' | 'end' = 'start'
) => {
	if (!value) return undefined;

	const selected = new Date(`${value}T${boundary === 'end' ? '23:59:59.000' : '00:00:00.000'}Z`);
	const lowerBound = new Date(`${oneYearAgoDate(now)}T00:00:00.000Z`);
	const upperBound = new Date(
		`${todayDate(now)}T${boundary === 'end' ? '23:59:59.000' : '00:00:00.000'}Z`
	);
	const clamped = new Date(
		Math.min(Math.max(selected.getTime(), lowerBound.getTime()), upperBound.getTime())
	);

	return clamped.getTime() / 1000;
};

export const resetLedgerCursor = ({
	cursor_created_at: _cursorCreatedAt,
	cursor_id: _cursorId,
	...query
}: LedgerQuery): LedgerQuery => ({ ...query });

export const buildLedgerQuery = (
	filters: LedgerQuery,
	cursor?: LedgerCursor | null
): LedgerQuery => ({
	...filters,
	...(cursor
		? { cursor_created_at: cursor.created_at, cursor_id: cursor.id }
		: { cursor_created_at: undefined, cursor_id: undefined })
});

export const updateLedgerPageCursors = (
	cursors: Array<LedgerCursor | null>,
	page: number,
	nextCursor: LedgerCursor | null
) => {
	const nextCursors = cursors.slice(0, page);
	if (nextCursor) nextCursors[page] = nextCursor;
	return nextCursors;
};

export const ledgerPaginationCount = (page: number, nextCursor: LedgerCursor | null) =>
	(page - 1) * LEDGER_PAGE_SIZE + LEDGER_PAGE_SIZE + (nextCursor ? 1 : 0);

export const ledgerDateRangeError = ({ since, until }: Pick<LedgerQuery, 'since' | 'until'>) =>
	since !== undefined && until !== undefined && since > until
		? 'credits.errors.invalidDateRange'
		: null;

type LedgerResourceModel = {
	id: string;
	name?: string;
};

export const ledgerResourceName = (
	resourceId: string | null,
	models: LedgerResourceModel[]
): string => {
	if (!resourceId) return '—';

	const model = models.find((item) => item.id === resourceId);
	if (!model) return '—';

	const name = model.name?.trim();
	if (!name || name === model.id) return '—';

	const separatorIndex = name.indexOf(' / ');
	return separatorIndex === -1 ? name : name.slice(separatorIndex + 3);
};

export const failedUsageNotice = (status: string | null) => status === 'failed';

const isPricingFactor = (value: unknown): value is { key: string; value: string | number } => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return false;

	const factor = value as Record<string, unknown>;
	return (
		typeof factor.key === 'string' &&
		(typeof factor.value === 'string' || typeof factor.value === 'number')
	);
};

export const formatPricingSnapshot = (snapshot: Record<string, unknown> | null) => {
	if (!snapshot || !Array.isArray(snapshot.factors)) return null;

	const factors = snapshot.factors.filter(isPricingFactor).slice(0, 4);
	if (factors.length === 0) return null;

	return factors.map((factor) => `${factor.key}: ${factor.value}`).join(' · ');
};
