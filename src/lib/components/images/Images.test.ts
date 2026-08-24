import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const read = (relative: string) =>
	readFileSync(fileURLToPath(new URL(relative, import.meta.url)), 'utf-8');

// 拆分后页面源码分布在多个文件：主页面（状态/提交/轮询）、表单（模型/参数/
// 选项面板）、结果卡片（batch 展示）与共享的幂等键实现。
const source = read('./Images.svelte');
const form = read('./ImagePromptForm.svelte');
const card = read('./ImageBatchCard.svelte');
const navigation = read('./ImagePageNavigation.svelte');
const commonNavigation = read('../common/GenerationPageNavigation.svelte');
const results = read('./ImageGenerationResults.svelte');
const library = read('./ImageLibraryPanel.svelte');
const pageState = read('./imagePageState.ts');
const draftState = read('./imageDraftState.ts');
const taskHistory = read('./imageTaskHistory.ts');
const referenceFiles = read('./imageReferenceFiles.ts');
const submission = read('./imageSubmission.ts');
const idempotency = read('../../utils/submission-idempotency.ts');
const all = [
	source,
	form,
	card,
	navigation,
	commonNavigation,
	results,
	library,
	pageState,
	draftState,
	taskHistory,
	referenceFiles,
	submission,
	idempotency
].join('\n');

