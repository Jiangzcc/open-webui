import { describe, expect, it, test } from 'vitest';

import {
	buildImageEditPayload,
	buildImageGenerationPayload,
	filterImageFiles,
	getImageModelCapability,
	getImageSizeForAspectRatio,
	getPrimaryImageModels,
	normalizeAspectRatio,
	normalizeImageGenerationModels,
	validateCustomSize,
	resolveActiveImageModel,
	resolveImageEditModel,
	supportsImageEditing,
	validateImagePrompt
} from './image-generation';

describe('image generation utils', () => {
	test('maps supported aspect ratios to backend sizes', () => {
		expect(getImageSizeForAspectRatio('auto')).toBeUndefined();
		expect(getImageSizeForAspectRatio('1:1')).toBe('1024x1024');
		expect(getImageSizeForAspectRatio('16:9')).toBe('1792x1024');
		expect(getImageSizeForAspectRatio('9:16')).toBe('1024x1792');
		expect(getImageSizeForAspectRatio('4:3')).toBe('1024x768');
		expect(getImageSizeForAspectRatio('3:4')).toBe('768x1024');
		expect(getImageSizeForAspectRatio('3:2')).toBe('1536x1024');
		expect(getImageSizeForAspectRatio('2:3')).toBe('1024x1536');
		expect(getImageSizeForAspectRatio('21:9')).toBe('1536x640');
	});

	test('normalizes unknown aspect ratios to auto', () => {
		expect(normalizeAspectRatio('default')).toBe('auto');
		expect(normalizeAspectRatio('bad')).toBe('auto');
		expect(getImageSizeForAspectRatio('bad')).toBeUndefined();
	});

	test('derives common model capabilities from model id', () => {
		expect(getImageModelCapability('dall-e-3')).toMatchObject({
			aspectRatios: ['1:1', '16:9', '9:16'],
			resolutions: [],
			imageCounts: [1]
		});

		expect(getImageModelCapability('gpt-image-1')).toMatchObject({
			aspectRatios: ['auto', '1:1', '3:2', '2:3'],
			resolutions: ['auto', '1024x1024', '1536x1024', '1024x1536']
		});
	});

	test('derives fal nano banana capabilities by model id', () => {
		expect(getImageModelCapability('fal-ai/nano-banana')).toMatchObject({
			aspectRatios: ['1:1', '16:9', '9:16'],
			resolutions: [],
			imageCounts: [1, 2, 3, 4],
			defaultAspectRatio: '1:1'
		});

		expect(getImageModelCapability('fal-ai/nano-banana-pro')).toMatchObject({
			aspectRatios: ['auto', '16:9', '9:16', '1:1', '2:3', '3:2', '4:3', '3:4', '21:9'],
			resolutions: ['1K', '2K', '4K'],
			imageCounts: [1, 2, 3, 4],
			defaultAspectRatio: 'auto',
			defaultResolution: '1K'
		});
	});

	test('preserves explicit unsupported capabilities without falling back to model presets', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'fal-ai/gpt-image-1.5',
				aspect_ratios: [],
				resolutions: ['1024x1024', '1536x1024', '1024x1536'],
				default_resolution: '1024x1024'
			}
		]);

		expect(model).toMatchObject({
			aspectRatios: [],
			resolutions: ['1024x1024', '1536x1024', '1024x1536']
		});
		expect(getImageModelCapability(model)).toMatchObject({
			aspectRatios: [],
			resolutions: ['1024x1024', '1536x1024', '1024x1536'],
			defaultResolution: '1024x1024'
		});
	});

	test('uses model-provided common dimensions for custom image sizes', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'openai/gpt-image-2',
				aspect_ratios: ['auto', '1:1', '4:3', '3:4'],
				resolutions: [],
				default_aspect_ratio: '4:3',
				custom_size_field: 'image_size',
				aspect_ratio_sizes: {
					auto: 'auto',
					'1:1': '1024x1024',
					'4:3': '1024x768',
					'3:4': '768x1024'
				}
			}
		]);

		expect(getImageModelCapability(model)).toMatchObject({
			aspectRatios: ['auto', '1:1', '4:3', '3:4'],
			resolutions: [],
			defaultAspectRatio: '4:3'
		});
		expect(getImageSizeForAspectRatio('auto', model)).toBe('auto');
		expect(getImageSizeForAspectRatio('4:3', model)).toBe('1024x768');
	});

	test('normalizes model metadata with explicit capabilities', () => {
		expect(
			normalizeImageGenerationModels([
				{
					id: 'custom-image',
					name: 'Custom Image',
					aspect_ratios: ['1:1', '4:3', '5:4', '1:8', 'bad'],
					size_options: ['512x512', 'auto', '0.5K', 'bad'],
					max_n: 3,
					default_aspect_ratio: '4:3',
					default_resolution: '512x512',
					output_formats: ['png', 'webp'],
					default_output_format: 'webp'
				}
			])
		).toEqual([
			{
				id: 'custom-image',
				name: 'Custom Image',
				aspectRatios: ['1:1', '4:3', '5:4', '1:8'],
				resolutions: ['512x512', 'auto', '0.5K'],
				maxImages: 3,
				defaultAspectRatio: '4:3',
				defaultResolution: '512x512',
				outputFormats: ['png', 'webp'],
				defaultOutputFormat: 'webp'
			}
		]);
	});

	test('normalizes only allowlisted advanced image fields and their ranges', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'advanced-image',
				advanced_fields: [
					{ field: 'seed', kind: 'integer', min: 0, max: 2147483647 },
					{ field: 'guidance_scale', kind: 'number', min: 1, max: 10 },
					{ field: 'enable_safety_checker', kind: 'boolean' },
					{ field: 'seed', kind: 'integer' }
				]
			}
		]);

		expect(getImageModelCapability(model).advancedFields).toEqual([
			{ field: 'seed', kind: 'integer', min: 0, max: 2147483647 },
			{ field: 'guidance_scale', kind: 'number', min: 1, max: 10 }
		]);
	});

	test('normalizes model base prices for text and edit modes', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'qwen-image',
				base_price: '4',
				edit_base_price: '7'
			}
		]);

		expect(model).toMatchObject({ basePrice: '4', editBasePrice: '7' });
	});

	test('preserves image model operation metadata for the user selector', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'public-image-model',
				visible: true,
				enabled: false,
				recommended: true,
				sort_order: 20,
				tags: ['Fast', 'Portrait'],
				maintenance_message: 'Capacity recovery in progress'
			}
		]);

		expect(model).toMatchObject({
			visible: true,
			enabled: false,
			recommended: true,
			sortOrder: 20,
			tags: ['Fast', 'Portrait'],
			maintenanceMessage: 'Capacity recovery in progress'
		});
	});

	test('keeps explicit auto model metadata', () => {
		expect(
			normalizeImageGenerationModels([
				{
					id: 'fal-ai/nano-banana-pro',
					aspect_ratios: ['auto', '16:9'],
					resolutions: ['1K', '2K'],
					image_counts: [1, 2],
					default_aspect_ratio: 'auto',
					default_resolution: '1K',
					provider: 'google',
					task: 'text-to-image',
					edit_model: 'fal-ai/nano-banana-pro/edit'
				}
			])
		).toEqual([
			{
				id: 'fal-ai/nano-banana-pro',
				name: undefined,
				provider: 'google',
				task: 'text-to-image',
				editModel: 'fal-ai/nano-banana-pro/edit',
				aspectRatios: ['auto', '16:9'],
				resolutions: ['1K', '2K'],
				imageCounts: [1, 2],
				defaultResolution: '1K'
			}
		]);
	});

	test('normalizes fal preset resolution metadata', () => {
		expect(
			normalizeImageGenerationModels([
				{
					id: 'openai/gpt-image-2',
					resolutions: ['auto', 'landscape_4_3', 'square_hd', 'bad'],
					default_resolution: 'landscape_4_3'
				},
				{
					id: 'fal-ai/bernini-r/edit-image',
					resolutions: ['848', '1024', 'bad'],
					default_resolution: '848'
				}
			])
		).toEqual([
			{
				id: 'openai/gpt-image-2',
				name: undefined,
				resolutions: ['auto', 'landscape_4_3', 'square_hd'],
				defaultResolution: 'landscape_4_3'
			},
			{
				id: 'fal-ai/bernini-r/edit-image',
				name: undefined,
				resolutions: ['848', '1024'],
				defaultResolution: '848'
			}
		]);
	});

	test('validates and trims prompts', () => {
		expect(validateImagePrompt('   ')).toEqual({ ok: false, reason: 'empty_prompt' });
		expect(validateImagePrompt('  cinematic cat  ')).toEqual({
			ok: true,
			prompt: 'cinematic cat'
		});
	});

	test('builds text-to-image payload with optional fields', () => {
		expect(
			buildImageGenerationPayload({
				prompt: '  misty harbor ',
				aspectRatio: '16:9',
				model: ' imagen ',
				n: 2,
				steps: 30,
				negative_prompt: ' blurry '
			})
		).toEqual({
			prompt: 'misty harbor',
			model: 'imagen',
			size: '1792x1024',
			aspect_ratio: '16:9',
			n: 2,
			steps: 30,
			negative_prompt: 'blurry'
		});
	});

	test('builds curated numeric advanced fields and a selected output format', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'advanced-image',
				output_formats: ['jpeg', 'png', 'webp'],
				default_output_format: 'jpeg'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'studio portrait',
				model,
				output_format: 'webp',
				seed: 42,
				guidance_scale: 3.5,
				strength: 0.65
			})
		).toMatchObject({
			output_format: 'webp',
			seed: 42,
			guidance_scale: 3.5,
			strength: 0.65
		});
	});

	test('omits unsupported aspect ratio fields', () => {
		expect(
			buildImageGenerationPayload({
				prompt: 'portrait',
				model: {
					id: 'fal-ai/gpt-image-1.5',
					aspectRatios: [],
					resolutions: ['1024x1024', '1536x1024', '1024x1536']
				},
				resolution: '1024x1536'
			})
		).toEqual({
			prompt: 'portrait',
			model: 'fal-ai/gpt-image-1.5',
			resolution: '1024x1536'
		});
	});

	test('sends selected aspect ratio and resolution from the public model catalog', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'nano-banana-pro',
				aspect_ratios: ['auto', '1:1', '16:9'],
				resolutions: ['1K', '2K', '4K'],
				default_resolution: '1K'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'landscape',
				model,
				aspectRatio: '16:9',
				resolution: '2K'
			})
		).toEqual({
			prompt: 'landscape',
			model: 'nano-banana-pro',
			aspect_ratio: '16:9',
			resolution: '2K'
		});
	});

	test('sends the mapped size selected through a public custom-size model', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'openai/gpt-image-2',
				aspect_ratios: ['1:1', '16:9'],
				aspect_ratio_sizes: {
					'1:1': '1024x1024',
					'16:9': '1536x864'
				},
				resolutions: []
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'landscape',
				model,
				aspectRatio: '16:9'
			})
		).toEqual({
			prompt: 'landscape',
			model: 'openai/gpt-image-2',
			size: '1536x864'
		});
	});

	test('sends only the resolution for a resolution-driven model like z-image', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'z-image-turbo',
				resolutions: ['1024x1024', '1024x576', '576x1024', '1024x768', '768x1024'],
				default_resolution: '1024x768'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'wide shot',
				model,
				resolution: '1024x576'
			})
		).toEqual({
			prompt: 'wide shot',
			model: 'z-image-turbo',
			resolution: '1024x576'
		});
	});

	test('includes explicit resolution with aspect ratio metadata', () => {
		expect(
			buildImageGenerationPayload({
				prompt: 'portrait',
				aspectRatio: '1:1',
				resolution: '2K'
			})
		).toEqual({
			prompt: 'portrait',
			size: '1024x1024',
			aspect_ratio: '1:1',
			resolution: '2K'
		});
	});

	test('omits the derived baseline size for catalog models with a resolution selector', () => {
		// 复盘 P0-2：seedream 类档位模型（resolutions + aspect_ratio_sizes）不再下发
		// 派生基线 size——档位 × 基线由后端合成，派生基线会抢占档位语义（选 4K 出 1K）。
		const [model] = normalizeImageGenerationModels([
			{
				id: 'bytedance-seedream-v5-pro',
				aspect_ratios: ['1:1', '16:9'],
				aspect_ratio_sizes: { '1:1': '1024x1024', '16:9': '1280x720' },
				resolutions: ['1K', '2K', '4K'],
				default_resolution: '1K',
				default_aspect_ratio: '1:1'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'landscape',
				model,
				aspectRatio: '16:9',
				resolution: '4K'
			})
		).toEqual({
			prompt: 'landscape',
			model: 'bytedance-seedream-v5-pro',
			aspect_ratio: '16:9',
			resolution: '4K'
		});
	});

	test('keeps an explicit custom size alongside a resolution selector', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'bytedance-seedream-v5-pro',
				aspect_ratios: ['1:1', '16:9'],
				aspect_ratio_sizes: { '1:1': '1024x1024', '16:9': '1280x720' },
				resolutions: ['1K', '2K', '4K'],
				default_resolution: '1K',
				default_aspect_ratio: '1:1'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'landscape',
				model,
				aspectRatio: '16:9',
				resolution: '4K',
				size: '1600x900'
			})
		).toEqual({
			prompt: 'landscape',
			model: 'bytedance-seedream-v5-pro',
			aspect_ratio: '16:9',
			resolution: '4K',
			size: '1600x900'
		});
	});

	test('uses explicit size before aspect-ratio size', () => {
		expect(
			buildImageGenerationPayload({
				prompt: 'portrait',
				aspectRatio: '1:1',
				size: '512x512'
			})
		).toEqual({
			prompt: 'portrait',
			size: '512x512',
			aspect_ratio: '1:1'
		});
	});

	test('omits optional generation fields when they are blank or invalid', () => {
		expect(
			buildImageGenerationPayload({
				prompt: 'portrait',
				aspectRatio: 'auto',
				model: ' ',
				n: 0,
				steps: -1,
				negative_prompt: ''
			})
		).toEqual({ prompt: 'portrait', aspect_ratio: 'auto' });
	});

	test('writes the model-declared default output format instead of hard-coding png', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'hidream-i1-dev',
				output_formats: ['jpeg', 'png'],
				default_output_format: 'jpeg'
			}
		]);

		expect(buildImageGenerationPayload({ prompt: 'field', model })).toMatchObject({
			output_format: 'jpeg'
		});
	});

	test('falls back to png when a model declares output formats without a default', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'unspecified-default',
				output_formats: ['jpeg', 'png', 'webp']
			}
		]);

		expect(buildImageGenerationPayload({ prompt: 'field', model })).toMatchObject({
			output_format: 'png'
		});
	});

	test('omits output_format when the model declares no formats', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'no-formats',
				aspect_ratios: ['1:1'],
				resolutions: []
			}
		]);

		expect(buildImageGenerationPayload({ prompt: 'field', model })).not.toHaveProperty(
			'output_format'
		);
	});

	test('builds image-to-image payload with one or many reference images', () => {		expect(
			buildImageEditPayload({
				prompt: 'turn it into ink art',
				referenceImages: ['data:image/png;base64,aaa'],
				aspectRatio: '1:1'
			})
		).toEqual({
			prompt: 'turn it into ink art',
			size: '1024x1024',
			aspect_ratio: '1:1',
			image: 'data:image/png;base64,aaa'
		});

		const [publicEditModel] = normalizeImageGenerationModels([
			{
				id: 'nano-banana-pro/edit',
				aspect_ratios: ['auto', '1:1', '16:9'],
				resolutions: ['1K', '2K', '4K']
			}
		]);
		expect(
			buildImageEditPayload({
				prompt: 'turn it into ink art',
				referenceImages: ['data:image/png;base64,aaa'],
				model: publicEditModel,
				aspectRatio: '16:9',
				resolution: '4K'
			})
		).toMatchObject({
			model: 'nano-banana-pro/edit',
			aspect_ratio: '16:9',
			resolution: '4K'
		});

		expect(
			buildImageEditPayload({
				prompt: 'combine references',
				referenceImages: ['a', 'b'],
				aspectRatio: '3:4',
				resolution: '1K',
				background: ' transparent '
			})
		).toEqual({
			prompt: 'combine references',
			size: '768x1024',
			aspect_ratio: '3:4',
			resolution: '1K',
			image: ['a', 'b'],
			background: 'transparent'
		});
	});

	test('filters image files by type, size, and count', () => {
		const png = { name: 'a.png', type: 'image/png', size: 100 };
		const jpeg = { name: 'b.jpg', type: 'image/jpeg', size: 100 };
		const pdf = { name: 'c.pdf', type: 'application/pdf', size: 100 };
		const huge = { name: 'd.png', type: 'image/png', size: 2000 };
		const extra = { name: 'e.webp', type: 'image/webp', size: 100 };

		const result = filterImageFiles([png, jpeg, pdf, huge, extra], { maxCount: 2, maxBytes: 1000 });

		expect(result.accepted).toEqual([png, jpeg]);
		expect(result.rejected).toEqual([
			{ file: pdf, reason: 'unsupported_type' },
			{ file: huge, reason: 'too_large' },
			{ file: extra, reason: 'too_many' }
		]);
	});


	test('lifts backend quality options onto the normalized model and capability', () => {
		const [withQuality, withoutQuality] = normalizeImageGenerationModels([
			{
				id: 'gpt-image-2',
				quality_options: ['low', 'medium', 'high'],
				default_quality: 'low'
			},
			{
				id: 'z-image-turbo',
				resolutions: ['1024x1024']
			}
		]);

		expect(withQuality).toMatchObject({
			id: 'gpt-image-2',
			qualityOptions: ['low', 'medium', 'high'],
			defaultQuality: 'low'
		});
		expect('qualityOptions' in withoutQuality).toBe(false);

		expect(getImageModelCapability(withQuality)).toMatchObject({
			qualityOptions: ['low', 'medium', 'high'],
			defaultQuality: 'low'
		});
		expect(getImageModelCapability(withoutQuality).qualityOptions).toEqual([]);
	});

	test('sends the selected quality for supporting models and omits it otherwise', () => {
		const [withQuality] = normalizeImageGenerationModels([
			{
				id: 'gpt-image-2',
				quality_options: ['low', 'medium', 'high'],
				default_quality: 'low'
			}
		]);

		expect(
			buildImageGenerationPayload({
				prompt: 'crisp photo',
				model: withQuality,
				quality: 'high'
			})
		).toMatchObject({ model: 'gpt-image-2', quality: 'high' });

		expect(buildImageGenerationPayload({ prompt: 'plain', quality: 'high' })).not.toHaveProperty(
			'quality'
		);
	});
});

