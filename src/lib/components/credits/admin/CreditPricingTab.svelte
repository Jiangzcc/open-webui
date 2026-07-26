<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';

	import {
		createCreditPrice,
		deleteCreditPrice,
		getCreditPrices,
		updateCreditPrice,
		type CreditPrice,
		type PriceRule
	} from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import {
		addExactMapEntry,
		hasBlankExactMapEntry,
		removeExactMapEntry,
		updateExactMapEntryKey,
		updateExactMapEntryMultiplier,
		validatePriceForm,
		type FormErrors,
		type PriceForm
	} from './admin-form-state';

	const i18n = getContext<Writable<I18n>>('i18n');

	const emptyForm = (): PriceForm => ({
		serviceType: 'image',
		resourceId: '',
		action: 'text-to-image',
		basePrice: '1',
		dimensions: []
	});

	const defaultRule = (kind: PriceRule['kind']): PriceRule => {
		if (kind === 'exact_map') return { key: '', kind, values: { default: '1' } };
		if (kind === 'numeric_tier') return { key: '', kind, tiers: [{ max: '1', multiplier: '1' }] };
		if (kind === 'unit_blocks')
			return { key: '', kind, block_size: '1', multiplier_per_block: '1' };
		if (kind === 'proportional') return { key: 'pixel_count', kind, unit_size: '1000000' };
		return { key: '', kind };
	};

	let prices: CreditPrice[] = [];
	let form = emptyForm();
	let editingPriceId: string | null = null;
	let errors: FormErrors = {};
	let loading = true;
	let saving = false;
	let error = '';
	let deletePrice: CreditPrice | null = null;
	let showDeleteConfirmation = false;

	const loadPrices = async () => {
		loading = true;
		error = '';
		try {
			prices = await getCreditPrices(localStorage.token, { skip: 0, limit: 100 });
		} catch (requestError) {
			prices = [];
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingLoadError');
		} finally {
			loading = false;
		}
	};

	const priceLabel = (group: 'serviceTypes' | 'actions', value: string) =>
		$i18n.exists(`credits.${group}.${value}`) ? $i18n.t(`credits.${group}.${value}`) : value;

	const resetForm = () => {
		form = emptyForm();
		editingPriceId = null;
		errors = {};
		error = '';
	};

	const selectPrice = (price: CreditPrice) => {
		editingPriceId = price.id;
		form = {
			serviceType: price.service_type,
			resourceId: price.resource_id,
			action: price.action,
			basePrice: price.base_price,
			dimensions: structuredClone(price.rules.dimensions)
		};
		errors = {};
		error = '';
	};

	const addRule = (kind: PriceRule['kind']) => {
		form = { ...form, dimensions: [...form.dimensions, defaultRule(kind)] };
	};

	const updateRule = (index: number, updates: Record<string, unknown>) => {
		form = {
			...form,
			dimensions: form.dimensions.map((rule, ruleIndex) =>
				ruleIndex === index ? { ...rule, ...updates } : rule
			)
		};
	};

	const replaceRule = (index: number, nextRule: PriceRule) => {
		form = {
			...form,
			dimensions: form.dimensions.map((rule, ruleIndex) => (ruleIndex === index ? nextRule : rule))
		};
	};

	const removeRule = (index: number) => {
		form = { ...form, dimensions: form.dimensions.filter((_, ruleIndex) => ruleIndex !== index) };
	};

	const savePrice = async () => {
		errors = validatePriceForm(form);
		if (Object.keys(errors).length > 0) return;

		saving = true;
		error = '';
		const input = {
			service_type: form.serviceType.trim(),
			resource_id: form.resourceId.trim(),
			action: form.action.trim(),
			base_price: form.basePrice,
			rules: { schema_version: 1 as const, dimensions: form.dimensions }
		};

		try {
			if (editingPriceId) {
				await updateCreditPrice(localStorage.token, editingPriceId, {
					base_price: input.base_price,
					rules: input.rules
				});
			} else {
				await createCreditPrice(localStorage.token, { ...input, enabled: true });
			}
			resetForm();
			await loadPrices();
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingSaveError');
		} finally {
			saving = false;
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

	const confirmDelete = async () => {
		if (!deletePrice) return;
		try {
			await deleteCreditPrice(localStorage.token, deletePrice.id);
			if (editingPriceId === deletePrice.id) resetForm();
			await loadPrices();
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.admin.pricingDeleteError');
		} finally {
			deletePrice = null;
			showDeleteConfirmation = false;
		}
	};

	onMount(loadPrices);
</script>

<ConfirmDialog
	bind:show={showDeleteConfirmation}
	title={$i18n.t('credits.admin.pricing.deleteTitle')}
	message={$i18n.t('credits.admin.pricing.deleteMessage')}
	confirmLabel={$i18n.t('credits.common.delete')}
	onConfirm={confirmDelete}
/>

<div class="grid h-full gap-6 xl:grid-cols-[minmax(0,1fr)_26rem]">
	<div class="min-w-0">
		<div class="mb-4">
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.pricingTitle')}
			</h2>
			<p class="mt-1 text-sm text-gray-500">
				{$i18n.t('credits.admin.pricingDescription')}
			</p>
		</div>

		{#if error}
			<div
				class="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
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
										on:click={() => selectPrice(price)}
										type="button">{$i18n.t('credits.common.edit')}</button
									>
									<button
										class="text-xs text-red-600 underline"
										on:click={() => {
											deletePrice = price;
											showDeleteConfirmation = true;
										}}
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
		{/if}
	</div>

	<form
		class="rounded-xl border border-gray-100 p-4 dark:border-gray-800"
		on:submit|preventDefault={savePrice}
	>
		<div class="mb-4 flex items-center justify-between gap-3">
			<h3 class="font-medium dark:text-gray-100">
				{editingPriceId
					? $i18n.t('credits.admin.pricing.editTitle')
					: $i18n.t('credits.admin.pricing.newTitle')}
			</h3>
			{#if editingPriceId}<button class="text-xs underline" on:click={resetForm} type="button"
					>{$i18n.t('credits.common.new')}</button
				>{/if}
		</div>

		<div class="space-y-3">
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.admin.pricing.serviceType')}<input
					class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.serviceType}
					disabled={Boolean(editingPriceId)}
				/></label
			>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.admin.pricing.resourceId')}<input
					class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.resourceId}
					disabled={Boolean(editingPriceId)}
				/></label
			>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.common.action')}<input
					class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.action}
					disabled={Boolean(editingPriceId)}
				/></label
			>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.admin.pricing.basePrice')}<input
					class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					class:border-red-500={Boolean(errors.basePrice)}
					bind:value={form.basePrice}
					inputmode="decimal"
				/>{#if errors.basePrice}<span class="mt-1 block text-xs text-red-500"
						>{$i18n.t(errors.basePrice)}</span
					>{/if}</label
			>
		</div>

		<div class="mt-5 border-t border-gray-100 pt-4 dark:border-gray-800">
			<div class="mb-3 flex items-center justify-between">
				<div class="text-sm font-medium dark:text-gray-100">
					{$i18n.t('credits.admin.dimensionsTitle')}
				</div>
				<select
					class="rounded-lg border border-gray-200 bg-transparent px-2 py-1 text-xs dark:border-gray-700"
					on:change={(event) => {
						const kind = event.currentTarget.value as PriceRule['kind'];
						if (kind) {
							addRule(kind);
							event.currentTarget.value = '';
						}
					}}
					><option value="">{$i18n.t('credits.admin.pricing.addDimension')}</option><option
						value="exact_map">{$i18n.t('credits.admin.pricing.ruleKinds.exact_map')}</option
					><option value="proportional"
						>{$i18n.t('credits.admin.pricing.ruleKinds.proportional')}</option
					><option value="quantity">{$i18n.t('credits.admin.pricing.ruleKinds.quantity')}</option
					></select
				>
			</div>
			{#if errors.dimensions}<div class="mb-2 text-xs text-red-500">
					{$i18n.t(errors.dimensions)}
				</div>{/if}
			<div class="space-y-3">
				{#each form.dimensions as rule, index (index)}
					<div class="rounded-xl bg-gray-50 p-3 dark:bg-gray-900">
						<div class="mb-2 flex gap-2">
							<input
								class="min-w-0 flex-1 rounded-lg border border-gray-200 bg-transparent px-2 py-1 text-xs outline-hidden dark:border-gray-700"
								value={rule.key}
								on:input={(event) => updateRule(index, { key: event.currentTarget.value })}
								placeholder={$i18n.t('credits.admin.pricing.dimensionKey')}
							/><span class="rounded-lg bg-white px-2 py-1 text-xs dark:bg-gray-800"
								>{$i18n.t(`credits.admin.pricing.ruleKinds.${rule.kind}`)}</span
							><button class="text-xs text-red-600" on:click={() => removeRule(index)} type="button"
								>{$i18n.t('credits.common.remove')}</button
							>
						</div>
						{#if rule.kind === 'exact_map'}
							<div class="space-y-2">
								<div
									class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] gap-2 px-1 text-[0.7rem] text-gray-500"
								>
									<span>{$i18n.t('credits.common.value')}</span>
									<span>{$i18n.t('credits.common.multiplier')}</span>
									<span class="sr-only">{$i18n.t('credits.common.actions')}</span>
								</div>
								{#each Object.entries(rule.values as Record<string, string>) as [entryKey, multiplier]}
									<div class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] gap-2">
										<input
											aria-label={$i18n.t('credits.common.value')}
											class="min-w-0 rounded-lg border border-gray-200 bg-transparent px-2 py-1 text-xs outline-hidden disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700"
											disabled={entryKey === 'default'}
											value={entryKey}
											on:input={(event) =>
												replaceRule(
													index,
													updateExactMapEntryKey(
														rule as PriceRule & {
															kind: 'exact_map';
															values: Record<string, string>;
														},
														entryKey,
														event.currentTarget.value
													)
												)}
											placeholder={$i18n.t('credits.common.value')}
										/><input
											aria-label={$i18n.t('credits.common.multiplier')}
											class="min-w-0 rounded-lg border border-gray-200 bg-transparent px-2 py-1 text-xs outline-hidden dark:border-gray-700"
											inputmode="decimal"
											value={multiplier}
											on:input={(event) =>
												replaceRule(
													index,
													updateExactMapEntryMultiplier(
														rule as PriceRule & {
															kind: 'exact_map';
															values: Record<string, string>;
														},
														entryKey,
														event.currentTarget.value
													)
												)}
											placeholder={$i18n.t('credits.common.multiplier')}
										/>{#if entryKey === 'default'}
											<span class="w-10" aria-hidden="true"></span>
										{:else}
											<button
												aria-label={$i18n.t('credits.common.remove')}
												class="w-10 text-xs text-red-600"
												on:click={() =>
													replaceRule(
														index,
														removeExactMapEntry(
															rule as PriceRule & {
																kind: 'exact_map';
																values: Record<string, string>;
															},
															entryKey
														)
													)}
												type="button">{$i18n.t('credits.common.remove')}</button
											>
										{/if}
									</div>
								{/each}
								<button
									class="text-xs font-medium text-gray-600 underline disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-300"
									disabled={hasBlankExactMapEntry(
										rule as PriceRule & {
											kind: 'exact_map';
											values: Record<string, string>;
										}
									)}
									on:click={() =>
										replaceRule(
											index,
											addExactMapEntry(
												rule as PriceRule & {
													kind: 'exact_map';
													values: Record<string, string>;
												}
											)
										)}
									type="button">{$i18n.t('credits.admin.pricing.addMapping')}</button
								>
							</div>
						{:else if rule.kind === 'proportional'}
							<div class="space-y-2">
								<label class="block text-xs font-medium text-gray-500"
									>{$i18n.t('credits.admin.pricing.unitSize')}<input
										aria-label={$i18n.t('credits.admin.pricing.unitSize')}
										class="mt-1 w-full rounded-lg border border-gray-200 bg-transparent px-2 py-1.5 text-xs outline-hidden dark:border-gray-700"
										inputmode="decimal"
										value={String(rule.unit_size ?? '')}
										on:input={(event) =>
											updateRule(index, { unit_size: event.currentTarget.value })}
									/></label
								>
								<p class="text-xs leading-5 text-gray-500">
									{$i18n.t('credits.admin.pricing.proportionalDescription')}
								</p>
							</div>
						{:else}
							<div class="text-xs text-gray-500">
								{$i18n.t('credits.admin.pricing.quantityDescription')}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<button
			class="mt-5 w-full rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
			disabled={saving}
			type="submit"
			>{saving ? $i18n.t('credits.common.saving') : $i18n.t('credits.common.save')}</button
		>
	</form>
</div>
