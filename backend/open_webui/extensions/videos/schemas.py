from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from open_webui.extensions.creations.task_states import GenerationTaskStatus

VideoTask = Literal['text-to-video', 'image-to-video', 'video-to-video']
# 复盘 P2：任务状态枚举收敛至 task_states 单一事实源（此前 6+ 处散落）。
VideoTaskStatus = GenerationTaskStatus


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class VideoAssetReference(_StrictModel):
    role: Literal[
        'start_image',
        'end_image',
        'source_video',
        'reference_image',
        'reference_video',
        'reference_audio',
    ]
    file_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')


class VideoTaskSubmitForm(_StrictModel):
    task: VideoTask
    model: str = Field(min_length=1, max_length=128)
    prompt: str = Field(default='', max_length=10000)
    assets: tuple[VideoAssetReference, ...] = Field(default=(), max_length=20)
    params: dict[str, bool | str | int | float | None] = Field(default_factory=dict)

    @field_validator('prompt')
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        return value.strip()


class VideoTaskResult(_StrictModel):
    creation_id: str
    file_id: str
    # 复盘 P1：封面是展示增强而非视频本体——真实视频封面提取失败时按
    # 无封面交付（此前静默降级 mock 欢迎图，违反 mock 与生产路径隔离）。
    # 前端已把 poster_url 视为可空（列表回退 content_url、video poster 传
    # undefined）。
    poster_file_id: str | None = None
    url: str
    poster_url: str | None = None
    duration_seconds: int = Field(gt=0)
    mime_type: Literal['video/mp4'] = 'video/mp4'


class VideoTaskResponse(_StrictModel):
    id: str
    status: VideoTaskStatus
    task: VideoTask
    prompt: str
    model_id: str
    params: dict[str, object]
    assets: tuple[VideoAssetReference, ...]
    result: VideoTaskResult | None
    error_code: str | None
    created_at: int = Field(ge=0)
    started_at: int | None = Field(default=None, ge=0)
    completed_at: int | None = Field(default=None, ge=0)
    updated_at: int = Field(ge=0)


class VideoTaskListResponse(_StrictModel):
    items: tuple[VideoTaskResponse, ...]
    next_cursor: str | None = None
