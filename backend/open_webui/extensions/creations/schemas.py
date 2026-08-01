from __future__ import annotations

import base64
import binascii
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AuthorizationScope = Literal['direct', 'chat', 'tool']
CreationTask = Literal['text-to-image', 'image-to-image']
CreationSource = Literal['web', 'api', 'chat', 'tool']
CreationKind = Literal['image']
CreationAvailability = Literal['available', 'missing']
DiscoverySort = Literal['latest', 'popular']
ReactionKind = Literal['like', 'favorite']
ImageGenerationTaskStatus = Literal['queued', 'running', 'succeeded', 'failed']
CreationPublicationFilter = Literal['published', 'unpublished']
CreationListSort = Literal['newest', 'oldest']

_CURSOR_VERSION = 1
_MAX_ENCODED_CURSOR_LENGTH = 512
_MIN_CREATED_AT = 0
_MAX_CREATED_AT = 2**63 - 1
_MIN_CREATION_ID_LENGTH = 1
_MAX_CREATION_ID_LENGTH = 128
_MAX_CAPTION_CODE_POINTS = 1000
_PROMPT_PREVIEW_CHARS = 200


@dataclass(frozen=True)
class PreparedReference:
    payload: bytes
    mime_type: str
    sha256: str
    position: int


@dataclass(frozen=True)
class CapturedImageResult:
    url: str
    file_id: str
    file_user_id: str
    file_created_at: int
    mime_type: str


@dataclass(frozen=True)
class ReusedImageResult:
    url: str


@dataclass(frozen=True)
class CapturedReferenceResult:
    file_id: str
    file_user_id: str
    file_created_at: int
    mime_type: str
    sha256: str
    position: int


@dataclass(frozen=True)
class CapturedImageBatch:
    images: tuple[CapturedImageResult | ReusedImageResult, ...]
    references: tuple[CapturedReferenceResult, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.images, tuple):
            object.__setattr__(self, 'images', tuple(self.images))
        if not isinstance(self.references, tuple):
            object.__setattr__(self, 'references', tuple(self.references))


