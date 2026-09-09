"""归一化生成媒体的清晰度档位与画幅比例。

providers 对尺寸的表述方言不一：fal 图片可能写 ``resolution='hd'/'1k'/'2k'``
或 ``size='1024x1024'``，视频写 ``resolution='720p'/'1080p'``、
``aspect_ratio='16:9'``。直接对 ``params_json`` 原值做 SQL 筛选会漏掉用其他
方言写入的作品。写入 ``CreationMediaItem`` 时先经这里归一化到独立列，列表
筛选才是可靠的等值匹配。

归一化规则（优先级从高到低）：

- 清晰度：``resolution`` 里的具名档位（sd/hd、480p/720p/1080p、1k/2k/4k）；
  否则 ``size`` 的 ``WxH`` 取短边归档（>=2160→4k，>=1440→2k，>=1080→fhd，
  >=720→hd，其余→sd）。无法判定时为 ``None``（旧数据/未上报尺寸）。
- 比例：``aspect_ratio`` 的 ``a:b``（含 ``square``）；否则 ``size`` 的宽高比。
  都按 2% 容差吸附到常用画幅标签，吸附不中为 ``None``。
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

CLARITY_TIERS: tuple[str, ...] = ('sd', 'hd', 'fhd', '2k', '4k')
ASPECT_RATIOS: tuple[str, ...] = ('1:1', '4:3', '3:4', '3:2', '2:3', '16:9', '9:16', '21:9')

# 吸附容差：1024/1536=0.6667 与 2:3 的偏差约 0.05% 就能命中；
# 2% 足够宽容近似档（如 1024x1020）又不会把 5:4 吸到 4:3。
_RATIO_TOLERANCE = 0.02

_RATIO_VALUES = {
    label: int(label.split(':')[0]) / int(label.split(':')[1]) for label in ASPECT_RATIOS
}

_SIZE_PATTERN = re.compile(r'^(\d{2,5})\s*[xX×]\s*(\d{2,5})$')
_HEIGHT_PATTERN = re.compile(r'^(\d{3,4})p$', re.IGNORECASE)
_K_PATTERN = re.compile(r'^([1-4])k$', re.IGNORECASE)
_RATIO_PATTERN = re.compile(r'^(\d{1,2}):(\d{1,2})$')

_NAMED_TIERS = {
    'sd': 'sd',
    'hd': 'hd',
    'full_hd': 'fhd',
    'full-hd': 'fhd',
    'fhd': 'fhd',
}

_SHORT_SIDE_TIERS: tuple[tuple[int, str], ...] = (
    (2160, '4k'),
    (1440, '2k'),
    (1080, 'fhd'),
    (720, 'hd'),
)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tier_from_pixels(pixels: int) -> str:
    for threshold, tier in _SHORT_SIDE_TIERS:
        if pixels >= threshold:
            return tier
    return 'sd'


def _tier_from_named(text: str) -> str | None:
    named = _NAMED_TIERS.get(text.lower())
    if named:
        return named
    height = _HEIGHT_PATTERN.match(text)
    if height:
        return _tier_from_pixels(int(height.group(1)))
    kilo = _K_PATTERN.match(text)
    if kilo:
        kilos = int(kilo.group(1))
        # 1k ≈ 1024，短边落在 720–1080 档之间，按 hd 归档；4k 及以上按 4k。
        if kilos >= 4:
            return '4k'
        if kilos >= 2:
            return '2k'
        return 'hd'
    return None


def _dimensions(text: str | None) -> tuple[int, int] | None:
    if text is None:
        return None
    match = _SIZE_PATTERN.match(text)
    if match is None:
        return None
    width, height = int(match.group(1)), int(match.group(2))
    return (width, height) if width > 0 and height > 0 else None


def clarity_tier_from_params(params: Mapping[str, Any] | None) -> str | None:
    if not params:
        return None
    resolution = _as_text(params.get('resolution'))
    if resolution:
        tier = _tier_from_named(resolution)
        if tier:
            return tier
        dimensions = _dimensions(resolution)
        if dimensions:
            return _tier_from_pixels(min(dimensions))
    dimensions = _dimensions(_as_text(params.get('size')))
    if dimensions:
        return _tier_from_pixels(min(dimensions))
    return None


def _snap_ratio(value: float) -> str | None:
    for label, ratio in _RATIO_VALUES.items():
        if abs(value - ratio) / ratio <= _RATIO_TOLERANCE:
            return label
    return None


def aspect_ratio_from_params(params: Mapping[str, Any] | None) -> str | None:
    if not params:
        return None
    declared = _as_text(params.get('aspect_ratio'))
    if declared:
        if declared.lower() == 'square':
            return '1:1'
        match = _RATIO_PATTERN.match(declared)
        if match:
            width, height = int(match.group(1)), int(match.group(2))
            if width > 0 and height > 0:
                return _snap_ratio(width / height)
    dimensions = _dimensions(_as_text(params.get('size')))
    if dimensions is None:
        dimensions = _dimensions(_as_text(params.get('resolution')))
    if dimensions:
        return _snap_ratio(dimensions[0] / dimensions[1])
    return None


def derive_media_attributes(params: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
    """写入前一次性算出 ``(clarity_tier, aspect_ratio)``，供列字段使用。"""
    return clarity_tier_from_params(params), aspect_ratio_from_params(params)
