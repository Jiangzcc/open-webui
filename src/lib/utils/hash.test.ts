import { afterEach, describe, expect, it, vi } from 'vitest';
import { computeFileHash, sha256Hex } from '$lib/utils/hash';

// NIST FIPS 180-2 官方测试向量：subtle 与纯 JS fallback 两条路径都必须命中。
// 第三条 56 字节，恰好触发「数据 + 长度塞不进一块」的双块 padding 分支；
// 第四条百万字节，跨 15625 个块做边界压力。
const KNOWN_VECTORS: [string, string][] = [
	['', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
	['abc', 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
	[
		'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq',
		'248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1'
	],
	['a'.repeat(1000000), 'cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0']
];

afterEach(() => {
	vi.unstubAllGlobals();
});

describe('sha256Hex (crypto.subtle path)', () => {
	it('matches NIST test vectors', async () => {
		for (const [input, expected] of KNOWN_VECTORS) {
			await expect(sha256Hex(input)).resolves.toBe(expected);
		}
	});
});

describe('sha256Hex pure-JS fallback (no crypto.subtle)', () => {
	it('matches NIST test vectors when crypto.subtle is unavailable', async () => {
		// 纯 HTTP 部署下 globalThis.crypto?.subtle 为 undefined，走 fallback。
		// fallback 一旦算错，幂等指纹会静默产出错误哈希，必须用官方向量钉死。
		vi.stubGlobal('crypto', {});
		for (const [input, expected] of KNOWN_VECTORS) {
			await expect(sha256Hex(input)).resolves.toBe(expected);
		}
	});

	it('agrees with the subtle path on multibyte UTF-8 input', async () => {
		// 多字节走 TextEncoder 路径，官方向量不含非 ASCII，用两条路径对账覆盖。
		const multibyte = '视频生成:参数={"分辨率":"1080p"} — 你好 🌊';
		const subtleResult = await sha256Hex(multibyte);
		vi.stubGlobal('crypto', {});
		await expect(sha256Hex(multibyte)).resolves.toBe(subtleResult);
	});
});

describe('computeFileHash', () => {
	it('hashes file contents through both paths', async () => {
		const file = new File(['abc'], 'abc.txt');
		await expect(computeFileHash(file)).resolves.toBe(KNOWN_VECTORS[1][1]);
		vi.stubGlobal('crypto', {});
		await expect(computeFileHash(file)).resolves.toBe(KNOWN_VECTORS[1][1]);
	});
});
