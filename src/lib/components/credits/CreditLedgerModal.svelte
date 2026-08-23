<script lang="ts">
	import { createEventDispatcher, getContext, onDestroy } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import { getImageGenerationModels } from '$lib/apis/images';
	import {
		getMyCreditLedger,
		getMyCredits,
		type LedgerCursor,
		type LedgerItem,
		type LedgerQuery
	} from '$lib/apis/credits';
	import Modal from '$lib/components/common/Modal.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import { registerCreditTranslations } from '$lib/components/credits/credits-i18n';
	import CreditRedemptionForm from '$lib/components/credits/CreditRedemptionForm.svelte';
	import {
		normalizeImageGenerationModels,
		type ImageGenerationModel
	} from '$lib/utils/image-generation';

	import {
		buildLedgerQuery,
		failedUsageNotice,
		formatPricingSnapshot,
		ledgerDateRangeError,
		ledgerPaginationCount,
		ledgerResourceName,
		LEDGER_PAGE_SIZE,
		oneYearAgoDate,
		resetLedgerCursor,
		toUnixTimestamp,
		todayDate,
		updateLedgerPageCursors
	} from './credit-ledger-state';

	const i18n = getContext<Writable<I18n>>('i18n');
	registerCreditTranslations($i18n);

	export let show = false;

	const dispatch = createEventDispatcher<{ refresh: void }>();

	let entries: LedgerItem[] = [];
	let pageCursors: Array<LedgerCursor | null> = [null];
	let page = 1;
	let requestedPage = 1;
	let paginationCount = LEDGER_PAGE_SIZE;
	let loading = false;
	let error = '';
	let currentBalance: number | null = null;
	let imageModels: ImageGenerationModel[] = [];
	let requestController: AbortController | null = null;
	let filters: LedgerQuery = { limit: LEDGER_PAGE_SIZE };

	const refreshBalance = async () => {
		try {
			currentBalance = (await getMyCredits(localStorage.token)).balance;
			dispatch('refresh');
		} catch {
			return;
		}
	};

	const loadImageModels = async () => {
		try {
			const result = await getImageGenerationModels(localStorage.token);
			imageModels = normalizeImageGenerationModels(result);
		} catch {
			imageModels = [];
		}
	};

	const loadLedger = async (targetPage = page) => {
		const dateRangeError = ledgerDateRangeError(filters);
		if (dateRangeError) {
			error = $i18n.t(dateRangeError);
			return;
		}

		requestController?.abort();
		requestController = new AbortController();
		loading = true;
		error = '';

		try {
			const result = await getMyCreditLedger(
				localStorage.token,
				buildLedgerQuery(filters, pageCursors[targetPage - 1]),
				requestController.signal
			);
			entries = result.items;
			pageCursors = updateLedgerPageCursors(pageCursors, targetPage, result.next_cursor);
			paginationCount = ledgerPaginationCount(targetPage, result.next_cursor);
			requestedPage = targetPage;
			dispatch('refresh');
		} catch (requestError) {
			if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
			entries = [];
			paginationCount = (targetPage - 1) * LEDGER_PAGE_SIZE;
			error = $i18n.t('credits.unavailable');
		} finally {
			loading = false;
		}
	};

	const ledgerLabel = (group: 'entryTypes' | 'reasons', value: string | null) =>
		value && $i18n.exists(`credits.${group}.${value}`)
			? $i18n.t(`credits.${group}.${value}`)
			: (value ?? '—');

	const resetPagination = () => {
		page = 1;
		requestedPage = 1;
		pageCursors = [null];
		paginationCount = LEDGER_PAGE_SIZE;
	};

	const updateFilters = (next: LedgerQuery) => {
		filters = resetLedgerCursor(next);
		resetPagination();
	};

	const applyFilters = () => loadLedger(1);

	$: if (show) {
		currentBalance = null;
		resetPagination();
		void Promise.all([refreshBalance(), loadImageModels(), loadLedger(1)]);
	}

	$: if (show && page !== requestedPage && (page === 1 || pageCursors[page - 1])) {
		void loadLedger(page);
	}

	onDestroy(() => requestController?.abort());
</script>

