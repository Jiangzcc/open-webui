import { describe, expect, it } from 'vitest';
import {
	groupByVendor,
	vendorLogoUrl,
	isProxyModel,
	stripVendorFromName
} from '$lib/utils/images-dropdown';
import type { ImageGenerationModel } from '$lib/utils/image-generation';

describe('images-dropdown utils', () => {
	it('groups models by provider', () => {
		const models: ImageGenerationModel[] = [
			{ id: 'qwen-image', provider: 'alibaba' },
			{ id: 'z-image-turbo', provider: 'alibaba' },
			{ id: 'nano-banana', provider: 'google' },
			{ id: 'legacy-no-provider' }
		];
		const groups = groupByVendor(models);
		expect(groups.alibaba.map((m) => m.id)).toEqual(['qwen-image', 'z-image-turbo']);
		expect(groups.google.map((m) => m.id)).toEqual(['nano-banana']);
		expect(groups.other.map((m) => m.id)).toEqual(['legacy-no-provider']);
	});

	it('builds vendor logo url', () => {
		expect(vendorLogoUrl('alibaba')).toBe('/assets/vendors/alibaba.webp');
		expect(vendorLogoUrl('google')).toBe('/assets/vendors/google.webp');
	});

	it('detects proxy hosting', () => {
		expect(isProxyModel({ id: 'x', hosting: 'proxy' })).toBe(true);
		expect(isProxyModel({ id: 'x', hosting: 'serverless' })).toBe(false);
		expect(isProxyModel({ id: 'x' })).toBe(false);
	});

	it('strips the leading vendor segment from model display name', () => {
		// 阿里这批 name 形如 'Alibaba / Qwen Image',左栏已显示厂商,右栏只留模型短名
		expect(stripVendorFromName({ id: 'fal-ai/qwen-image', name: 'Alibaba / Qwen Image' })).toBe(
			'Qwen Image'
		);
		expect(
			stripVendorFromName({
				id: 'fal-ai/wan/v2.2-5b/text-to-image',
				name: 'Alibaba / Wan 2.2 (5B)'
			})
		).toBe('Wan 2.2 (5B)');
		// 多段只砍第一段,模型名本身含 ' / ' 时保留后半
		expect(stripVendorFromName({ id: 'x', name: 'Foo / Bar / Baz' })).toBe('Bar / Baz');
		// 无分隔符的原样返回
		expect(stripVendorFromName({ id: 'x', name: 'Plain' })).toBe('Plain');
		// name 缺失时空回退到 id
		expect(stripVendorFromName({ id: 'fallback-id' })).toBe('fallback-id');
		expect(stripVendorFromName({ id: 'fallback-id', name: '' })).toBe('fallback-id');
	});
});
