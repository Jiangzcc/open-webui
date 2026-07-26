from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal, DecimalException, InvalidOperation, localcontext
from typing import Callable, Protocol, cast

from pydantic import TypeAdapter, ValidationError

from .constants import MAX_CREDIT_VALUE, MAX_DECIMAL_INPUT_LENGTH
from .errors import CreditError
from .schemas import (
    ExactMapRule,
    NumericTierRule,
    PositivePrice,
    PriceRuleSet,
    QuantityRule,
    UnitBlocksRule,
)


@dataclass(frozen=True)
class PriceFactor:
    key: str
    value: str | int
    multiplier: str


@dataclass(frozen=True)
class PriceQuote:
    service_type: str
    resource_id: str
    action: str
    base_price: str
    factors: tuple[PriceFactor, ...]
    raw_price: str
    charged_credits: int


class PriceLike(Protocol):
    service_type: str
    resource_id: str
    action: str
    base_price: object
    rules: object
    enabled: object


def _metadata(price: PriceLike | None) -> dict[str, object]:
    if price is None:
        return {}
    return {
        key: getattr(price, key)
        for key in ('service_type', 'resource_id', 'action')
        if isinstance(getattr(price, key, None), str)
    }


def _error(price: PriceLike | None, reason: str, dimension: str | None = None) -> CreditError:
    context = _metadata(price)
    if dimension is not None:
        context['dimension'] = dimension
    context['reason'] = reason
    return CreditError(code='price_rule_incomplete', context=context)


def _plain(value: Decimal) -> str:
    return format(value, 'f').lstrip('+')


def _positive_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    if isinstance(value, str) and len(value) > MAX_DECIMAL_INPUT_LENGTH:
        return None
    if isinstance(value, int) and value > MAX_CREDIT_VALUE:
        return None
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    if not decimal.is_finite() or decimal <= 0 or decimal > MAX_CREDIT_VALUE:
        return None
    return decimal


def _exact_value(value: object) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_base_price(value: object) -> Decimal | None:
    try:
        return TypeAdapter(PositivePrice).validate_python(value)
    except (TypeError, ValueError, ValidationError):
        return None


def _resolve_exact(rule: ExactMapRule, value: object) -> tuple[str, Decimal] | None:
    normalized = _exact_value(value)
    if normalized is None:
        return None
    multiplier = rule.values.get(normalized, rule.values.get('default'))
    if multiplier is None:
        return None
    return normalized, multiplier


def _resolve_numeric(rule: NumericTierRule, value: object) -> tuple[str, Decimal] | None:
    decimal = _positive_decimal(value)
    if decimal is None:
        return None
    for tier in rule.tiers:
        if decimal <= tier.max_value:
            return _plain(decimal), tier.multiplier
    return None


def _resolve_unit_blocks(rule: UnitBlocksRule, value: object) -> tuple[str, Decimal] | None:
    decimal = _positive_decimal(value)
    if decimal is None:
        return None
    blocks = (decimal / rule.block_size).to_integral_value(rounding=ROUND_CEILING)
    return _plain(decimal), blocks * rule.multiplier_per_block


def _resolve_quantity(rule: QuantityRule, value: object) -> tuple[int, Decimal] | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or value > MAX_CREDIT_VALUE:
        return None
    return value, Decimal(value)


def _resolve_rule(rule: object, value: object) -> tuple[tuple[str | int, Decimal] | None, str]:
    if isinstance(rule, ExactMapRule):
        reason = 'exact_value_not_found' if _exact_value(value) is not None else 'invalid_dimension_value'
        return _resolve_exact(rule, value), reason
    if isinstance(rule, NumericTierRule):
        reason = 'numeric_value_out_of_range' if _positive_decimal(value) is not None else 'invalid_dimension_value'
        return _resolve_numeric(rule, value), reason
    if isinstance(rule, UnitBlocksRule):
        return _resolve_unit_blocks(rule, value), 'invalid_dimension_value'
    return _resolve_quantity(cast(QuantityRule, rule), value), 'invalid_dimension_value'


def _next_multiplier(base_price: Decimal, multiplier: Decimal, factor: Decimal) -> Decimal | None:
    next_multiplier = multiplier * factor
    next_raw = base_price * next_multiplier
    values = (factor, next_multiplier, next_raw)
    if any(not value.is_finite() or value > MAX_CREDIT_VALUE for value in values):
        return None
    return next_multiplier


def _finalize_price(price: PriceLike, base_price: Decimal, multiplier: Decimal) -> tuple[Decimal, int]:
    try:
        raw = base_price * multiplier
        charged_credits = max(1, int(raw.to_integral_value(rounding=ROUND_CEILING)))
    except (DecimalException, ValueError, OverflowError):
        raise _error(price, 'price_overflow') from None
    if not raw.is_finite() or raw > MAX_CREDIT_VALUE or charged_credits > MAX_CREDIT_VALUE:
        raise _error(price, 'price_overflow')
    return raw, charged_credits


