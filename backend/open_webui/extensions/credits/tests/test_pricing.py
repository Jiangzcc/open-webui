import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, dataclass
from decimal import Decimal, Overflow, localcontext

import pytest
from open_webui.extensions.credits.constants import MAX_CREDIT_VALUE
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.pricing import PriceFactor, PriceQuote, compute_price


@dataclass(frozen=True)
class FakePrice:
    service_type: str = 'image'
    resource_id: str = 'image-model'
    action: str = 'generate'
    base_price: object = '1'
    rules: object = None
    enabled: object = True


def make_price(rules: dict, **overrides: object) -> FakePrice:
    return FakePrice(rules=rules, **overrides)


def exact_rule(key: str, values: dict[str, object]) -> dict[str, object]:
    return {'key': key, 'kind': 'exact_map', 'values': values}


def numeric_rule(key: str, tiers: list[dict[str, object]]) -> dict[str, object]:
    return {'key': key, 'kind': 'numeric_tier', 'tiers': tiers}


def unit_rule(key: str, block_size: object, multiplier: object) -> dict[str, object]:
    return {
        'key': key,
        'kind': 'unit_blocks',
        'block_size': block_size,
        'multiplier_per_block': multiplier,
    }


def quantity_rule(key: str) -> dict[str, object]:
    return {'key': key, 'kind': 'quantity'}


def rule_set(*dimensions: dict[str, object]) -> dict[str, object]:
    return {'schema_version': 1, 'dimensions': list(dimensions)}


def assert_error(price: FakePrice | None, context: dict[str, object], code: str) -> CreditError:
    with pytest.raises(CreditError) as raised:
        compute_price(price, context)
    assert raised.value.code == code
    return raised.value


def test_compute_price_multiplies_dimensions_in_declared_order() -> None:
    price = make_price(
        rule_set(
            exact_rule('size', {'small': '1.5'}),
            numeric_rule('resolution', [{'max': 2048, 'multiplier': '2'}]),
            exact_rule('aspect_ratio', {'square': '1.1'}),
            exact_rule('quality', {'hd': '1.3'}),
            quantity_rule('image_count'),
        ),
        base_price='2',
    )

    quote = compute_price(
        price,
        {
            'size': 'small',
            'resolution': 1024,
            'aspect_ratio': 'square',
            'quality': 'hd',
            'image_count': 2,
        },
    )

    assert quote == PriceQuote(
        service_type='image',
        resource_id='image-model',
        action='generate',
        base_price='2',
        factors=(
            PriceFactor(key='size', value='small', multiplier='1.5'),
            PriceFactor(key='resolution', value='1024', multiplier='2'),
            PriceFactor(key='aspect_ratio', value='square', multiplier='1.1'),
            PriceFactor(key='quality', value='hd', multiplier='1.3'),
            PriceFactor(key='image_count', value=2, multiplier='2'),
        ),
        raw_price='17.160',
        charged_credits=18,
    )


def test_compute_price_uses_exact_decimal_ceiling_and_minimum_charge() -> None:
    rules = rule_set(exact_rule('quality', {'standard': '1.3'}))

    assert compute_price(make_price(rules, base_price='7'), {'quality': 'standard'}).raw_price == '9.1'
    assert compute_price(make_price(rules, base_price='0.1'), {'quality': 'standard'}).charged_credits == 1
    assert compute_price(make_price(rules, base_price='10'), {'quality': 'standard'}).charged_credits == 13


def test_exact_map_normalizes_whitespace_but_not_case_and_supports_default() -> None:
    rules = rule_set(exact_rule('quality', {'hd': '1.5', 'default': '0.8'}))

    explicit = compute_price(make_price(rules), {'quality': '  hd  '})
    fallback = compute_price(make_price(rules), {'quality': ' cinema '})

    assert explicit.factors[0] == PriceFactor(key='quality', value='hd', multiplier='1.5')
    assert fallback.factors[0] == PriceFactor(key='quality', value='cinema', multiplier='0.8')
    no_default = rule_set(exact_rule('quality', {'hd': '1.5'}))
    error = assert_error(make_price(no_default), {'quality': 'HD'}, 'price_rule_incomplete')
    assert error.context['reason'] == 'exact_value_not_found'


