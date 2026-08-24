from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class VideoExecutionError(Exception):
    def __init__(
        self,
        code: str,
        message: str | None = None,
        *,
        provider_submitted: bool = False,
        provider_completed: bool = False,
        retryable: bool = False,
    ):
        super().__init__(message or code)
        self.code = code[:64]
        # Provider completion implies submission. Delivery failures after this
        # boundary must retain the prepaid charge for recovery/reconciliation.
        self.provider_submitted = provider_submitted or provider_completed
        self.provider_completed = provider_completed
        self.retryable = retryable


@dataclass(frozen=True)
class VideoExecutionOutput:
    video_path: Path
    content_type: str
    duration_seconds: int | None = None


__all__ = ['VideoExecutionError', 'VideoExecutionOutput']
