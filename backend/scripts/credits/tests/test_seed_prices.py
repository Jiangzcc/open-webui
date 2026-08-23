from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from open_webui.extensions.credits.pricing import compute_price
from scripts.credits.seed_prices import PRICES

# seed_prices.py 由 init_prices.py 生成后手工同步（生成器依赖一次性的
# /tmp/fal_prices.json 快照，无法随时重跑），seedance-2.0 的 480p/4k 倍率
# 与 fast 基准价又来自 FAL 文档换算，故用测试锁住，防止后续手工编辑漂移。
# 换算依据见 init_prices.py 的 _VIDEO_TIER_BASE / _VIDEO_RESOLUTION_TIERS 注释。


@dataclass(frozen=True)
class _PriceRow:
    """compute_price 所需的最小行形态（字段名与 CreditPrice 行一致）。"""

    service_type: str
    resource_id: str
    action: str
    base_price: str
    rules: dict
    enabled: bool = True


def _seedance_entries() -> dict[str, dict[str, Any]]:
    entries = {
        entry['resource_id']: entry
        for entry in PRICES
        if entry['resource_id'].startswith('bytedance/seedance-2.0')
    }
    assert set(entries) == {
        'bytedance/seedance-2.0/text-to-video',
        'bytedance/seedance-2.0/image-to-video',
        'bytedance/seedance-2.0/fast/text-to-video',
        'bytedance/seedance-2.0/fast/image-to-video',
    }
    return entries


def _resolution_values(entry: dict[str, Any]) -> dict[str, str]:
    dimension = next(d for d in entry['rules']['dimensions'] if d['key'] == 'resolution')
    assert dimension['kind'] == 'exact_map'
    return dimension['values']


def _raw_price(resource_id: str, resolution: str, duration: str) -> Decimal:
    entry = _seedance_entries()[resource_id]
    row = _PriceRow(
        service_type=entry['service_type'],
        resource_id=entry['resource_id'],
        action=entry['action'],
        base_price=entry['base_price'],
        rules=entry['rules'],
    )
    quote = compute_price(row, {'resolution': resolution, 'duration': duration})
    return Decimal(quote.raw_price)


def test_seedance_resolution_tiers_match_fal_documented_pricing() -> None:
    entries = _seedance_entries()

    # 标准版基准 720p $0.3034/s → 364.08 积分/秒（×1000 积分/$ ×1.2 利润）。
    # 480p/4k 无 per-second 价，按 FAL token 计费换算：480p 等价 $0.1345/s、
    # 4k 等价 $1.5552/s（tokens = w×h×duration×24/1024）。
    for resource_id in (
        'bytedance/seedance-2.0/text-to-video',
        'bytedance/seedance-2.0/image-to-video',
    ):
        assert entries[resource_id]['base_price'] == '364.08'
        assert _resolution_values(entries[resource_id]) == {
            '480p': '0.443',
            '720p': '1',
            '1080p': '2.248',
            '4k': '5.126',
            'default': '1',
        }

    # fast 基准 720p $0.2419/s → 290.28 积分/秒。FAL API 返回的 $0.0112 是
    # 每千 token 价而非每秒价（720p 每秒 21600 token，旧值 13.44 少收 21.6 倍）；
    # fast 仅支持 480p/720p，480p 按 $0.0112/千 token 换算等价 $0.1076/s。
    for resource_id in (
        'bytedance/seedance-2.0/fast/text-to-video',
        'bytedance/seedance-2.0/fast/image-to-video',
    ):
        assert entries[resource_id]['base_price'] == '290.28'
        assert _resolution_values(entries[resource_id]) == {
            '480p': '0.445',
            '720p': '1',
            'default': '1',
        }


def test_seedance_token_billed_resolutions_charge_expected_credits() -> None:
    # 720p 10s：$0.3034×10×1.2×1000 = 3640.8 积分。
    assert _raw_price('bytedance/seedance-2.0/text-to-video', '720p', '10') == Decimal('3640.8')
    # 480p 10s：364.08×0.443×10 = 1612.8744（对应 $0.1345/s）。
    assert _raw_price('bytedance/seedance-2.0/text-to-video', '480p', '10') == Decimal('1612.8744')
    # 4k 10s：364.08×5.126×10 = 18662.7408（对应 $1.5552/s）。
    assert _raw_price('bytedance/seedance-2.0/text-to-video', '4k', '10') == Decimal('18662.7408')
    # fast 720p 10s：$0.2419×10×1.2×1000 = 2902.8 积分。
    assert _raw_price('bytedance/seedance-2.0/fast/text-to-video', '720p', '10') == Decimal('2902.8')
    # fast 480p 10s：290.28×0.445×10 = 1291.746（对应 $0.1076/s）。
    assert _raw_price('bytedance/seedance-2.0/fast/text-to-video', '480p', '10') == Decimal('1291.746')
