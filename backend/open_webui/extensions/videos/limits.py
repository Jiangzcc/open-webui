from __future__ import annotations

from open_webui.extensions.generation_gate import GenerationGate

# 视频任务通常更重、更慢：提交速率与每用户进行中任务上限都比图片更保守。
VIDEO_GENERATION_RATE_LIMIT = 4
VIDEO_GENERATION_RATE_WINDOW_SECONDS = 60
VIDEO_GENERATION_MAX_CONCURRENT_PER_USER = 1

_gate = GenerationGate(
    bucket_prefix='videos:generation',
    limit=VIDEO_GENERATION_RATE_LIMIT,
    window_seconds=VIDEO_GENERATION_RATE_WINDOW_SECONDS,
    max_concurrent_per_user=VIDEO_GENERATION_MAX_CONCURRENT_PER_USER,
)

enforce_video_generation_rate = _gate.enforce_rate
acquire_video_generation_slot = _gate.acquire_slot
release_video_generation_slot = _gate.release_slot


__all__ = [
    'acquire_video_generation_slot',
    'enforce_video_generation_rate',
    'release_video_generation_slot',
]