def test_exact_map_rejects_missing_empty_and_wrong_type_values() -> None:
    rules = rule_set(exact_rule('quality', {'hd': '1'}))

    for value in ('', '   ', True, 1.5, Decimal('1')):
        error = assert_error(make_price(rules), {'quality': value}, 'price_rule_incomplete')
        assert error.context['reason'] == 'invalid_dimension_value'
    assert_error(make_price(rules), {}, 'price_rule_incomplete')


def test_numeric_tier_uses_first_matching_boundary_and_fails_closed_above_last() -> None:
    rules = rule_set(
        numeric_rule(
            'pixels',
            [
                {'max': 10, 'multiplier': '1.1'},
                {'max': 100, 'multiplier': '2'},
                {'max': 1000, 'multiplier': '3'},
            ],
        )
    )

    for value, expected in [(1, '1.1'), ('10', '1.1'), ('10.1', '2'), ('100', '2'), ('1000', '3')]:
        quote = compute_price(make_price(rules), {'pixels': value})
        assert quote.factors[0].multiplier == expected
    error = assert_error(make_price(rules), {'pixels': '1000.1'}, 'price_rule_incomplete')
    assert error.context['reason'] == 'numeric_value_out_of_range'


@pytest.mark.parametrize('value', [True, 1.5, Decimal('1'), 0, -1, '0', '-1', 'NaN', 'Infinity', '-Infinity'])
def test_numeric_tier_rejects_non_positive_non_finite_or_non_decimal_values(value: object) -> None:
    rules = rule_set(numeric_rule('pixels', [{'max': 100, 'multiplier': '1'}]))

    error = assert_error(make_price(rules), {'pixels': value}, 'price_rule_incomplete')
    assert error.context['reason'] == 'invalid_dimension_value'


def test_numeric_tier_rejects_missing_value() -> None:
    error = assert_error(
        make_price(rule_set(numeric_rule('pixels', [{'max': 100, 'multiplier': '1'}]))),
        {},
        'price_rule_incomplete',
    )
    assert error.context['reason'] == 'missing_dimension'


@pytest.mark.parametrize(
    ('value', 'expected_value', 'expected_multiplier'),
    [
        ('1', '1', '0.25'),
        (100, '100', '0.25'),
        ('100.01', '100.01', '0.50'),
        ('250.1', '250.1', '0.75'),
        ('0.5', '0.5', '0.25'),
    ],
)
def test_unit_blocks_ceil_divides_exact_values(value: object, expected_value: str, expected_multiplier: str) -> None:
    rules = rule_set(unit_rule('tokens', '100', '0.25'))

    factor = compute_price(make_price(rules), {'tokens': value}).factors[0]

    assert factor.value == expected_value
    assert factor.multiplier == expected_multiplier


@pytest.mark.parametrize('value', [True, 1.5, Decimal('1'), 0, -1, '0', '-1', 'NaN', 'Infinity'])
def test_unit_blocks_rejects_invalid_request_values(value: object) -> None:
    rules = rule_set(unit_rule('tokens', '100', '0.25'))

    error = assert_error(make_price(rules), {'tokens': value}, 'price_rule_incomplete')
    assert error.context['reason'] == 'invalid_dimension_value'


def test_unit_blocks_rejects_missing_value_and_invalid_rule_block_size() -> None:
    error = assert_error(make_price(rule_set(unit_rule('tokens', '100', '0.25'))), {}, 'price_rule_incomplete')
    assert error.context['reason'] == 'missing_dimension'
    error = assert_error(make_price(rule_set(unit_rule('tokens', '0', '0.25'))), {'tokens': 1}, 'price_rule_incomplete')
    assert error.context['reason'] == 'invalid_rules'


