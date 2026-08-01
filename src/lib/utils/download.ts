/**
 * 通用下载工具：抽自 Images.svelte 与 CreationsLibrary.svelte 的重复实现。
 *
 * - downloadBlob：触发单文件下载；延迟释放 ObjectURL，避免某些引擎的下载
 *   fetch 尚未读完 blob 即被撤销而产生 0 字节文件（swagger-ui 同样用
 *   setTimeout 规避该竞态）。
 * - zipAndDownload：并发抓取多个 URL 打包成 ZIP 下载，文件名由调用方决定。
 */

import JSZip from 'jszip';

export const blobExtension = (blob: Blob): string => {
	const sub = blob.type?.split('/')[1]?.replace('jpeg', 'jpg');
	return sub && /^[a-z0-9]+$/.test(sub) ? sub : 'png';
};

export const downloadBlob = (blob: Blob, filename: string) => {
	const url = URL.createObjectURL(blob);
	const anchor = document.createElement('a');
	anchor.href = url;
	anchor.download = filename;
	document.body.appendChild(anchor);
	anchor.click();
	anchor.remove();
	setTimeout(() => URL.revokeObjectURL(url), 4_000);
};

export type ZipEntry = {
	url: string;
	/** 入口文件名，调用方可借助 blobExtension(blob) 决定扩展名。 */
	filename: string | ((index: number, blob: Blob) => string);
};

export const zipAndDownload = async (entries: ZipEntry[], zipName: string) => {
	const zip = new JSZip();
	await Promise.all(
		entries.map(async (entry, index) => {
			const response = await fetch(entry.url);
			if (!response.ok) throw new Error('download failed');
			const blob = await response.blob();
			const filename =
				typeof entry.filename === 'function' ? entry.filename(index, blob) : entry.filename;
			zip.file(filename, blob);
		})
	);
	const archive = await zip.generateAsync({ type: 'blob' });
	downloadBlob(archive, zipName);
};
