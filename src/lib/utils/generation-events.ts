// 生成事件流（SSE）的共享消费器：图片页与视频页使用同一套连接、重连与
// 兜底轮询逻辑，只差事件 kind 与单任务刷新回调。
//
// 关键行为（与原 Images.svelte/Videos.svelte 内联实现保持一致）：
// - 事件到达即把重连退避重置为初始值；
// - 旧调用的 finally 只在其 controller 仍是活跃 controller 时才调度重连，
//   避免旧定时器周期性 abort 新连接，造成 SSE 连接振荡；
// - 非主动中断的断流触发一次兜底轮询，捕获错过的事件。

import {
	GENERATION_EVENT_RECONNECT_INITIAL_MS,
	iterateGenerationEvents,
	nextGenerationEventReconnectDelay,
	subscribeToGenerationEvents
} from '$lib/apis/creations/generation-tasks';

export type GenerationEventStream = {
	start: () => Promise<void>;
	stop: () => void;
};

export const createGenerationEventStream = (
	kind: 'image' | 'video',
	refreshTask: (taskId: string) => Promise<void> | void,
	fallbackPoll: () => Promise<void> | void
): GenerationEventStream => {
	let controller: AbortController | null = null;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	let reconnectDelay = GENERATION_EVENT_RECONNECT_INITIAL_MS;
	let destroyed = false;

	const consume = async () => {
		controller?.abort();
		const active = new AbortController();
		controller = active;
		try {
			for await (const event of iterateGenerationEvents(
				subscribeToGenerationEvents(localStorage.token, active.signal)
			)) {
				reconnectDelay = GENERATION_EVENT_RECONNECT_INITIAL_MS;
				if (event.kind === kind && event.task_id) {
					await Promise.resolve(refreshTask(event.task_id)).catch(() => undefined);
				}
			}
		} catch (error) {
			if (!(error instanceof DOMException && error.name === 'AbortError')) {
				await Promise.resolve(fallbackPoll()).catch(() => undefined);
			}
		} finally {
			// 仅当此调用的 controller 仍为活跃 controller 时才设重连定时器。
			// 如果已被新调用替换（abort），旧调用的 finally 不应再调度重连，
			// 否则定时器会周期性 abort 新连接，造成 SSE 连接振荡。
			const wasActive = controller === active;
			if (wasActive) controller = null;
			if (wasActive && !destroyed) {
				const reconnectAfter = reconnectDelay;
				reconnectDelay = nextGenerationEventReconnectDelay(reconnectDelay);
				reconnectTimer = setTimeout(() => void consume(), reconnectAfter);
			}
		}
	};

	return {
		start: () => consume(),
		stop: () => {
			destroyed = true;
			controller?.abort();
			if (reconnectTimer) clearTimeout(reconnectTimer);
		}
	};
};
