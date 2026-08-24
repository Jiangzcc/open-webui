<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';
	import { toast } from 'svelte-sonner';

	import {
		createCreditPrice,
		updateCreditPrice,
		type CreditPrice,
		type PriceRule
	} from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Select from '$lib/components/common/Select.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import {
		hasBlankExactMapEntry,
		addExactMapEntry,
		removeExactMapEntry,
		updateExactMapEntryKey,
		updateExactMapEntryMultiplier,
		validatePriceForm,
		type FormErrors,
		type PriceForm
	} from './admin-form-state';

	const i18n = getContext<Writable<I18n>>('i18n');

	export let show = false;
	export let price: CreditPrice | null = null;
	export let onSaved: () => void = () => {};

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

	let form: PriceForm = emptyForm();
	let errors: FormErrors = {};
	let saving = false;
	let requestError = '';

	const priceLabel = (group: 'serviceTypes' | 'actions', value: string) =>
		$i18n.exists(`credits.${group}.${value}`) ? $i18n.t(`credits.${group}.${value}`) : value;

	const actionsForService = (serviceType: string) =>
		serviceType === 'video'
			? ['text-to-video', 'image-to-video', 'video-to-video']
			: ['text-to-image', 'image-to-image'];

	const selectServiceType = (serviceType: string) => {
		form = {
			...form,
			serviceType,
			action: actionsForService(serviceType)[0]
		};
	};

	const reset = () => {
		if (price) {
			form = {
				serviceType: price.service_type,
				resourceId: price.resource_id,
				action: price.action,
				basePrice: price.base_price,
				dimensions: structuredClone(price.rules.dimensions)
			};
		} else {
			form = emptyForm();
		}
		errors = {};
		requestError = '';
		saving = false;
	};

	const close = () => {
		show = false;
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

	const save = async () => {
		errors = validatePriceForm(form);
		if (Object.keys(errors).length > 0) return;

		saving = true;
		requestError = '';
		const input = {
			service_type: form.serviceType.trim(),
			resource_id: form.resourceId.trim(),
			action: form.action.trim(),
			base_price: form.basePrice,
			rules: { schema_version: 1 as const, dimensions: form.dimensions }
		};

		try {
			if (price) {
				await updateCreditPrice(localStorage.token, price.id, {
					base_price: input.base_price,
					rules: input.rules
				});
				toast.success($i18n.t('credits.admin.pricing.saved'));
			} else {
				await createCreditPrice(localStorage.token, { ...input, enabled: true });
				toast.success($i18n.t('credits.admin.pricing.saved'));
			}
			close();
			onSaved();
		} catch (requestError_) {
			requestError = translateCreditApiError(
				$i18n,
				requestError_,
				'credits.admin.pricingSaveError'
			);
		} finally {
			saving = false;
		}
	};

	$: if (show) {
		reset();
	}
</script>

<Modal size="md" bind:show>
	<div class="px-5 py-4">
		<div class="mb-5 flex items-center justify-between gap-4">
			<div>
				<div class="text-lg font-medium dark:text-gray-100">
					{price
						? $i18n.t('credits.admin.pricing.editTitle')
						: $i18n.t('credits.admin.pricing.newTitle')}
				</div>
			</div>
			<button
				class="rounded-lg p-1 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
				on:click={close}
				type="button"
				aria-label={$i18n.t('credits.common.close')}
			>
				<XMark className="size-5" />
			</button>
		</div>

		{#if requestError}
			<div
				class="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
			>
				{requestError}
			</div>
		{/if}

		<form class="space-y-3" on:submit|preventDefault={save}>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.admin.pricing.serviceType')}
				<Select
					value={form.serviceType}
					items={[
						{ value: 'image', label: $i18n.t('credits.admin.imageService') },
						{ value: 'video', label: $i18n.t('credits.admin.videoService') }
					]}
					ariaLabel={$i18n.t('credits.admin.pricing.serviceType')}
					triggerClass="mt-1 w-full items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
					disabled={Boolean(price)}
					onChange={(value) => selectServiceType(value)}
				/></label
			>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.admin.pricing.resourceId')}<input
					class="mt-1 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.resourceId}
					disabled={Boolean(price)}
				/></label
			>
			<label class="block text-xs font-medium text-gray-500"
				>{$i18n.t('credits.common.action')}
				<Select
					value={form.action}
					items={actionsForService(form.serviceType).map((action) => ({
						value: action,
						label: priceLabel('actions', action)
					}))}
					ariaLabel={$i18n.t('credits.common.action')}
					triggerClass="mt-1 w-full items-center rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm dark:border-gray-700"
					disabled={Boolean(price)}
					onChange={(value) => (form.action = value)}
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
								><button
									class="text-xs text-red-600"
									on:click={() => removeRule(index)}
									type="button">{$i18n.t('credits.common.remove')}</button
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

			<div class="mt-6 flex justify-end gap-2">
				<button
					class="rounded-3xl bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
					on:click={close}
					type="button"
				>
					{$i18n.t('credits.common.cancel')}
				</button>
				<button
					class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
					disabled={saving}
					type="submit"
				>
					{saving ? $i18n.t('credits.common.saving') : $i18n.t('credits.common.save')}
				</button>
			</div>
		</form>
	</div>
</Modal>
