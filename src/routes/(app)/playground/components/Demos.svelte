<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { WEBUI_NAME, showSidebar, mobile } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';

	const i18n = getContext<Writable<i18nType>>('i18n');

	// 分类目录，点击平滑滚动到对应锚点
	type Category = { id: string; label: string };
	let categories: Category[] = [];
	$: categories = [
		{ id: 'display', label: $i18n.t('Display Components') },
		{ id: 'buttons', label: $i18n.t('Button Components') },
		{ id: 'inputs', label: $i18n.t('Input Components') },
		{ id: 'selects', label: $i18n.t('Select Components') },
		{ id: 'overlays', label: $i18n.t('Overlay Components') },
		{ id: 'navigation', label: $i18n.t('Navigation Components') },
		{ id: 'media', label: $i18n.t('Media & Preview') },
		{ id: 'files', label: $i18n.t('Files & Lists') },
		{ id: 'editors', label: $i18n.t('Editors & Forms') },
		{ id: 'tools', label: $i18n.t('Tool Calls') },
		{ id: 'icons', label: $i18n.t('Icons') }
	];

	let activeCategory = 'display';

	const scrollTo = (id: string) => {
		activeCategory = id;
		document
			.getElementById(`section-${id}`)
			?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	};
</script>

<svelte:head>
	<title>
		{$i18n.t('Components')} / {$i18n.t('Playground')} / {$WEBUI_NAME}
	</title>
</svelte:head>

<!-- 仅由 +page.svelte 在开发构建中动态挂载（管理员 + DEV 门控），无需自身守卫 -->
<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	<nav class="pb-1 px-2.5 pt-2 backdrop-blur-xl drag-region select-none">
		<div class="flex items-center gap-0.5 md:gap-1">
			{#if $mobile}
				<div class="{$showSidebar ? 'md:hidden' : ''} self-center flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							id="sidebar-toggle-button"
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							aria-label={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
							on:click={() => {
								showSidebar.set(!$showSidebar);
							}}
						>
							<div class="self-center p-1.5">
								<Sidebar className="size-4" />
							</div>
						</button>
					</Tooltip>
				</div>
			{/if}

			<div class="flex w-full items-center gap-2">
				<a
					draggable="false"
					class="min-w-fit px-1 text-sm text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white transition select-none"
					href="/playground">{$i18n.t('Playground')}</a
				>
				<span class="text-gray-300 dark:text-gray-600 text-sm select-none">/</span>
				<span class="min-w-fit px-1 text-sm select-none">{$i18n.t('Components')}</span>
			</div>
		</div>
	</nav>

	<div class="flex-1 max-h-full overflow-y-auto">
		<div class="flex flex-col md:flex-row w-full max-w-full">
			<!-- 侧边目录：桌面端固定窄列，移动端顶部水平横滚 -->
			<aside
				class="md:w-52 md:shrink-0 md:sticky md:top-0 md:self-start border-b md:border-b-0 md:border-r border-gray-100 dark:border-gray-850 bg-white/80 dark:bg-gray-900/80 backdrop-blur z-10"
			>
				<div
					class="md:p-3 flex md:flex-col gap-1 overflow-x-auto md:overflow-y-auto md:max-h-full p-2"
				>
					{#each categories as cat (cat.id)}
						<button
							class="text-left whitespace-nowrap md:whitespace-normal px-2.5 py-1.5 rounded-lg text-xs transition {activeCategory ===
							cat.id
								? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-medium'
								: 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-850'}"
							on:click={() => scrollTo(cat.id)}
						>
							{cat.label}
						</button>
					{/each}
				</div>
			</aside>

			<main class="flex-1 min-w-0 p-4 md:p-6 space-y-12">
				<!-- ============================================ -->
				<!-- 展示类组件 -->
				<!-- ============================================ -->
				<section id="section-display" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Display Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Pure visual primitives: badges, loaders, marquee, etc.')}
					</p>

					<!-- 演示卡片网格 -->
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						<!-- 演示卡片：统一外壳，便于对比 -->
						{#await import('./_components/BadgeDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SpinnerDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/MarqueeDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/LoaderDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/OverlayDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/TooltipDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 按钮类组件 -->
				<!-- ============================================ -->
				<section id="section-buttons" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Button Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Action triggers: submit, create, access, etc.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						{#await import('./_components/AccessButtonDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/GenerationSubmitButtonDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SplitCreateButtonDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 输入类组件 -->
				<!-- ============================================ -->
				<section id="section-inputs" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Input Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Text, sensitive, toggle, checkbox inputs.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#await import('./_components/CheckboxDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SwitchDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/TextareaDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SensitiveInputDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/TagsDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 选择类组件 -->
				<!-- ============================================ -->
				<section id="section-selects" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Select Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Native and custom dropdown selectors.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#await import('./_components/NativeSelectDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SettingsSelectDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SelectDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SelectorDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/DropdownOptionsDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/MultiSelectDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/DropdownDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/DropdownSubDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 浮层类组件 -->
				<!-- ============================================ -->
				<section id="section-overlays" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Overlay Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Modal, drawer, confirm dialog. Click buttons to open.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						{#await import('./_components/ModalDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/DrawerDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/ConfirmDialogDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 导航类组件 -->
				<!-- ============================================ -->
				<section id="section-navigation" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Navigation Components')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Collapsible, pagination, sidebar.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#await import('./_components/CollapsibleDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/PaginationDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SidebarDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 媒体预览类 -->
				<!-- ============================================ -->
				<section id="section-media" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Media & Preview')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Image, full-screen preview, slideshow, SVG pan/zoom, iframe.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						{#await import('./_components/ImageDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/ImagePreviewDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SlideShowDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/SVGPanZoomDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/PanzoomContainerDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/FullHeightIframeDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 文件与列表类 -->
				<!-- ============================================ -->
				<section id="section-files" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Files & Lists')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('File rows, folders, chat list, banners. Mock data, no backend.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#await import('./_components/FileItemDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/FolderDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/ChatListDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/BannerDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 编辑器与表单类 -->
				<!-- ============================================ -->
				<section id="section-editors" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Editors & Forms')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Rich text, code editor, code modal, JSON-Schema form.')}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#await import('./_components/RichTextInputDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/CodeEditorDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/CodeEditorModalDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/ValvesDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 工具调用 -->
				<!-- ============================================ -->
				<section id="section-tools" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Tool Calls')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t('Tool-call display: executing / done states. Mock attributes.')}
					</p>

					<div class="grid grid-cols-1 gap-3">
						{#await import('./_components/ToolCallDisplayDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<!-- ============================================ -->
				<!-- 图标 -->
				<!-- ============================================ -->
				<section id="section-icons" class="scroll-mt-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
						{$i18n.t('Icons')}
					</h2>
					<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
						{$i18n.t(
							'All SVG icon components under $lib/components/icons. Click to copy import statement.'
						)}
					</p>

					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-3">
						{#await import('./_components/EmojiDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/VendorLogoDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}

						{#await import('./_components/DragGhostDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>

					<div class="grid grid-cols-1 gap-3">
						{#await import('./_components/IconsDemo.svelte')}
							<div class="h-28 animate-pulse bg-gray-100 dark:bg-gray-800 rounded-xl"></div>
						{:then Component}
							<Component.default />
						{/await}
					</div>
				</section>

				<div class="h-8"></div>
			</main>
		</div>
	</div>
</div>
