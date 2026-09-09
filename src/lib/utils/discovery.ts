export type DiscoverySort = 'featured' | 'latest' | 'popular';
export type DiscoveryFeed = DiscoverySort | 'favorites';
export type DiscoveryCategory = string;

export type DiscoveryCategoryItem = {
	id: DiscoveryCategory;
	display_name: string;
	enabled: boolean;
	sort_order: number;
};

export type DiscoveryCategoryUpdateInput = Partial<
	Pick<DiscoveryCategoryItem, 'display_name' | 'enabled' | 'sort_order'>
>;

export type DiscoveryCategoryCreateInput = Pick<
	DiscoveryCategoryItem,
	'display_name' | 'enabled' | 'sort_order'
>;

export type PublicOwner = {
	user_id: string;
	name: string | null;
	profile_image_url: string | null;
	deleted: boolean;
};

export type DiscoveryPostSummary = {
	id: string;
	title: string | null;
	description: string | null;
	content_url: string | null;
	poster_url: string | null;
	kind: 'image' | 'video';
	duration_seconds: number | null;
	// 归一化比例（如 '16:9'）：瀑布流用它做渲染前的均衡分列。
	aspect_ratio?: string | null;
	availability: 'available' | 'missing';
	mime_type: string | null;
	prompt_preview: string | null;
	model_name: string | null;
	owner: PublicOwner;
	like_count: number;
	favorite_count: number;
	liked: boolean;
	favorited: boolean;
	published_at: number;
	category: DiscoveryCategory;
	featured: boolean;
	featured_rank: number;
};

export type DiscoveryOperationInput = {
	category?: DiscoveryCategory;
	featured?: boolean;
	featured_rank?: number;
};

export type CreationPublication = {
	post_id: string;
	status: 'published' | 'withdrawn' | 'hidden';
	title: string | null;
	description: string | null;
	show_prompt: boolean;
	category: DiscoveryCategory;
	featured: boolean;
	featured_rank: number;
	published_at: number;
};

export type DiscoveryPostDetail = DiscoveryPostSummary & {
	model_id: string | null;
	prompt: string | null;
	negative_prompt: string | null;
	params: Record<string, unknown> | null;
	task: 'text-to-image' | 'image-to-image' | 'text-to-video' | 'image-to-video' | 'video-to-video';
};

export type DiscoveryPostListResponse = {
	items: DiscoveryPostSummary[];
	next_cursor: string | null;
};

export type ReactionKind = 'like' | 'favorite';

export type ReactionState = {
	post_id: string;
	kind: ReactionKind;
	active: boolean;
	like_count: number;
	favorite_count: number;
};

export type DiscoveryFeedState = {
	items: DiscoveryPostSummary[];
	nextCursor: string | null;
	loaded: boolean;
	loading: boolean;
	error: Error | null;
	requestGeneration: number;
};

export const createDiscoveryFeedState = (
	initial: DiscoveryPostSummary[] = []
): DiscoveryFeedState => ({
	items: [...initial],
	nextCursor: null,
	loaded: initial.length > 0,
	loading: false,
	error: null,
	requestGeneration: 0
});

export const beginDiscoveryRequest = (state: DiscoveryFeedState): number => {
	state.requestGeneration += 1;
	state.loading = true;
	state.error = null;
	return state.requestGeneration;
};

export const applyDiscoveryPage = (
	state: DiscoveryFeedState,
	generation: number,
	page: DiscoveryPostListResponse | null,
	isFirst: boolean
): boolean => {
	if (generation !== state.requestGeneration) return false;
	if (page === null) {
		state.loading = false;
		state.error = new Error('discovery load failed');
		return true;
	}
	if (isFirst) state.items = [];
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
	state.error = null;
	return true;
};

export const applyReactionState = (item: DiscoveryPostSummary, reaction: ReactionState): void => {
	item.like_count = reaction.like_count;
	item.favorite_count = reaction.favorite_count;
	if (reaction.kind === 'like') item.liked = reaction.active;
	else item.favorited = reaction.active;
};
