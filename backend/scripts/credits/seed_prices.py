"""Idempotently load the single declarative credit-price catalog."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from uuid import uuid4

from open_webui.extensions.credits.db import credit_session
from open_webui.extensions.credits.models import CreditPrice
from sqlalchemy import select

_PRICE_CATALOG_PATH = Path(__file__).with_name('credit_prices.json')


def load_prices() -> list[dict[str, object]]:
    value = json.loads(_PRICE_CATALOG_PATH.read_text(encoding='utf-8'))
    if not isinstance(value, list) or not value:
        raise ValueError('credit price catalog must be a non-empty list')
    return value


PRICES = load_prices()


def _update_row(row: CreditPrice, item: dict[str, object], now: int) -> None:
    row.base_price = str(item['base_price'])
    row.rules = item['rules']
    row.enabled = True
    row.updated_by_id = 'system'
    row.updated_by_name_snapshot = 'System'
    row.updated_at = now


async def seed_prices() -> None:
    """Insert or update every declarative image/video price record."""
    now = int(time())
    async with credit_session() as session:
        existing = (
            await session.scalars(
                select(CreditPrice).where(CreditPrice.service_type.in_(['image', 'video']))
            )
        ).all()
        existing_map = {(row.service_type, row.resource_id, row.action): row for row in existing}
        for item in PRICES:
            key = (str(item['service_type']), str(item['resource_id']), str(item['action']))
            row = existing_map.get(key)
            if row is None:
                row = CreditPrice(
                    id=uuid4().hex,
                    service_type=key[0],
                    resource_id=key[1],
                    action=key[2],
                    base_price=str(item['base_price']),
                    rules=item['rules'],
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            _update_row(row, item, now)
        await session.commit()


if __name__ == '__main__':
    import asyncio

    asyncio.run(seed_prices())
