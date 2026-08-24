<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';
	import { toast } from 'svelte-sonner';

	import {
		compensateCreditReconciliationCase,
		getCreditReconciliationCases,
		type ReconciliationItem,
		type ReconciliationStatus
	} from '$lib/apis/credits';
	import Select from '$lib/components/common/Select.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext<Writable<I18n>>('i18n');
	const pageSize = 15;
	let items: ReconciliationItem[] = [];
	let total = 0;
	let page = 1;
	let loading = true;
	let error = '';
	let status: ReconciliationStatus | '' = '';
	let compensated: '' | 'true' | 'false' = '';
	let userId = '';
	let pending = new Set<string>();
	let notes: Record<string, string> = {};
	let mounted = false;
	let pendingCompensation: ReconciliationItem | null = null;
	let showCompensationConfirm = false;

	const load = async () => {
		loading = true;
		error = '';
		try {
			const result = await getCreditReconciliationCases(localStorage.token, {
				status: status || undefined,
				compensated: compensated === '' ? undefined : compensated === 'true',
				user_id: userId.trim() || undefined,
				skip: (page - 1) * pageSize,
				limit: pageSize
			});
			items = result.items;
			total = result.total;
		} catch {
			items = [];
			total = 0;
			error = $i18n.t('credits.admin.reconciliationLoadError');
		} finally {
			loading = false;
		}
	};

	const applyFilters = () => {
		if (page === 1) {
			load();
		} else {
			page = 1;
		}
	};

	const requestCompensation = (item: ReconciliationItem) => {
		if (pending.has(item.usage_id) || item.compensation_ledger_id) return;
		pendingCompensation = item;
		showCompensationConfirm = true;
	};

	const confirmCompensation = async () => {
		if (!pendingCompensation) return;
		const item = pendingCompensation;
		pendingCompensation = null;
		showCompensationConfirm = false;
		pending.add(item.usage_id);
		pending = new Set(pending);
		try {
			const result = await compensateCreditReconciliationCase(
				localStorage.token,
				item.usage_id,
				notes[item.usage_id]
			);
			items = items.map((candidate) =>
				candidate.usage_id === item.usage_id
					? { ...candidate, compensation_ledger_id: result.ledger_id }
					: candidate
			);
			toast.success($i18n.t('credits.admin.compensationSaved'));
		} catch {
			toast.error($i18n.t('credits.admin.compensationError'));
		} finally {
			pending.delete(item.usage_id);
			pending = new Set(pending);
		}
	};

	$: if (mounted && page > 0) {
		load();
	}

	onMount(() => {
		mounted = true;
	});
</script>

