from dataclasses import dataclass
from typing import Literal

CreditErrorCode = Literal[
    'price_not_configured',
    'price_rule_incomplete',
    'insufficient_credits',
    'idempotency_key_conflict',
    'usage_processing',
    'credit_account_conflict',
    'invalid_adjustment',
    'credit_service_unavailable',
    'provider_failed',
    'invalid_image_size',
    'generation_cancelled',
    'rate_limited',
    'redeem_code_invalid',
    'redeem_code_used',
    'redeem_code_voided',
    'redeem_code_expired',
    'redeem_code_limit_reached',
    'redeem_batch_not_found',
]


@dataclass(frozen=True)
class PublicErrorDefinition:
    status_code: int
    message: str


PUBLIC_ERRORS: dict[CreditErrorCode, PublicErrorDefinition] = {
    'price_not_configured': PublicErrorDefinition(409, 'Price is not configured'),
    'price_rule_incomplete': PublicErrorDefinition(409, 'Price rule is incomplete'),
    'insufficient_credits': PublicErrorDefinition(402, 'Insufficient credits'),
    'idempotency_key_conflict': PublicErrorDefinition(409, 'Idempotency key conflicts with another request'),
    'usage_processing': PublicErrorDefinition(202, 'Usage request is still processing'),
    'credit_account_conflict': PublicErrorDefinition(409, 'Credit account was updated concurrently'),
    'invalid_adjustment': PublicErrorDefinition(422, 'Credit adjustment is invalid'),
    'credit_service_unavailable': PublicErrorDefinition(503, 'Credit service is unavailable'),
    'provider_failed': PublicErrorDefinition(502, 'Image provider request failed'),
    'invalid_image_size': PublicErrorDefinition(422, 'Image size is invalid'),
    'generation_cancelled': PublicErrorDefinition(409, 'Image generation was cancelled'),
    'rate_limited': PublicErrorDefinition(429, 'Too many generation requests'),
    'redeem_code_invalid': PublicErrorDefinition(404, 'Redeem code is invalid'),
    'redeem_code_used': PublicErrorDefinition(409, 'Redeem code has already been used'),
    'redeem_code_voided': PublicErrorDefinition(409, 'Redeem code has been voided'),
    'redeem_code_expired': PublicErrorDefinition(410, 'Redeem code has expired'),
    'redeem_code_limit_reached': PublicErrorDefinition(409, 'Redeem limit has been reached'),
    'redeem_batch_not_found': PublicErrorDefinition(404, 'Redeem-code batch was not found'),
}


class CreditError(Exception):
    def __init__(
        self,
        *,
        code: CreditErrorCode,
        context: dict[str, object] | None = None,
    ) -> None:
        try:
            definition = PUBLIC_ERRORS[code]
        except KeyError as error:
            raise ValueError('unsupported credit error code') from error

        super().__init__(definition.message)
        self.code = code
        self.status_code = definition.status_code
        self.context = dict(context or {})

    def to_envelope(self) -> dict[str, object]:
        return {
            'code': self.code,
            'message': PUBLIC_ERRORS[self.code].message,
            'context': dict(self.context),
        }
