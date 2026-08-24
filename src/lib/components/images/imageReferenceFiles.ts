import { filterImageFiles } from '$lib/utils/image-generation';

export const MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024;

export type ReferenceImage = { url: string; name: string };
export type ReferenceRejectionReason = 'unsupported_type' | 'too_large' | 'too_many';
export type ReferenceFileFeedback = {
	key: string;
	values?: { count: number };
};

export const referenceFileFeedback = (
	rejected: Set<ReferenceRejectionReason>,
	maxCount: number
): ReferenceFileFeedback[] => [
	...(rejected.has('unsupported_type') ? [{ key: 'Only image files are supported.' }] : []),
	...(rejected.has('too_large') ? [{ key: 'Images must be smaller than 10 MB.' }] : []),
	...(rejected.has('too_many')
		? [{ key: 'You can attach up to {{count}} reference images.', values: { count: maxCount } }]
		: [])
];

const readFileAsDataUrl = (file: File): Promise<string> =>
	new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = (event) => {
			if (typeof event.target?.result === 'string') resolve(event.target.result);
			else reject(new Error('Invalid file content'));
		};
		reader.onerror = () => reject(reader.error ?? new Error('Failed to read file'));
		reader.readAsDataURL(file);
	});

export const loadReferenceFiles = async (
	files: File[],
	remainingSlots: number,
	fallbackName: string
): Promise<{ images: ReferenceImage[]; rejected: Set<ReferenceRejectionReason> }> => {
	const filtered = filterImageFiles(files, {
		maxCount: remainingSlots,
		maxBytes: MAX_REFERENCE_IMAGE_BYTES
	});
	const images = await Promise.all(
		filtered.accepted.map(async (file) => ({
			url: await readFileAsDataUrl(file as File),
			name: file.name || fallbackName
		}))
	);
	return { images, rejected: new Set(filtered.rejected.map((item) => item.reason)) };
};

export const resolveDraftReferenceImage = async (url: string, token: string): Promise<string> => {
	if (/^(data:|https?:\/\/)/.test(url)) return url;
	const response = await fetch(url, { headers: { authorization: `Bearer ${token}` } });
	if (!response.ok) throw new Error('reference image unavailable');
	const blob = await response.blob();
	if (!blob.type.startsWith('image/') || blob.size > MAX_REFERENCE_IMAGE_BYTES) {
		throw new Error('invalid reference image');
	}
	return readFileAsDataUrl(
		new File([blob], 'previous-creation', { type: blob.type || 'image/png' })
	);
};
