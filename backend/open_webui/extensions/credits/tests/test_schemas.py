from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest
from open_webui.extensions.credits.constants import (
    MAX_ADJUSTMENT,
    MAX_CREDIT_VALUE,
    MAX_DIMENSION_KEY_LENGTH,
    MAX_DISCRETE_VALUE_KEY_LENGTH,
    MAX_EXACT_MAP_ENTRIES,
    MAX_NOTE_LENGTH,
    MAX_NUMERIC_TIERS,
    MAX_RULE_DIMENSIONS,
)
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.schemas import (
    AdjustmentRequest,
    ExactMapRule,
    IdempotencyKey,
    LedgerItem,
    NumericTierRule,
    PaginationParams,
    PositivePrice,
    PriceRuleSet,
    ProportionalRule,
    QuantityRule,
    RequestAuditContext,
    UnitBlocksRule,
)
from pydantic import TypeAdapter, ValidationError


@pytest.mark.parametrize('amount', [0, -1, MAX_ADJUSTMENT + 1])
def test_adjustment_amount_must_be_within_approved_bounds(amount: int) -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(direction='increase', amount=amount, reason_code='offline_recharge')


@pytest.mark.parametrize('amount', [True, '1', 1.0])
def test_adjustment_amount_requires_strict_integer(amount: object) -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(direction='increase', amount=amount, reason_code='offline_recharge')


def test_adjustment_rejects_unknown_reason() -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(direction='increase', amount=1, reason_code='not_approved')


@pytest.mark.parametrize('note', [None, '', '   '])
def test_other_adjustment_requires_non_empty_note(note: str | None) -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(direction='increase', amount=1, reason_code='other', note=note)


def test_adjustment_normalizes_optional_note_without_mutating_input() -> None:
    body = {
        'direction': 'decrease',
        'amount': MAX_ADJUSTMENT,
        'reason_code': 'manual_refund',
        'note': '  duplicate charge  ',
    }
    request = AdjustmentRequest.model_validate(body)

    assert request.note == 'duplicate charge'
    assert body['note'] == '  duplicate charge  '
    assert AdjustmentRequest(direction='increase', amount=1, reason_code='promotion_gift', note='   ').note is None


def test_adjustment_rejects_note_over_approved_limit() -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(
            direction='increase', amount=1, reason_code='promotion_gift', note='n' * (MAX_NOTE_LENGTH + 1)
        )


@pytest.mark.parametrize('source', ['web', 'api', 'api_key', 'internal_admin'])
def test_request_audit_accepts_approved_sources(source: str) -> None:
    context = RequestAuditContext(source=source, request_id='r' * 128, remote_address_hash=None)

    assert context.source == source
    with pytest.raises(FrozenInstanceError):
        context.request_id = 'replacement'


@pytest.mark.parametrize('source', ['browser', '', 'admin'])
def test_request_audit_rejects_unknown_source(source: str) -> None:
    with pytest.raises((TypeError, ValueError)):
        RequestAuditContext(source=source, request_id='request-1', remote_address_hash=None)


@pytest.mark.parametrize('request_id', ['', 'r' * 129, 'line\nbreak', 'tab\tvalue', 'café', '\x7f'])
def test_request_audit_requires_printable_ascii_request_id(request_id: str) -> None:
    with pytest.raises(ValueError):
        RequestAuditContext(source='web', request_id=request_id, remote_address_hash=None)


def test_request_audit_accepts_canonical_sha256_remote_address_hash() -> None:
    context = RequestAuditContext(source='api', request_id='request-1', remote_address_hash='a0' * 32)

    assert context.remote_address_hash == 'a0' * 32


@pytest.mark.parametrize('value', ['127.0.0.1', 'a' * 63, 'a' * 65, 'A' * 64, 'g' * 64, 'hash'])
def test_request_audit_rejects_noncanonical_remote_address_hash(value: str) -> None:
    with pytest.raises(ValueError):
        RequestAuditContext(source='api', request_id='request-1', remote_address_hash=value)


def test_adjustment_body_cannot_spoof_audit_fields() -> None:
    with pytest.raises(ValidationError):
        AdjustmentRequest(
            direction='increase',
            amount=1,
            reason_code='promotion_gift',
            source='internal_admin',
            request_id='forged',
            remote_address_hash='forged',
        )


@pytest.mark.parametrize('key', ['a', 'visible ASCII 123 !@#', '~' * 128])
def test_idempotency_key_accepts_printable_ascii(key: str) -> None:
    assert TypeAdapter(IdempotencyKey).validate_python(key) == key