<div class="flex h-full flex-col gap-3">
	<div>
		<div class="flex flex-wrap items-baseline justify-between gap-2">
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.reconciliationTitle')}
			</h2>
			<span class="text-xs text-gray-500">{total}</span>
		</div>
		<p class="mt-1 text-sm text-gray-500">{$i18n.t('credits.admin.reconciliationDescription')}</p>
	</div>

	<div class="grid gap-2 sm:grid-cols-[minmax(0,1fr)_12rem_12rem_auto]">
		<input
			class="min-h-10 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			bind:value={userId}
			placeholder={$i18n.t('credits.admin.userId')}
		/>
		<Select
			value={status}
			items={[
				{ value: '', label: $i18n.t('credits.admin.allStatuses') },
				{ value: 'failed', label: $i18n.t('Failed') },
				{ value: 'unknown', label: $i18n.t('Unknown') }
			]}
			ariaLabel={$i18n.t('credits.admin.allStatuses')}
			triggerClass="flex min-h-10 items-center rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			onChange={(value) => {
				if (value === '' || value === 'failed' || value === 'unknown') status = value;
			}}
		/>
		<Select
			value={compensated}
			items={[
				{ value: '', label: $i18n.t('credits.admin.allCompensation') },
				{ value: 'false', label: $i18n.t('credits.admin.uncompensated') },
				{ value: 'true', label: $i18n.t('credits.admin.compensated') }
			]}
			ariaLabel={$i18n.t('credits.admin.allCompensation')}
			triggerClass="flex min-h-10 items-center rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
			onChange={(value) => {
				if (value === '' || value === 'false' || value === 'true') compensated = value;
			}}
		/>
		<button
			class="min-h-10 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white dark:bg-white dark:text-gray-900"
			type="button"
			on:click={applyFilters}>{$i18n.t('credits.common.applyFilters')}</button
		>
	</div>

	{#if error}
		<div class="rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
			{error}
		</div>
	{/if}
	{#if loading}
		<div class="flex min-h-40 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if items.length === 0}
		<div
			class="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-700"
		>
			{$i18n.t('credits.admin.reconciliationEmpty')}
		</div>
	{:else}
		<div class="flex flex-col gap-2">
			{#each items as item (item.usage_id)}
				<article class="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
					<div class="flex flex-wrap items-center gap-x-3 gap-y-1.5">
						<div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
							<span
								class="whitespace-nowrap rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950/40 dark:text-red-300"
								>{$i18n.t(item.status === 'failed' ? 'Failed' : 'Unknown')}</span
							>
							<strong class="truncate text-sm dark:text-gray-100">{item.resource_id}</strong>
							{#if item.execution_mode}
								<span
									class="whitespace-nowrap rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-600 dark:bg-gray-800 dark:text-gray-300"
								>
									{$i18n.t(
										item.execution_mode === 'mock'
											? 'credits.admin.mockMode'
											: 'credits.admin.realFalMode'
									)}
								</span>
							{/if}
							<span
								class="whitespace-nowrap text-sm font-medium tabular-nums text-amber-700 dark:text-amber-300"
								>-{item.charged_credits} {$i18n.t('credits.common.unit')}</span
							>
							<span class="truncate text-xs text-gray-500">
								{item.user_name_snapshot ?? item.user_email_snapshot ?? item.user_id}
							</span>
							<span class="whitespace-nowrap text-xs text-gray-400">
								{new Date(item.created_at * 1000).toLocaleString()}
							</span>
						</div>
						<div class="flex shrink-0 items-center gap-2">
							{#if item.compensation_ledger_id}
								<span
									class="whitespace-nowrap rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
									>{$i18n.t('credits.admin.compensated')}</span
								>
							{:else}
								<input
									class="min-h-8 w-40 rounded-lg border border-gray-200 bg-transparent px-2 text-xs dark:border-gray-700"
									bind:value={notes[item.usage_id]}
									placeholder={$i18n.t('credits.admin.compensationNote')}
								/>
								<button
									class="min-h-8 rounded-lg bg-gray-900 px-3 text-xs font-medium text-white disabled:opacity-50 dark:bg-white dark:text-gray-900"
									type="button"
									disabled={pending.has(item.usage_id)}
									on:click={() => requestCompensation(item)}
								>
									{pending.has(item.usage_id)
										? $i18n.t('credits.common.saving')
										: $i18n.t('credits.admin.compensate')}
								</button>
							{/if}
						</div>
					</div>
					{#if item.error_summary ?? item.error_code}
						<p class="mt-1.5 truncate text-xs text-gray-500">
							{item.error_summary ?? item.error_code}
						</p>
					{/if}
				</article>
			{/each}
		</div>
		<div class="flex justify-end">
			<Pagination bind:page count={total} perPage={pageSize} />
		</div>
	{/if}
</div>

<ConfirmDialog
	bind:show={showCompensationConfirm}
	title={$i18n.t('credits.admin.compensationConfirmTitle')}
	message={$i18n.t('credits.admin.compensationConfirmMessage', {
		user:
			pendingCompensation?.user_name_snapshot ??
			pendingCompensation?.user_email_snapshot ??
			pendingCompensation?.user_id ??
			'',
		credits: pendingCompensation?.charged_credits ?? 0
	})}
	confirmLabel={$i18n.t('credits.common.confirm')}
	onConfirm={confirmCompensation}
/>
