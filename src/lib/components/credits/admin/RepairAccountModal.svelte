<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { repairCreditAccount, type CreditAccount } from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();

	export let show = false;
	export let account: CreditAccount | null = null;
	export let onRepaired: () => void = () => {};

	let incidentId = '';
	let expectedBalance = '';
	let note = '';
	let backupConfirmed = false;
	let saving = false;
	let requestError = '';

	const reset = () => {
		incidentId = '';
		expectedBalance = '';
		note = '';
		backupConfirmed = false;
		saving = false;
		requestError = '';
	};

	const close = () => {
		show = false;
		reset();
	};

	$: expectedBalanceNumber = /^-?\d+$/.test(expectedBalance.trim())
		? Number.parseInt(expectedBalance.trim(), 10)
		: null;
	$: canSubmit =
		Boolean(account) &&
		incidentId.trim().length > 0 &&
		expectedBalanceNumber !== null &&
		expectedBalanceNumber >= 0 &&
		note.trim().length > 0 &&
		backupConfirmed &&
		!saving;

	const submit = async () => {
		if (!account || expectedBalanceNumber === null) return;

		saving = true;
		requestError = '';
		try {
			await repairCreditAccount(localStorage.token, account.user_id, {
				incident_id: incidentId.trim(),
				expected_balance: expectedBalanceNumber,
				note: note.trim(),
				backup_confirmed: backupConfirmed
			});
			toast.success($i18n.t('credits.admin.repair.saved'));
			close();
			onRepaired();
		} catch (error) {
			requestError = translateCreditApiError($i18n, error, 'credits.admin.repair.saveError');
		} finally {
			saving = false;
		}
	};

	$: if (!show) {
		reset();
	}
</script>

<Modal size="sm" bind:show>
	<div class="px-5 py-4">
		<div class="mb-5 flex items-center justify-between gap-4">
			<div>
				<div class="text-lg font-medium dark:text-gray-100">
					{$i18n.t('credits.admin.repair.title')}
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
			<p
				class="rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-200"
			>
				{$i18n.t('credits.admin.repair.description')}
			</p>

			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.admin.repair.incidentId')}
				<input
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={incidentId}
					placeholder="INC-2026-0001"
				/>
			</label>

			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.admin.repair.expectedBalance')}
				<input
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={expectedBalance}
					inputmode="numeric"
					placeholder="0"
				/>
			</label>

			<label class="block text-sm font-medium dark:text-gray-200">
				{$i18n.t('credits.admin.repair.note')}
				<textarea
					class="mt-1.5 w-full rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
					bind:value={note}
					rows="3"
				></textarea>
			</label>

			<label class="flex items-center gap-2 text-sm dark:text-gray-200">
				<input type="checkbox" bind:checked={backupConfirmed} />
				{$i18n.t('credits.admin.repair.backupConfirmed')}
			</label>

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
				class="rounded-3xl bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900"
				disabled={!canSubmit}
				on:click={submit}
				type="button"
			>
				{saving ? $i18n.t('credits.common.saving') : $i18n.t('credits.admin.repair.submit')}
			</button>
		</div>
	</div>
</Modal>
