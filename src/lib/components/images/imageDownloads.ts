import { blobExtension, downloadBlob, zipAndDownload } from '$lib/utils/download';
import type { GeneratedImage } from '$lib/utils/image-generation';
import type { ImageGenerationBatch } from '$lib/utils/image-generation-batches';

export const downloadGeneratedImage = async (
	image: GeneratedImage,
	index: number
): Promise<void> => {
	const response = await fetch(image.url);
	if (!response.ok) throw new Error('download failed');
	const blob = await response.blob();
	downloadBlob(
		blob,
		`generated-image-${image.createdAt ?? Date.now()}-${index + 1}.${blobExtension(blob)}`
	);
};

export const downloadGenerationBatch = (batch: ImageGenerationBatch): Promise<void> =>
	zipAndDownload(
		batch.images.map((image) => ({
			url: image.url,
			filename: (index: number, blob: Blob) =>
				`${String(index + 1).padStart(2, '0')}.${blobExtension(blob)}`
		})),
		`generation-${batch.createdAt ?? Date.now()}.zip`
	);