@dataclass(frozen=True)
class CreationCaptureContext:
    user_id: str
    task: CreationTask
    source: CreationSource
    prompt: str
    negative_prompt: str | None
    public_model_id: str | None
    model_name_snapshot: str | None
    params: Mapping[str, object]
    batch_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, 'params', MappingProxyType(dict(self.params)))


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class CaptionUpdateForm(_StrictModel):
    caption: str | None = Field(default=None, max_length=_MAX_CAPTION_CODE_POINTS)

    @field_validator('caption', mode='before')
    @classmethod
    def _normalize_caption(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('caption must be a string or null')
        stripped = value.strip()
        if not stripped:
            return None
        if len(stripped) > _MAX_CAPTION_CODE_POINTS:
            raise ValueError('caption exceeds the maximum unicode code point length')
        return stripped


class BulkCreationDeleteForm(_StrictModel):
    ids: tuple[str, ...] = Field(min_length=1, max_length=100)

    @field_validator('ids')
    @classmethod
    def _normalize_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(dict.fromkeys(item.strip() for item in value if item.strip()))
        if not normalized:
            raise ValueError('at least one creation id is required')
        if any(len(item) > _MAX_CREATION_ID_LENGTH for item in normalized):
            raise ValueError('creation id exceeds maximum length')
        return normalized


class BulkCreationDeleteResponse(_StrictModel):
    removed_ids: tuple[str, ...]


class PublishCreationForm(_StrictModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    show_prompt: bool = True

    @field_validator('title', 'description', mode='before')
    @classmethod
    def _normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('value must be a string or null')
        return value.strip() or None


class ImageGenerationTaskSubmitForm(_StrictModel):
    kind: CreationTask
    payload: dict[str, object]


class ImageGenerationTaskResponse(_StrictModel):
    id: str
    status: ImageGenerationTaskStatus
    kind: CreationTask
    prompt: str
    model_id: str | None
    params: dict[str, object] | None
    expected_count: int = Field(ge=1)
    result: tuple[dict[str, object], ...]
    error_code: str | None
    created_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    started_at: int | None = Field(default=None, ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    completed_at: int | None = Field(default=None, ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    updated_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)


class ImageGenerationTaskListResponse(_StrictModel):
    items: tuple[ImageGenerationTaskResponse, ...]
    next_cursor: str | None = None


class CreationPublication(_StrictModel):
    post_id: str
    status: Literal['published', 'withdrawn', 'hidden']
    title: str | None
    description: str | None
    show_prompt: bool
    published_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)


class PublicOwner(_StrictModel):
    user_id: str
    name: str | None = None
    profile_image_url: str | None = None
    deleted: bool = False


class DiscoveryPostSummary(_StrictModel):
    id: str
    title: str | None
    description: str | None
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None
    prompt_preview: str | None
    model_name: str | None
    owner: PublicOwner
    like_count: int = Field(ge=0)
    favorite_count: int = Field(ge=0)
    liked: bool
    favorited: bool
    published_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)


class DiscoveryPostDetail(DiscoveryPostSummary):
    model_id: str | None
    prompt: str | None
    negative_prompt: str | None
    params: dict[str, object] | None
    task: CreationTask


class DiscoveryPostListResponse(_StrictModel):
    items: tuple[DiscoveryPostSummary, ...]
    next_cursor: str | None


class ReactionState(_StrictModel):
    post_id: str
    kind: ReactionKind
    active: bool
    like_count: int = Field(ge=0)
    favorite_count: int = Field(ge=0)


class CreationReference(_StrictModel):
    position: int = Field(ge=0)
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None


class CreationSummary(_StrictModel):
    id: str = Field(min_length=_MIN_CREATION_ID_LENGTH, max_length=_MAX_CREATION_ID_LENGTH)
    kind: CreationKind
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None
    caption: str | None
    prompt_preview: str | None
    model_name: str | None
    task: CreationTask
    publication_status: Literal['published', 'withdrawn', 'hidden'] | None = None
    created_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    updated_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)


class CreationDetail(_StrictModel):
    id: str = Field(min_length=_MIN_CREATION_ID_LENGTH, max_length=_MAX_CREATION_ID_LENGTH)
    kind: CreationKind
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None
    caption: str | None
    model_id: str | None
    model_name: str | None
    task: CreationTask
    prompt: str
    negative_prompt: str | None
    params: dict[str, object] | None
    source: CreationSource
    batch_id: str
    references: tuple[CreationReference, ...]
    created_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    updated_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    publication: CreationPublication | None = None


class CreationListResponse(_StrictModel):
    items: tuple[CreationSummary, ...]
    next_cursor: str | None


class AdminOwner(_StrictModel):
    user_id: str = Field(min_length=_MIN_CREATION_ID_LENGTH, max_length=_MAX_CREATION_ID_LENGTH)
    name: str | None = None
    email: str | None = None
    profile_image_url: str | None = None
    deleted: bool = False


class AdminCreationSummary(_StrictModel):
    id: str = Field(min_length=_MIN_CREATION_ID_LENGTH, max_length=_MAX_CREATION_ID_LENGTH)
    kind: CreationKind
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None
    caption: str | None
    prompt_preview: str | None
    model_name: str | None
    task: CreationTask
    publication_status: Literal['published', 'withdrawn', 'hidden'] | None = None
    created_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    updated_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    owner: AdminOwner


class AdminCreationDetail(_StrictModel):
    id: str = Field(min_length=_MIN_CREATION_ID_LENGTH, max_length=_MAX_CREATION_ID_LENGTH)
    kind: CreationKind
    content_url: str | None
    availability: CreationAvailability
    mime_type: str | None
    caption: str | None
    model_id: str | None
    model_name: str | None
    task: CreationTask
    prompt: str
    negative_prompt: str | None
    params: dict[str, object] | None
    source: CreationSource
    batch_id: str
    references: tuple[CreationReference, ...]
    created_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    updated_at: int = Field(ge=_MIN_CREATED_AT, le=_MAX_CREATED_AT)
    publication: CreationPublication | None = None
    owner: AdminOwner


