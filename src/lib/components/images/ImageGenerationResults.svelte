<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { deleteImageGenerationTask } from '$lib/apis/creations/generation-tasks';
	import ImagePreview from '$lib/components/common/ImagePreview.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Loader from '$lib/components/common/Loader.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import ImageBatchCard from './ImageBatchCard.svelte';
	import type { GeneratedImage, ImageGenerationModel } from '$lib/utils/image-generation';
	import type { ImageGenerationBatch } from '$lib/utils/image-generation-batches';
	import { downloadGeneratedImage, downloadGenerationBatch } from './imageDownloads';
	import { getI18nContext } from '$lib/i18n/context';

	const i18n = getI18nContext();

	export let batches: ImageGenerationBatch[];
	export let models: ImageGenerationModel[];
	export let canHover: boolean;
	export let supportsEditing: boolean;
	export let elapsedNow: number;
	export let hasMore: boolean;
	export let loadingMore: boolean;
	export let onReuseAsReference: (batch: ImageGenerationBatch, image: GeneratedImage) => void;
	export let onRemix: (batch: ImageGenerationBatch, image: GeneratedImage) => void;
	export let onEditAgain: (batch: ImageGenerationBatch) => void;
	export let onRegenerate: (batch: ImageGenerationBatch) => void;
	export let onBatchRemoved: (batchId: string) => void;
	export let onLoadMore: () => void;
	export let onViewOlder: () => void;

	let downloadingIds = new Set<string>();
	let deletingIds = new Set<string>();
	let batchToDelete: ImageGenerationBatch | null = null;
	let showDeleteConfirm = false;
	let showPreview = false;
	let previewUrl = '';
	let previewAlt = '';

	const openPreview = (image: GeneratedImage) => {
		previewUrl = image.url;
		previewAlt = image.prompt ?? $i18n.t('Generated image');
		showPreview = true;
	};

	const downloadImage = async (image: GeneratedImage, index: number) => {
		try {
			await downloadGeneratedImage(image, index);
		} catch {
			toast.error($i18n.t('Failed to download image'));
		}
	};

	const downloadBatch = async (batch: ImageGenerationBatch) => {
		if (!batch.images.length || downloadingIds.has(batch.id)) return;
		downloadingIds = new Set(downloadingIds).add(batch.id);
		try {
			await downloadGenerationBatch(batch);
		} catch {
			toast.error($i18n.t('Failed to download images'));
		} finally {
			const next = new Set(downloadingIds);
			next.delete(batch.id);
			downloadingIds = next;
		}
	};

	const requestDelete = (batch: ImageGenerationBatch) => {
		if (deletingIds.has(batch.id)) return;
		batchToDelete = batch;
		showDeleteConfirm = true;
	};

	const confirmDelete = async () => {
		const batch = batchToDelete;
		batchToDelete = null;
		if (!batch) return;
		deletingIds = new Set(deletingIds).add(batch.id);
		try {
			await deleteImageGenerationTask(localStorage.token, batch.id);
			onBatchRemoved(batch.id);
			toast.success($i18n.t('Record removed'));
		} catch {
			toast.error($i18n.t('Failed to remove record'));
		} finally {
			const next = new Set(deletingIds);
			next.delete(batch.id);
			deletingIds = next;
		}
	};
</script>

{#if batches.length === 0}
	<section class="flex min-h-[calc(100dvh-20rem)] items-center justify-center py-12">
		<div class="px-4 text-center">
			<div
				class="mx-auto mb-5 flex size-16 items-center justify-center rounded-[1.5rem] bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200"
			>
				<Sparkles className="size-7" strokeWidth="1.75" />
			</div>
			<h1
				class="text-3xl font-semibold tracking-tight text-gray-900 md:text-4xl dark:text-gray-100"
			>
				{$i18n.t('What do you want to create?')}
			</h1>
			<p class="mt-3 text-base text-gray-500 dark:text-gray-400">
				{$i18n.t('Describe an image, or upload a reference image to create a new version.')}
			</p>
		</div>
	</section>
{:else}
	<section class="space-y-4 pb-6 pt-4 sm:pt-8" aria-live="polite">
		{#each batches as batch (batch.id)}
			<ImageBatchCard
				{batch}
				{models}
				{canHover}
				{supportsEditing}
				{elapsedNow}
				downloading={downloadingIds.has(batch.id)}
				deleting={deletingIds.has(batch.id)}
				onPreview={openPreview}
				onDownloadImage={downloadImage}
				{onReuseAsReference}
				{onRemix}
				{onEditAgain}
				{onRegenerate}
				onDownloadBatch={downloadBatch}
				onRemove={requestDelete}
			/>
		{/each}
		<div class="flex justify-center py-4">
			{#if hasMore}
				{#if loadingMore}<Spinner className="size-5" />{:else}<Loader
						on:visible={onLoadMore}
					/>{/if}
			{:else}
				<button
					type="button"
					class="min-h-11 text-xs text-gray-400 transition hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
					on:click={onViewOlder}
				>
					{$i18n.t('View older creations in Assets')}
				</button>
			{/if}
		</div>
	</section>
{/if}

<ConfirmDialog
	bind:show={showDeleteConfirm}
	title={$i18n.t('Remove record?')}
	message={$i18n.t('Remove this record from your history?')}
	confirmLabel={$i18n.t('Remove')}
	onConfirm={confirmDelete}
/>

<ImagePreview bind:show={showPreview} src={previewUrl} alt={previewAlt} />