@pytest.mark.parametrize('key', ['', 'a' * 129, 'line\nbreak', 'tab\tkey', 'café', '\x7f'])
def test_idempotency_key_rejects_invalid_format(key: str) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(IdempotencyKey).validate_python(key)


@pytest.mark.parametrize(
    'value',
    ['0', '-1', 'NaN', 'Infinity', '1000000.00000001', '1.000000001', '12345678901.12345678'],
)
def test_positive_price_rejects_non_positive_non_finite_out_of_range_or_over_precision(value: str) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(PositivePrice).validate_python(value)


@pytest.mark.parametrize('value', [1, 1.0, True, Decimal('1')])
def test_positive_price_only_accepts_decimal_string_input(value: object) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(PositivePrice).validate_python(value)


def test_positive_price_accepts_approved_decimal_boundary() -> None:
    assert TypeAdapter(PositivePrice).validate_python('1000000') == Decimal('1000000')


def test_price_rule_set_strictly_contains_only_schema_version_and_dimensions() -> None:
    rules = PriceRuleSet(schema_version=1, dimensions=[])

    assert rules.model_dump() == {'schema_version': 1, 'dimensions': []}
    with pytest.raises(ValidationError):
        PriceRuleSet(schema_version=1, dimensions=[], base_price='1')


def test_exact_map_requires_entries_and_valid_multipliers() -> None:
    with pytest.raises(ValidationError):
        ExactMapRule(key='quality', kind='exact_map', values={})
    with pytest.raises(ValidationError):
        ExactMapRule(key='quality', kind='exact_map', values={'hd': '0'})

    rule = ExactMapRule(key='quality', kind='exact_map', values={'hd': '1.25'})
    assert rule.values == {'hd': Decimal('1.25')}


@pytest.mark.parametrize('value', [1, 1.0, True, Decimal('1')])
def test_exact_map_multiplier_only_accepts_decimal_string_input(value: object) -> None:
    with pytest.raises(ValidationError):
        ExactMapRule(key='quality', kind='exact_map', values={'hd': value})


def test_exact_map_validates_and_normalizes_keys_without_mutating_input() -> None:
    values = {' hd ': '1'}
    rule = ExactMapRule(key=' quality ', kind='exact_map', values=values)

    assert rule.key == 'quality'
    assert rule.values == {'hd': Decimal('1')}
    assert values == {' hd ': '1'}

    for key in ('   ', 'k' * (MAX_DIMENSION_KEY_LENGTH + 1)):
        with pytest.raises(ValidationError):
            ExactMapRule(key=key, kind='exact_map', values={'hd': '1'})
    for value_key in ('   ', 'v' * (MAX_DISCRETE_VALUE_KEY_LENGTH + 1)):
        with pytest.raises(ValidationError):
            ExactMapRule(key='quality', kind='exact_map', values={value_key: '1'})


def test_exact_map_rejects_more_than_approved_entry_limit() -> None:
    values = {f'v{index}': '1' for index in range(MAX_EXACT_MAP_ENTRIES + 1)}
    with pytest.raises(ValidationError):
        ExactMapRule(key='quality', kind='exact_map', values=values)


def test_numeric_tiers_use_max_and_must_be_strictly_increasing() -> None:
    with pytest.raises(ValidationError):
        NumericTierRule(
            key='pixels',
            kind='numeric_tier',
            tiers=[{'max': 1024, 'multiplier': '1'}, {'max': 1024, 'multiplier': '2'}],
        )

    rule = NumericTierRule(
        key='pixels',
        kind='numeric_tier',
        tiers=[{'max': 1024, 'multiplier': '1'}, {'max': 2048, 'multiplier': '2'}],
    )
    assert [tier.max_value for tier in rule.tiers] == [1024, 2048]
    assert rule.model_dump(by_alias=True)['tiers'][0]['max'] == Decimal('1024')

    with pytest.raises(ValidationError):
        NumericTierRule(key='pixels', kind='numeric_tier', tiers=[{'up_to': 1024, 'multiplier': '1'}])


def test_numeric_tier_boundaries_require_strict_bounded_exact_values() -> None:
    accepted = NumericTierRule(
        key='pixels',
        kind='numeric_tier',
        tiers=[{'max': MAX_CREDIT_VALUE, 'multiplier': '1'}],
    )
    assert accepted.tiers[0].max_value == Decimal(MAX_CREDIT_VALUE)

    for value in (True, 1.0, Decimal('1'), 0, -1, '0', '-1', 'NaN', 'Infinity', '1' * 65, MAX_CREDIT_VALUE + 1):
        with pytest.raises(ValidationError):
            NumericTierRule(key='pixels', kind='numeric_tier', tiers=[{'max': value, 'multiplier': '1'}])


