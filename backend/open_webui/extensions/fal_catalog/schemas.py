from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_MODEL_ROUTE_PATTERN = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9._/-]*[A-Za-z0-9])?$')
_PROVIDER_PATTERN = re.compile(r'^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$')
_INPUT_FIELD_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class CatalogDefaults(_StrictModel):
    text_to_image: str = Field(min_length=1, alias='text-to-image')
    image_to_image: str = Field(min_length=1, alias='image-to-image')


class CatalogManifest(_StrictModel):
    schema_version: Literal[1]
    modality: Literal['image']
    defaults: CatalogDefaults
    files: list[str] = Field(min_length=1)

    @field_validator('files')
    @classmethod
    def validate_catalog_files(cls, files: list[str]) -> list[str]:
        if len(files) != len(set(files)):
            raise ValueError('catalog file names must be unique')
        for filename in files:
            path = PurePosixPath(filename)
            if path.name != filename or path.suffix != '.json' or '..' in path.parts:
                raise ValueError('catalog files must be direct .json children')
        return files


class _InputField(_StrictModel):
    field: str = Field(min_length=1)
    source: str | None = Field(default=None, min_length=1)

    @field_validator('field', 'source')
    @classmethod
    def validate_field_name(cls, value: str | None) -> str | None:
        if value is not None and _INPUT_FIELD_PATTERN.fullmatch(value) is None:
            raise ValueError('input field names must use lowercase snake_case')
        return value


class OptionField(_InputField):
    options: list[str] = Field(min_length=1)
    default: str | None = None

    @model_validator(mode='after')
    def validate_default(self) -> OptionField:
        if len(self.options) != len(set(self.options)):
            raise ValueError('option values must be unique')
        if self.default is not None and self.default not in self.options:
            raise ValueError('option default must be included in options')
        return self


class BooleanField(_InputField):
    default: bool | None = None


class IntegerField(_InputField):
    min: int | None = None
    max: int | None = None

    @model_validator(mode='after')
    def validate_range(self) -> IntegerField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('integer field min must not exceed max')
        return self


class NumberField(_InputField):
    min: float | None = None
    max: float | None = None

    @model_validator(mode='after')
    def validate_range(self) -> NumberField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError('number field min must not exceed max')
        return self


class TextField(_InputField):
    pass


class FalImageModelDefinition(_StrictModel):
    id: str = Field(min_length=1, max_length=256)
    public_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    provider: str = Field(min_length=1, max_length=64)
    task: Literal['text-to-image', 'image-to-image']
    generation_model: str | None = Field(default=None, min_length=1, max_length=256)
    edit_model: str | None = Field(default=None, min_length=1, max_length=256)
    image_counts: list[int] | None = None
    count_field: str | None = Field(default=None, min_length=1)
    aspect_ratios: list[str] | None = None
    aspect_ratio_sizes: dict[str, str] | None = None
    aspect_ratio_field: str | None = Field(default=None, min_length=1)
    resolutions: list[str] | None = None
    default_aspect_ratio: str | None = None
    default_resolution: str | None = None
    resolution_field: str | None = Field(default=None, min_length=1)
    custom_size_field: str | None = Field(default=None, min_length=1)
    image_size_whitelist: dict[str, str] | None = None
    output_formats: list[str] | None = None
    default_output_format: str | None = None
    image_input_field: str | None = Field(default=None, min_length=1)
    image_input_max_count: int | None = Field(default=None, ge=1)
    option_fields: list[OptionField] | None = None
    boolean_fields: list[BooleanField] | None = None
    integer_fields: list[IntegerField] | None = None
    number_fields: list[NumberField] | None = None
    text_fields: list[TextField] | None = None
    supports_system_prompt: bool | None = None
    supports_prompt: bool | None = None
    hosting: Literal['serverless', 'proxy'] | None = None

    @field_validator('id', 'public_id', 'generation_model', 'edit_model')
    @classmethod
    def validate_model_route(cls, value: str | None) -> str | None:
        if value is None:
            return None
        segments = value.split('/')
        if (
            value != value.strip().strip('/')
            or _MODEL_ROUTE_PATTERN.fullmatch(value) is None
            or '//' in value
            or any(segment in {'.', '..'} for segment in segments)
        ):
            raise ValueError('model identifiers must be normalized route identifiers')
        return value

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, value: str) -> str:
        if _PROVIDER_PATTERN.fullmatch(value) is None:
            raise ValueError('provider must be a lowercase slug')
        return value

    @field_validator('image_counts')
    @classmethod
    def validate_image_counts(cls, counts: list[int] | None) -> list[int] | None:
        if counts is not None and (
            not counts or len(counts) != len(set(counts)) or any(count <= 0 for count in counts)
        ):
            raise ValueError('image counts must be unique positive integers')
        return counts

    @model_validator(mode='after')
    def validate_capabilities(self) -> FalImageModelDefinition:
        fields = [
            field.field
            for group in (
                self.option_fields,
                self.boolean_fields,
                self.integer_fields,
                self.number_fields,
                self.text_fields,
            )
            if group is not None
            for field in group
        ]
        if len(fields) != len(set(fields)):
            raise ValueError('request input field names must be unique within a model')
        if self.task == 'text-to-image' and self.generation_model is not None:
            raise ValueError('text-to-image models cannot declare generation_model')
        if self.task == 'image-to-image' and self.edit_model is not None:
            raise ValueError('image-to-image models cannot declare edit_model')
        if self.task == 'text-to-image' and (
            self.image_input_field is not None or self.image_input_max_count is not None
        ):
            raise ValueError('text-to-image models cannot declare image input fields')
        for label, default, options in (
            ('aspect ratio', self.default_aspect_ratio, self.aspect_ratios),
            ('resolution', self.default_resolution, self.resolutions),
            ('output format', self.default_output_format, self.output_formats),
        ):
            if default is not None and options and default not in options:
                raise ValueError(f'default {label} must be included in non-empty options')
        return self

    def to_legacy_dict(self) -> dict[str, object]:
        # ``None`` can be an intentional legacy override (for example a model
        # with ``count_field: null`` must not receive a quantity field). Keep
        # explicitly configured nulls while excluding schema defaults that were
        # absent from the source document.
        return self.model_dump(exclude={'public_id'}, exclude_unset=True)
