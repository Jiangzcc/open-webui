import type { ImageQuote, ImageQuoteInput } from '$lib/apis/credits';

export type ImageQuoteStatus =
	| 'loading'
	| 'ready'
	| 'insufficient'
	| 'unconfigured'
	| 'error'
	| 'exempt';

export type ImageQuoteState = {
	status: ImageQuoteStatus;
	chargedCredits?: number;
	errorCode?: string;
};

export type ImageQuoteRequest = ImageQuoteInput;

type QuoteImageCredits = (input: ImageQuoteRequest, signal: AbortSignal) => Promise<ImageQuote>;

type ImageQuoteStateOptions = {
	quote: QuoteImageCredits;
	debounceMs?: number;
	onChange?: (state: ImageQuoteState) => void;
};

const defaultState: ImageQuoteState = { status: 'loading' };

export const isImageQuoteSubmittable = (state: Pick<ImageQuoteState, 'status'>) =>
	state.status === 'ready' || state.status === 'exempt';

export const createImageSubmissionIdempotency = (createKey = () => crypto.randomUUID()) => {
	const idempotencyKey = createKey();

	return {
		idempotencyKey,
		run: <T>(request: (key: string) => Promise<T>) => request(idempotencyKey)
	};
};

export const quoteErrorMessage = (error: unknown) => {
	if (typeof error === 'object' && error !== null && 'code' in error) {
		if (error.code === 'insufficient_credits') {
			return 'Insufficient credits';
		}
	}

	return 'Credit service is unavailable';
};

const quoteStateFromResponse = (quote: ImageQuote): ImageQuoteState => {
	if (quote.exempt) {
		return { status: 'exempt', chargedCredits: 0 };
	}
	if (!quote.configured) {
		return { status: 'unconfigured', errorCode: quote.error ?? undefined };
	}
	if (!quote.sufficient) {
		return { status: 'insufficient', chargedCredits: quote.charged_credits ?? undefined };
	}
	if (quote.charged_credits === null) {
		return { status: 'error' };
	}

	return { status: 'ready', chargedCredits: quote.charged_credits };
};

export const createImageQuoteState = ({
	quote,
	debounceMs = 275,
	onChange
}: ImageQuoteStateOptions) => {
	let state = defaultState;
	let timer: ReturnType<typeof setTimeout> | undefined;
	let controller: AbortController | undefined;
	let generation = 0;

	const setState = (nextState: ImageQuoteState) => {
		state = nextState;
		onChange?.(state);
	};

	const requestQuote = async (input: ImageQuoteRequest, currentGeneration: number) => {
		controller?.abort();
		controller = new AbortController();
		setState({ status: 'loading' });

		const requestController = controller;
		try {
			const response = await quote(input, requestController.signal);
			if (currentGeneration === generation) {
				setState(quoteStateFromResponse(response));
			}
		} catch (error) {
			if (currentGeneration === generation && !requestController.signal.aborted) {
				setState({ status: 'error', errorCode: quoteErrorMessage(error) });
			}
		}
	};

	const schedule = (input: ImageQuoteRequest) => {
		generation += 1;
		const currentGeneration = generation;
		if (timer) {
			clearTimeout(timer);
		}
		controller?.abort();
		setState({ status: 'loading' });
		timer = setTimeout(() => {
			void requestQuote(input, currentGeneration);
		}, debounceMs);
	};

	const dispose = () => {
		if (timer) {
			clearTimeout(timer);
		}
		controller?.abort();
	};

	return {
		get value() {
			return state;
		},
		schedule,
		dispose
	};
};