class AdminCreationListResponse(_StrictModel):
    items: tuple[AdminCreationSummary, ...]
    next_cursor: str | None


def encode_keyset_cursor(created_at: int, row_id: str) -> str:
    if not isinstance(created_at, int) or isinstance(created_at, bool):
        raise ValueError('created_at must be an integer')
    if not (_MIN_CREATED_AT <= created_at <= _MAX_CREATED_AT):
        raise ValueError('created_at out of signed 64-bit range')
    if not isinstance(row_id, str) or not (_MIN_CREATION_ID_LENGTH <= len(row_id) <= _MAX_CREATION_ID_LENGTH):
        raise ValueError('row id length must be between 1 and 128')

    payload = json.dumps(
        {'v': _CURSOR_VERSION, 'created_at': created_at, 'id': row_id},
        separators=(',', ':'),
        sort_keys=True,
    )
    encoded = base64.urlsafe_b64encode(payload.encode('utf-8')).rstrip(b'=').decode('ascii')
    if len(encoded) > _MAX_ENCODED_CURSOR_LENGTH:
        raise ValueError('encoded cursor exceeds the maximum length')
    return encoded


def decode_keyset_cursor(cursor: str) -> tuple[int, str]:
    if not isinstance(cursor, str) or not cursor:
        raise ValueError('invalid cursor')
    if len(cursor) > _MAX_ENCODED_CURSOR_LENGTH or re.fullmatch(r'[A-Za-z0-9_-]+', cursor) is None:
        raise ValueError('invalid cursor')

    padding = '=' * (-len(cursor) % 4)
    try:
        decoded = base64.b64decode((cursor + padding).encode('ascii'), altchars=b'-_', validate=True)
        canonical = base64.urlsafe_b64encode(decoded).rstrip(b'=').decode('ascii')
        if canonical != cursor:
            raise ValueError('non-canonical cursor')
        payload = json.loads(decoded.decode('utf-8'))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise ValueError('invalid cursor') from None

    if not isinstance(payload, dict):
        raise ValueError('invalid cursor')
    if payload.get('v') != _CURSOR_VERSION:
        raise ValueError('invalid cursor')
    created_at = payload.get('created_at')
    row_id = payload.get('id')
    if not isinstance(created_at, int) or isinstance(created_at, bool):
        raise ValueError('invalid cursor')
    if not (_MIN_CREATED_AT <= created_at <= _MAX_CREATED_AT):
        raise ValueError('invalid cursor')
    if not isinstance(row_id, str) or not (_MIN_CREATION_ID_LENGTH <= len(row_id) <= _MAX_CREATION_ID_LENGTH):
        raise ValueError('invalid cursor')
    return created_at, row_id


__all__ = [
    'AdminCreationDetail',
    'AdminCreationListResponse',
    'AdminCreationSummary',
    'AdminOwner',
    'AuthorizationScope',
    'BulkCreationDeleteForm',
    'BulkCreationDeleteResponse',
    'CaptionUpdateForm',
    'CapturedImageBatch',
    'CapturedImageResult',
    'CapturedReferenceResult',
    'CreationAvailability',
    'CreationCaptureContext',
    'CreationDetail',
    'CreationKind',
    'CreationListSort',
    'CreationListResponse',
    'CreationReference',
    'CreationSource',
    'CreationSummary',
    'CreationTask',
    'CreationPublication',
    'CreationPublicationFilter',
    'DiscoveryPostDetail',
    'DiscoveryPostListResponse',
    'DiscoveryPostSummary',
    'DiscoverySort',
    'ImageGenerationTaskListResponse',
    'ImageGenerationTaskResponse',
    'ImageGenerationTaskStatus',
    'ImageGenerationTaskSubmitForm',
    'PreparedReference',
    'PublicOwner',
    'PublishCreationForm',
    'ReactionKind',
    'ReactionState',
    'ReusedImageResult',
    'decode_keyset_cursor',
    'encode_keyset_cursor',
]
