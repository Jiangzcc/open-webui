// 提交幂等键（图片/视频生成共用）：对提交载荷做指纹，跨重试复用同一个
// idempotency key，防止网络失败后的重试创建第二个付费请求。指纹与 key
// 持久化在 sessionStorage，浏览器刷新后仍可复用；每类生成用独立的
// storage key（'pending-image-submission' / 'pending-video-submission'）。

import { v4 as uuidv4 } from 'uuid';

import { sha256Hex } from '$lib/utils/hash';

type PendingSubmission = { fingerprint: string; idempotencyKey: string };

export const submissionFingerprint = async (payload: object) => {
	// sha256Hex 带 HTTP 部署的纯 JS 降级：非安全上下文（crypto.subtle 不可用）
	// 时提交指纹仍可计算，幂等重试保护不因部署形态失效。
	return sha256Hex(JSON.stringify(payload));
};

export type SubmissionIdempotency = {
	idempotencyKeyFor: (payload: object) => Promise<string>;
	clearPendingSubmission: () => void;
};

export const createSubmissionIdempotency = (storageKey: string): SubmissionIdempotency => {
	let pendingSubmission: PendingSubmission | null = null;

	return {
		idempotencyKeyFor: async (payload: object) => {
			const fingerprint = await submissionFingerprint(payload);
			if (pendingSubmission?.fingerprint === fingerprint) {
				return pendingSubmission.idempotencyKey;
			}
			try {
				const stored = JSON.parse(
					sessionStorage.getItem(storageKey) ?? 'null'
				) as PendingSubmission | null;
				if (stored?.fingerprint === fingerprint && stored.idempotencyKey) {
					pendingSubmission = stored;
					return stored.idempotencyKey;
				}
			} catch {
				// Replace malformed browser state below.
			}
			const idempotencyKey = uuidv4();
			pendingSubmission = { fingerprint, idempotencyKey };
			try {
				sessionStorage.setItem(storageKey, JSON.stringify(pendingSubmission));
			} catch {
				// In-memory reuse still protects retries when sessionStorage is unavailable.
			}
			return idempotencyKey;
		},
		clearPendingSubmission: () => {
			pendingSubmission = null;
			try {
				sessionStorage.removeItem(storageKey);
			} catch {
				// Nothing else to clear when browser storage is unavailable.
			}
		}
	};
};
