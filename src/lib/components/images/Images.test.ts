import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';

const source = readFileSync(fileURLToPath(new URL('./Images.svelte', import.meta.url)), 'utf-8');

describe('images page controls', () => {
	test('uses concise option headings and omits generation mode helper text', () => {
		expect(source).toContain("$i18n.t('Ratio')");
		expect(source).toContain("$i18n.t('Resolution')");
		expect(source).toContain("$i18n.t('Quantity')");
		expect(source).not.toContain("$i18n.t('Select aspect ratio')");
		expect(source).not.toContain(': modeLabel}');
	});

	test('uses auto without ratio or resolution icons in the selected options', () => {
		const composerStart = source.indexOf(
			'class="mt-2 flex min-w-0 items-center justify-between gap-2"'
		);
		const composerEnd = source.indexOf('</form>', composerStart);
		const composer = source.slice(composerStart, composerEnd);

		expect(source).toContain("ratio === DEFAULT_IMAGE_ASPECT_RATIO ? $i18n.t('Auto') : ratio");
		expect(composer).not.toMatch(/getAspectRatioPreviewClass\(\s*selectedAspectRatio\s*\)/);
		expect(composer).not.toContain('getAspectRatioPreviewStyle(selectedAspectRatio)');
		expect(source).not.toContain('<ArrowsPointingOut');
		expect(source).not.toContain('<Grid');
	});

	test('uses compact illustrative ratio thumbnails instead of exact large ratios', () => {
		expect(source).toContain('const previewSize = 20;');
		expect(source).toContain('const minimumPreviewSize = 12;');
		expect(source).toContain('Math.max(minimumPreviewSize');
	});

	test('shows only the model name in the trigger but keeps the provider in popup options', () => {
		expect(source).toContain('getImageModelDisplayName');
		expect(source).toContain('getImageModelDisplayName(selectedModelConfig)');
		// popup 选项剥掉厂商前缀只留模型短名(trigger 仍走 getImageModelDisplayName)；
		// 内联映射现走 stripVendorFromName(model)，由共享 GenerationModelSelector 渲染短名。
		expect(source).toContain('name: stripVendorFromName(model)');
		expect(source).not.toContain('getImageModelDisplayName(model)');
	});

	test('shows operation metadata only while choosing a model', () => {
		// recommended / tags / maintenance 现作为 SelectableModel 字段传入共享
		// GenerationModelSelector，由后者内联渲染；页面不再直接写 {#if model.recommended}。
		expect(source).toContain('recommended: model.recommended');
		expect(source).toContain('tags: model.tags');
		expect(source).toContain('maintenance: model.maintenanceMessage');
		expect(source).not.toContain('selectedModelConfig?.recommended');
		expect(source).not.toContain('selectedModelConfig?.tags');
		expect(source).not.toContain('selectedModelConfig?.maintenanceMessage');
	});

	test('keeps only the mobile sidebar toggle in the page header', () => {
		const navStart = source.indexOf('<nav ');
		const navEnd = source.indexOf('</nav>', navStart);
		const nav = source.slice(navStart, navEnd);

		expect(nav).toContain('SidebarIcon');
		expect(nav).not.toContain("$i18n.t('Images')");
		expect(nav).not.toContain('bind:this={modelSelectorElement}');
	});

	test('quotes the selected or default model before a prompt is entered', () => {
		expect(source).toContain('const CREDIT_QUOTE_PLACEHOLDER_PROMPT =');
		expect(source).toContain('prompt: CREDIT_QUOTE_PLACEHOLDER_PROMPT');
		expect(source).not.toContain('quotePrompt: string');
		expect(source).toContain('$: selectedModelConfig =');
		expect(source).toContain(
			'primaryModels.find((model) => model.isDefault && model.enabled !== false)'
		);
		expect(source).toContain('buildImageQuoteInput(\n\t\tselectedAspectRatio,');
		expect(source).toContain('\n\t\treferenceImages,\n\t\tcustomSizeValue\n\t)');
		expect(source).toContain('$: if (loaded && quoteInput) {');
	});

	test('uses a generic localized error instead of stringifying submission API errors', () => {
		const submitHandlerStart = source.indexOf('const submitHandler = async () => {');
		const submitHandlerEnd = source.indexOf('\n\tonMount', submitHandlerStart);
		const submitHandler = source.slice(submitHandlerStart, submitHandlerEnd);

		expect(submitHandler).toContain('toast.error(imageGenerationErrorMessage(error))');
		expect(submitHandler).not.toContain('toast.error(`${error}`)');
	});

	test('replaces the current creation draft without a confirmation dialog', () => {
		const applyDraftStart = source.indexOf('const applyCreationDraft = async');
		const applyDraftEnd = source.indexOf('\n\tconst loadRecentGenerationTasks', applyDraftStart);
		const applyDraft = source.slice(applyDraftStart, applyDraftEnd);

		expect(applyDraft).not.toContain('window.confirm');
		expect(applyDraft).not.toContain("$i18n.t('Replace your current creation draft?')");
		expect(applyDraft).toContain('prompt = draft.prompt;');
	});

	test('places the credit quote directly before the submit button on the right', () => {
		const toolbarStart = source.indexOf(
			'class="mt-2 flex min-w-0 items-center justify-between gap-2"'
		);
		const toolbarEnd = source.indexOf('</form>', toolbarStart);
		const toolbar = source.slice(toolbarStart, toolbarEnd);

		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeGreaterThan(
			toolbar.indexOf('bind:this={imageOptionsElement}')
		);
		expect(toolbar.indexOf('<ImageCreditQuoteBadge')).toBeLessThan(
			toolbar.indexOf('<GenerationSubmitButton')
		);
	});

	test('places the model selector above the composer in normal flow and shares the generation button', () => {
		// 模型选择器从表单内 absolute 定位改为表单上方正常文档流，避免与结果图片重叠。
		expect(source).not.toContain('absolute bottom-full');
		expect(source).toContain('mb-2 flex flex-row items-center gap-2');
		expect(source).toContain('<GenerationModelSelector');
		expect(source).toContain('<GenerationSubmitButton');
	});

	test('does not render loading text while the credit quote is pending', () => {
		const badgeSource = readFileSync(
			fileURLToPath(new URL('../credits/ImageCreditQuoteBadge.svelte', import.meta.url)),
			'utf-8'
		);

		expect(badgeSource).not.toContain("$i18n.t('credits.common.loading')");
	});

	test('uses accessible generate and library tabs without unmounting page state', () => {
		expect(source).toContain("let selection: 'generate' | 'mine' | 'all' = 'generate';");
		expect(source).toContain('role="tablist"');
		expect(source).toContain('role="tab"');
		expect(source).toContain('aria-selected={selection ===');
		expect(source).toContain('on:keydown={handleTabKeydown}');
		expect(source).toContain('aria-labelledby="images-generate-tab"');
		expect(source).toContain(
			"aria-labelledby={selection === 'all' ? 'images-admin-tab' : 'images-library-tab'}"
		);
		expect(source).toContain('id="images-library-panel"');
		expect(source).toContain("hidden={view !== 'library'}");
		expect(source).not.toContain('{#if canUseImages}');
	});

	test('sizes completed result cards as fixed square thumbnails in a 4/2 column grid', () => {
		// 图网格固定列数（宽屏 4 列、窄屏 2 列），单张图尺寸不随数量变化。
		// 图框 aspect-square + object-cover；无 contain 退路、无按比例定型的旧 style。
		expect(source).toContain('const getGeneratedImageCardClass = ()');
		expect(source).toContain('aspect-square w-full');
		expect(source).toContain('block h-full w-full object-cover');
		expect(source).not.toContain('block h-full w-full object-contain');
		expect(source).toMatch(/getCompletedBatchGridClass\(\)/);
		expect(source).toMatch(/getGeneratedImageFrameClass\(\)/);
		expect(source).toMatch(/getGeneratedImageClass\(\)/);
		expect(source).toContain("'grid grid-cols-2 gap-1.5 sm:gap-2 lg:grid-cols-4'");
		// 已删除按数量动态算列数与移动端横滚分支。
		expect(source).not.toContain('getCompletedBatchMobileClass');
		expect(source).not.toContain('lg:grid-cols-${n}');

		const completedResultStart = source.indexOf("{#if batch.status === 'succeeded'");
		const completedResultEnd = source.indexOf('{:else if batch.status', completedResultStart);
		const completedResult = source.slice(completedResultStart, completedResultEnd);

		expect(completedResult).toContain('getGeneratedImageFrameClass()');
		// aspect-square 在 frame class 定义里；骨架/失败块用 batchSquareStyle（aspect-ratio: 1/1）。
		expect(source).toContain('aspect-square');
		expect(source).toContain('style={batchSquareStyle()}');
		expect(source).not.toContain('style={batchAspectStyle(batch)}');
	});

	test('keeps repeated metadata labels from colliding in a keyed each block', () => {
		expect(source).toContain(
			'{#each getBatchMetaPills(batch, primaryModels) as pill, index (`${index}-${pill}`)}'
		);
		expect(source).not.toContain('{#each getBatchMetaPills(batch, primaryModels) as pill (pill)}');
	});

	test('lifts the three-segment pill out of flow so the library tops out', () => {
		expect(source).toContain('pointer-events-none absolute inset-x-0');
		expect(source).toContain('pointer-events-auto');
		expect(source).toContain("$i18n.t('My creations')");
		expect(source).toContain('{#if isAdmin}');
		expect(source).toContain('id="images-admin-tab"');
		expect(source).toContain("$i18n.t('All creations')");
		expect(source).toContain("selectSelection('all')");
	});

	test('lets the library scroller hug the viewport edge', () => {
		const panelStart = source.indexOf('id="images-library-panel"');
		const panelDecl = source.slice(panelStart, panelStart + 280);
		expect(panelDecl).toContain('overflow-y-auto');
		expect(panelDecl).not.toContain('px-3');
		expect(panelDecl).not.toContain('md:px-6');
	});

	test('styles image tabs as a centered floating pill while preserving accessibility', () => {
		expect(source).toContain('rounded-full border border-gray-200/80');
		expect(source).toContain('bg-white/80');
		expect(source).toContain('backdrop-blur-xl');
		expect(source).toContain('shadow-lg shadow-black/10');
		expect(source).toContain('aria-selected={selection ===');
		expect(source).toContain('on:keydown={handleTabKeydown}');
	});

	test('derives view and library scope from the unified selection', () => {
		expect(source).toContain("$: view = selection === 'generate' ? 'generate' : 'library';");
		expect(source).toContain("$: libraryScope = selection === 'all' ? 'all' : 'mine';");
		expect(source).toMatch(/hidden=\{view !== 'generate'\}|hidden=\{view === 'library'\}/);
	});

	test('increments library revision after a successful generation', () => {
		// 成功判定从旧的同步 generatedImages 路径迁到 pollGenerationTasks 轮询：
		// 任务转 succeeded 时自增 libraryRevision，触发作品库刷新。
		const pollStart = source.indexOf('const pollGenerationTasks');
		const pollEnd = source.indexOf('} finally', pollStart);
		const poll = source.slice(pollStart, pollEnd);
		expect(poll).toContain("task.status === 'succeeded'");
		expect(poll).toContain('libraryRevision += 1;');
	});

	test('drops the canUseImagesPage import and reactive gate', () => {
		expect(source).not.toContain('canUseImagesPage');
		expect(source).not.toContain('$: canUseImages =');
		expect(source).not.toContain("$i18n.t('Image generation is not available)");
	});

	// --- Task #14: drop binary model filtering so every model stays selectable --
	//
	// 产品方针改为「始终显示全部模型」,上传参考图不再把 text-to-image 整族
	// 过滤出去。与之耦合的被动偷换 reaction(选中 t2i 且有参考图就强行 flip 到
	// editModel,反之亦然)也随之拆除,腾出位置给 #15/#16 的灰显与温和降级。
	test('#14 removes the passive task-flip reactions around referenceImages', () => {
		// 旧的两组 reaction:选中 t2i 且有参考图 → 强切 editModel;选中 i2i 且无参考图 → 强切 generationModel
		expect(source).not.toContain(
			"$: if (loaded && selectedModelConfig?.task === 'text-to-image' && referenceImages.length > 0)"
		);
		expect(source).not.toContain(
			"$: if (loaded && selectedModelConfig?.task === 'image-to-image' && referenceImages.length === 0)"
		);
		expect(source).not.toContain('selectModel(selectedModelConfig.generationModel ?? ');
		expect(source).not.toContain('? `${selectedModelConfig.id}/edit`');
	});

	// --- Task #16: auto-switch to a same-brand enabled model with a toast --------
	test('shows model base price and proxy latency inline in the model list', () => {
		// 价格/慢启动现通过 extras 具名槽由页面注入共享 GenerationModelSelector 渲染，
		// 引用 modelBasePrice(model.raw as ImageGenerationModel) 与对应 i18n。
		expect(source).toContain('modelBasePrice(model.raw as ImageGenerationModel)');
		expect(source).toContain("$i18n.t('credits.common.unit')");
		expect(source).not.toContain("$i18n.t('credits.unit')");
		expect(source).toContain("$i18n.t('First image may be slower')");
		expect(source).not.toContain("<Tooltip content={$i18n.t('First image may be slower')}");
	});

	test('left-aligns model names in the dropdown options', () => {
		// 名称占据剩余空间并左对齐,右侧留给价格/慢启动/不支持等徽标;
		// 按钮不再用 justify-between,否则名称会被挤到中间而不是贴着 Logo。
		// 「左对齐」样式现内联在共享 GenerationModelSelector 里。
		expect(source).toContain('<GenerationModelSelector');
		expect(source).not.toContain('flex w-full items-center justify-between gap-2 rounded-xl');
	});

	test('positions the model list from its trigger and respects the mobile visual viewport', () => {
		const modelStart = source.indexOf('<GenerationModelSelector');
		const modelEnd = source.indexOf('{#if referenceImages.length > 0}', modelStart);
		const modelSelector = source.slice(modelStart, modelEnd);

		expect(source).toContain('<GenerationModelSelector');
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
		expect(source).not.toContain('isModelEnabledForMode');
		expect(source).not.toContain('pickFallbackModel');
		expect(source).not.toContain('ensureSelectableModelForMode');
		expect(source).not.toContain('disabled={!modelEnabled}');
		expect(source).not.toContain("$i18n.t('Unsupported')");
	});

	test('marks primary models that support reference images', () => {
		expect(source).toContain('supportsImageEditing(model, models)');
		expect(source).toContain("$i18n.t('Supports reference images')");
	});

	test('hides and blocks reference uploads for unsupported primary models', () => {
		expect(source).toContain('{#if selectedModelSupportsEditing}');
		expect(source).toContain('if (!selectedModelSupportsEditing) {\n\t\t\treturn;\n\t\t}');
		expect(source).toContain('referenceImages = [];');
		expect(source).toContain(
			"$i18n.t('This model does not support reference images. Uploaded images were removed.')"
		);
	});

	test('places the model selector above the unchanged reference image strip and textarea', () => {
		const formStart = source.indexOf('<form');
		const formEnd = source.indexOf('</form>', formStart);
		const form = source.slice(formStart, formEnd);
		expect(form.indexOf('bind:this={modelSelectorElement}')).toBeLessThan(
			form.indexOf('{#if referenceImages.length > 0}')
		);
		expect(form.indexOf('{#if referenceImages.length > 0}')).toBeLessThan(
			form.indexOf('bind:this={promptTextareaElement}')
		);
	});

	test('keeps image options, quote, and submit control on one mobile row', () => {
		expect(source).toContain('mt-2 flex min-w-0 items-center justify-between gap-2');
		expect(source).not.toContain(
			'mt-2 flex flex-col gap-2 sm:h-8 sm:flex-row sm:items-center sm:justify-between'
		);
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
