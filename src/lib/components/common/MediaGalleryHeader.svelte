<script lang="ts">
	import MediaGalleryNavigation from './MediaGalleryNavigation.svelte';

	export let title = '';
	export let items: ReadonlyArray<{ value: string; label: string }> = [];
	export let selected = '';
	export let ariaLabel = '';
	export let idPrefix = 'media-gallery-header-tab';
	export let divider = true;
	export let onSelect: (value: string) => void = () => {};
</script>

<header
	class="media-gallery-header sticky top-0 z-20 shrink-0 {divider
		? 'media-gallery-header--divided'
		: ''}"
>
	<div class="relative z-[1] mx-auto w-full max-w-[96rem] px-4 sm:px-6 lg:px-8">
		<div class="flex h-[52px] min-w-0 items-center gap-3 sm:gap-5">
			<h1
				class="shrink-0 text-xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-[22px] dark:text-slate-50"
			>
				{title}
			</h1>

			{#if items.length > 1}
				<MediaGalleryNavigation
					{items}
					{selected}
					{ariaLabel}
					{idPrefix}
					className="ml-auto min-w-0"
					{onSelect}
				/>
			{/if}
		</div>

		<slot />
	</div>
</header>

<style>
	.media-gallery-header {
		isolation: isolate;
		background:
			linear-gradient(135deg, rgb(255 255 255 / 0.72), rgb(244 247 252 / 0.48)),
			rgb(239 243 248 / 0.4);
		-webkit-backdrop-filter: blur(24px) saturate(165%) contrast(1.03);
		backdrop-filter: blur(24px) saturate(165%) contrast(1.03);
		box-shadow:
			inset 0 1px 0 rgb(255 255 255 / 0.9),
			inset 0 -1px 0 rgb(255 255 255 / 0.26),
			0 10px 34px rgb(69 84 118 / 0.06);
	}

	.media-gallery-header::before {
		position: absolute;
		inset: 0;
		z-index: 0;
		background:
			radial-gradient(circle at 12% 0%, rgb(255 255 255 / 0.78), transparent 34%),
			linear-gradient(90deg, rgb(255 255 255 / 0.2), transparent 45%, rgb(91 110 225 / 0.035));
		content: '';
		pointer-events: none;
	}

	.media-gallery-header--divided::after {
		position: absolute;
		inset-inline: 0;
		bottom: 0;
		z-index: 2;
		height: 1px;
		background: linear-gradient(
			90deg,
			transparent,
			rgb(100 116 139 / 0.2) 16%,
			rgb(100 116 139 / 0.2) 84%,
			transparent
		);
		content: '';
		pointer-events: none;
	}

	:global(.dark) .media-gallery-header {
		background:
			linear-gradient(135deg, rgb(31 38 52 / 0.72), rgb(12 16 24 / 0.58)), rgb(11 14 20 / 0.56);
		box-shadow:
			inset 0 1px 0 rgb(255 255 255 / 0.12),
			inset 0 -1px 0 rgb(255 255 255 / 0.035),
			0 12px 38px rgb(2 6 23 / 0.2);
	}

	:global(.dark) .media-gallery-header::before {
		background:
			radial-gradient(circle at 12% 0%, rgb(255 255 255 / 0.09), transparent 34%),
			linear-gradient(90deg, rgb(255 255 255 / 0.025), transparent 45%, rgb(91 110 225 / 0.07));
	}

	:global(.dark) .media-gallery-header--divided::after {
		background: linear-gradient(
			90deg,
			transparent,
			rgb(255 255 255 / 0.1) 16%,
			rgb(255 255 255 / 0.1) 84%,
			transparent
		);
	}

	@media (prefers-reduced-transparency: reduce) {
		.media-gallery-header {
			background: rgb(247 249 252 / 0.98);
			-webkit-backdrop-filter: none;
			backdrop-filter: none;
		}

		:global(.dark) .media-gallery-header {
			background: rgb(14 18 26 / 0.98);
		}
	}
</style>
