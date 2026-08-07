<script lang="ts">
	import { getContext, onMount } from 'svelte';

	import { getAdminCreditDimensions, type CreditDimensions } from '$lib/apis/credits';
	import { translateCreditApiError } from '$lib/components/credits/credits-i18n';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let serviceType = 'image';
	let registry: CreditDimensions | null = null;
	let loading = true;
	let error = '';

	const loadDimensions = async () => {
		loading = true;
		error = '';
		try {
			registry = await getAdminCreditDimensions(localStorage.token, serviceType);
		} catch (requestError) {
			registry = null;
			error = translateCreditApiError($i18n, requestError, 'credits.admin.dimensionsLoadError');
		} finally {
			loading = false;
		}
	};

	const dimensionLabel = (group: string, value: string) =>
		$i18n.exists(`credits.${group}.${value}`) ? $i18n.t(`credits.${group}.${value}`) : value;

	onMount(loadDimensions);
</script>

<div class="flex h-full flex-col gap-4">
	<div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
		<div>
			<h2 class="text-base font-medium dark:text-gray-100">
				{$i18n.t('credits.admin.dimensionsTitle')}
			</h2>
			<p class="mt-1 text-sm text-gray-500">
				{$i18n.t('credits.admin.dimensionsDescription')}
			</p>
		</div>
		<select
			class="rounded-xl border border-gray-200 bg-transparent px-3 py-2 text-sm outline-hidden dark:border-gray-700"
			bind:value={serviceType}
			on:change={loadDimensions}
		>
			<option value="image">{$i18n.t('credits.admin.imageService')}</option>
			<option value="video">{$i18n.t('credits.admin.videoService')}</option>
		</select>
	</div>

	<div
		class="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-800 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200"
	>
		{$i18n.t('credits.admin.dimensionsNotice')}
	</div>

	{#if error}
		<div
			class="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300"
		>
			{error}
			<button class="ml-2 underline" on:click={loadDimensions} type="button"
				>{$i18n.t('credits.common.retry')}</button
			>
		</div>
	{/if}

	{#if loading}
		<div class="flex flex-1 items-center justify-center"><Spinner className="size-5" /></div>
	{:else if registry && Object.keys(registry.dimensions).length > 0}
		<div class="grid gap-3 md:grid-cols-2">
			{#each Object.entries(registry.dimensions) as [action, dimensions]}
				<section class="rounded-xl border border-gray-100 p-4 dark:border-gray-800">
					<h3 class="font-medium dark:text-gray-100">{dimensionLabel('actions', action)}</h3>
					<ul class="mt-3 space-y-2">
						{#each dimensions as dimension (dimension.key)}
							<li class="flex items-center justify-between gap-3 text-sm">
								<span class="font-mono text-xs dark:text-gray-200">{dimension.key}</span>
								<span class="text-xs text-gray-500"
									>{dimension.rule_types
										.map((ruleType) => dimensionLabel('admin.pricing.ruleKinds', ruleType))
										.join(', ')}</span
								>
							</li>
						{/each}
					</ul>
				</section>
			{/each}
		</div>
	{:else}
		<div
			class="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-500 dark:border-gray-700"
		>
			{$i18n.t('credits.admin.dimensionsEmpty')}
		</div>
	{/if}
</div>
