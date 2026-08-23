<script lang="ts">
	import { getContext, onMount } from 'svelte';

	import { getAdminCreditLedger, type AdminLedgerQuery, type LedgerItem } from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');
	const pageSize = 25;

	let entries: LedgerItem[] = [];
	let total = 0;
	let page = 1;
	let loading = true;
	let error = '';
	let filters: AdminLedgerQuery = { skip: 0, limit: pageSize };
	let mounted = false;

	const asTimestamp = (value: string) =>
		value ? Math.floor(new Date(value).getTime() / 1000) : undefined;

	const ledgerLabel = (group: 'entryTypes' | 'reasons', value: string | null) =>
		value && $i18n.exists(`credits.${group}.${value}`)
			? $i18n.t(`credits.${group}.${value}`)
			: (value ?? '—');

	const loadLedger = async () => {
		loading = true;
		error = '';
		try {
			const result = await getAdminCreditLedger(localStorage.token, {
				...filters,
				skip: (page - 1) * pageSize,
				limit: pageSize
			});
			entries = result.items;
			total = result.total;
		} catch (requestError) {
			entries = [];
			total = 0;
			error = translateCreditApiError($i18n, requestError, 'credits.admin.ledgerLoadError');
		} finally {
			loading = false;
		}
	};

	const applyFilters = () => {
		if (page === 1) {
			loadLedger();
		} else {
			page = 1;
		}
	};

	$: if (mounted && page > 0) {
		loadLedger();
	}

	onMount(() => {
		mounted = true;
	});
</script>

<div class="flex h-full flex-col gap-4">
	<div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
		<div>
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.ledgerTitle')}
			</h2>
			<p class="mt-1 text-sm text-gray-500">
				{$i18n.t('credits.admin.ledgerDescription')}
			</p>
		</div>
		<span class="text-xs text-gray-500">{total}</span>
	</div>

	<div class="grid gap-2 md:grid-cols-3 lg:grid-cols-6">
		<input
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.user_id}
			placeholder={$i18n.t('credits.admin.userId')}
		/>
		<select
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.entry_type}
		>
			<option value={undefined}>{$i18n.t('credits.admin.allTypes')}</option>
			<option value="consumption">{$i18n.t('credits.entryTypes.consumption')}</option>
			<option value="admin_adjustment">{$i18n.t('credits.entryTypes.admin_adjustment')}</option>
			<option value="system_adjustment">{$i18n.t('credits.entryTypes.system_adjustment')}</option>
		</select>
		<select
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.reason_code}
		>
			<option value={undefined}>{$i18n.t('credits.admin.allReasons')}</option>
			<option value="promotion_gift">{$i18n.t('credits.reasons.promotion_gift')}</option>
			<option value="manual_refund">{$i18n.t('credits.reasons.manual_refund')}</option>
			<option value="violation_deduction">{$i18n.t('credits.reasons.violation_deduction')}</option>
			<option value="redeem">{$i18n.t('credits.reasons.redeem')}</option>
			<option value="other">{$i18n.t('credits.reasons.other')}</option>
		</select>
		<input
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.resource_id}
			placeholder={$i18n.t('credits.admin.modelOrResource')}
		/>
		<input
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.action}
			placeholder={$i18n.t('credits.common.action')}
		/>
		<button
			class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
			on:click={applyFilters}
			type="button"
		>
			{$i18n.t('credits.common.applyFilters')}
		</button>
	</div>

	<div class="grid gap-2 sm:grid-cols-2">
		<label class="text-xs text-gray-500">
			{$i18n.t('credits.common.from')}
			<input
				class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
				type="date"
				value={filters.since ? new Date(filters.since * 1000).toISOString().slice(0, 10) : ''}
				on:change={(event) => {
					filters = { ...filters, since: asTimestamp(event.currentTarget.value) };
				}}
			/>
		</label>
		<label class="text-xs text-gray-500">
			{$i18n.t('credits.common.to')}
			<input
				class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
				type="date"
				value={filters.until ? new Date(filters.until * 1000).toISOString().slice(0, 10) : ''}
				on:change={(event) => {
					filters = { ...filters, until: asTimestamp(event.currentTarget.value) };
				}}
			/>
		</label>
	</div>

	{#if error}
		<div
			class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
		>
			{error}
			<button class="ml-2 underline" on:click={() => loadLedger()} type="button"
				>{$i18n.t('credits.common.retry')}</button
			>
		</div>
	{/if}

	{#if loading && entries.length === 0}
		<div class="flex flex-1 items-center justify-center"><Spinner className="size-5" /></div>
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
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.user')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.amount')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.type')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.resource')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.createdAt')}</th>
					</tr>
				</thead>
				<tbody>
					{#each entries as entry (entry.id)}
						<tr class="border-b border-gray-50 last:border-0 dark:border-gray-850">
							<td class="px-4 py-3">
								<div class="font-medium dark:text-gray-100">
									{entry.user_name_snapshot ?? $i18n.t('credits.common.deletedUser')}
								</div>
								<div class="mt-0.5 text-xs text-gray-500">
									{entry.user_email_snapshot ?? entry.user_id}
								</div>
							</td>
							<td class="px-4 py-3 font-medium tabular-nums"
								>{entry.amount > 0 ? '+' : ''}{entry.amount}</td
							>
							<td class="px-4 py-3">
								{ledgerLabel(
									entry.reason_code ? 'reasons' : 'entryTypes',
									entry.reason_code ?? entry.entry_type
								)}
							</td>
							<td class="px-4 py-3">{entry.resource_id ?? entry.action ?? '—'}</td>
							<td class="px-4 py-3 text-gray-500"
								>{new Date(entry.created_at * 1000).toLocaleString()}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		{#if total > pageSize}
			<div class="flex justify-end">
				<Pagination bind:page count={total} perPage={pageSize} />
			</div>
		{/if}
	{/if}
</div>
