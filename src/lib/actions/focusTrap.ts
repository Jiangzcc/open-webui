/**
 * 弹窗焦点陷阱 Svelte action。
 * 打开时将焦点移至弹窗内首个可聚焦元素，Tab/Shift+Tab 在弹窗内循环，
 * 关闭后焦点恢复到触发元素。
 */
export function trapFocus(node: HTMLElement) {
	// 记录触发元素，弹窗关闭后恢复焦点
	const previouslyFocused = document.activeElement as HTMLElement | null;

	const focusableSelector =
		'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

	const getFocusable = () =>
		Array.from(node.querySelectorAll<HTMLElement>(focusableSelector));

	function handleKeydown(e: KeyboardEvent) {
		if (e.key !== 'Tab') return;
		const elements = getFocusable();
		if (elements.length === 0) return;
		const first = elements[0];
		const last = elements[elements.length - 1];
		if (e.shiftKey && document.activeElement === first) {
			e.preventDefault();
			last.focus();
		} else if (!e.shiftKey && document.activeElement === last) {
			e.preventDefault();
			first.focus();
		}
	}

	node.addEventListener('keydown', handleKeydown);

	// 初始焦点：移至弹窗内首个可聚焦元素
	requestAnimationFrame(() => {
		const elements = getFocusable();
		if (elements.length > 0) {
			elements[0].focus();
		} else {
			node.setAttribute('tabindex', '-1');
			node.focus();
		}
	});

	return {
		destroy() {
			node.removeEventListener('keydown', handleKeydown);
			// 恢复焦点到触发元素
			previouslyFocused?.focus?.();
		}
	};
}
