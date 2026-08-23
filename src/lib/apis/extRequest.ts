/**
 * 二开共享 request helper（复盘 P2：provider-ops / videos / media-model-ops /
 * discovery 四份 request 封装逐字重复——收敛为单一实现）。
 *
 * 统一约定：
 * - Authorization 由 token 是否非空决定（未登录浏览路径可不传）；
 * - 有请求体时才设置 Content-Type: application/json；
 * - 204 No Content 直接返回 undefined，不解析响应体；
 * - 非 2xx 默认 throw 解析后的 JSON 错误负载（解析失败为 null），
 *   需要自定义错误形态的调用方（如 videos 的 i18n 错误码）传 decodeError。
 */
export interface ExtRequestInit extends RequestInit {
	token?: string;
	decodeError?: (payload: unknown, status: number) => unknown;
}

export const extRequest = async <T>(url: string, init: ExtRequestInit = {}): Promise<T> => {
	const { token, decodeError, ...fetchInit } = init;
	const response = await fetch(url, {
		...fetchInit,
		headers: {
			Accept: 'application/json',
			...(fetchInit.body ? { 'Content-Type': 'application/json' } : {}),
			...(token ? { Authorization: `Bearer ${token}` } : {}),
			...(fetchInit.headers ?? {})
		}
	});
	// 204 No Content 无响应体，直接返回 undefined。
	if (response.status === 204) return undefined as T;
	if (!response.ok) {
		const payload = await response.json().catch(() => null);
		throw decodeError ? decodeError(payload, response.status) : payload;
	}
	return (await response.json()) as T;
};
