<script lang="ts">
	import { getContext, onDestroy } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';

	import {
		createCreditRedeemBatch,
		getCreditRedeemAudit,
		getCreditRedeemBatches,
		getCreditRedeemCodes,
		voidCreditRedeemBatch,
		voidCreditRedeemCode,
		type CreditRedeemAudit,
		type CreditRedeemBatch,
		type CreditRedeemBatchCreated,
		type CreditRedeemCode
	} from '$lib/apis/credits';
	import Modal from '$lib/components/common/Modal.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import { copyToClipboard } from '$lib/utils';
	import { registerCreditTranslations, translateCreditApiError } from '../credits-i18n';

	const BATCH_PAGE_SIZE = 20;
	const DETAIL_PAGE_SIZE = 50;

	const i18n = getContext<Writable<I18n>>('i18n');
	registerCreditTranslations($i18n);

	let batches: CreditRedeemBatch[] = [];
	let total = 0;
	let page = 1;
	let loadedPage = 0;
	let loading = false;
	let error = '';
	let listController: AbortController | null = null;

	let createOpen = false;
	let creating = false;
	let createError = '';
	let createdBatch: CreditRedeemBatchCreated | null = null;
	let copied = false;
	let name = '';
	let faceValue = 100;
	let quantity = 10;
	let expiresDate = '';
	let perUserLimit: number | null = null;

	let detailsOpen = false;
	let selectedBatch: CreditRedeemBatch | null = null;
	let detailMode: 'codes' | 'audit' = 'codes';
	let codes: CreditRedeemCode[] = [];
	let audits: CreditRedeemAudit[] = [];
	let detailTotal = 0;
	let detailPage = 1;
	let loadedDetailPage = 0;
	let detailLoading = false;
	let detailError = '';
	let detailController: AbortController | null = null;

	const loadBatches = async (targetPage = page) => {
		listController?.abort();
		const controller = new AbortController();
		listController = controller;
		loading = true;
		error = '';
		try {
			const result = await getCreditRedeemBatches(
				localStorage.token,
				{ skip: (targetPage - 1) * BATCH_PAGE_SIZE, limit: BATCH_PAGE_SIZE },
				controller.signal
			);
			if (controller !== listController) return;
			batches = result.items;
			total = result.total;
			loadedPage = targetPage;
		} catch (requestError) {
			if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
			if (controller !== listController) return;
			batches = [];
			error = $i18n.t('credits.admin.redeem.loadError');
		} finally {
			if (controller === listController) loading = false;
		}
	};

	const resetCreateForm = () => {
		name = '';
		faceValue = 100;
		quantity = 10;
		expiresDate = '';
		perUserLimit = null;
		createError = '';
		createdBatch = null;
		copied = false;
	};

	const closeCreate = () => {
		createOpen = false;
		resetCreateForm();
	};

	const expiryTimestamp = () => {
		if (!expiresDate) return null;
		// 过期时间统一按 UTC 日界构造：与服务器口径一致，避免管理员本地时区
		// 领先服务器时「今天过期」被判为 expires_at <= created_at（审查发现 #13）。
		const value = new Date(`${expiresDate}T23:59:59Z`);
		return Number.isNaN(value.getTime()) ? null : Math.floor(value.getTime() / 1000);
	};

	const createBatch = async () => {
		if (creating || !name.trim() || faceValue < 1 || quantity < 1) return;
		creating = true;
		createError = '';
		try {
			createdBatch = await createCreditRedeemBatch(localStorage.token, {
				name: name.trim(),
				face_value: faceValue,
				quantity,
				expires_at: expiryTimestamp(),
				per_user_limit: perUserLimit && perUserLimit > 0 ? perUserLimit : null
			});
			page = 1;
			await loadBatches(1);
		} catch (requestError) {
			if (
				typeof requestError === 'object' &&
				requestError !== null &&
				(requestError as { context?: { reason?: string } }).context?.reason ===
					'redeem_expiry_not_future'
			) {
				createError = $i18n.t('credits.admin.redeem.expiryNotFuture');
			} else {
				createError = translateCreditApiError(
					$i18n,
					requestError,
					'credits.admin.redeem.createError'
				);
			}
		} finally {
			creating = false;
		}
	};

	const copyCodes = async () => {
		if (!createdBatch) return;
		// 走带 execCommand 降级的工具函数：非安全上下文（http 内网部署）下
		// navigator.clipboard 不存在时仍可复制（审查发现 #13）。
		if (await copyToClipboard(createdBatch.codes.join('\n'))) {
			copied = true;
		} else {
			createError = $i18n.t('credits.admin.redeem.copyError');
		}
	};

	const csvCell = (value: string | number) => `"${String(value).replaceAll('"', '""')}"`;

	const downloadCodes = () => {
		if (!createdBatch) return;
		const rows = [
			['batch_id', 'index', 'code'],
			...createdBatch.codes.map((code, index) => [createdBatch?.id ?? '', index + 1, code])
		];
		const blob = new Blob(['\ufeff', rows.map((row) => row.map(csvCell).join(',')).join('\r\n')], {
			type: 'text/csv;charset=utf-8'
		});
		const url = URL.createObjectURL(blob);
		const anchor = document.createElement('a');
		anchor.href = url;
		anchor.download = `credit-redeem-${createdBatch.id}.csv`;
		anchor.click();
		URL.revokeObjectURL(url);
	};

	const voidBatch = async (batch: CreditRedeemBatch) => {
		if (!window.confirm($i18n.t('credits.admin.redeem.voidBatchConfirm'))) return;
		error = '';
		try {
			await voidCreditRedeemBatch(localStorage.token, batch.id);
			await loadBatches(page);
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.admin.redeem.voidError');
		}
	};

	const loadDetails = async (targetPage = detailPage) => {
		if (!selectedBatch) return;
		detailController?.abort();
		const controller = new AbortController();
		detailController = controller;
		detailLoading = true;
		detailError = '';
		try {
			const query = { skip: (targetPage - 1) * DETAIL_PAGE_SIZE, limit: DETAIL_PAGE_SIZE };
			if (detailMode === 'codes') {
				const result = await getCreditRedeemCodes(
					localStorage.token,
					selectedBatch.id,
					query,
					controller.signal
				);
				if (controller !== detailController) return;
				codes = result.items;
				audits = [];
				detailTotal = result.total;
			} else {
				const result = await getCreditRedeemAudit(
					localStorage.token,
					selectedBatch.id,
					query,
					controller.signal
				);
				if (controller !== detailController) return;
				audits = result.items;
				codes = [];
				detailTotal = result.total;
			}
			loadedDetailPage = targetPage;
		} catch (requestError) {
			if (requestError instanceof DOMException && requestError.name === 'AbortError') return;
			if (controller !== detailController) return;
			detailError = $i18n.t('credits.admin.redeem.loadError');
		} finally {
			if (controller === detailController) detailLoading = false;
		}
	};

	const openDetails = (batch: CreditRedeemBatch) => {
		selectedBatch = batch;
		detailsOpen = true;
		detailMode = 'codes';
		detailPage = 1;
		loadedDetailPage = 0;
	};

	const changeDetailMode = (mode: 'codes' | 'audit') => {
		if (detailMode === mode) return;
		detailMode = mode;
		detailPage = 1;
		loadedDetailPage = 0;
	};

	const handleDetailTabKeydown = (event: KeyboardEvent) => {
		if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
		event.preventDefault();
		if (event.key === 'Home') {
			changeDetailMode('codes');
		} else if (event.key === 'End') {
			changeDetailMode('audit');
		} else {
			changeDetailMode(detailMode === 'codes' ? 'audit' : 'codes');
		}
		requestAnimationFrame(() =>
			document.getElementById(`credit-redeem-detail-${detailMode}`)?.focus()
		);
	};

	const voidCode = async (code: CreditRedeemCode) => {
		if (!selectedBatch || code.status !== 'available') return;
		detailError = '';
		try {
			await voidCreditRedeemCode(localStorage.token, selectedBatch.id, code.id);
			await Promise.all([loadDetails(detailPage), loadBatches(page)]);
		} catch (requestError) {
			detailError = translateCreditApiError($i18n, requestError, 'credits.admin.redeem.voidError');
		}
	};

	const percentage = (batch: CreditRedeemBatch) =>
		Math.round((batch.redeemed_count / Math.max(1, batch.code_count)) * 100);

	const statusLabel = (status: CreditRedeemCode['status']) =>
		$i18n.t(`credits.admin.redeem.${status === 'available' ? 'available' : status}`);

	$: if (page !== loadedPage) void loadBatches(page);
	$: if (detailsOpen && detailMode && detailPage !== loadedDetailPage) void loadDetails(detailPage);

	onDestroy(() => {
		listController?.abort();
		detailController?.abort();
		createdBatch = null;
	});