def test_quantity_requires_strict_positive_integer_without_int_truncation() -> None:
    rules = rule_set(quantity_rule('image_count'))

    assert compute_price(make_price(rules), {'image_count': 1}).factors[0].multiplier == '1'
    assert compute_price(make_price(rules), {'image_count': 3}).factors[0].value == 3
    for value in (0, -1, True, 1.5, Decimal('2'), '2'):
        error = assert_error(make_price(rules), {'image_count': value}, 'price_rule_incomplete')
        assert error.context['reason'] == 'invalid_dimension_value'


@pytest.mark.parametrize('price', [None, FakePrice(enabled=False)])
def test_none_or_disabled_price_is_not_configured(price: FakePrice | None) -> None:
    error = assert_error(price, {'prompt': 'secret prompt'}, 'price_not_configured')

    assert set(error.context) <= {'service_type', 'resource_id', 'action', 'dimension', 'reason'}


@pytest.mark.parametrize(
    'base_price',
    [1, 1.0, True, Decimal('1'), 'NaN', 'Infinity', '0', '-1', '1000000.00000001', '1.000000001'],
)
def test_invalid_base_price_is_incomplete_without_leaking_validator_details(base_price: object) -> None:
    price = make_price(rule_set(), base_price=base_price)

    error = assert_error(price, {}, 'price_rule_incomplete')

    assert error.context == {
        'service_type': 'image',
        'resource_id': 'image-model',
        'action': 'generate',
        'reason': 'invalid_base_price',
    }
    assert 'validation' not in str(error.context).lower()


@pytest.mark.parametrize(
    'rules',
    [
        rule_set(exact_rule('quality', {'hd': 1})),
        rule_set(exact_rule('quality', {'hd': 'NaN'})),
        rule_set(exact_rule('quality', {'hd': 'Infinity'})),
        rule_set(exact_rule('quality', {'hd': '0'})),
        rule_set(exact_rule('quality', {'hd': '-1'})),
        rule_set(exact_rule('quality', {'hd': '1.000000001'})),
        {'schema_version': 1, 'dimensions': [{'key': 'quality', 'kind': 'mystery'}]},
        rule_set(quantity_rule('quality'), quantity_rule(' quality ')),
    ],
)
def test_invalid_rules_are_incomplete_and_do_not_expose_rule_payload(rules: dict[str, object]) -> None:
    error = assert_error(make_price(rules), {'quality': 'hd', 'prompt': 'secret prompt'}, 'price_rule_incomplete')

    assert error.context == {
        'service_type': 'image',
        'resource_id': 'image-model',
        'action': 'generate',
        'reason': 'invalid_rules',
    }
    assert 'secret prompt' not in str(error.context)
    assert 'mystery' not in str(error.context)


def test_missing_dimension_and_errors_only_contain_low_sensitivity_fields() -> None:
    context = {
        'quality': 'hd',
        'prompt': 'a private prompt',
        'image': 'base64-secret',
        'Authorization': 'Bearer secret-token',
    }
    price = make_price(rule_set(quantity_rule('image_count')))

    error = assert_error(price, context, 'price_rule_incomplete')

    assert error.context == {
        'service_type': 'image',
        'resource_id': 'image-model',
        'action': 'generate',
        'dimension': 'image_count',
        'reason': 'missing_dimension',
    }
    assert not any(secret in str(error.context) for secret in ('private prompt', 'base64-secret', 'secret-token'))


def test_price_inputs_are_not_mutated_and_snapshot_contains_no_input_mapping_or_rules() -> None:
    rules = rule_set(exact_rule('quality', {'hd': '1.5'}))
    context = {'quality': ' hd ', 'prompt': 'private'}
    original_rules = deepcopy(rules)
    original_context = deepcopy(context)

    quote = compute_price(make_price(rules), context)

    assert rules == original_rules
    assert context == original_context
    serialized = json.dumps(asdict(quote))
    assert 'private' not in serialized
    assert 'schema_version' not in serialized
    assert 'mapping' not in serialized

    with pytest.raises(FrozenInstanceError):
        quote.raw_price = '2'
    with pytest.raises(FrozenInstanceError):
        quote.factors[0].multiplier = '2'


