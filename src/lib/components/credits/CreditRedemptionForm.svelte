<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import type { i18n as I18n } from 'i18next';
	import type { Writable } from 'svelte/store';

	import { redeemCreditCode, type CreditRedeemResult } from '$lib/apis/credits';
	import { registerCreditTranslations, translateCreditApiError } from './credits-i18n';

	const i18n = getContext<Writable<I18n>>('i18n');
	registerCreditTranslations($i18n);

	const dispatch = createEventDispatcher<{ redeemed: CreditRedeemResult }>();

	let expanded = false;
	let code = '';
	let submitting = false;
	let error = '';
	let success = '';

	const submit = async () => {
		const normalized = code.trim();
		if (!normalized || submitting) return;

		submitting = true;
		error = '';
		success = '';
		try {
			const result = await redeemCreditCode(localStorage.token, normalized);
			code = '';
			success = $i18n.t('credits.redeem.success', { credits: result.credited });
			dispatch('redeemed', result);
		} catch (requestError) {
			error = translateCreditApiError($i18n, requestError, 'credits.redeem.failed');
		} finally {
			submitting = false;
		}
	};

	const toggle = () => {
		expanded = !expanded;
		error = '';
		success = '';
		if (!expanded) code = '';
	};
</script>

<div
	class="mt-4 rounded-2xl border border-gray-100 bg-gray-50/70 p-3 dark:border-gray-800 dark:bg-gray-900/40"
>
	<button
		class="flex min-h-11 w-full items-center justify-between gap-3 rounded-xl px-2 text-left text-sm font-medium outline-hidden focus-visible:ring-2 focus-visible:ring-gray-400"
		type="button"
		aria-expanded={expanded}
		aria-controls="credit-redemption-panel"
		on:click={toggle}
	>
		<span>{$i18n.t('credits.redeem.title')}</span>
		<span class="text-lg leading-none text-gray-500" aria-hidden="true">{expanded ? '−' : '+'}</span
		>
	</button>

	{#if expanded}
		<form id="credit-redemption-panel" class="mt-2" on:submit|preventDefault={submit}>
			<div class="flex flex-col gap-2 sm:flex-row sm:items-end">
				<div class="min-w-0 flex-1">
					<label
						class="mb-1.5 block text-sm text-gray-600 dark:text-gray-300"
						for="credit-redemption-code"
					>
						{$i18n.t('credits.redeem.codeLabel')}
					</label>
					<input
						id="credit-redemption-code"
						class="min-h-11 w-full min-w-0 rounded-xl border border-gray-200 bg-white px-3 text-sm uppercase tracking-wide outline-hidden focus:border-gray-400 focus:ring-2 focus:ring-gray-200 dark:border-gray-700 dark:bg-gray-950 dark:focus:border-gray-500 dark:focus:ring-gray-800"
						type="text"
						bind:value={code}
						maxlength="64"
						autocomplete="off"
						spellcheck="false"
						placeholder={$i18n.t('credits.redeem.placeholder')}
						disabled={submitting}
					/>
				</div>
				<button
					class="min-h-11 rounded-xl bg-gray-900 px-5 text-sm font-medium text-white outline-hidden hover:bg-gray-800 focus-visible:ring-2 focus-visible:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
					type="submit"
					disabled={submitting || !code.trim()}
				>
					{submitting ? $i18n.t('credits.redeem.submitting') : $i18n.t('credits.redeem.submit')}
				</button>
			</div>
			{#if error}
				<p class="mt-2 text-sm text-red-700 dark:text-red-300" role="alert">{error}</p>
			{/if}
			{#if success}
				<p class="mt-2 text-sm text-green-700 dark:text-green-300" role="status">{success}</p>
			{/if}
		</form>
	{/if}
</div>
