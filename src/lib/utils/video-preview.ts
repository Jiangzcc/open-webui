type PreviewVideo = Pick<HTMLVideoElement, 'currentTime' | 'muted' | 'pause' | 'play'>;

export const playMutedPreview = async (
	video: PreviewVideo | null,
	hoverCapable: boolean
): Promise<boolean> => {
	if (!hoverCapable || !video) return false;
	video.muted = true;
	try {
		await video.play();
		return true;
	} catch {
		return false;
	}
};

export const stopPreview = (video: PreviewVideo | null) => {
	if (!video) return;
	video.pause();
	video.currentTime = 0;
};
