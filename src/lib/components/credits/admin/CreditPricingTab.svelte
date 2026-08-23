<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import {
		deleteCreditPrice,
		getCreditPrices,
		updateCreditPrice,
		type CreditPrice,
		type CreditPriceQuery
	} from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Select from '$lib/components/common/Select.svelte';
import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Pagination from '$lib/components/common/Pagination.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import CreditPriceModal from './CreditPriceModal.svelte';

	const i18n = getContext<Writable<I18n>>('i18n');
	const pageSize = 25;

	let prices: CreditPrice[] = [];
	let total = 0;
	let page = 1;
	let loading = true;
	let error = '';
	let filters: CreditPriceQuery = {};
	let mounted = false;

	let editingPrice: CreditPrice | null = null;
	let showPriceModal = false;
	let deleteTarget: CreditPrice | null = null;
	let showDeleteConfirmation = false;

	const loadPrices = async () => {
		loading = true;
		error = '';
		try {
			const result = await getCreditPrices(localStorage.token, {
				...filters,
				resource_id: filters.resource_id?.trim() || undefined,
				skip: (page - 1) * pageSize,
				limit: pageSize
			});
			prices = result.items;
			total = result.total;
		} catch (requestError) {
			prices = [];
			total = 0;
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingLoadError');
		} finally {
			loading = false;
		}
	};

	const priceLabel = (group: 'serviceTypes' | 'actions', value: string) =>
		$i18n.exists(`credits.${group}.${value}`) ? $i18n.t(`credits.${group}.${value}`) : value;

	const applyFilters = () => {
		if (page === 1) {
			loadPrices();
		} else {
			page = 1;
		}
	};

	const openCreate = () => {
		editingPrice = null;
		showPriceModal = true;
	};

	const openEdit = (price: CreditPrice) => {
		editingPrice = price;
		showPriceModal = true;
	};

	const requestDelete = (price: CreditPrice) => {
		deleteTarget = price;
		showDeleteConfirmation = true;
	};

	const confirmDelete = async () => {
		if (!deleteTarget) return;
		try {
			await deleteCreditPrice(localStorage.token, deleteTarget.id);
			if (prices.length === 1 && page > 1) {
				page -= 1;
			} else {
				await loadPrices();
			}
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingDeleteError');
		} finally {
			deleteTarget = null;
			showDeleteConfirmation = false;
		}
	};

	const toggleEnabled = async (price: CreditPrice) => {
		try {
			await updateCreditPrice(localStorage.token, price.id, { enabled: !price.enabled });
			await loadPrices();
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingSaveError');
		}
	};

	$: if (mounted && page > 0) {
		loadPrices();
	}

	onMount(() => {
		mounted = true;
	});
</script>

<ConfirmDialog
	bind:show={showDeleteConfirmation}
	title={$i18n.t('credits.admin.pricing.deleteTitle')}
	message={$i18n.t('credits.admin.pricing.deleteMessage')}
	confirmLabel={$i18n.t('credits.common.delete')}
	onConfirm={confirmDelete}
/>

<CreditPriceModal
	bind:show={showPriceModal}
	price={editingPrice}
	onSaved={() => {
		loadPrices();
	}}
/>