def _compute_factors(
    price: PriceLike,
    context: Mapping[str, object],
    rules: PriceRuleSet,
    base_price: Decimal,
) -> tuple[list[PriceFactor], Decimal]:
    factors: list[PriceFactor] = []
    multiplier = Decimal('1')
    for rule in rules.dimensions:
        if rule.key not in context:
            raise _error(price, 'missing_dimension', rule.key)
        value = context[rule.key]
        try:
            resolved, reason = _resolve_rule(rule, value)
        except DecimalException:
            raise _error(price, 'price_overflow', rule.key) from None
        if resolved is None:
            raise _error(price, reason, rule.key)
        factor_value, factor_multiplier = resolved
        try:
            next_multiplier = _next_multiplier(base_price, multiplier, factor_multiplier)
        except DecimalException:
            raise _error(price, 'price_overflow', rule.key) from None
        if next_multiplier is None:
            raise _error(price, 'price_overflow', rule.key)
        factors.append(PriceFactor(rule.key, factor_value, _plain(factor_multiplier)))
        multiplier = next_multiplier
    return factors, multiplier


def compute_price(price: PriceLike | None, context: Mapping[str, object]) -> PriceQuote:
    """Compute a normalized immutable pricing snapshot without accessing persistence."""
    if price is None or getattr(price, 'enabled', None) is not True:
        raise CreditError(code='price_not_configured', context=_metadata(price))

    base_price = _parse_base_price(price.base_price)
    if base_price is None:
        raise _error(price, 'invalid_base_price')

    try:
        rules = PriceRuleSet.model_validate(price.rules)
    except (TypeError, ValueError, ValidationError):
        raise _error(price, 'invalid_rules') from None

    factors: list[PriceFactor] = []
    multiplier = Decimal('1')
    with localcontext() as decimal_context:
        decimal_context.prec = MAX_DECIMAL_INPUT_LENGTH * (len(rules.dimensions) + 2)
        factors, multiplier = _compute_factors(price, context, rules, base_price)
        raw, charged_credits = _finalize_price(price, base_price, multiplier)
    return PriceQuote(
        service_type=price.service_type,
        resource_id=price.resource_id,
        action=price.action,
        base_price=_plain(base_price),
        factors=tuple(factors),
        raw_price=_plain(raw),
        charged_credits=charged_credits,
    )


def attach_model_base_prices(
	models: list[dict[str, object]],
	prices: list[PriceLike],
	*,
	id_resolver: 'Callable[[str], str | None]' | None = None,
) -> list[dict[str, object]]:
	"""Decorate a list of public image-model dicts with their credit base prices.

	Each model in ``models`` carries a public ``id`` (e.g. ``qwen-image``); each
	price in ``prices`` carries an internal ``resource_id`` (e.g.
	``fal-ai/qwen-image``). ``id_resolver`` bridges the two namespaces by turning
	a public id into the internal resource id that the prices table stores. When
	omitted, it lazily falls back to ``internal_fal_image_model_id``.

	For every model we attach ``base_price`` (its text-to-image price) and/or
	``edit_base_price`` (its image-to-image price) as strings whenever an enabled
	price exists for that (internal id, action) pair; missing pairs are silently
	left out so the frontend can hide the price badge. Input dicts are not
	mutated — each returned dict is a shallow copy with the extra keys layered on.
	"""
	if id_resolver is None:
		from open_webui.utils.images.fal_models import internal_fal_image_model_id

		id_resolver = internal_fal_image_model_id

	index: dict[tuple[str, str], str] = {}
	for price in prices:
		if not getattr(price, 'enabled', True):
			continue
		resource_id = getattr(price, 'resource_id', None)
		action = getattr(price, 'action', None)
		base_price = getattr(price, 'base_price', None)
		if not isinstance(resource_id, str) or not isinstance(action, str):
			continue
		if not isinstance(base_price, str):
			continue
		index[(resource_id, action)] = base_price

	enriched: list[dict[str, object]] = []
	for model in models:
		public_id = model.get('id')
		edit_public = model.get('edit_model')
		gen_public = model.get('generation_model')
		internal_id = id_resolver(public_id) if isinstance(public_id, str) else None
		edit_internal = id_resolver(edit_public) if isinstance(edit_public, str) else None
		gen_internal = id_resolver(gen_public) if isinstance(gen_public, str) else None
		copy = dict(model)
		# base_price = 该模型(或其 t2i twin)的 text-to-image 价
		t2i_source = internal_id if model.get('task') != 'image-to-image' else gen_internal
		# edit_base_price = 该模型(或其 i2i twin)的 image-to-image 价
		i2i_source = internal_id if model.get('task') != 'text-to-image' else edit_internal
		if isinstance(t2i_source, str):
			t2i = index.get((t2i_source, 'text-to-image'))
			if t2i is not None:
				copy['base_price'] = t2i
		if isinstance(i2i_source, str):
			i2i = index.get((i2i_source, 'image-to-image'))
			if i2i is not None:
				copy['edit_base_price'] = i2i
		enriched.append(copy)
	return enriched


__all__ = ['PriceFactor', 'PriceQuote', 'attach_model_base_prices', 'compute_price']
