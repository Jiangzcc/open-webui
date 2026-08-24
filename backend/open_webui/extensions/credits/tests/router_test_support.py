from dataclasses import dataclass

from open_webui.extensions.credits.models import CreditPrice


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    name: str
    email: str
    role: str = 'user'


async def seed_credit_price(
    sessions,
    *,
    price_id: str = 'price-1',
    created_at: int = 1,
) -> None:
    async with sessions() as session, session.begin():
        session.add(
            CreditPrice(
                id=price_id,
                service_type='image',
                resource_id='model-a',
                action='text-to-image',
                base_price='1',
                rules={'schema_version': 1, 'dimensions': []},
                enabled=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )


__all__ = ['AuthenticatedUser', 'seed_credit_price']