<div class="flex h-full flex-col gap-4">
	<div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
		<div>
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.pricingTitle')}
			</h2>
			<p class="mt-1 text-sm text-gray-500">
				{$i18n.t('credits.admin.pricingDescription')}
			</p>
		</div>
		<button
			class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
			on:click={openCreate}
			type="button"
		>
			{$i18n.t('credits.common.new')}
		</button>
	</div>

	<div class="grid gap-2 md:grid-cols-3 lg:grid-cols-5">
		<Select
			value={filters.service_type ?? ''}
			items={[
				{ value: '', label: $i18n.t('credits.admin.allTypes') },
				{ value: 'image', label: $i18n.t('credits.serviceTypes.image') },
				{ value: 'video', label: $i18n.t('credits.serviceTypes.video') }
			]}
			ariaLabel={$i18n.t('credits.admin.allTypes')}
			triggerClass="flex items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
			onChange={(value) => (filters.service_type = value || undefined)}
		/>
		<input
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={filters.resource_id}
			placeholder={$i18n.t('credits.admin.modelOrResource')}
		/>
		<Select
			value={filters.action ?? ''}
			items={[
				{ value: '', label: $i18n.t('credits.admin.allTypes') },
				{ value: 'text-to-image', label: $i18n.t('credits.actions.text-to-image') },
				{ value: 'image-to-image', label: $i18n.t('credits.actions.image-to-image') },
				{ value: 'text-to-video', label: $i18n.t('credits.actions.text-to-video') },
				{ value: 'image-to-video', label: $i18n.t('credits.actions.image-to-video') },
				{ value: 'video-to-video', label: $i18n.t('credits.actions.video-to-video') }
			]}
			ariaLabel={$i18n.t('credits.common.action')}
			triggerClass="flex items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
			onChange={(value) => (filters.action = value || undefined)}
		/>
		<Select
			value={filters.enabled === undefined || filters.enabled === null ? '' : String(filters.enabled)}
			items={[
				{ value: '', label: $i18n.t('credits.admin.allTypes') },
				{ value: 'true', label: $i18n.t('credits.common.enabled') },
				{ value: 'false', label: $i18n.t('credits.common.disabled') }
			]}
			ariaLabel={$i18n.t('credits.admin.allTypes')}
			triggerClass="flex items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
			onChange={(value) => (filters.enabled = value === '' ? undefined : value === 'true')}
		/>
		<button
			class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
			on:click={applyFilters}
			type="button"
		>
			{$i18n.t('credits.common.applyFilters')}
		</button>
	</div>

	{#if error}
		<div
			class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
		>
			{error}
		</div>
	{/if}

	{#if loading}
		<div class="flex min-h-40 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if prices.length === 0}
		<div
			class="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-700"
		>
			{$i18n.t('credits.admin.pricingEmpty')}
		</div>
	{:else}
		<div class="overflow-x-auto rounded-xl border border-gray-100 dark:border-gray-800">
			<table class="w-full text-left text-sm">
				<thead class="border-b border-gray-100 text-xs text-gray-500 dark:border-gray-800">
					<tr>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.admin.pricing.service')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.resource')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.admin.pricing.basePrice')}</th>
						<th class="px-4 py-3 font-medium">{$i18n.t('credits.common.enabled')}</th>
						<th class="px-4 py-3 font-medium"
							><span class="sr-only">{$i18n.t('credits.common.actions')}</span></th
						>
					</tr>
				</thead>
				<tbody>
					{#each prices as price (price.id)}
						<tr class="border-b border-gray-50 last:border-0 dark:border-gray-850">
							<td class="px-4 py-3"
								>{priceLabel('serviceTypes', price.service_type)}
								<div class="text-xs text-gray-500">{priceLabel('actions', price.action)}</div></td
							>
							<td class="px-4 py-3">{price.resource_id}</td>
							<td class="px-4 py-3 tabular-nums">{price.base_price}</td>
							<td class="px-4 py-3">
								<button class="underline" on:click={() => toggleEnabled(price)} type="button">
									{price.enabled
										? $i18n.t('credits.common.enabled')
										: $i18n.t('credits.common.disabled')}
								</button>
							</td>
							<td class="px-4 py-3 text-right">
								<button
									class="mr-3 text-xs underline"
									on:click={() => openEdit(price)}
									type="button">{$i18n.t('credits.common.edit')}</button
								>
								<button
									class="text-xs text-red-600 underline"
									on:click={() => requestDelete(price)}
									type="button"
								>
									{$i18n.t('credits.common.delete')}
								</button>
							</td>
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
