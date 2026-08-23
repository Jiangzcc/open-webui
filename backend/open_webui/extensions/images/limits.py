from __future__ import annotations

from open_webui.extensions.generation_gate import GenerationGate

IMAGE_GENERATION_RATE_LIMIT = 10
IMAGE_GENERATION_RATE_WINDOW_SECONDS = 60
IMAGE_GENERATION_MAX_CONCURRENT_PER_USER = 3

_gate = GenerationGate(
    bucket_prefix='images:generation',
    limit=IMAGE_GENERATION_RATE_LIMIT,
    window_seconds=IMAGE_GENERATION_RATE_WINDOW_SECONDS,
    max_concurrent_per_user=IMAGE_GENERATION_MAX_CONCURRENT_PER_USER,
)

enforce_image_generation_rate = _gate.enforce_rate
acquire_image_generation_slot = _gate.acquire_slot
release_image_generation_slot = _gate.release_slot


__all__ = [
    'acquire_image_generation_slot',
    'enforce_image_generation_rate',
    'release_image_generation_slot',
]