describe('alibaba t2i hosting field', () => {
	it('exposes hosting on capability for proxy model', () => {
		const cap = getImageModelCapability({
			id: 'qwen-image-2-pro',
			hosting: 'proxy',
			aspectRatios: ['1:1'],
			resolutions: ['1024x1024'],
			imageCounts: [1, 2, 3, 4]
		});
		expect(cap.aspectRatios).toEqual(['1:1']);
	});

	it('treats single-image-count model as fixed one', () => {
		const cap = getImageModelCapability({
			id: 'wan-2.2-5b',
			hosting: 'serverless',
			imageCounts: [1]
		});
		expect(cap.imageCounts).toEqual([1]);
		expect(cap.imageCounts.length).toBe(1);
	});
});

describe('primary image model mapping', () => {
	const primary = {
		id: 'nano-banana',
		task: 'text-to-image' as const,
		editModel: 'nano-banana/edit'
	};
	const edit = {
		id: 'nano-banana/edit',
		task: 'image-to-image' as const,
		generationModel: 'nano-banana'
	};
	const textOnly = { id: 'z-image-turbo', task: 'text-to-image' as const };
	const models = [primary, edit, textOnly];

	test('exposes only primary models in the selector', () => {
		expect(getPrimaryImageModels(models).map((model) => model.id)).toEqual([
			'nano-banana',
			'z-image-turbo'
		]);
	});

	test('resolves only edit mappings that exist in the catalog', () => {
		expect(resolveImageEditModel(primary, models)?.id).toBe('nano-banana/edit');
		expect(resolveImageEditModel({ ...primary, editModel: 'missing/edit' }, models)).toBeNull();
		expect(resolveImageEditModel(textOnly, models)).toBeNull();
	});

	test('reports reference-image support from a valid edit mapping', () => {
		expect(supportsImageEditing(primary, models)).toBe(true);
		expect(supportsImageEditing(textOnly, models)).toBe(false);
	});

	test('derives the active model without changing the selected primary model', () => {
		expect(resolveActiveImageModel(primary, models, false)?.id).toBe('nano-banana');
		expect(resolveActiveImageModel(primary, models, true)?.id).toBe('nano-banana/edit');
		expect(resolveActiveImageModel(textOnly, models, true)?.id).toBe('z-image-turbo');
	});
});

