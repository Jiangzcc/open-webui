<script lang="ts">
	import { getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { adjustCreditAccount, type CreditAccount } from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import {
		createAdjustmentForm,
		toCreditAdjustmentInput,
		validateAdjustmentForm,
		type AdjustmentForm,
		type FormErrors
	} from './admin-form-state';

	const i18n = getContext('i18n');

	export let show = false;
	export let account: CreditAccount | null = null;
	export let onAdjusted: () => void = () => {};

	const reasonOptions = [
		'offline_recharge',
		'promotion_gift',
		'manual_refund',
		'accounting_correction',
		'violation_deduction',
		'other'
	] as const;

	let form: AdjustmentForm = createAdjustmentForm();
	let errors: FormErrors = {};
	let showConfirmation = false;
	let saving = false;
	let requestError = '';

	const reset = () => {
		form = createAdjustmentForm();
		errors = {};
		showConfirmation = false;
		saving = false;
		requestError = '';
	};

	const close = () => {
		show = false;
		reset();
	};

	const requestConfirmation = () => {
		errors = validateAdjustmentForm(form);
		if (Object.keys(errors).length === 0) {
			showConfirmation = true;
		}
	};

	const confirmAdjustment = async () => {
		if (!account) return;

		saving = true;
		requestError = '';
		try {
			await adjustCreditAccount(localStorage.token, account.user_id, toCreditAdjustmentInput(form));
			toast.success($i18n.t('credits.admin.adjustment.saved'));
			close();
			onAdjusted();
		} catch (error) {
			requestError = translateCreditApiError($i18n, error, 'credits.admin.adjustment.saveError');
		} finally {
			saving = false;
		}
	};

	$: if (!show) {
		reset();
	}
</script>

<ConfirmDialog
	bind:show={showConfirmation}
	title={$i18n.t('credits.admin.adjustment.confirmTitle')}
	message={$i18n.t('credits.admin.adjustment.confirmMessage')}
	confirmLabel={$i18n.t('credits.common.confirm')}
	onConfirm={confirmAdjustment}
/>

<Modal size="sm" bind:show>
	<div class="px-5 py-4">
		<div class="mb-5 flex items-center justify-between gap-4">
			<div>
				<div class="text-lg font-medium dark:text-gray-100">
					{$i18n.t('credits.admin.adjustment.title')}
				</div>
				<div class="mt-1 text-sm text-gray-500">
					{account?.name ?? account?.email ?? account?.user_id}
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

		<div class="space-y-4">
			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.admin.adjustment.direction')}
				<select
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.direction}
				>
					<option value="increase">{$i18n.t('credits.admin.adjustment.increase')}</option>
					<option value="decrease">{$i18n.t('credits.admin.adjustment.decrease')}</option>
				</select>
			</label>

			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.common.amount')}
				<input
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					class:border-red-500={Boolean(errors.amount)}
					bind:value={form.amount}
					inputmode="numeric"
					placeholder="0"
				/>
				{#if errors.amount}<div class="mt-1 text-xs text-red-500">
						{$i18n.t(errors.amount)}
					</div>{/if}
			</label>

			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.admin.adjustment.reason')}
				<select
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={form.reasonCode}
				>
					{#each reasonOptions as reason}
						<option value={reason}>{$i18n.t(`credits.reasons.${reason}`)}</option>
					{/each}
				</select>
			</label>

			{#if form.reasonCode === 'other'}
				<label class="block text-sm font-medium dark:text-gray-200">
					{$i18n.t('credits.admin.adjustment.note')}
					<textarea
						class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
						class:border-red-500={Boolean(errors.note)}
						bind:value={form.note}
						rows="3"
					/>
					{#if errors.note}<div class="mt-1 text-xs text-red-500">{$i18n.t(errors.note)}</div>{/if}
				</label>
			{/if}

			{#if requestError}
				<div
					class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
				>
					{requestError}
				</div>
			{/if}
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
				class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900"
				disabled={saving}
				on:click={requestConfirmation}
				type="button"
			>
				{saving ? $i18n.t('credits.common.saving') : $i18n.t('credits.admin.adjustCredits')}
			</button>
		</div>
	</div>
</Modal>
