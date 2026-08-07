import type { ImageGenerationModel } from '$lib/utils/image-generation';

export const groupByVendor = (
	models: ImageGenerationModel[]
): Record<string, ImageGenerationModel[]> => {
	const groups: Record<string, ImageGenerationModel[]> = {};
	for (const model of models) {
		const vendor = model.provider ?? 'other';
		(groups[vendor] ??= []).push(model);
	}
	return groups;
};

export const vendorLogoUrl = (provider: string): string => `/assets/vendors/${provider}.webp`;

export const isProxyModel = (model: ImageGenerationModel): boolean => model.hosting === 'proxy';

/**
 * Drop the leading vendor segment from a model's display name.
 *
 * Back-end names follow `Provider / Model Short Name` (e.g. `Alibaba / Qwen Image`).
 * Since the brand column already shows the vendor, repeating it in the model column
 * is noise — strip only the first ` / `-delimited segment and keep the rest intact
 * (so a model name that legitimately contains ` / ` is preserved). Falls back to the
 * model id when the name is missing or empty.
 */
export const stripVendorFromName = (
	model: Pick<ImageGenerationModel, 'id' | 'name'> & { provider?: string | null }
): string => {
	const segments = (model.name ?? '').split(' / ');
	let stripped = segments.length > 1 ? segments.slice(1).join(' / ').trim() : (model.name ?? '');
	const provider = model.provider?.trim();
	if (provider) {
		const escapedProvider = provider.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
		stripped = stripped.replace(new RegExp(`^${escapedProvider}\\s+`, 'i'), '');
	}
	return stripped || model.id;
};
