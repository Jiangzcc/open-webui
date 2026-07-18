import { IMAGES_API_BASE_URL } from '$lib/constants';
import type {
	GeneratedImage,
	ImageEditPayload,
	ImageGenerationPayload
} from '$lib/utils/image-generation';

type ImageGenerationOptions = {
	idempotencyKey?: string;
};

const isAbortError = (error: unknown) =>
	error instanceof DOMException && error.name === 'AbortError';

type ImageGenerationErrorCode =
	| 'insufficient_credits'
	| 'price_not_configured'
	| 'price_rule_incomplete'
	| 'idempotency_key_conflict'
	| 'usage_processing'
	| 'credit_account_conflict'
	| 'invalid_adjustment'
	| 'credit_service_unavailable'
	| 'provider_failed'
	| 'image_generation_failed';

type ImageGenerationError = {
	code: ImageGenerationErrorCode;
};

const publicCreditErrorCodes = new Set<ImageGenerationErrorCode>([
	'insufficient_credits',
	'price_not_configured',
	'price_rule_incomplete',
	'idempotency_key_conflict',
	'usage_processing',
	'credit_account_conflict',
	'invalid_adjustment',
	'credit_service_unavailable',
	'provider_failed'
]);

export const getImageGenerationErrorCode = (error: unknown): ImageGenerationErrorCode => {
	if (
		typeof error === 'object' &&
		error !== null &&
		'code' in error &&
		typeof error.code === 'string' &&
		publicCreditErrorCodes.has(error.code as ImageGenerationErrorCode)
	) {
		return error.code as ImageGenerationErrorCode;
	}

	return 'image_generation_failed';
};

const parseImageApiError = (error: unknown): ImageGenerationError => ({
	code: getImageGenerationErrorCode(error)
});

const requestImageGeneration = async (
	path: string,
	token: string,
	payload: ImageGenerationPayload | ImageEditPayload,
	options?: ImageGenerationOptions
): Promise<GeneratedImage[]> => {
	try {
		const response = await fetch(`${IMAGES_API_BASE_URL}${path}`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` }),
				...(options?.idempotencyKey && { 'Idempotency-Key': options.idempotencyKey })
			},
			body: JSON.stringify(payload)
		});

		if (!response.ok) {
			throw await response.json().catch(() => null);
		}

		return (await response.json()) as GeneratedImage[];
	} catch (error) {
		if (isAbortError(error)) {
			throw error;
		}
		throw parseImageApiError(error);
	}
};

export const createImageGeneration = async (
	token: string = '',
	payload: ImageGenerationPayload,
	options?: ImageGenerationOptions
) => requestImageGeneration('/generations', token, payload, options);

export const editImageGeneration = async (
	token: string = '',
	payload: ImageEditPayload,
	options?: ImageGenerationOptions
) => requestImageGeneration('/edit', token, payload, options);
