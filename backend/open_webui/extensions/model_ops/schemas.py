from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class ModelOperationUpdate(StrictModel):
    visible: bool | None = None
    enabled: bool | None = None
    recommended: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)
    tags: tuple[str, ...] | None = Field(default=None, max_length=12)
    maintenance_message: str | None = Field(default=None, max_length=500)

    @field_validator('tags')
    @classmethod
    def normalize_tags(cls, tags: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if tags is None:
            return None
        normalized = tuple(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
        if any(len(tag) > 32 for tag in normalized):
            raise ValueError('model operation tag is too long')
        return normalized

    @field_validator('maintenance_message')
    @classmethod
    def normalize_message(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode='after')
    def require_change(self) -> ModelOperationUpdate:
        if not self.model_fields_set:
            raise ValueError('at least one model operation field is required')
        return self


class ModelOperationItem(StrictModel):
    model_id: str
    public_id: str
    name: str
    provider: str
    task: str
    visible: bool
    enabled: bool
    recommended: bool
    sort_order: int = Field(ge=0)
    tags: tuple[str, ...]
    maintenance_message: str | None
    updated_at: int | None


class ModelOperationList(StrictModel):
    items: tuple[ModelOperationItem, ...]

