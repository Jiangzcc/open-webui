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
