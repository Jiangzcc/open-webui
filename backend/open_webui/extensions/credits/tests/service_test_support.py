from __future__ import annotations

import time
from dataclasses import dataclass

from open_webui.extensions.credits.compat import ImageBillingContext
from open_webui.extensions.credits.models import CreditPrice
from open_webui.extensions.credits.schemas import AdjustmentRequest, RequestAuditContext, UserSnapshot
from open_webui.extensions.credits.service import adjust_balance
from open_webui.models.users import User
from sqlalchemy import insert


@dataclass
class HeaderRequest:
    headers: dict[str, object]


async def create_user(
    sessions,
    user_id: str,
    *,
    name: str | None = None,
    email: str | None = None,
) -> UserSnapshot:
    snapshot = UserSnapshot(
        id=user_id,
        name=name or f'Name {user_id}',
        email=email or f'{user_id}@example.test',
    )
    async with sessions() as session, session.begin():
        await session.execute(insert(User).values(id=snapshot.id, name=snapshot.name, email=snapshot.email))
    return snapshot


def image_context(
    *,
    resource_id: str = 'model-a',
    request_hash: str = 'b' * 64,
) -> ImageBillingContext:
    return ImageBillingContext(
        service_type='image',
        resource_id=resource_id,
        action='text-to-image',
        channel='web',
        dimensions={'size': '512x512', 'image_count': 1},
        prompt_hash='a' * 64,
        reference_hashes=(),
        request_hash=request_hash,
    )


async def add_price(
    sessions,
    *,
    resource_id: str = 'model-a',
    enabled: bool = True,
    base_price: str = '3',
) -> None:
    now = int(time.time())
    async with sessions() as session, session.begin():
        session.add(
            CreditPrice(
                id=f'price-{resource_id}',
                service_type='image',
                resource_id=resource_id,
                action='text-to-image',
                base_price=base_price,
                rules={'schema_version': 1, 'dimensions': []},
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
        )


async def credit_user(sessions, user: UserSnapshot, amount: int = 10) -> None:
    audit = RequestAuditContext(
        source='internal_admin',
        request_id='seed',
        remote_address_hash='a0' * 32,
    )
    adjustment = AdjustmentRequest(
        direction='increase',
        amount=amount,
        reason_code='accounting_correction',
    )
    operator = UserSnapshot(id='admin-1', name='Admin', email='admin@example.test')
    async with sessions() as session:
        await adjust_balance(session, user, operator, adjustment, audit)


__all__ = ['HeaderRequest', 'add_price', 'create_user', 'credit_user', 'image_context']