@pytest.mark.parametrize('value', [1, 1.0, True, Decimal('1')])
def test_numeric_tier_multiplier_only_accepts_decimal_string_input(value: object) -> None:
    with pytest.raises(ValidationError):
        NumericTierRule(key='pixels', kind='numeric_tier', tiers=[{'max': 1024, 'multiplier': value}])


def test_numeric_tiers_reject_more_than_approved_limit() -> None:
    tiers = [{'max': index + 1, 'multiplier': '1'} for index in range(MAX_NUMERIC_TIERS + 1)]
    with pytest.raises(ValidationError):
        NumericTierRule(key='pixels', kind='numeric_tier', tiers=tiers)


@pytest.mark.parametrize('block_size', [0, -1, True, 1.5, '0', '-1', 'NaN', 'Infinity'])
def test_unit_blocks_rejects_invalid_block_size(block_size: object) -> None:
    with pytest.raises(ValidationError):
        UnitBlocksRule(key='tokens', kind='unit_blocks', block_size=block_size, multiplier_per_block='1')


@pytest.mark.parametrize(('block_size', 'expected'), [(1000, Decimal('1000')), ('0.5', Decimal('0.5'))])
def test_unit_blocks_accepts_positive_integer_or_exact_decimal_string(block_size: object, expected: Decimal) -> None:
    rule = UnitBlocksRule(key='tokens', kind='unit_blocks', block_size=block_size, multiplier_per_block='0.125')

    assert rule.block_size == expected


def test_unit_block_sizes_require_strict_bounded_exact_values() -> None:
    for block_size in (Decimal('1'), '1' * 65, MAX_CREDIT_VALUE + 1):
        with pytest.raises(ValidationError):
            UnitBlocksRule(key='tokens', kind='unit_blocks', block_size=block_size, multiplier_per_block='1')


@pytest.mark.parametrize('value', [1, 1.0, True, Decimal('1')])
def test_unit_blocks_multiplier_only_accepts_decimal_string_input(value: object) -> None:
    with pytest.raises(ValidationError):
        UnitBlocksRule(key='tokens', kind='unit_blocks', block_size=1000, multiplier_per_block=value)


@pytest.mark.parametrize('unit_size', [0, -1, True, 1.5, '0', '-1', 'NaN', 'Infinity', Decimal('1')])
def test_proportional_rejects_invalid_unit_size(unit_size: object) -> None:
    with pytest.raises(ValidationError):
        ProportionalRule(key='pixel_count', kind='proportional', unit_size=unit_size)


@pytest.mark.parametrize(('unit_size', 'expected'), [(1_000_000, Decimal('1000000')), ('0.5', Decimal('0.5'))])
def test_proportional_accepts_positive_integer_or_exact_decimal_string(unit_size: object, expected: Decimal) -> None:
    rule = ProportionalRule(key='pixel_count', kind='proportional', unit_size=unit_size)

    assert rule.unit_size == expected


def test_quantity_rule_requires_positive_integer_request_value() -> None:
    rule = QuantityRule(key='images', kind='quantity')

    assert rule.validate_request_value(3) == 3
    for value in (0, -1, 1.5, True, '2'):
        with pytest.raises(ValueError):
            rule.validate_request_value(value)


def test_price_rule_set_rejects_duplicate_keys_and_unknown_kinds() -> None:
    with pytest.raises(ValidationError):
        PriceRuleSet(
            schema_version=1,
            dimensions=[
                {'key': 'quality', 'kind': 'exact_map', 'values': {'hd': '1'}},
                {'key': ' quality ', 'kind': 'quantity'},
            ],
        )
    with pytest.raises(ValidationError):
        PriceRuleSet(
            schema_version=1,
            dimensions=[{'key': 'quality', 'kind': 'mystery'}],
        )


def test_price_rule_set_rejects_more_than_approved_dimension_limit() -> None:
    dimensions = [{'key': f'd{index}', 'kind': 'quantity'} for index in range(MAX_RULE_DIMENSIONS + 1)]
    with pytest.raises(ValidationError):
        PriceRuleSet(schema_version=1, dimensions=dimensions)


def test_price_rule_set_accepts_all_dimension_kinds() -> None:
    rules = PriceRuleSet(
        schema_version=1,
        dimensions=[
            {'key': 'quality', 'kind': 'exact_map', 'values': {'hd': '1.5'}},
            {'key': 'pixels', 'kind': 'numeric_tier', 'tiers': [{'max': 1024, 'multiplier': '2'}]},
            {'key': 'tokens', 'kind': 'unit_blocks', 'block_size': 1000, 'multiplier_per_block': '0.25'},
            {'key': 'pixel_count', 'kind': 'proportional', 'unit_size': 1_000_000},
            {'key': 'images', 'kind': 'quantity'},
        ],
    )

    assert len(rules.dimensions) == 5


