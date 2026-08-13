<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import { toast } from 'svelte-sonner';
	import type { i18n as I18n } from 'i18next';

	import {
		getProviderOverview,
		listProviderAnalytics,
		listProviderBillingEvents,
		listProviderModelSummary,
		syncFalProvider,
		type ProviderAnalytics,
		type ProviderBillingEvent,
		type ProviderModelSummary,
		type ProviderOverview
	} from '$lib/apis/provider-ops';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext<Writable<I18n>>('i18n');
	let provider = 'fal';
	let windowHours = 24;
	let overview: ProviderOverview | null = null;
	let models: ProviderModelSummary[] = [];
	let billingEvents: ProviderBillingEvent[] = [];
	let analytics: ProviderAnalytics[] = [];
	let loading = true;
	let syncing = false;
	let loadSequence = 0;

	$: latestAnalytics = analytics.reduce<Record<string, ProviderAnalytics>>((latest, item) => {
		if (!latest[item.provider_model_id]) latest[item.provider_model_id] = item;
		return latest;
	}, {});

	const percentage = (value: number, total: number) =>
		total > 0 ? `${((value / total) * 100).toFixed(1)}%` : '—';

	const duration = (milliseconds: number | null | undefined) => {
		if (milliseconds === null || milliseconds === undefined) return '—';
		return milliseconds >= 1000
			? `${(milliseconds / 1000).toFixed(milliseconds >= 10000 ? 1 : 2)} s`
			: `${Math.round(milliseconds)} ms`;
	};

	const money = (costs: Record<string, string>) => {
		const entries = Object.entries(costs);
		if (entries.length === 0) return '—';
		return entries
			.map(([currency, value]) =>
				new Intl.NumberFormat(undefined, {
					style: 'currency',
					currency,
					minimumFractionDigits: 2,
					maximumFractionDigits: 6
				}).format(Number(value))
			)
			.join(' · ');
	};

	const dateTime = (timestamp: number | null) =>
		timestamp
			? new Intl.DateTimeFormat(undefined, { dateStyle: 'short', timeStyle: 'short' }).format(
					timestamp
				)
			: '—';

	const load = async () => {
		const sequence = ++loadSequence;
		loading = true;
		try {
			const [nextOverview, nextModels, nextBillingEvents, nextAnalytics] = await Promise.all([
				getProviderOverview(localStorage.token, provider, windowHours),
				listProviderModelSummary(localStorage.token, provider, windowHours),
				listProviderBillingEvents(localStorage.token, provider, windowHours, 100),
				listProviderAnalytics(localStorage.token, provider, windowHours, 500)
			]);
			if (sequence !== loadSequence) return;
			overview = nextOverview;
			models = nextModels;
			billingEvents = nextBillingEvents;
			analytics = nextAnalytics;
		} catch {
			if (sequence === loadSequence) toast.error($i18n.t('Failed to load provider operations'));
		} finally {
			if (sequence === loadSequence) loading = false;
		}
	};

	const sync = async () => {
		if (syncing) return;
		syncing = true;
		try {
			const result = await syncFalProvider(
				localStorage.token,
				windowHours,
				windowHours <= 48 ? 'hour' : 'day'
			);
			if (result.status === 'failed') {
				toast.error(
					$i18n.t('Provider synchronization failed: {{code}}', {
						code: result.error_code ?? 'unknown'
					})
				);
			} else {
				toast.success($i18n.t('Provider data synchronized'));
			}
			await load();
		} catch {
			toast.error($i18n.t('Provider synchronization failed'));
		} finally {
			syncing = false;
		}
	};

	onMount(load);
</script>

