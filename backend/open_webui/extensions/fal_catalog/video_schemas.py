from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from open_webui.extensions.schema import StrictFrozenModel as _StrictModel
from pydantic import Field, field_validator, model_validator

_MODEL_ROUTE_PATTERN = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9._/-]*[A-Za-z0-9])?$')
_PROVIDER_PATTERN = re.compile(r'^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$')
_FIELD_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')

VideoTask = Literal['text-to-video', 'image-to-video', 'video-to-video']
VideoAssetRole = Literal[
    'start_image',
    'end_image',
    'source_video',
    'reference_image',
    'reference_video',
    'reference_audio',
]
VideoAudioMode = Literal['silent', 'generate', 'upload', 'preserve', 'auto']


class VideoCatalogDefaults(_StrictModel):
    text_to_video: str = Field(min_length=1, alias='text-to-video')
    image_to_video: str = Field(min_length=1, alias='image-to-video')
    video_to_video: str = Field(min_length=1, alias='video-to-video')


class VideoCatalogManifest(_StrictModel):
    schema_version: Literal[1]
    modality: Literal['video']
    defaults: VideoCatalogDefaults
    files: list[str] = Field(min_length=1)

    @field_validator('files')
    @classmethod
    def validate_files(cls, files: list[str]) -> list[str]:
        if len(files) != len(set(files)):
            raise ValueError('video catalog file names must be unique')
        for filename in files:
            path = PurePosixPath(filename)
            if path.name != filename or path.suffix != '.json' or '..' in path.parts:
                raise ValueError('video catalog files must be direct .json children')
        return files


class VideoAssetInput(_StrictModel):
    role: VideoAssetRole
    field: str = Field(min_length=1)
    required: bool = False
    multiple: bool = False
    max_count: int = Field(default=1, ge=1, le=20)
    mime_types: list[str] = Field(min_length=1)
    max_bytes: int = Field(gt=0, le=500 * 1024 * 1024)
    max_total_bytes: int | None = Field(default=None, gt=0, le=500 * 1024 * 1024)
    min_duration_seconds: float | None = Field(default=None, ge=0, le=300)
    max_duration_seconds: float | None = Field(default=None, gt=0, le=300)

    @field_validator('field')
    @classmethod
    def validate_field(cls, value: str) -> str:
        if _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video input fields must use lowercase snake_case')
        return value

    @field_validator('mime_types')
    @classmethod
    def validate_mime_types(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or any('/' not in value for value in values):
            raise ValueError('video asset mime types must be unique MIME values')
        return values

    @model_validator(mode='after')
    def validate_constraints(self) -> VideoAssetInput:
        if not self.multiple and self.max_count != 1:
            raise ValueError('single video asset inputs must have max_count 1')
        if (
            self.min_duration_seconds is not None
            and self.max_duration_seconds is not None
            and self.min_duration_seconds > self.max_duration_seconds
        ):
            raise ValueError('video asset minimum duration must not exceed maximum duration')
        return self


class VideoAudioOption(_StrictModel):
    mode: VideoAudioMode
    values: dict[str, bool | str | int | float | None] = Field(default_factory=dict)

    @field_validator('values')
    @classmethod
    def validate_values(cls, values: dict[str, object]) -> dict[str, object]:
        if any(_FIELD_PATTERN.fullmatch(key) is None for key in values):
            raise ValueError('video audio payload fields must use lowercase snake_case')
        return values


class VideoOptionField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    options: list[str] = Field(min_length=1)
    default: str | None = None
    advanced: bool = True

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video option fields must use lowercase snake_case')
        return value

    @model_validator(mode='after')
    def validate_default(self) -> VideoOptionField:
        if len(self.options) != len(set(self.options)):
            raise ValueError('video option values must be unique')
        if self.default is not None and self.default not in self.options:
            raise ValueError('video option default must be included in options')
        return self


class VideoBooleanField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    default: bool | None = None
    advanced: bool = True

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video boolean fields must use lowercase snake_case')
        return value


class VideoIntegerField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    min: int | None = None
    max: int | None = None
    default: int | None = None
    advanced: bool = True

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video integer fields must use lowercase snake_case')
        return value

    @model_validator(mode='after')
    def validate_range(self) -> VideoIntegerField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('video integer minimum must not exceed maximum')
        if self.default is not None and (
            (self.min is not None and self.default < self.min) or (self.max is not None and self.default > self.max)
        ):
            raise ValueError('video integer default must be within range')
        return self


class VideoNumberField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    min: float | None = None
    max: float | None = None
    step: float | None = Field(default=None, gt=0)
    default: float | None = None
    advanced: bool = True

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video number fields must use lowercase snake_case')
        return value

    @model_validator(mode='after')
    def validate_range(self) -> VideoNumberField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('video number minimum must not exceed maximum')
        if self.default is not None and (
            (self.min is not None and self.default < self.min) or (self.max is not None and self.default > self.max)
        ):
            raise ValueError('video number default must be within range')
        return self


class VideoTextField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    max_length: int = Field(default=2000, ge=1, le=10000)
    advanced: bool = True

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video text fields must use lowercase snake_case')
        return value


class VideoJsonField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)
    required: bool = False
    primary_input: bool = False
    max_length: int = Field(default=20000, ge=2, le=100000)
    advanced: bool = True
    format: Literal['json'] = 'json'

    @field_validator('field', 'source')
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video JSON fields must use lowercase snake_case')
        return value

    @model_validator(mode='after')
    def validate_primary_input(self) -> VideoJsonField:
        if self.primary_input and not self.required:
            raise ValueError('primary JSON inputs must be required')
        return self


