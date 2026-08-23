/**
 * Prompt-tag helpers.
 *
 * 标签是「快捷提示词片段」：点击标签时 insert_text 直接插入输入框，
 * 提交/落库都是所见即所得的纯文本。
 */

/**
 * 点击标签时把 insert_text 追加到提示词输入框：已有内容按逗号分段拼接，
 * 空输入框直接放入片段。
 */
export function appendPromptText(existing: string, text: string): string {
	const snippet = text.trim();
	if (!snippet) return existing;
	// 去掉已有的尾部分隔符（逗号/空白）再拼接，避免 "a street , , rain"。
	const trimmed = existing.trim().replace(/[,\s]+$/, '');
	if (!trimmed) return snippet;
	return `${trimmed}, ${snippet}`;
}