describe('images page controls', () => {
	test('does not expose user cancellation for image generation tasks', () => {
		expect(all).not.toContain('cancelImageGenerationTask');
		expect(all).not.toContain('cancelGenerationBatch');
		expect(all).not.toContain("$i18n.t('Cancel generation')");
	});

	test('uses concise option headings and omits generation mode helper text', () => {
		expect(form).toContain("$i18n.t('Ratio')");
		expect(form).toContain("$i18n.t('Resolution')");
		expect(form).toContain("$i18n.t('Quantity')");
		expect(all).not.toContain("$i18n.t('Select aspect ratio')");
		expect(all).not.toContain(': modeLabel}');
	});

	test('renders only model-advertised advanced controls in a responsive disclosure', () => {
		expect(form).toContain('{#if hasAdvancedSettings}');
		expect(form).toContain('aria-controls="image-advanced-settings"');
		expect(form).toContain('class="mt-2 grid min-w-0 gap-4 sm:grid-cols-2"');
		expect(form).toContain('{#if seedField}');
		expect(form).toContain('{#if stepsField}');
		expect(form).toContain('{#if guidanceScaleField}');
		expect(form).toContain('{#if strengthField}');
		expect(form).toContain('{#if negativePromptField}');
		expect(all).not.toContain('enable_safety_checker');
		expect(all).not.toContain('sync_mode');
	});

	test('keeps advanced touch controls large and blocks invalid numeric submissions', () => {
		expect(form).toContain('class="flex min-h-11 w-full');
		expect(form).toContain('class="mt-1 min-h-11 w-full');
		expect(form).toContain('advancedSettingsInvalid ||');
		expect(source).toContain("toast.error($i18n.t('Check the advanced settings'))");
	});

	test('uses auto without ratio or resolution icons in the selected options', () => {
		const composerStart = form.indexOf(
			'class="mt-2 flex min-w-0 items-center justify-between gap-2"'
		);
		const composerEnd = form.indexOf('</form>', composerStart);
		const composer = form.slice(composerStart, composerEnd);

		// Auto 文案映射集中在 imageLabels.ts，由表单包一层 $i18n.t 渲染。
		const labels = read('./imageLabels.ts');
		expect(labels).toContain("ratio === DEFAULT_IMAGE_ASPECT_RATIO ? 'Auto' : ratio");
		expect(composer).not.toMatch(/getAspectRatioPreviewClass\(\s*selectedAspectRatio\s*\)/);
		expect(composer).not.toContain('getAspectRatioPreviewStyle(selectedAspectRatio)');
		expect(all).not.toContain('<ArrowsPointingOut');
		expect(all).not.toContain('<Grid');
	});

	test('uses compact illustrative ratio thumbnails instead of exact large ratios', () => {
		expect(form).toContain('const previewSize = 20;');
		expect(form).toContain('const minimumPreviewSize = 12;');
		expect(form).toContain('Math.max(minimumPreviewSize');
	});

	test('shows only the model name in the trigger but keeps the provider in popup options', () => {
		expect(source).toContain('getImageModelDisplayName');
		expect(source).toContain('getImageModelDisplayName(selectedModelConfig)');
		// popup 选项剥掉厂商前缀只留模型短名(trigger 仍走 getImageModelDisplayName)；
		// 内联映射现走 stripVendorFromName(model)，由共享 GenerationModelSelector 渲染短名。
		expect(form).toContain('name: stripVendorFromName(model)');
		expect(all).not.toContain('getImageModelDisplayName(model)');
	});

	test('shows operation metadata only while choosing a model', () => {
		// recommended / tags / maintenance 现作为 SelectableModel 字段传入共享
		// GenerationModelSelector，由后者内联渲染；页面不再直接写 {#if model.recommended}。
		expect(form).toContain('recommended: model.recommended');
		expect(form).toContain('tags: model.tags');
		expect(form).toContain('maintenance: model.maintenanceMessage');
		expect(all).not.toContain('selectedModelConfig?.recommended');
		expect(all).not.toContain('selectedModelConfig?.tags');
		expect(all).not.toContain('selectedModelConfig?.maintenanceMessage');
	});

	test('mobile page header carries the sidebar toggle and the tabs together', () => {
		// 移动端：侧栏图标与创作/我的作品 tab 同处顶部 nav 一行，顶到页面最上面，
		// 不再让 tab 浮在侧栏图标下方单独一行。桌面端 tab 仍浮动在内容区顶部、不进 nav。
		const navStart = commonNavigation.indexOf('<nav');
		const navEnd = commonNavigation.indexOf('</nav>', navStart);
		const nav = commonNavigation.slice(navStart, navEnd);

		expect(nav).toContain('SidebarIcon');
		expect(nav).toContain('{@render pageTabs()}');
		expect(all).not.toContain('bind:this={modelSelectorElement}');
	});

	test('quotes the selected or default model before a prompt is entered', () => {
		expect(pageState).toContain("export const CREDIT_QUOTE_PLACEHOLDER_PROMPT = 'credit-quote'");
		expect(pageState).toContain('prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT');
		expect(source).not.toContain('quotePrompt: string');
		expect(source).toContain('$: selectedModelConfig =');
		expect(source).toContain(
			'primaryModels.find((model) => model.isDefault && model.enabled !== false)'
		);
		expect(source).toContain('buildImageQuoteInput(\n\t\tselectedAspectRatio,');
		expect(source).toContain(
			'\n\t\treferenceImages.map((image) => image.url),\n\t\tcustomSizeValue\n\t)'
		);
		expect(source).toContain('$: if (loaded && quoteInput) {');
	});

	test('uses a generic localized error instead of stringifying submission API errors', () => {
		const submitHandlerStart = source.indexOf('const submitHandler = async () => {');
		const submitHandlerEnd = source.indexOf('\n\tonMount', submitHandlerStart);
		const submitHandler = source.slice(submitHandlerStart, submitHandlerEnd);

		expect(submitHandler).toContain('toast.error(imageGenerationErrorMessage(error))');
		expect(submitHandler).not.toContain('toast.error(`${error}`)');
	});

	test('reuses the idempotency key for retried identical submissions', () => {
		// 复盘 #6：每次点击生成新 uuid 会让网络失败后的重试变成二次扣费。
		// 现在与视频端共享 submission-idempotency.ts 工厂：同载荷指纹复用同一键
		// （内存 + sessionStorage 兜底），成功或收到确定性 4xx（408/429 除外）后清除。
		expect(idempotency).toContain('const submissionFingerprint = async (payload: object) => {');
		expect(idempotency).toContain("sessionStorage.getItem(storageKey) ?? 'null'");
		expect(source).toContain(
			"const imageSubmissionIdempotency = createSubmissionIdempotency('pending-image-submission')"
		);
		expect(submission).toContain('await idempotency.idempotencyKeyFor(payload)');
		expect(all).not.toContain('payload,\n\t\t\t\tuuidv4()');
		const submitHandlerStart = source.indexOf('const submitHandler = async () => {');
		const submitHandlerEnd = source.indexOf('\n\tonMount', submitHandlerStart);
		const submitHandler = source.slice(submitHandlerStart, submitHandlerEnd);
		expect(submission).toContain('error instanceof ImageTaskRequestError');
		expect(submission).toContain('![408, 429].includes(error.status)');
		expect(submitHandler).toContain('imageSubmissionIdempotency.clearPendingSubmission()');
	});

	test('replaces the current creation draft without a confirmation dialog', () => {
		const applyDraftStart = source.indexOf('const applyCreationDraft = async');
		const applyDraftEnd = source.indexOf('\n\tconst loadRecentGenerationTasks', applyDraftStart);
		const applyDraft = source.slice(applyDraftStart, applyDraftEnd);

		expect(applyDraft).not.toContain('window.confirm');
		expect(applyDraft).not.toContain("$i18n.t('Replace your current creation draft?')");
		// 草稿 prompt 为纯文本，直接应用。
		expect(draftState).toContain("prompt: draft.prompt ?? ''");
		expect(applyDraft).toContain('prompt = fields.prompt');
	});

	test('places the credit quote directly before the submit button on the right', () => {
		const toolbarStart = form.indexOf(
			'class="mt-2 flex min-w-0 items-center justify-between gap-2"'
		);
		const toolbarEnd = form.indexOf('</form>', toolbarStart);
		const toolbar = form.slice(toolbarStart, toolbarEnd);

		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeGreaterThan(
			toolbar.indexOf('aria-controls={IMAGE_OPTIONS_DIALOG_ID}')
		);
		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeLessThan(
			toolbar.indexOf('<GenerationSubmitButton')
		);
	});

	test('places the model selector above the composer in normal flow and shares the generation button', () => {
		// 模型选择器从表单内 absolute 定位改为表单上方正常文档流，避免与结果图片重叠。
		expect(all).not.toContain('absolute bottom-full');
		expect(form).toContain('mb-2 flex flex-row items-center gap-2');
		expect(form).toContain('<GenerationModelSelector');
		expect(form).toContain('<GenerationSubmitButton');
	});

	test('does not render loading text while the credit quote is pending', () => {
		const badgeSource = read('../credits/ImageCreditQuoteBadge.svelte');

		expect(badgeSource).not.toContain("$i18n.t('credits.common.loading')");
	});

	test('uses accessible generate and library tabs without unmounting page state', () => {
		expect(source).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(commonNavigation).toContain('role="tablist"');
		expect(commonNavigation).toContain('role="tab"');
		expect(commonNavigation).toContain('aria-selected={selection ===');
		expect(commonNavigation).toContain('on:keydown={handleKeydown}');
		expect(source).toContain('aria-labelledby="images-generate-tab"');
		expect(source).toContain(
			"labelledBy={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}"
		);
		expect(library).toContain('id="images-library-panel"');
		expect(library).toContain('hidden={!active}');
		expect(source).not.toContain('{#if canUseImages}');
	});

	test('sizes completed result cards as fixed square thumbnails in a 4/2 column grid', () => {
		// 图网格固定列数（宽屏 4 列、窄屏 2 列），单张图尺寸不随数量变化。
		// 图框 aspect-square + object-cover；无 contain 退路、无按比例定型的旧 style。
		expect(card).toContain('const getGeneratedImageCardClass = ()');
		expect(card).toContain('aspect-square w-full');
		expect(card).toContain('block h-full w-full object-cover');
		expect(card).not.toContain('block h-full w-full object-contain');
		expect(card).toMatch(/getCompletedBatchGridClass\(\)/);
		expect(card).toMatch(/getGeneratedImageFrameClass\(\)/);
		expect(card).toMatch(/getGeneratedImageClass\(\)/);
		expect(card).toContain("'grid grid-cols-2 gap-1.5 sm:gap-2 lg:grid-cols-4'");
		// 已删除按数量动态算列数与移动端横滚分支。
		expect(all).not.toContain('getCompletedBatchMobileClass');
		expect(all).not.toContain('lg:grid-cols-${n}');

		const completedResultStart = card.indexOf("{#if batch.status === 'succeeded'");
		const completedResultEnd = card.indexOf('{:else if batch.status', completedResultStart);
		const completedResult = card.slice(completedResultStart, completedResultEnd);

		expect(completedResult).toContain('getGeneratedImageFrameClass()');
		// aspect-square 在 frame class 定义里；骨架/失败块用 batchSquareStyle（aspect-ratio: 1/1）。
		expect(card).toContain('aspect-square');
		expect(card).toContain('style={batchSquareStyle()}');
		expect(all).not.toContain('style={batchAspectStyle(batch)}');
	});

	test('keeps repeated metadata labels from colliding in a keyed each block', () => {
		expect(card).toContain('{#each getBatchMetaPills(batch) as pill, index (`${index}-${pill}`)}');
		expect(card).not.toContain('{#each getBatchMetaPills(batch) as pill (pill)}');
	});

	test('lifts the three-segment pill out of flow so the library tops out', () => {
		expect(commonNavigation).toContain('pointer-events-none absolute inset-x-0');
		expect(commonNavigation).toContain('pointer-events-auto');
		expect(navigation).toContain("label: 'My creations'");
		expect(navigation).toContain("id: 'all'");
		expect(navigation).toContain("elementId: 'images-admin-tab'");
		expect(navigation).toContain("label: 'All creations'");
		expect(source).toContain(
			'<ImagePageNavigation {selection} {isAdmin} onSelect={selectSelection} />'
		);
	});

	test('lets the library scroller hug the viewport edge', () => {
		const panelStart = library.indexOf('id="images-library-panel"');
		const panelDecl = library.slice(panelStart, panelStart + 280);
		expect(panelDecl).toContain('overflow-y-auto');
		expect(panelDecl).not.toContain('px-3');
		expect(panelDecl).not.toContain('md:px-6');
	});

	test('styles image tabs as a centered floating pill while preserving accessibility', () => {
		expect(commonNavigation).toContain('rounded-full border border-gray-200/80');
		expect(commonNavigation).toContain('bg-white/80');
		expect(commonNavigation).toContain('backdrop-blur-xl');
		expect(commonNavigation).toContain('shadow-lg shadow-black/10');
		expect(commonNavigation).toContain('aria-selected={selection ===');
		expect(commonNavigation).toContain('on:keydown={handleKeydown}');
	});

	test('derives view and library scope from the unified selection', () => {
		expect(source).toContain("$: view = selection === 'generate' ? 'generate' : 'library';");
		expect(source).toContain("$: libraryScope = selection === 'all' ? 'all' : 'mine';");
		expect(source).toMatch(/hidden=\{view !== 'generate'\}|hidden=\{view === 'library'\}/);
	});

	test('increments library revision after a successful generation', () => {
		// 成功判定从旧的同步 generatedImages 路径迁到 pollGenerationTasks 轮询：
		// 任务转 succeeded 时自增 libraryRevision，触发作品库刷新。
		expect(taskHistory).toContain("task.status === 'succeeded'");
		expect(taskHistory).toContain("previous?.status !== 'succeeded'");
		expect(source).toContain('libraryRevision += result.completed;');
	});

	test('drops the canUseImagesPage import and reactive gate', () => {
		expect(all).not.toContain('canUseImagesPage');
		expect(all).not.toContain('$: canUseImages =');
		expect(all).not.toContain("$i18n.t('Image generation is not available)");
	});

	// --- Task #14: drop binary model filtering so every model stays selectable --
	//
	// 产品方针改为「始终显示全部模型」,上传参考图不再把 text-to-image 整族
	// 过滤出去。与之耦合的被动偷换 reaction(选中 t2i 且有参考图就强行 flip 到
	// editModel,反之亦然)也随之拆除,腾出位置给 #15/#16 的灰显与温和降级。
	test('#14 removes the passive task-flip reactions around referenceImages', () => {
		// 旧的两组 reaction:选中 t2i 且有参考图 → 强切 editModel;选中 i2i 且无参考图 → 强切 generationModel
		expect(all).not.toContain(
			"$: if (loaded && selectedModelConfig?.task === 'text-to-image' && referenceImages.length > 0)"
		);
		expect(all).not.toContain(
			"$: if (loaded && selectedModelConfig?.task === 'image-to-image' && referenceImages.length === 0)"
		);
		expect(all).not.toContain('selectModel(selectedModelConfig.generationModel ?? ');
		expect(all).not.toContain('? `${selectedModelConfig.id}/edit`');
	});

	// --- Task #16: auto-switch to a same-brand enabled model with a toast --------
	test('shows model base price and proxy latency inline in the model list', () => {
		// 价格/慢启动现通过 extras 具名槽由表单注入共享 GenerationModelSelector 渲染，
		// 引用 modelBasePrice(model.raw as ImageGenerationModel) 与对应 i18n。
		expect(form).toContain('modelBasePrice(model.raw as ImageGenerationModel)');
		expect(form).toContain("$i18n.t('credits.common.unit')");
		expect(all).not.toContain("$i18n.t('credits.unit')");
		expect(form).toContain("$i18n.t('First image may be slower')");
		expect(all).not.toContain("<Tooltip content={$i18n.t('First image may be slower')}");
	});

	test('left-aligns model names in the dropdown options', () => {
		// 名称占据剩余空间并左对齐,右侧留给价格/慢启动/不支持等徽标;
		// 按钮不再用 justify-between,否则名称会被挤到中间而不是贴着 Logo。
		// 「左对齐」样式现内联在共享 GenerationModelSelector 里。
		expect(form).toContain('<GenerationModelSelector');
		expect(all).not.toContain('flex w-full items-center justify-between gap-2 rounded-xl');
	});

	test('positions the model list from its trigger and respects the mobile visual viewport', () => {
		const modelStart = form.indexOf('<GenerationModelSelector');
		const modelEnd = form.indexOf('{#if referenceImages.length > 0}', modelStart);
		const modelSelector = form.slice(modelStart, modelEnd);

		expect(form).toContain('<GenerationModelSelector');
		// 弹出层宽度已内联在共享 GenerationModelSelector（统一为 32rem 上限），
		// 页面不再写 w-[min(30rem,...)]；只确认共享组件被引用且无旧 fixed 浮层残留。
		expect(modelSelector).not.toContain('fixed inset-x-3 bottom-14');
	});

	test('uses the selected primary model and derives its active edit model', () => {
		expect(source).toContain('$: primaryModels = getPrimaryImageModels(models);');
		expect(source).toContain('$: activeModelConfig = resolveActiveImageModel(');
		expect(source).toContain('$: selectedModelSupportsEditing = supportsImageEditing(');
		expect(source).toContain('selectedModelConfig,\n\t\tmodels,\n\t\treferenceImages.length > 0');
		expect(source).toContain('activeModelConfig ?? selectedModelConfig ?? selectedModel');
	});

	test('shows only primary models without foreign-mode dimming or fallback switching', () => {
		expect(source).toContain('$: availableModels = primaryModels;');
		expect(all).not.toContain('isModelEnabledForMode');
		expect(all).not.toContain('pickFallbackModel');
		expect(all).not.toContain('ensureSelectableModelForMode');
		expect(all).not.toContain('disabled={!modelEnabled}');
		expect(all).not.toContain("$i18n.t('Unsupported')");
	});

	test('marks primary models that support reference images', () => {
		expect(form).toContain('supportsImageEditing(model.raw as ImageGenerationModel, models)');
		expect(form).toContain("$i18n.t('Supports reference images')");
	});

	test('hides and blocks reference uploads for unsupported primary models', () => {
		expect(form).toContain('{#if selectedModelSupportsEditing}');
		expect(source).toContain('if (!selectedModelSupportsEditing) {\n\t\t\treturn;\n\t\t}');
		expect(source).toContain('referenceImages = [];');
		expect(source).toContain(
			"$i18n.t('This model does not support reference images. Uploaded images were removed.')"
		);
	});

	test('places the model selector above the unchanged reference image strip and textarea', () => {
		const formStart = form.indexOf('<form');
		const formEnd = form.indexOf('</form>', formStart);
		const formBody = form.slice(formStart, formEnd);
		expect(formBody.indexOf('<GenerationModelSelector')).toBeLessThan(
			formBody.indexOf('{#if referenceImages.length > 0}')
		);
		// 提示词输入框是原生 textarea；点击标签直接插入实际文本。
		expect(formBody.indexOf('{#if referenceImages.length > 0}')).toBeLessThan(
			formBody.indexOf('bind:this={promptEditorElement}')
		);
	});

	test('inserts tag text into the prompt box on picker click', () => {
		// 标签退化为快捷提示词片段：点击即把 insert_text 追加进输入框，
		// 提交/落库都是所见即所得的纯文本。
		expect(source).toContain('appendPromptText(prompt, text)');
		expect(source).toContain('const validation = validateImagePrompt(prompt);');
		expect(all).not.toContain('composePromptWithTags');
	});

	test('keeps image options, quote, and submit control on one mobile row', () => {
		expect(form).toContain('mt-2 flex min-w-0 items-center justify-between gap-2');
		expect(form).toContain('inline-flex h-11');
		expect(form).toContain('sm:h-8 sm:gap-4');
		expect(all).not.toContain(
			'mt-2 flex flex-col gap-2 sm:h-8 sm:flex-row sm:items-center sm:justify-between'
		);
	});

	test('makes the image options popover keyboard-dismissible and semantically related', () => {
		// 开关/外点关闭/Esc/焦点归还统一由 Dropdown 组件提供（与标签、模型选择器一致）。
		expect(form).toContain('bind:show={showAspectRatioPicker}');
		expect(form).toContain('aria-haspopup="dialog"');
		expect(form).toContain('aria-controls={IMAGE_OPTIONS_DIALOG_ID}');
		expect(form).toContain('role="dialog"');
		expect(form).toContain("aria-label={$i18n.t('Parameters')}");
	});

	test('uses mobile touch targets for image option controls', () => {
		expect(form).toContain('class="h-11 rounded-xl border text-sm transition sm:h-9');
		expect(form).toContain('class="h-11 rounded-xl border text-sm capitalize transition sm:h-9');
		expect(form).toContain('class="flex min-h-11 items-center gap-1.5');
	});

	// --- Task #17: cap reference-image uploads to the selected model’s capacity -----
	test('#17 tightens the reference-image quota for single-image-family models', () => {
		// 有效上限派生自 selectedModelConfig.imageInputMaxCount,缺省回退到全局 4
		expect(source).toContain('$: effectiveMaxReferenceImages =');
		expect(source).toContain(
			'resolveImageEditModel(selectedModelConfig, models)?.imageInputMaxCount ??\n\t\tselectedModelConfig?.imageInputMaxCount ??\n\t\tMAX_REFERENCE_IMAGES'
		);
		// addFiles 使用动态上限而非硬编码常量
		expect(source).toContain('Math.max(effectiveMaxReferenceImages - referenceImages.length, 0)');
		expect(source).toContain('count: effectiveMaxReferenceImages');
		// 切到更低容量模型时,持有的多余参考图被裁剪并 toast 提示
		expect(source).toContain('referenceImages.length > effectiveMaxReferenceImages');
		expect(source).toContain('referenceImages.slice(0, effectiveMaxReferenceImages)');
		expect(source).toContain("'Trimmed to {{count}} reference image(s) for this model.'");
	});
});