<div class="flex min-h-0 flex-col gap-5" data-testid="provider-operations">
	<header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
		<div class="min-w-0">
			<h2 class="text-base font-medium dark:text-gray-100">{$i18n.t('Provider operations')}</h2>
			<p class="mt-1 max-w-3xl text-sm text-gray-500">
				{$i18n.t(
					'Reconcile local generation records with provider requests, billing events and service analytics.'
				)}
			</p>
		</div>
		<div class="grid grid-cols-2 gap-2 sm:flex sm:shrink-0">
			<label class="sr-only" for="provider-operations-provider">{$i18n.t('Provider')}</label>
			<select
				id="provider-operations-provider"
				class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
				bind:value={provider}
				on:change={load}
			>
				<option value="fal">fal.ai</option>
			</select>
			<label class="sr-only" for="provider-operations-window">{$i18n.t('Time window')}</label>
			<select
				id="provider-operations-window"
				class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 text-sm dark:border-gray-700"
				bind:value={windowHours}
				on:change={load}
			>
				<option value={24}>{$i18n.t('Last 24 hours')}</option>
				<option value={168}>{$i18n.t('Last 7 days')}</option>
				<option value={720}>{$i18n.t('Last 30 days')}</option>
			</select>
			<button
				class="col-span-2 flex min-h-11 items-center justify-center gap-2 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-gray-900 sm:col-span-1"
				type="button"
				disabled={syncing}
				on:click={sync}
			>
				{#if syncing}<Spinner className="size-4" />{/if}
				{syncing ? $i18n.t('Synchronizing') : $i18n.t('Synchronize now')}
			</button>
		</div>
	</header>

	{#if loading && !overview}
		<div class="flex min-h-64 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if overview}
		<section
			class="grid grid-cols-2 gap-2 lg:grid-cols-5"
			aria-label={$i18n.t('Provider overview')}
		>
			<div class="min-w-0 rounded-2xl border border-gray-200 p-3 dark:border-gray-800 sm:p-4">
				<div class="text-xs text-gray-500">{$i18n.t('Actual cost')}</div>
				<div
					class="mt-2 truncate text-lg font-semibold tabular-nums dark:text-gray-100"
					title={money(overview.exact_costs)}
				>
					{money(overview.exact_costs)}
				</div>
				<div class="mt-1 text-[11px] text-gray-500">{$i18n.t('From billing events')}</div>
			</div>
			<div class="min-w-0 rounded-2xl border border-gray-200 p-3 dark:border-gray-800 sm:p-4">
				<div class="text-xs text-gray-500">{$i18n.t('Attributed cost')}</div>
				<div
					class="mt-2 truncate text-lg font-semibold tabular-nums dark:text-gray-100"
					title={money(overview.matched_exact_costs)}
				>
					{money(overview.matched_exact_costs)}
				</div>
				<div class="mt-1 text-[11px] text-gray-500">{$i18n.t('Matched to local requests')}</div>
			</div>
			<div class="rounded-2xl border border-gray-200 p-3 dark:border-gray-800 sm:p-4">
				<div class="text-xs text-gray-500">{$i18n.t('Success rate')}</div>
				<div class="mt-2 text-lg font-semibold tabular-nums dark:text-gray-100">
					{percentage(overview.success_count, overview.invocation_count)}
				</div>
				<div class="mt-1 text-[11px] text-gray-500">
					{overview.success_count} / {overview.invocation_count}
				</div>
			</div>
			<div class="rounded-2xl border border-gray-200 p-3 dark:border-gray-800 sm:p-4">
				<div class="text-xs text-gray-500">{$i18n.t('Average duration')}</div>
				<div class="mt-2 text-lg font-semibold tabular-nums dark:text-gray-100">
					{duration(overview.average_duration_ms)}
				</div>
				<div class="mt-1 text-[11px] text-gray-500">{$i18n.t('Provider execution time')}</div>
			</div>
			<div
				class="col-span-2 rounded-2xl border border-gray-200 p-3 dark:border-gray-800 sm:p-4 lg:col-span-1"
			>
				<div class="text-xs text-gray-500">{$i18n.t('Billing match rate')}</div>
				<div class="mt-2 text-lg font-semibold tabular-nums dark:text-gray-100">
					{percentage(overview.matched_billing_event_count, overview.billing_event_count)}
				</div>
				<div class="mt-1 text-[11px] text-gray-500">
					{overview.matched_billing_event_count} / {overview.billing_event_count}
				</div>
			</div>
		</section>

		<div
			class="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500"
			aria-live="polite"
		>
			<span>{$i18n.t('Last synchronized')}: {dateTime(overview.last_synced_at)}</span>
			<span>
				{$i18n.t('Provider requests matched')}: {overview.matched_provider_request_count} / {overview.provider_request_count}
			</span>
		</div>

		<section class="grid min-w-0 gap-4 xl:grid-cols-2">
			<div class="min-w-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
				<div class="border-b border-gray-100 px-4 py-3 dark:border-gray-800">
					<h3 class="text-sm font-medium dark:text-gray-100">{$i18n.t('Model reliability')}</h3>
				</div>
				{#if models.length === 0}
					<div class="flex min-h-40 items-center justify-center p-4 text-sm text-gray-500">
						{$i18n.t('No provider request data')}
					</div>
				{:else}
					<div class="max-h-[30rem] overflow-y-auto overscroll-contain">
						{#each models as model (`${model.provider}:${model.media_kind}:${model.provider_model_id}`)}
							<article
								class="grid gap-2 border-b border-gray-100 px-4 py-3 last:border-0 dark:border-gray-800/70 sm:grid-cols-[minmax(0,1fr)_5rem_6rem_6rem] sm:items-center"
							>
								<div class="min-w-0">
									<div class="truncate text-sm font-medium dark:text-gray-100">
										{model.provider_model_id}
									</div>
									<div class="mt-0.5 text-[11px] text-gray-500">
										{$i18n.t(model.media_kind === 'video' ? 'Video' : 'Image')}
									</div>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden"
										>{$i18n.t('Requests')} ·
									</span><span class="text-sm tabular-nums">{model.request_count}</span>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden"
										>{$i18n.t('Success rate')} ·
									</span><span class="text-sm tabular-nums"
										>{percentage(model.success_count, model.request_count)}</span
									>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden"
										>{$i18n.t('Average duration')} ·
									</span><span class="text-sm tabular-nums"
										>{duration(model.average_execution_duration_ms)}</span
									>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</div>

			<div class="min-w-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800">
				<div class="border-b border-gray-100 px-4 py-3 dark:border-gray-800">
					<h3 class="text-sm font-medium dark:text-gray-100">{$i18n.t('Provider performance')}</h3>
				</div>
				{#if Object.keys(latestAnalytics).length === 0}
					<div class="flex min-h-40 items-center justify-center p-4 text-sm text-gray-500">
						{$i18n.t('No provider analytics')}
					</div>
				{:else}
					<div class="max-h-[30rem] overflow-y-auto overscroll-contain">
						{#each Object.values(latestAnalytics) as item (item.provider_model_id)}
							<article
								class="grid gap-2 border-b border-gray-100 px-4 py-3 last:border-0 dark:border-gray-800/70 sm:grid-cols-[minmax(0,1fr)_5rem_6rem_6rem] sm:items-center"
							>
								<div class="min-w-0">
									<div class="truncate text-sm font-medium dark:text-gray-100">
										{item.provider_model_id}
									</div>
									<div class="mt-0.5 text-[11px] text-gray-500">{item.bucket_start}</div>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden"
										>{$i18n.t('Requests')} ·
									</span><span class="text-sm tabular-nums"
										>{item.metrics.request_count ?? '—'}</span
									>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden">P95 · </span><span
										class="text-sm tabular-nums"
										>{duration(
											item.metrics.p95_duration === undefined
												? null
												: item.metrics.p95_duration * 1000
										)}</span
									>
								</div>
								<div>
									<span class="text-[10px] text-gray-500 sm:hidden"
										>{$i18n.t('Errors')} ·
									</span><span class="text-sm tabular-nums"
										>{(item.metrics.user_error_count ?? 0) + (item.metrics.error_count ?? 0)}</span
									>
								</div>
							</article>
						{/each}
					</div>
				{/if}
			</div>
		</section>

		<section
			class="min-w-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800"
		>
			<div
				class="flex items-center justify-between gap-3 border-b border-gray-100 px-4 py-3 dark:border-gray-800"
			>
				<h3 class="text-sm font-medium dark:text-gray-100">{$i18n.t('Recent billing events')}</h3>
				<span class="text-xs tabular-nums text-gray-500">{billingEvents.length}</span>
			</div>
			{#if billingEvents.length === 0}
				<div class="flex min-h-32 items-center justify-center p-4 text-sm text-gray-500">
					{$i18n.t('No billing events')}
				</div>
			{:else}
				<div class="max-h-[30rem] overflow-y-auto overscroll-contain">
					{#each billingEvents as event (`${event.provider}:${event.provider_request_id}`)}
						<article
							class="grid gap-2 border-b border-gray-100 px-4 py-3 last:border-0 dark:border-gray-800/70 sm:grid-cols-[minmax(0,1fr)_10rem_8rem_7rem] sm:items-center"
						>
							<div class="min-w-0">
								<div class="truncate text-sm font-medium dark:text-gray-100">
									{event.provider_model_id}
								</div>
								<div class="truncate text-[11px] text-gray-500" title={event.provider_request_id}>
									{event.provider_request_id}
								</div>
							</div>
							<div class="text-xs text-gray-500">{event.event_timestamp}</div>
							<div class="text-sm font-medium tabular-nums dark:text-gray-100">
								{money({ [event.currency]: event.cost_total })}
							</div>
							<div>
								<span
									class="inline-flex rounded-md px-2 py-1 text-[11px] {event.matched_invocation
										? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
										: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'}"
								>
									{$i18n.t(event.matched_invocation ? 'Matched' : 'Unmatched')}
								</span>
							</div>
						</article>
					{/each}
				</div>
			{/if}
		</section>
	{/if}
</div>
