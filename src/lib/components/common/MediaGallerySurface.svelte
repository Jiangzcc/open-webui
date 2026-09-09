<div
	class="media-gallery-surface min-h-0 min-w-0 flex-1 overflow-y-auto text-slate-950 dark:text-slate-100"
>
	<slot />
</div>

<style>
	.media-gallery-surface {
		/* 筛选加载期间内容会暂时变短，固定预留滚动条槽位以避免标题栏水平位移。 */
		scrollbar-gutter: stable;
		background-color: #f2f4f7;
		background-image:
			radial-gradient(circle at 14% -8%, rgb(255 255 255 / 0.96), transparent 30rem),
			radial-gradient(circle at 86% 0%, rgb(91 110 225 / 0.08), transparent 26rem);
	}

	:global(.dark) .media-gallery-surface {
		background-color: #0b0e14;
		background-image:
			radial-gradient(circle at 16% -10%, rgb(60 72 105 / 0.22), transparent 30rem),
			radial-gradient(circle at 86% 0%, rgb(91 110 225 / 0.12), transparent 28rem);
	}

	@media (prefers-reduced-transparency: reduce) {
		.media-gallery-surface,
		:global(.dark) .media-gallery-surface {
			background-image: none;
		}
	}
</style>