describe('imageInputMaxCount normalization', () => {
	// #17:单图派 i2i 端点在后端声明 image_input_max_count=1;前端需透过 normalize
	// 把 snake_case 采集成 camelCase,供上传组件据此收紧参考图数量上限。
	test('collects image_input_max_count into imageInputMaxCount', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'qwen-image/edit',
				task: 'image-to-image',
				image_input_max_count: 1
			}
		]);
		expect(model.imageInputMaxCount).toBe(1);
	});

	test('omits imageInputMaxCount when the source does not declare it', () => {
		// 多图派不下发该字段,前端不应臆造一个值,以免误限
		const [model] = normalizeImageGenerationModels([
			{ id: 'qwen-image-2/edit', task: 'image-to-image' }
		]);
		expect(model.imageInputMaxCount).toBeUndefined();
	});

	test('ignores non-positive or non-integer values defensively', () => {
		const [zero] = normalizeImageGenerationModels([{ id: 'a', image_input_max_count: 0 }]);
		expect(zero.imageInputMaxCount).toBeUndefined();
		const [frac] = normalizeImageGenerationModels([{ id: 'b', image_input_max_count: 2.5 }]);
		expect(frac.imageInputMaxCount).toBeUndefined();
	});
});

describe('custom size constraints', () => {
	const constraints = {
		min_width: 512,
		max_width: 2048,
		min_height: 512,
		max_height: 2048,
		multiple_of: 16,
		max_pixels: 4_194_304
	};

	test('normalizes snake_case custom_size and presets onto the model', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'flux-2',
				custom_size_field: 'image_size',
				custom_size: constraints,
				image_size_whitelist: {
					'1024x1024': '1024x1024',
					'1024x576': '1024x576',
					'512x512': '512x512'
				}
			}
		]);
		expect(model.customSize).toMatchObject({
			minWidth: 512,
			maxWidth: 2048,
			multipleOf: 16,
			maxPixels: 4_194_304
		});
		expect(model.presetSizes).toEqual(['512x512', '1024x576', '1024x1024']);
		expect(getImageModelCapability(model).customSize).toBeDefined();
		expect(getImageModelCapability(model).presetSizes).toEqual([
			'512x512',
			'1024x576',
			'1024x1024'
		]);
	});

	test('passes a curated preset size straight through as payload.size', () => {
		const [model] = normalizeImageGenerationModels([
			{
				id: 'flux-2',
				custom_size_field: 'image_size',
				custom_size: constraints,
				image_size_whitelist: { '1024x1024': '1024x1024' }
			}
		]);
		expect(buildImageGenerationPayload({ prompt: 'p', model, size: '1024x1024' })).toMatchObject({
			size: '1024x1024'
		});
	});

	test('validateCustomSize rejects violations and accepts valid sizes', () => {
		const cs = {
			minWidth: 512,
			maxWidth: 2048,
			minHeight: 512,
			maxHeight: 2048,
			multipleOf: 16,
			maxPixels: 4_194_304
		};
		expect(validateCustomSize(1024, 1024, cs)).toBeNull();
		expect(validateCustomSize(513, 1024, cs)?.field).toBe('width'); // not multiple of 16
		expect(validateCustomSize(4096, 1024, cs)?.field).toBe('width'); // exceeds max
		expect(validateCustomSize(512, 512, cs)?.field).toBeUndefined(); // 512 valid min
		expect(validateCustomSize(0, 512)?.field).toBe('width'); // shared backend guard without model constraints
	});

	test('validateCustomSize returns i18n keys with interpolation params', () => {
		// Validation messages must be i18n keys (English literals) — not hardcoded
		// localized strings — so the caller can pass them through $i18n.t.
		const positiveInteger = validateCustomSize(0, 512);
		expect(positiveInteger?.message).toBe('Width and height must be positive integers');
		expect(positiveInteger?.messageParams).toBeUndefined();

		// Width/height bounds (no multipleOf so the dimension-multiple check is skipped).
		const bounds = {
			minWidth: 512,
			maxWidth: 2048,
			minHeight: 512,
			maxHeight: 2048
		};
		expect(validateCustomSize(100, 1024, bounds)?.message).toBe('Width must be at least {{min}}');
		expect(validateCustomSize(100, 1024, bounds)?.messageParams).toEqual({ min: 512 });
		expect(validateCustomSize(4096, 1024, bounds)?.message).toBe('Width must be at most {{max}}');
		expect(validateCustomSize(4096, 1024, bounds)?.messageParams).toEqual({ max: 2048 });
		expect(validateCustomSize(1024, 100, bounds)?.message).toBe('Height must be at least {{min}}');
		expect(validateCustomSize(1024, 4096, bounds)?.message).toBe('Height must be at most {{max}}');

		// Dimensions multiple + pixel + aspect checks.
		const cs = {
			multipleOf: 16,
			minPixels: 1_048_576,
			maxPixels: 4_194_304,
			aspectRatioMin: 0.5,
			aspectRatioMax: 2
		};
		expect(validateCustomSize(513, 1024, cs)?.message).toBe(
			'Dimensions must be a multiple of {{multipleOf}}'
		);
		expect(validateCustomSize(513, 1024, cs)?.messageParams).toEqual({ multipleOf: 16 });
		expect(validateCustomSize(512, 512, cs)?.message).toBe(
			'Total pixels must be at least {{min}}'
		);
		// 2064×2048 = 4_227_072 > maxPixels; both dims are multiples of 16, ratio in range.
		expect(validateCustomSize(2064, 2048, cs)?.message).toBe(
			'Total pixels must be at most {{max}}'
		);
		expect(validateCustomSize(2048, 512, cs)?.message).toBe(
			'Aspect ratio is above the maximum ({{max}})'
		);
		expect(validateCustomSize(512, 2048, cs)?.message).toBe(
			'Aspect ratio is below the minimum ({{min}})'
		);
	});

	test('validateCustomSize enforces pixel and aspect-ratio bounds', () => {
		const cs = {
			minPixels: 1_048_576,
			maxPixels: 4_194_304,
			aspectRatioMin: 0.0625,
			aspectRatioMax: 16
		};
		expect(validateCustomSize(1024, 1024, cs)).toBeNull();
		expect(validateCustomSize(512, 512, cs)?.field).toBe('pixels'); // below min pixels
		expect(validateCustomSize(4096, 2000, cs)?.field).toBe('pixels'); // above max pixels
		expect(validateCustomSize(4096, 256, cs)).toBeNull(); // ratio exactly 16, min pixels satisfied
	});

	test('validateCustomSize flags aspect-ratio overflow independently', () => {
		// Lower the pixel floor so a skinny size can reach the aspect-ratio check.
		const cs = { aspectRatioMin: 0.5, aspectRatioMax: 2 };
		expect(validateCustomSize(1024, 1024, cs)).toBeNull();
		expect(validateCustomSize(2048, 512, cs)?.field).toBe('aspect'); // ratio 4 > 2
		expect(validateCustomSize(512, 2048, cs)?.field).toBe('aspect'); // ratio 0.25 < 0.5
	});
});