def test_all_pydantic_domain_models_are_frozen() -> None:
    models = [
        AdjustmentRequest(direction='increase', amount=1, reason_code='promotion_gift'),
        ExactMapRule(key='quality', kind='exact_map', values={'hd': '1'}),
        NumericTierRule(key='pixels', kind='numeric_tier', tiers=[{'max': 1, 'multiplier': '1'}]),
        UnitBlocksRule(key='tokens', kind='unit_blocks', block_size=1, multiplier_per_block='1'),
        ProportionalRule(key='pixel_count', kind='proportional', unit_size=1_000_000),
        QuantityRule(key='images', kind='quantity'),
        PriceRuleSet(schema_version=1, dimensions=[]),
        PaginationParams(),
    ]

    for model in models:
        with pytest.raises(ValidationError):
            model.key = 'replacement'


def test_ledger_item_snapshots_are_deeply_immutable_and_serializable() -> None:
    pricing_snapshot = {'factors': [{'key': 'quality', 'value': 'hd'}]}
    metadata_snapshot = {'channel': 'web', 'tags': ['image']}
    item = LedgerItem(
        id='ledger-1',
        user_id='user-1',
        amount=-3,
        balance_before=10,
        balance_after=7,
        entry_type='consumption',
        reason_code=None,
        note=None,
        user_name_snapshot=None,
        user_email_snapshot=None,
        operator_id=None,
        operator_name_snapshot=None,
        operator_email_snapshot=None,
        request_source='web',
        request_id='request-1',
        service_type='image',
        resource_id='model-1',
        action='text-to-image',
        usage_status='succeeded',
        pricing_snapshot=pricing_snapshot,
        metadata_snapshot=metadata_snapshot,
        created_at=1,
    )

    pricing_snapshot['factors'][0]['value'] = 'mutated'
    metadata_snapshot['tags'].append('mutated')

    assert item.pricing_snapshot == {'factors': ({'key': 'quality', 'value': 'hd'},)}
    assert item.metadata_snapshot == {'channel': 'web', 'tags': ('image',)}
    with pytest.raises(TypeError):
        item.pricing_snapshot['factors'][0]['value'] = 'mutated'
    with pytest.raises(AttributeError):
        item.metadata_snapshot['tags'].append('mutated')
    assert item.model_dump(mode='json')['pricing_snapshot'] == {
        'factors': [{'key': 'quality', 'value': 'hd'}],
    }


def test_pagination_defaults_to_50_and_rejects_more_than_100() -> None:
    assert PaginationParams().limit == 50
    assert PaginationParams(limit=100).limit == 100
    with pytest.raises(ValidationError):
        PaginationParams(limit=101)


ERROR_CASES = [
    ('price_not_configured', 409, 'Price is not configured'),
    ('price_rule_incomplete', 409, 'Price rule is incomplete'),
    ('insufficient_credits', 402, 'Insufficient credits'),
    ('idempotency_key_conflict', 409, 'Idempotency key conflicts with another request'),
    ('usage_processing', 202, 'Usage request is still processing'),
    ('credit_account_conflict', 409, 'Credit account was updated concurrently'),
    ('invalid_adjustment', 422, 'Credit adjustment is invalid'),
    ('credit_service_unavailable', 503, 'Credit service is unavailable'),
    ('provider_failed', 502, 'Image provider request failed'),
    ('invalid_image_size', 422, 'Image size is invalid'),
    ('generation_cancelled', 409, 'Image generation was cancelled'),
    ('rate_limited', 429, 'Too many image generation requests'),
]


@pytest.mark.parametrize(('code', 'status_code', 'message'), ERROR_CASES)
def test_credit_error_derives_stable_status_and_public_message(code: str, status_code: int, message: str) -> None:
    error = CreditError(code=code, context={'required': 10})

    assert error.status_code == status_code
    assert error.to_envelope() == {'code': code, 'message': message, 'context': {'required': 10}}


def test_credit_error_rejects_unknown_code_and_caller_controlled_status_or_message() -> None:
    with pytest.raises(ValueError):
        CreditError(code='unknown', context={})
    with pytest.raises(TypeError):
        CreditError(code='provider_failed', status_code=418, context={})
    with pytest.raises(TypeError):
        CreditError(code='provider_failed', context={}, message='database password secret-db-password')
