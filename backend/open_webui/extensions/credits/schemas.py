import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Annotated, Generic, Literal, TypeVar

from open_webui.extensions.credits.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_ADJUSTMENT,
    MAX_CREDIT_VALUE,
    MAX_DECIMAL_INPUT_LENGTH,
    MAX_DIMENSION_KEY_LENGTH,
    MAX_DISCRETE_VALUE_KEY_LENGTH,
    MAX_EXACT_MAP_ENTRIES,
    MAX_IDEMPOTENCY_KEY_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_NUMERIC_TIERS,
    MAX_PAGE_SIZE,
    MAX_PRICE_DECIMAL_PLACES,
    MAX_PRICE_DIGITS,
    MAX_PRICE_VALUE,
    MAX_REQUEST_ID_LENGTH,
    MAX_RULE_DIMENSIONS,
    MAX_USER_EMAIL_LENGTH,
    MAX_USER_ID_LENGTH,
    MAX_USER_NAME_LENGTH,
)
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    field_serializer,
    field_validator,
    model_validator,
)

AdjustmentReason = Literal[
    'offline_recharge',
    'promotion_gift',
    'manual_refund',
    'accounting_correction',
    'violation_deduction',
    'other',
]
AuditSource = Literal['web', 'api', 'api_key', 'internal_admin']
IdempotencyKey = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=MAX_IDEMPOTENCY_KEY_LENGTH,
        pattern=r'^[\x20-\x7E]+$',
    ),
]


def parse_decimal_string(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError('value must be a decimal string')
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError('value must be a decimal string') from error


def parse_exact_positive_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError('value must be a positive integer or decimal string')
    if isinstance(value, str) and len(value) > MAX_DECIMAL_INPUT_LENGTH:
        raise ValueError('decimal string is too long')
    if isinstance(value, int) and value > MAX_CREDIT_VALUE:
        raise ValueError('integer is too large')
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError('value must be a positive integer or decimal string') from error


PositivePrice = Annotated[
    Decimal,
    BeforeValidator(parse_decimal_string),
    Field(
        gt=0,
        le=MAX_PRICE_VALUE,
        max_digits=MAX_PRICE_DIGITS,
        decimal_places=MAX_PRICE_DECIMAL_PLACES,
        allow_inf_nan=False,
    ),
]
PositiveExactDecimal = Annotated[
    Decimal,
    BeforeValidator(parse_exact_positive_decimal),
    Field(gt=0, le=MAX_CREDIT_VALUE, allow_inf_nan=False),
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class AdjustmentRequest(StrictModel):
    direction: Literal['increase', 'decrease']
    amount: StrictInt = Field(gt=0, le=MAX_ADJUSTMENT)
    reason_code: AdjustmentReason
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)

    @field_validator('note')
    @classmethod
    def normalize_note(cls, note: str | None) -> str | None:
        if note is None:
            return None
        return note.strip() or None

    @model_validator(mode='after')
    def require_note_for_other(self) -> 'AdjustmentRequest':
        if self.reason_code == 'other' and not self.note:
            raise ValueError('note is required when reason_code is other')
        return self


@dataclass(frozen=True)
class RequestAuditContext:
    source: AuditSource
    request_id: str
    remote_address_hash: str | None

    def __post_init__(self) -> None:
        if self.source not in ('web', 'api', 'api_key', 'internal_admin'):
            raise ValueError('unsupported audit source')
        if not re.fullmatch(rf'[\x20-\x7E]{{1,{MAX_REQUEST_ID_LENGTH}}}', self.request_id):
            raise ValueError('request_id must contain 1 to 128 printable ASCII characters')
        if self.remote_address_hash is not None and not re.fullmatch(r'[0-9a-f]{64}', self.remote_address_hash):
            raise ValueError('remote_address_hash must be a lowercase SHA-256 hex digest')


class DimensionRuleBase(StrictModel):
    key: str = Field(max_length=MAX_DIMENSION_KEY_LENGTH)

    @field_validator('key')
    @classmethod
    def normalize_key(cls, key: str) -> str:
        normalized = key.strip()
        if not normalized:
            raise ValueError('dimension key must not be blank')
        return normalized


class ExactMapRule(DimensionRuleBase):
    kind: Literal['exact_map']
    values: dict[str, PositivePrice] = Field(min_length=1, max_length=MAX_EXACT_MAP_ENTRIES)

    @field_validator('values', mode='before')
    @classmethod
    def normalize_value_keys(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized_values: dict[str, object] = {}
        for key, value in values.items():
            if not isinstance(key, str):
                raise ValueError('exact_map keys must be strings')
            normalized_key = key.strip()
            if not normalized_key or len(normalized_key) > MAX_DISCRETE_VALUE_KEY_LENGTH:
                raise ValueError('exact_map key has invalid length')
            if normalized_key in normalized_values:
                raise ValueError('exact_map keys must be unique after normalization')
            normalized_values[normalized_key] = value
        return normalized_values


class NumericTier(StrictModel):
    max_value: PositiveExactDecimal = Field(alias='max')
    multiplier: PositivePrice


class NumericTierRule(DimensionRuleBase):
    kind: Literal['numeric_tier']
    tiers: list[NumericTier] = Field(min_length=1, max_length=MAX_NUMERIC_TIERS)

    @field_validator('tiers')
    @classmethod
    def validate_tier_order(cls, tiers: list[NumericTier]) -> list[NumericTier]:
        boundaries = [tier.max_value for tier in tiers]
        if any(current <= previous for previous, current in zip(boundaries, boundaries[1:], strict=False)):
            raise ValueError('numeric tier boundaries must be strictly increasing')
        return tiers


class UnitBlocksRule(DimensionRuleBase):
    kind: Literal['unit_blocks']
    block_size: PositiveExactDecimal
    multiplier_per_block: PositivePrice


class ProportionalRule(DimensionRuleBase):
    kind: Literal['proportional']
    unit_size: PositiveExactDecimal


class QuantityRule(DimensionRuleBase):
    kind: Literal['quantity']

    def validate_request_value(self, value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError('quantity request value must be a positive integer')
        return value


DimensionRule = Annotated[
    ExactMapRule | NumericTierRule | UnitBlocksRule | ProportionalRule | QuantityRule,
    Field(discriminator='kind'),
]


class PriceRuleSet(StrictModel):
    schema_version: Literal[1]
    dimensions: list[DimensionRule] = Field(max_length=MAX_RULE_DIMENSIONS)

    @field_validator('dimensions')
    @classmethod
    def reject_duplicate_dimension_keys(cls, dimensions: list[DimensionRule]) -> list[DimensionRule]:
        keys = [dimension.key for dimension in dimensions]
        if len(keys) != len(set(keys)):
            raise ValueError('dimension keys must be unique')
        return dimensions


class PaginationParams(StrictModel):
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)


@dataclass(frozen=True)
class UserSnapshot:
    id: str
    name: str | None
    email: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id or len(self.id) > MAX_USER_ID_LENGTH:
            raise ValueError('user id must be a non-empty string within the database limit')
        if self.name is not None and (not isinstance(self.name, str) or len(self.name) > MAX_USER_NAME_LENGTH):
            raise ValueError('user name must be a string within the database limit or None')
        if self.email is not None and (not isinstance(self.email, str) or len(self.email) > MAX_USER_EMAIL_LENGTH):
            raise ValueError('user email must be a string within the database limit or None')


class LedgerQuery(PaginationParams):
    since: int | None = Field(default=None, ge=0)
    until: int | None = Field(default=None, ge=0)
    cursor_created_at: int | None = Field(default=None, ge=0)
    cursor_id: str | None = Field(default=None, min_length=1, max_length=128)

    @model_validator(mode='after')
    def validate_ranges_and_cursor(self) -> 'LedgerQuery':
        if self.since is not None and self.until is not None and self.since > self.until:
            raise ValueError('since must not be after until')
        if (self.cursor_created_at is None) != (self.cursor_id is None):
            raise ValueError('cursor_created_at and cursor_id must be supplied together')
        return self


class UserLedgerQuery(LedgerQuery):
    category: Literal['income', 'consumption', 'adjustment'] | None = None


class AdminLedgerQuery(LedgerQuery):
    user_id: str | None = Field(default=None, min_length=1, max_length=128)
    entry_type: Literal['consumption', 'admin_adjustment', 'system_adjustment'] | None = None
    reason_code: AdjustmentReason | None = None
    service_type: str | None = Field(default=None, min_length=1, max_length=64)
    resource_id: str | None = Field(default=None, min_length=1, max_length=128)
    action: str | None = Field(default=None, min_length=1, max_length=64)


class ReconciliationQuery(PaginationParams):
    status: Literal['failed', 'unknown'] | None = None
    compensated: bool | None = None
    user_id: str | None = Field(default=None, min_length=1, max_length=128)
    skip: int = Field(default=0, ge=0)


class ReconciliationItem(StrictModel):
    usage_id: str
    user_id: str
    user_name_snapshot: str | None
    user_email_snapshot: str | None
    status: Literal['failed', 'unknown']
    charged_credits: int = Field(ge=0)
    resource_id: str
    action: str
    channel: str
    error_code: str | None
    error_summary: str | None
    consumption_ledger_id: str | None
    compensation_ledger_id: str | None
    created_at: int = Field(ge=0)
    completed_at: int | None = Field(default=None, ge=0)


class ReconciliationPage(StrictModel):
    items: tuple[ReconciliationItem, ...]
    total: int = Field(ge=0)


class CompensationRequest(StrictModel):
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)

    @field_validator('note')
    @classmethod
    def normalize_compensation_note(cls, note: str | None) -> str | None:
        return note.strip() or None if note is not None else None


T = TypeVar('T')


def _freeze_snapshot_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_snapshot_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_snapshot_value(item) for item in value)
    return value


