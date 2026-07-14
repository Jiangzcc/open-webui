import { IMAGES_API_BASE_URL } from '$lib/constants';
import type { ImageEditPayload, ImageGenerationPayload } from '$lib/utils/image-generation';

const parseImageApiError = (err: any) => {
	if ('detail' in err) {
		if (Array.isArray(err.detail)) {
			return err.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(', ');
		}

		return err.detail;
	}

	return 'Server connection failed';
};

export const createImageGeneration = async (
	token: string = '',
	payload: ImageGenerationPayload
) => {
	let error = null;

	const res = await fetch(`${IMAGES_API_BASE_URL}/generations`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(payload)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = parseImageApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const editImageGeneration = async (token: string = '', payload: ImageEditPayload) => {
	let error = null;

	const res = await fetch(`${IMAGES_API_BASE_URL}/edit`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(payload)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = parseImageApiError(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
