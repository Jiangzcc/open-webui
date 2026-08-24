/**
 * 二开共享：图片/视频生成任务的统一状态类型。
 *
 * 与后端 open_webui/extensions/creations/task_states.py 的 GenerationTaskStatus
 * 对齐（复盘 P2：此前 3 处手写联合 + 1 处 `| string` 放宽导致类型检查失效）。
 */
export type GenerationTaskStatus = 'queued' | 'running' | 'succeeded' | 'failed';

/** 仍在执行中的任务（未终态）。 */
export const ACTIVE_GENERATION_TASK_STATUSES: readonly GenerationTaskStatus[] = [
	'queued',
	'running'
];