def test_request_numeric_values_enforce_length_and_big_integer_bounds() -> None:
    rules = rule_set(numeric_rule('pixels', [{'max': MAX_CREDIT_VALUE, 'multiplier': '1'}]))
    unit_rules = rule_set(unit_rule('tokens', 1, '1'))

    for value in ('1' * 65, MAX_CREDIT_VALUE + 1):
        numeric_error = assert_error(make_price(rules), {'pixels': value}, 'price_rule_incomplete')
        unit_error = assert_error(make_price(unit_rules), {'tokens': value}, 'price_rule_incomplete')
        assert numeric_error.context['reason'] == 'invalid_dimension_value'
        assert unit_error.context['reason'] == 'invalid_dimension_value'


def test_quantity_enforces_big_integer_bound() -> None:
    error = assert_error(
        make_price(rule_set(quantity_rule('image_count'))),
        {'image_count': MAX_CREDIT_VALUE + 1},
        'price_rule_incomplete',
    )

    assert error.context['reason'] == 'invalid_dimension_value'


def test_price_overflow_fails_closed_after_each_multiplication() -> None:
    rules = rule_set(quantity_rule('first'), quantity_rule('second'))
    price = make_price(rules, base_price='1000000')

    error = assert_error(
        price,
        {'first': MAX_CREDIT_VALUE, 'second': MAX_CREDIT_VALUE},
        'price_rule_incomplete',
    )

    assert error.context['reason'] == 'price_overflow'
    assert set(error.context) == {'service_type', 'resource_id', 'action', 'dimension', 'reason'}


def test_raw_price_and_charged_credits_cannot_exceed_big_integer_limit() -> None:
    price = make_price(rule_set(quantity_rule('quantity')), base_price='1000000')

    error = assert_error(price, {'quantity': MAX_CREDIT_VALUE}, 'price_rule_incomplete')

    assert error.context['reason'] == 'price_overflow'


def test_decimal_arithmetic_exception_is_sanitized() -> None:
    price = make_price(rule_set(unit_rule('tokens', '0.00000000000000000001', '1')))

    with localcontext() as decimal_context:
        decimal_context.traps[Overflow] = True
        decimal_context.Emax = 9
        error = assert_error(price, {'tokens': MAX_CREDIT_VALUE}, 'price_rule_incomplete')

    assert error.context['reason'] == 'price_overflow'
    assert set(error.context) == {'service_type', 'resource_id', 'action', 'dimension', 'reason'}


def test_decimal_products_preserve_all_audit_precision_beyond_default_context() -> None:
    dimensions = tuple(exact_rule(f'factor_{index}', {'x': '1.12345678'}) for index in range(4))
    context = {f'factor_{index}': 'x' for index in range(4)}

    quote = compute_price(make_price(rule_set(*dimensions)), context)

    assert quote.raw_price == '1.59303558866393455169015543139856'


def test_quote_and_factors_are_json_serializable_and_have_stable_plain_decimal_strings() -> None:
    quote = compute_price(
        make_price(rule_set(unit_rule('tokens', '0.3', '0.2')), base_price='1.00'),
        {'tokens': '0.31'},
    )

    assert quote.base_price == '1.00'
    assert quote.raw_price == '0.400'
    assert quote.factors[0].multiplier == '0.4'
    numeric_strings = [quote.base_price, quote.raw_price, *(factor.multiplier for factor in quote.factors)]
    assert all('e-' not in value.lower() and 'e+' not in value.lower() for value in numeric_strings)
    assert json.loads(json.dumps(asdict(quote)))['charged_credits'] == 1
