import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, dataclass
from decimal import Decimal, Overflow, localcontext

import pytest
from open_webui.extensions.credits.constants import MAX_CREDIT_VALUE
from open_webui.extensions.credits.errors import CreditError
from open_webui.extensions.credits.pricing import (
    PriceFactor,
    PriceQuote,
    attach_model_base_prices,
    compute_price,
)


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


def proportional_rule(key: str, unit_size: object) -> dict[str, object]:
    return {'key': key, 'kind': 'proportional', 'unit_size': unit_size}


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


def test_proportional_price_uses_fractional_megapixels_before_final_rounding() -> None:
    rules = rule_set(proportional_rule('pixel_count', 1_000_000), quantity_rule('image_count'))

    quote = compute_price(
        make_price(rules, base_price='5'),
        {'pixel_count': 1024 * 768, 'image_count': 2},
    )

    assert quote.factors == (
        PriceFactor(key='pixel_count', value='786432', multiplier='0.786432'),
        PriceFactor(key='image_count', value=2, multiplier='2'),
    )
    assert quote.raw_price == '7.864320'
    assert quote.charged_credits == 8


@pytest.mark.parametrize('value', [True, 0, -1, 1.5, Decimal('1'), 'NaN', 'Infinity'])
def test_proportional_price_rejects_untrusted_or_invalid_dimension_values(value: object) -> None:
    price = make_price(rule_set(proportional_rule('pixel_count', 1_000_000)), base_price='5')

    error = assert_error(price, {'pixel_count': value}, 'price_rule_incomplete')

    assert error.context['reason'] == 'invalid_dimension_value'


# --- attach_model_base_prices: inject base_price/edit_base_price into model list --
#
# 需求1:images 页 /models 端点要给每个模型附带基础积分价。前端模型 id 是公共
# id,prices 的 resource_id 是内部 id,函数借一个 id_resolver 把公共转内部再 join。
# 只采纳 enabled 的价格;无对应价则该字段不出现(前端据此隐藏价格牌)。


def test_attach_base_prices_joins_via_resolver_for_both_actions():
    models = [
        {'id': 'qwen-image', 'task': 'text-to-image', 'edit_model': 'qwen-image/edit'},
        {
            'id': 'qwen-image/edit',
            'task': 'image-to-image',
            'generation_model': 'qwen-image',
        },
    ]
    prices = [
        FakePrice(resource_id='fal-ai/qwen-image', action='text-to-image', base_price='4'),
        FakePrice(resource_id='fal-ai/qwen-image/image-to-image', action='image-to-image', base_price='4'),
    ]

    def resolver(public_id):
        return {
            'qwen-image': 'fal-ai/qwen-image',
            'qwen-image/edit': 'fal-ai/qwen-image/image-to-image',
        }.get(public_id)

    enriched = attach_model_base_prices(models, prices, id_resolver=resolver)

    by_id = {m['id']: m for m in enriched}
    assert by_id['qwen-image']['base_price'] == '4'
    assert by_id['qwen-image']['edit_base_price'] == '4'
    assert by_id['qwen-image/edit']['base_price'] == '4'
    assert by_id['qwen-image/edit']['edit_base_price'] == '4'


def test_attach_base_prices_skips_disabled_and_missing_prices():
    models = [{'id': 'lonely'}, {'id': 'priced'}]
    prices = [
        FakePrice(resource_id='int/priced', action='text-to-image', base_price='7', enabled=True),
        FakePrice(resource_id='int/disabled', action='text-to-image', base_price='99', enabled=False),
    ]

    def resolver(public_id):
        return {'priced': 'int/priced', 'lonely': 'int/lonely'}.get(public_id)

    enriched = attach_model_base_prices(models, prices, id_resolver=resolver)
    priced = next(m for m in enriched if m['id'] == 'priced')
    lonely = next(m for m in enriched if m['id'] == 'lonely')

    assert priced['base_price'] == '7'
    assert 'base_price' not in lonely
    assert 'edit_base_price' not in lonely


def test_attach_base_prices_only_adds_action_that_exists():
    # 某 t2i 模型只有 text-to-image 价,没有 image-to-image 价(不支持 i2i)
    models = [{'id': 'z-image-base', 'task': 'text-to-image'}]
    prices = [FakePrice(resource_id='fal-ai/z-image/base', action='text-to-image', base_price='2')]

    def resolver(public_id):
        return {'z-image-base': 'fal-ai/z-image/base'}.get(public_id)

    enriched = attach_model_base_prices(models, prices, id_resolver=resolver)
    model = enriched[0]
    assert model['base_price'] == '2'
    assert 'edit_base_price' not in model


def test_attach_base_prices_preserves_other_model_fields_and_does_not_mutate_input():
    models = [{'id': 'keep-me', 'task': 'text-to-image', 'resolutions': ['1024x1024']}]
    prices = [FakePrice(resource_id='int/keep', action='text-to-image', base_price='3')]

    def resolver(public_id):
        return {'keep-me': 'int/keep'}.get(public_id)

    enriched = attach_model_base_prices(deepcopy(models), prices, id_resolver=resolver)
    assert enriched[0]['resolutions'] == ['1024x1024']
    assert enriched[0]['base_price'] == '3'
    # 原输入不被改写
    assert 'base_price' not in models[0]


def test_attach_base_prices_accepts_orm_decimal_compatible_strings_only():
    models = [{'id': 'priced'}]
    prices = [FakePrice(resource_id='int/priced', action='text-to-image', base_price=Decimal('7'))]

    enriched = attach_model_base_prices(models, prices, id_resolver=lambda _: 'int/priced')

    assert 'base_price' not in enriched[0]


def test_attach_base_prices_handles_unknown_public_ids_gracefully():
    # resolver 返回 None(公共 id 没有对应内部 id)时,该模型安静跳过,不报错
    models = [{'id': 'ghost'}, {'id': 'real'}]
    prices = [FakePrice(resource_id='int/real', action='text-to-image', base_price='5')]

    def resolver(public_id):
        return {'real': 'int/real'}.get(public_id)  # ghost -> None

    enriched = attach_model_base_prices(models, prices, id_resolver=resolver)
    ghost = next(m for m in enriched if m['id'] == 'ghost')
    real = next(m for m in enriched if m['id'] == 'real')
    assert 'base_price' not in ghost
    assert real['base_price'] == '5'