def _serialize_snapshot_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _serialize_snapshot_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_serialize_snapshot_value(item) for item in value]
    return value


class LedgerCursor(StrictModel):
    created_at: int = Field(ge=0)
    id: str = Field(min_length=1, max_length=128)


class LedgerItem(StrictModel):
    id: str
    user_id: str
    amount: int
    balance_before: int
    balance_after: int
    entry_type: str
    reason_code: str | None
    note: str | None
    user_name_snapshot: str | None
    user_email_snapshot: str | None
    operator_id: str | None
    operator_name_snapshot: str | None
    operator_email_snapshot: str | None
    request_source: str
    request_id: str
    service_type: str | None
    resource_id: str | None
    action: str | None
    usage_status: Literal['debited', 'invoking', 'succeeded', 'failed', 'unknown'] | None
    pricing_snapshot: Mapping[str, object] | None
    metadata_snapshot: Mapping[str, object] | None
    created_at: int

    @field_validator('pricing_snapshot', 'metadata_snapshot')
    @classmethod
    def freeze_snapshots(cls, value: Mapping[str, object] | None) -> Mapping[str, object] | None:
        frozen = _freeze_snapshot_value(value)
        return frozen if isinstance(frozen, Mapping) else None

    @field_serializer('pricing_snapshot', 'metadata_snapshot')
    def serialize_snapshots(self, value: Mapping[str, object] | None) -> dict[str, object] | None:
        serialized = _serialize_snapshot_value(value)
        return serialized if isinstance(serialized, dict) else None


class Page(StrictModel, Generic[T]):
    items: tuple[T, ...]
    next_cursor: LedgerCursor | None