</script>

<section aria-labelledby="credit-redemption-heading">
	<div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
		<div>
			<h2 id="credit-redemption-heading" class="text-lg font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.redeem.title')}
			</h2>
			<p class="mt-1 max-w-3xl text-sm text-gray-500">
				{$i18n.t('credits.admin.redeem.description')}
			</p>
		</div>
		<button
			class="min-h-11 shrink-0 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white outline-hidden hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 dark:bg-gray-100 dark:text-gray-900"
			type="button"
			on:click={() => {
				resetCreateForm();
				createOpen = true;
			}}
		>
			{$i18n.t('credits.admin.redeem.create')}
		</button>
	</div>

	{#if error}
		<div
			class="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
			role="alert"
		>
			{error}
			<button class="ml-2 min-h-11 underline" type="button" on:click={() => loadBatches(page)}>
				{$i18n.t('credits.common.retry')}
			</button>
		</div>
	{/if}

	{#if loading && batches.length === 0}
		<div class="flex min-h-48 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if batches.length === 0}
		<div
			class="mt-5 rounded-2xl border border-dashed border-gray-200 p-10 text-center text-sm text-gray-500 dark:border-gray-700"
		>
			{$i18n.t('credits.admin.redeem.empty')}
		</div>
	{:else}
		<div class="mt-5 grid gap-4 xl:grid-cols-2">
			{#each batches as batch (batch.id)}
				<article class="min-w-0 rounded-2xl border border-gray-100 p-4 dark:border-gray-800">
					<div class="flex min-w-0 items-start justify-between gap-3">
						<div class="min-w-0">
							<h3 class="truncate font-medium dark:text-gray-100">{batch.name}</h3>
							<p class="mt-1 text-sm text-gray-500">
								{batch.face_value}
								{$i18n.t('credits.common.unit')} × {batch.code_count}
							</p>
						</div>
						<span
							class="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300"
						>
							{percentage(batch)}%
						</span>
					</div>

					<div
						class="mt-4 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800"
						role="progressbar"
						aria-label={$i18n.t('credits.admin.redeem.redeemed')}
						aria-valuenow={batch.redeemed_count}
						aria-valuemin="0"
						aria-valuemax={batch.code_count}
					>
						<div
							class="h-full rounded-full bg-green-500"
							style={`width: ${percentage(batch)}%`}
						></div>
					</div>

					<dl class="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
						<div>
							<dt class="text-gray-500">{$i18n.t('credits.admin.redeem.redeemed')}</dt>
							<dd class="mt-1 font-medium tabular-nums">{batch.redeemed_count}</dd>
						</div>
						<div>
							<dt class="text-gray-500">{$i18n.t('credits.admin.redeem.available')}</dt>
							<dd class="mt-1 font-medium tabular-nums">{batch.available_count}</dd>
						</div>
						<div>
							<dt class="text-gray-500">{$i18n.t('credits.admin.redeem.unused')}</dt>
							<dd class="mt-1 font-medium tabular-nums">{batch.unused_count}</dd>
						</div>
						<div>
							<dt class="text-gray-500">{$i18n.t('credits.admin.redeem.voided')}</dt>
							<dd class="mt-1 font-medium tabular-nums">{batch.voided_count}</dd>
						</div>
					</dl>

					<div class="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
						<span
							>{batch.expires_at
								? $i18n.t('credits.admin.redeem.expires', {
										date: new Date(batch.expires_at * 1000).toLocaleDateString()
									})
								: $i18n.t('credits.admin.redeem.neverExpires')}</span
						>
						{#if batch.per_user_limit}<span
								>{$i18n.t('credits.admin.redeem.perUser', { count: batch.per_user_limit })}</span
							>{/if}
						<span>{new Date(batch.created_at * 1000).toLocaleString()}</span>
					</div>

					<div class="mt-4 flex flex-col gap-2 sm:flex-row">
						<button
							class="min-h-11 flex-1 rounded-xl border border-gray-200 px-3 text-sm font-medium outline-hidden hover:bg-gray-50 focus-visible:ring-2 focus-visible:ring-gray-400 dark:border-gray-700 dark:hover:bg-gray-900"
							type="button"
							on:click={() => openDetails(batch)}
						>
							{$i18n.t('credits.admin.redeem.viewDetails')}
						</button>
						{#if batch.available_count > 0}
							<button
								class="min-h-11 rounded-xl border border-red-200 px-3 text-sm text-red-700 outline-hidden hover:bg-red-50 focus-visible:ring-2 focus-visible:ring-red-300 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950/30"
								type="button"
								on:click={() => voidBatch(batch)}
							>
								{$i18n.t('credits.admin.redeem.voidBatch')}
							</button>
						{/if}
					</div>
				</article>
			{/each}
		</div>
	{/if}

	{#if total > BATCH_PAGE_SIZE}
		<div class="mt-5"><Pagination bind:page count={total} perPage={BATCH_PAGE_SIZE} /></div>
	{/if}
</section>

{#if createOpen}
	<Modal size="md" bind:show={createOpen}>
		<div class="max-h-[min(90dvh,780px)] overflow-y-auto p-5 sm:p-6">
			<div class="flex items-start justify-between gap-3">
				<h2 class="text-lg font-medium dark:text-gray-100">
					{$i18n.t(
						createdBatch ? 'credits.admin.redeem.createdTitle' : 'credits.admin.redeem.createTitle'
					)}
				</h2>
				<button
					class="min-h-11 min-w-11 rounded-xl p-2 text-gray-500 outline-hidden hover:bg-gray-100 focus-visible:ring-2 focus-visible:ring-gray-400 dark:hover:bg-gray-800"
					type="button"
					aria-label={$i18n.t('credits.common.close')}
					on:click={closeCreate}
				>
					<XMark className="size-5" strokeWidth="1.5" />
				</button>
			</div>

			{#if createdBatch}
				<textarea
					class="mt-4 h-64 w-full resize-y rounded-xl border border-gray-200 bg-gray-50 p-3 font-mono text-xs outline-hidden dark:border-gray-700 dark:bg-gray-950"
					readonly
					spellcheck="false"
					value={createdBatch.codes.join('\n')}
				></textarea>
				<div class="mt-4 grid gap-2 sm:grid-cols-2">
					<button
						class="min-h-11 rounded-xl border border-gray-200 px-4 text-sm font-medium outline-hidden hover:bg-gray-50 focus-visible:ring-2 focus-visible:ring-gray-400 dark:border-gray-700 dark:hover:bg-gray-900"
						type="button"
						on:click={copyCodes}
					>
						{$i18n.t(copied ? 'credits.admin.redeem.copied' : 'credits.admin.redeem.copyAll')}
					</button>
					<button
						class="min-h-11 rounded-xl bg-gray-900 px-4 text-sm font-medium text-white outline-hidden hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 dark:bg-gray-100 dark:text-gray-900"
						type="button"
						on:click={downloadCodes}
					>
						{$i18n.t('credits.admin.redeem.downloadCsv')}
					</button>
				</div>
				<button
					class="mt-3 min-h-11 w-full rounded-xl px-4 text-sm text-gray-600 underline outline-hidden focus-visible:ring-2 focus-visible:ring-gray-400 dark:text-gray-300"
					type="button"
					on:click={closeCreate}
				>
					{$i18n.t('credits.admin.redeem.closeAfterSave')}
				</button>
			{:else}
				<form class="mt-5 grid gap-4" on:submit|preventDefault={createBatch}>
					<label class="grid gap-1.5 text-sm"
						><span>{$i18n.t('credits.admin.redeem.batchName')}</span><input
							class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 outline-hidden focus:ring-2 focus:ring-gray-300 dark:border-gray-700"
							bind:value={name}
							maxlength="128"
							required
							placeholder={$i18n.t('credits.admin.redeem.batchNamePlaceholder')}
						/></label
					>
					<div class="grid gap-4 sm:grid-cols-2">
						<label class="grid gap-1.5 text-sm"
							><span>{$i18n.t('credits.admin.redeem.faceValue')}</span><input
								class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 outline-hidden focus:ring-2 focus:ring-gray-300 dark:border-gray-700"
								type="number"
								min="1"
								max="1000000000"
								bind:value={faceValue}
								required
							/></label
						>
						<label class="grid gap-1.5 text-sm"
							><span>{$i18n.t('credits.admin.redeem.quantity')}</span><input
								class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 outline-hidden focus:ring-2 focus:ring-gray-300 dark:border-gray-700"
								type="number"
								min="1"
								max="1000"
								bind:value={quantity}
								required
							/></label
						>
						<label class="grid gap-1.5 text-sm"
							><span>{$i18n.t('credits.admin.redeem.expiresAt')}</span><input
								class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 outline-hidden focus:ring-2 focus:ring-gray-300 dark:border-gray-700"
								type="date"
								min={new Date().toISOString().slice(0, 10)}
								bind:value={expiresDate}
							/></label
						>
						<label class="grid gap-1.5 text-sm"
							><span>{$i18n.t('credits.admin.redeem.perUserLimit')}</span><input
								class="min-h-11 min-w-0 rounded-xl border border-gray-200 bg-transparent px-3 outline-hidden focus:ring-2 focus:ring-gray-300 dark:border-gray-700"
								type="number"
								min="1"
								max={quantity}
								bind:value={perUserLimit}
							/></label
						>
					</div>
					{#if createError}<p class="text-sm text-red-700 dark:text-red-300" role="alert">
							{createError}
						</p>{/if}
					<div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
						<button
							class="min-h-11 rounded-xl px-4 text-sm outline-hidden hover:bg-gray-100 focus-visible:ring-2 focus-visible:ring-gray-400 dark:hover:bg-gray-800"
							type="button"
							on:click={closeCreate}>{$i18n.t('credits.common.cancel')}</button
						>
						<button
							class="min-h-11 rounded-xl bg-gray-900 px-5 text-sm font-medium text-white outline-hidden hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
							type="submit"
							disabled={creating || !name.trim()}
							>{creating
								? $i18n.t('credits.admin.redeem.generating')
								: $i18n.t('credits.admin.redeem.generate')}</button
						>
					</div>
				</form>
			{/if}
		</div>
	</Modal>
{/if}

{#if detailsOpen && selectedBatch}
	<Modal size="lg" bind:show={detailsOpen}>
		<div class="max-h-[min(90dvh,820px)] overflow-y-auto p-5 sm:p-6">
			<div class="flex items-start justify-between gap-3">
				<div class="min-w-0">
					<h2 class="truncate text-lg font-medium dark:text-gray-100">{selectedBatch.name}</h2>
					<p class="mt-1 text-sm text-gray-500">
						{selectedBatch.face_value}
						{$i18n.t('credits.common.unit')} × {selectedBatch.code_count}
					</p>
				</div>
				<button
					class="min-h-11 min-w-11 rounded-xl p-2 text-gray-500 outline-hidden hover:bg-gray-100 focus-visible:ring-2 focus-visible:ring-gray-400 dark:hover:bg-gray-800"
					type="button"
					aria-label={$i18n.t('credits.common.close')}
					on:click={() => (detailsOpen = false)}
					><XMark className="size-5" strokeWidth="1.5" /></button
				>
			</div>
			<div
				class="mt-5 flex gap-1 overflow-x-auto border-b border-gray-100 dark:border-gray-800"
				role="tablist"
				aria-label={$i18n.t('credits.admin.redeem.viewDetails')}
			>
				{#each ['codes', 'audit'] as mode}
					<button
						class="min-h-11 whitespace-nowrap border-b-2 px-4 text-sm font-medium outline-hidden focus-visible:ring-2 focus-visible:ring-gray-400 {detailMode ===
						mode
							? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
							: 'border-transparent text-gray-500'}"
						type="button"
						role="tab"
						id={`credit-redeem-detail-${mode}`}
						aria-selected={detailMode === mode}
						aria-controls="credit-redeem-detail-panel"
						tabindex={detailMode === mode ? 0 : -1}
						on:keydown={handleDetailTabKeydown}
						on:click={() => changeDetailMode(mode as 'codes' | 'audit')}
						>{$i18n.t(`credits.admin.redeem.${mode}`)}</button
					>
				{/each}
			</div>
			{#if detailError}<p
					class="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
					role="alert"
				>
					{detailError}
				</p>{/if}
			<div
				class="mt-4"
				id="credit-redeem-detail-panel"
				role="tabpanel"
				aria-labelledby={`credit-redeem-detail-${detailMode}`}
			>
				{#if detailLoading}<div class="flex min-h-40 items-center justify-center">
						<Spinner className="size-5" />
					</div>
				{:else if detailMode === 'codes'}
					{#if codes.length === 0}<p class="py-10 text-center text-sm text-gray-500">
							{$i18n.t('credits.admin.redeem.noCodes')}
						</p>{:else}
						<div class="grid gap-2">
							{#each codes as code (code.id)}
								<div
									class="flex flex-col gap-2 rounded-xl border border-gray-100 p-3 dark:border-gray-800 sm:flex-row sm:items-center"
								>
									<div class="min-w-0 flex-1">
										<div class="break-all font-mono text-sm">{code.hint}</div>
										<div class="mt-1 text-xs text-gray-500">
											{statusLabel(code.status)}{code.redeemed_by_name_snapshot
												? ` · ${code.redeemed_by_name_snapshot}`
												: ''}
										</div>
									</div>
									<div class="flex shrink-0 flex-wrap items-center gap-2">
										{#if code.status === 'available'}<button
												class="min-h-11 rounded-xl border border-red-200 px-3 text-sm text-red-700 outline-hidden focus-visible:ring-2 focus-visible:ring-red-300 dark:border-red-900 dark:text-red-300"
												type="button"
												on:click={() => voidCode(code)}
												>{$i18n.t('credits.admin.redeem.voidCode')}</button
											>{/if}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				{:else if audits.length === 0}<p class="py-10 text-center text-sm text-gray-500">
						{$i18n.t('credits.admin.redeem.noAudit')}
					</p>{:else}
					<div class="grid gap-2">
						{#each audits as audit (audit.id)}<div
								class="rounded-xl border border-gray-100 p-3 text-sm dark:border-gray-800"
							>
								<div class="font-medium">
									{$i18n.t(`credits.admin.redeem.actions.${audit.action}`)}
								</div>
								<div class="mt-1 break-words text-xs text-gray-500">
									{audit.actor_name_snapshot ?? audit.actor_id} · {new Date(
										audit.created_at * 1000
									).toLocaleString()} · {audit.request_source}
								</div>
							</div>{/each}
					</div>
				{/if}
			</div>
			{#if detailTotal > DETAIL_PAGE_SIZE}<div class="mt-5">
					<Pagination bind:page={detailPage} count={detailTotal} perPage={DETAIL_PAGE_SIZE} />
				</div>{/if}
		</div>
	</Modal>
{/if}