class FalVideoModelDefinition(_StrictModel):
    id: str = Field(min_length=1, max_length=256)
    public_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    provider: str = Field(min_length=1, max_length=64)
    task: VideoTask
    prompt_required: bool = True
    duration_field: str | None = Field(default=None, min_length=1)
    durations: list[str] | None = None
    default_duration: str | None = None
    duration_min: float | None = Field(default=None, ge=0, le=300)
    duration_max: float | None = Field(default=None, gt=0, le=300)
    duration_step: float | None = Field(default=None, gt=0, le=60)
    aspect_ratio_field: str | None = Field(default=None, min_length=1)
    aspect_ratios: list[str] | None = None
    default_aspect_ratio: str | None = None
    resolution_field: str | None = Field(default=None, min_length=1)
    resolutions: list[str] | None = None
    default_resolution: str | None = None
    audio_options: list[VideoAudioOption] | None = None
    default_audio_mode: VideoAudioMode | None = None
    asset_inputs: list[VideoAssetInput] | None = None
    option_fields: list[VideoOptionField] | None = None
    boolean_fields: list[VideoBooleanField] | None = None
    integer_fields: list[VideoIntegerField] | None = None
    number_fields: list[VideoNumberField] | None = None
    text_fields: list[VideoTextField] | None = None
    json_fields: list[VideoJsonField] | None = None
    fixed_fields: dict[str, bool | str | int | float | None] = Field(default_factory=dict)
    output_field: str = Field(default='video', min_length=1)
    output_mime_types: list[str] = Field(default_factory=lambda: ['video/mp4'], min_length=1)

    @field_validator('id', 'public_id')
    @classmethod
    def validate_model_route(cls, value: str) -> str:
        segments = value.split('/')
        if (
            value != value.strip().strip('/')
            or _MODEL_ROUTE_PATTERN.fullmatch(value) is None
            or '//' in value
            or any(segment in {'.', '..'} for segment in segments)
        ):
            raise ValueError('video model identifiers must be normalized route identifiers')
        return value

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, value: str) -> str:
        if _PROVIDER_PATTERN.fullmatch(value) is None:
            raise ValueError('video provider must be a lowercase slug')
        return value

    @field_validator(
        'duration_field',
        'aspect_ratio_field',
        'resolution_field',
        'output_field',
    )
    @classmethod
    def validate_request_field(cls, value: str | None) -> str | None:
        if value is not None and _FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('video request fields must use lowercase snake_case')
        return value

    @field_validator('fixed_fields')
    @classmethod
    def validate_fixed_fields(cls, values: dict[str, object]) -> dict[str, object]:
        if any(_FIELD_PATTERN.fullmatch(key) is None for key in values):
            raise ValueError('video fixed fields must use lowercase snake_case')
        return values

    def _validate_outputs(self) -> None:
        if len(self.output_mime_types) != len(set(self.output_mime_types)) or any(
            not value.startswith('video/') for value in self.output_mime_types
        ):
            raise ValueError('video outputs must use unique video MIME types')

    def _validate_duration(self) -> None:
        has_range = self.duration_min is not None or self.duration_max is not None
        if bool(self.durations) == has_range and (self.durations is not None or has_range):
            raise ValueError('video duration must use either options or numeric range')
        if self.durations is not None:
            if len(self.durations) != len(set(self.durations)):
                raise ValueError('video duration values must be unique')
            if self.default_duration is not None and self.default_duration not in self.durations:
                raise ValueError('default video duration must be included in options')
            return
        if self.default_duration is None:
            return
        try:
            default_duration = float(self.default_duration)
        except ValueError as error:
            raise ValueError('range video duration default must be numeric') from error
        if (self.duration_min is not None and default_duration < self.duration_min) or (
            self.duration_max is not None and default_duration > self.duration_max
        ):
            raise ValueError('default video duration must be within range')

    def _validate_primary_options(self) -> None:
        for label, default, options in (
            ('aspect ratio', self.default_aspect_ratio, self.aspect_ratios),
            ('resolution', self.default_resolution, self.resolutions),
        ):
            if options is not None and len(options) != len(set(options)):
                raise ValueError(f'video {label} values must be unique')
            if default is not None and options and default not in options:
                raise ValueError(f'default video {label} must be included in options')

    def _validate_audio(self) -> None:
        audio_modes = [option.mode for option in self.audio_options or ()]
        if len(audio_modes) != len(set(audio_modes)):
            raise ValueError('video audio modes must be unique')
        if self.default_audio_mode is not None and self.default_audio_mode not in audio_modes:
            raise ValueError('default video audio mode must be included in options')

    def _validate_assets(self) -> list[str]:
        assets = self.asset_inputs or ()
        roles = [asset.role for asset in assets]
        fields = [asset.field for asset in assets]
        if len(roles) != len(set(roles)) or len(fields) != len(set(fields)):
            raise ValueError('video asset roles and fields must be unique')
        required_roles = {asset.role for asset in assets if asset.required}
        expected = {'image-to-video': 'start_image', 'video-to-video': 'source_video'}.get(self.task)
        has_primary_json = any(field.required and field.primary_input for field in self.json_fields or ())
        if expected is not None and expected not in required_roles and not has_primary_json:
            raise ValueError(f'{self.task} models must require {expected}')
        return fields

    def _validate_provider_fields(self, asset_fields: list[str]) -> None:
        groups = (
            self.option_fields,
            self.boolean_fields,
            self.integer_fields,
            self.number_fields,
            self.text_fields,
            self.json_fields,
        )
        dynamic_fields = [field.field for group in groups if group is not None for field in group]
        provider_fields = asset_fields + dynamic_fields + list(self.fixed_fields)
        if len(provider_fields) != len(set(provider_fields)):
            raise ValueError('video provider request fields must be unique')

    @model_validator(mode='after')
    def validate_capabilities(self) -> FalVideoModelDefinition:
        self._validate_outputs()
        self._validate_duration()
        self._validate_primary_options()
        self._validate_audio()
        self._validate_provider_fields(self._validate_assets())
        return self
