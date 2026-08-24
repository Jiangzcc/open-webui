import {
	getImageGenerationTask,
	listImageGenerationTasks
} from '$lib/apis/creations/generation-tasks';
import {
	isGenerationTaskTerminal,
	mergeGenerationTask,
	type ImageGenerationBatch
} from '$lib/utils/image-generation-batches';
import { recentImageTaskSince } from './imagePageState';

const PAGE_SIZE = 10;

export const loadImageTaskPage = async (
	token: string,
	batches: ImageGenerationBatch[],
	cursor?: string | null
): Promise<{ batches: ImageGenerationBatch[]; cursor: string | null }> => {
	const page = await listImageGenerationTasks(
		token,
		PAGE_SIZE,
		cursor || undefined,
		recentImageTaskSince()
	);
	return {
		batches: page.items.reduce(mergeGenerationTask, batches),
		cursor: page.next_cursor ?? null
	};
};

export const pollActiveImageTasks = async (
	token: string,
	batches: ImageGenerationBatch[]
): Promise<{ batches: ImageGenerationBatch[]; completed: number }> => {
	const active = batches.filter((batch) => !isGenerationTaskTerminal(batch.status));
	if (!active.length) return { batches, completed: 0 };
	const tasks = await Promise.all(active.map((batch) => getImageGenerationTask(token, batch.id)));
	let completed = 0;
	const next = tasks.reduce((current, task) => {
		const previous = current.find((batch) => batch.id === task.id);
		if (task.status === 'succeeded' && previous?.status !== 'succeeded') completed += 1;
		return mergeGenerationTask(current, task);
	}, batches);
	return { batches: next, completed };
};

export const refreshImageTask = async (
	token: string,
	batches: ImageGenerationBatch[],
	taskId: string
): Promise<{ batches: ImageGenerationBatch[]; completed: boolean }> => {
	const previous = batches.find((batch) => batch.id === taskId);
	const task = await getImageGenerationTask(token, taskId);
	return {
		batches: mergeGenerationTask(batches, task),
		completed: task.status === 'succeeded' && previous?.status !== 'succeeded'
	};
};

export const loadLinkedImageTask = async (
	token: string,
	href: string,
	batches: ImageGenerationBatch[]
): Promise<{ batches: ImageGenerationBatch[]; taskId: string | null }> => {
	const taskId = new URL(href).searchParams.get('task');
	if (!taskId || batches.some((batch) => batch.id === taskId)) return { batches, taskId };
	const task = await getImageGenerationTask(token, taskId).catch(() => null);
	return { batches: task ? mergeGenerationTask(batches, task) : batches, taskId };
};

type ImageEventStream = { start: () => Promise<void>; stop: () => void };

const TASK_POLL_INTERVAL_MS = 10_000;
const ELAPSED_UPDATE_INTERVAL_MS = 1_000;

export const startImageTaskRuntime = (
	stream: ImageEventStream,
	poll: () => void,
	updateElapsed: () => void
): (() => void) => {
	void stream.start();
	const taskPollTimer = setInterval(poll, TASK_POLL_INTERVAL_MS);
	const elapsedTimer = setInterval(updateElapsed, ELAPSED_UPDATE_INTERVAL_MS);
	return () => {
		stream.stop();
		clearInterval(taskPollTimer);
		clearInterval(elapsedTimer);
	};
};
