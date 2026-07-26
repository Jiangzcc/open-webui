export type CreationScope = 'mine' | 'all';

export type CreationAvailability = 'available' | 'missing';

export type CreationReference = {
	position: number;
	content_url: string | null;
	availability: CreationAvailability;
	mime_type: string | null;
};

export type CreationSummary = {
	id: string;
	kind: 'image';
	content_url: string | null;
	availability: CreationAvailability;
	mime_type: string | null;
	caption: string | null;
	prompt_preview: string | null;
	model_name: string | null;
	task: 'text-to-image' | 'image-to-image';
	created_at: number;
	updated_at: number;
};

export type CreationPublication = {
	post_id: string;
	status: 'published' | 'withdrawn' | 'hidden';
	title: string | null;
	description: string | null;
	show_prompt: boolean;
	published_at: number;
};

export type CreationDetail = CreationSummary & {
	model_id: string | null;
	prompt: string;
	negative_prompt: string | null;
	params: Record<string, unknown> | null;
	source: 'web' | 'api' | 'chat' | 'tool';
	batch_id: string;
	references: CreationReference[];
	publication: CreationPublication | null;
};

export type AdminOwner = {
	user_id: string;
	name: string | null;
	email: string | null;
	profile_image_url: string | null;
	deleted: boolean;
};

export type AdminCreationSummary = CreationSummary & {
	owner: AdminOwner;
};

export type AdminCreationDetail = CreationDetail & {
	owner: AdminOwner;
};

export type CreationListResponse = {
	items: CreationSummary[];
	next_cursor: string | null;
};

export type AdminCreationListResponse = {
	items: AdminCreationSummary[];
	next_cursor: string | null;
};

export type CreationScopeState = {
	items: CreationSummary[];
	nextCursor: string | null;
	loaded: boolean;
	loading: boolean;
	error: Error | null;
	requestGeneration: number;
	stale: boolean;
};

export const createCreationScopeState = (initial: CreationSummary[] = []): CreationScopeState => ({
	items: [...initial],
	nextCursor: null,
	loaded: false,
	loading: false,
	error: null,
	requestGeneration: 0,
	stale: false
});

export const markCreationScopeStale = (state: CreationScopeState): void => {
	state.requestGeneration += 1;
	state.loading = false;
	state.stale = true;
};

export const beginCreationRequest = (state: CreationScopeState): number => {
	state.requestGeneration += 1;
	state.loading = true;
	state.error = null;
	return state.requestGeneration;
};

type RawPage = {
	items: CreationSummary[];
	next_cursor: string | null;
} | null;

export const applyCreationPage = (
	state: CreationScopeState,
	generation: number,
	page: RawPage,
	isFirst: boolean
): boolean => {
	if (generation !== state.requestGeneration) {
		return false;
	}

	if (page === null) {
		state.loading = false;
		state.error = new Error('creation load failed');
		return true;
	}

	const seen = new Set(state.items.map((item) => item.id));
	for (const item of page.items) {
		if (!seen.has(item.id)) {
			state.items.push(item);
			seen.add(item.id);
		}
	}

	state.nextCursor = page.next_cursor;
	state.loaded = true;
	state.loading = false;
	state.stale = false;
	state.error = null;
	return true;
};

export type RemovedCreation = {
	item: CreationSummary;
	index: number;
};

export const removeCreationOptimistically = (
	state: CreationScopeState,
	id: string
): RemovedCreation => {
	const index = state.items.findIndex((item) => item.id === id);
	if (index === -1) {
		throw new Error(`creation ${id} not found for optimistic removal`);
	}
	const [item] = state.items.splice(index, 1);
	return { item, index };
};

export const restoreCreation = (state: CreationScopeState, removed: RemovedCreation): void => {
	if (state.items.some((item) => item.id === removed.item.id)) {
		return;
	}
	const clampedIndex = Math.min(removed.index, state.items.length);
	state.items.splice(clampedIndex, 0, removed.item);
};

/**
 * Route a flat, server-ordered feed into `laneCount` vertical lanes using a
 * strict round-robin: item k falls into lane `k % laneCount`.
 *
 * Round-robin is deliberately chosen over "shortest-lane-next". Shortest-lane
 * sounds smarter, but it makes placement dependent on accumulated heights —
 * which means inserting/appending items can shift where earlier items would
 * land, defeating the entire point of leaving `columns-*` behind. Round-robin
 * is a pure function of index, so any prefix of the feed distributes to a
 * prefix of every lane: once an item is placed, rebuilding from a longer feed
 * leaves its lane and intra-lane ordinal untouched. Growth therefore proceeds
 * strictly downward at the tails, never sideways.
 */
export const assignLanes = <T>(items: readonly T[], laneCount: number): T[][] => {
	const lanes: T[][] = Array.from({ length: laneCount }, () => []);
	for (let i = 0; i < items.length; i += 1) {
		lanes[i % laneCount].push(items[i]);
	}
	return lanes;
};

/**
 * Curated subset of the backend `params` allowlist (see
 * `capture.py::_PARAM_WHITELIST`) promoted to readable chips in the detail
 * modal. Verbose prose (`system_prompt`) and operational toggles
 * (`enable_safety_checker`, `safety_tolerance`, `sync_mode`,
 * `limit_generations`, `enable_web_search`, `enable_prompt_expansion`) are
 * intentionally excluded — they drown a glance-level overview in noise the
 * viewer rarely cares about. Geometry siblings (`size`/`resolution`/
 * `aspect_ratio`) coexist because providers populate whichever axis their
 * model speaks; emitting whichever arrive costs nothing.
 */
const PARAM_TAG_ORDER = [
	'size',
	'resolution',
	'aspect_ratio',
	'quality',
	'image_count',
	'steps',
	'guidance_scale',
	'seed',
	'style',
	'output_format',
	'background',
	'acceleration',
	'input_fidelity',
	'thinking_level'
] as const;

export type ParamTag = {
	key: (typeof PARAM_TAG_ORDER)[number];
	value: string;
};

/**
 * Reduce a free-form `params` blob into a fixed-order list of display-ready
 * chips. Keys outside `PARAM_TAG_ORDER` are dropped outright; values that are
 * blank, boolean, or non-primitive (arrays/objects) are filtered so the chip
 * strip never renders a `[object Object]` or a misleading `true`. Numbers are
 * coerced to strings; strings are trimmed. Ordering obeys the curated map, not
 * the input object's enumeration order, so callers always paint the same rail
 * regardless of how the provider serialised its payload.
 */
export const extractParamTags = (
	params: Record<string, unknown> | null | undefined
): ParamTag[] => {
	if (!params) {
		return [];
	}
	const tags: ParamTag[] = [];
	for (const key of PARAM_TAG_ORDER) {
		const raw = params[key];
		if (raw === null || raw === undefined) {
			continue;
		}
		if (typeof raw === 'boolean') {
			continue;
		}
		if (Array.isArray(raw) || typeof raw === 'object') {
			continue;
		}
		if (typeof raw === 'number' && !Number.isFinite(raw)) {
			continue;
		}
		const text = String(raw).trim();
		if (!text) {
			continue;
		}
		// A numeric zero encodes absence (zero steps, zero seeds, zero count)
		// rather than a meaningful knob setting — treat it like a blank.
		if (typeof raw === 'number' && raw === 0) {
			continue;
		}
		tags.push({ key, value: text });
	}
	return tags;
};