{#if show}
	<Modal size="lg" bind:show>
		<div class="p-5 sm:p-6">
			<div class="flex items-start justify-between gap-4">
				<div>
					<h2 class="text-lg font-medium dark:text-gray-100">{$i18n.t('credits.ledger')}</h2>
					<div class="mt-1 text-sm text-gray-500">
						{$i18n.t('credits.balance')}:
						<span class="font-medium tabular-nums">{currentBalance ?? '—'}</span>
					</div>
				</div>
				<button
					class="rounded-lg p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900 dark:hover:bg-gray-800 dark:hover:text-gray-100"
					type="button"
					aria-label={$i18n.t('credits.common.close')}
					on:click={() => (show = false)}
				>
					<XMark className="size-5" strokeWidth="1.5" />
				</button>
			</div>

			<CreditRedemptionForm
				on:redeemed={() => {
					resetPagination();
					void Promise.all([refreshBalance(), loadLedger(1)]);
				}}
			/>

			<div class="mt-5 grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto]">
				<Select
					value={filters.category ?? ''}
					items={[
						{ value: '', label: $i18n.t('credits.filters.all') },
						{ value: 'income', label: $i18n.t('credits.filters.income') },
						{ value: 'consumption', label: $i18n.t('credits.filters.consumption') },
						{ value: 'adjustment', label: $i18n.t('credits.filters.adjustment') }
					]}
					placeholder={$i18n.t('credits.filters.all')}
					triggerClass="flex min-w-32 items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					onChange={(category) =>
						updateFilters({
							...filters,
							category: category ? (category as LedgerQuery['category']) : undefined
						})}
				/>
				<div class="flex flex-wrap items-center gap-2">
					<input
						class="w-36 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
						type="date"
						aria-label={$i18n.t('credits.common.from')}
						min={oneYearAgoDate()}
						max={todayDate()}
						value={filters.since ? new Date(filters.since * 1000).toISOString().slice(0, 10) : ''}
						on:change={(event) =>
							updateFilters({
								...filters,
								since: toUnixTimestamp(event.currentTarget.value)
							})}
					/>
					<span class="text-sm text-gray-400" aria-hidden="true">—</span>
					<input
						class="w-36 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
						type="date"
						aria-label={$i18n.t('credits.common.to')}
						min={oneYearAgoDate()}
						max={todayDate()}
						value={filters.until ? new Date(filters.until * 1000).toISOString().slice(0, 10) : ''}
						on:change={(event) =>
							updateFilters({
								...filters,
								until: toUnixTimestamp(event.currentTarget.value, new Date(), 'end')
							})}
					/>
				</div>
				<button
					class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
					type="button"
					disabled={loading}
					on:click={applyFilters}
				>
					{$i18n.t('credits.common.applyFilters')}
				</button>
			</div>

			{#if error}
				<div
					class="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
				>
					{error}
					<button class="ml-2 underline" type="button" on:click={() => loadLedger()}>
						{$i18n.t('credits.common.retry')}
					</button>
				</div>
			{/if}

			<div class="mt-5 max-h-[55vh] overflow-y-auto">
				{#if loading && entries.length === 0}
					<div class="flex min-h-40 items-center justify-center">
						<Spinner className="size-5" />
					</div>
				{:else if entries.length === 0}
					<div
						class="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-700"
					>
						{$i18n.t('credits.common.noLedgerEntries')}
					</div>
				{:else}
					<div class="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
						<table class="w-full text-left text-sm">
							<thead class="border-b border-gray-100 text-xs text-gray-500 dark:border-gray-800">
								<tr>
									<th class="whitespace-nowrap px-4 py-3 font-medium"
										>{$i18n.t('credits.common.createdAt')}</th
									>
									<th class="whitespace-nowrap px-4 py-3 font-medium"
										>{$i18n.t('credits.common.amount')}</th
									>
									<th class="whitespace-nowrap px-4 py-3 font-medium"
										>{$i18n.t('credits.common.type')}</th
									>
									<th class="whitespace-nowrap px-4 py-3 font-medium"
										>{$i18n.t('credits.common.resource')}</th
									>
								</tr>
							</thead>
							<tbody>
								{#each entries as entry (entry.id)}
									<tr class="border-b border-gray-50 last:border-0 dark:border-gray-850">
										<td class="whitespace-nowrap px-4 py-3 text-gray-500">
											{new Date(entry.created_at * 1000).toLocaleString()}
										</td>
										<td class="whitespace-nowrap px-4 py-3 font-medium tabular-nums">
											{entry.amount > 0 ? '+' : ''}{entry.amount}
										</td>
										<td class="whitespace-nowrap px-4 py-3">
											<div>
												{ledgerLabel(
													entry.reason_code ? 'reasons' : 'entryTypes',
													entry.reason_code ?? entry.entry_type
												)}
											</div>
											{#if failedUsageNotice(entry.usage_status)}
												<div class="mt-1 text-xs text-amber-700 dark:text-amber-300">
													{$i18n.t('credits.status.failedCharged')}
												</div>
											{/if}
										</td>
										<td class="px-4 py-3">
											<div>{ledgerResourceName(entry.resource_id, imageModels)}</div>
											{#if formatPricingSnapshot(entry.pricing_snapshot)}
												<div class="mt-1 max-w-64 truncate text-xs text-gray-500">
													{formatPricingSnapshot(entry.pricing_snapshot)}
												</div>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>

			{#if paginationCount > LEDGER_PAGE_SIZE}
				<div class="mt-4">
					<Pagination bind:page count={paginationCount} perPage={LEDGER_PAGE_SIZE} />
				</div>
			{/if}
		</div>
	</Modal>
{/if}
