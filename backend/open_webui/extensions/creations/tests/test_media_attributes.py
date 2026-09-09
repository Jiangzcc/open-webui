from __future__ import annotations

import pytest
from open_webui.extensions.creations.media_attributes import (
    ASPECT_RATIOS,
    CLARITY_TIERS,
    aspect_ratio_from_params,
    clarity_tier_from_params,
    derive_media_attributes,
)


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        # resolution 具名档位
        ({'resolution': 'sd'}, 'sd'),
        ({'resolution': 'hd'}, 'hd'),
        ({'resolution': 'HD'}, 'hd'),
        ({'resolution': 'full_hd'}, 'fhd'),
        ({'resolution': '1080p'}, 'fhd'),
        ({'resolution': '720p'}, 'hd'),
        ({'resolution': '540p'}, 'sd'),
        ({'resolution': '2k'}, '2k'),
        ({'resolution': '4K'}, '4k'),
        # 1k ≈ 1024，归 hd 档
        ({'resolution': '1k'}, 'hd'),
        # 部分图片模型把 WxH 放在 resolution，而非 size。
        ({'resolution': '1024x1024'}, 'hd'),
        ({'resolution': '1920X1080'}, 'fhd'),
        # resolution 不可识别时回退 size 短边
        ({'resolution': 'cinema', 'size': '1024x1024'}, 'hd'),
        ({'size': '768x768'}, 'hd'),
        ({'size': '1280x720'}, 'hd'),
        ({'size': '1920x1080'}, 'fhd'),
        ({'size': '2048x2048'}, '2k'),
        ({'size': '3840x2160'}, '4k'),
        ({'size': '512x512'}, 'sd'),
        # size 支持大写 X/乘号分隔
        ({'size': '1024X1024'}, 'hd'),
        # 无可用信息
        (None, None),
        ({}, None),
        ({'quality': 'high'}, None),
        ({'resolution': 'default'}, None),
        ({'resolution': '1024x0'}, None),
        ({'size': 'auto'}, None),
    ],
)
def test_clarity_tier_normalization(params, expected) -> None:
    assert clarity_tier_from_params(params) == expected


@pytest.mark.parametrize(
    ('params', 'expected'),
    [
        # 显式比例字符串直接吸附
        ({'aspect_ratio': '16:9'}, '16:9'),
        ({'aspect_ratio': '9:16'}, '9:16'),
        ({'aspect_ratio': '1:1'}, '1:1'),
        ({'aspect_ratio': '4:3'}, '4:3'),
        ({'aspect_ratio': '3:4'}, '3:4'),
        ({'aspect_ratio': '21:9'}, '21:9'),
        ({'aspect_ratio': 'square'}, '1:1'),
        # 未约分的等价比例也要吸附到常用标签
        ({'aspect_ratio': '32:18'}, '16:9'),
        ({'aspect_ratio': '20:20'}, '1:1'),
        # 非法分母不得让已成功的生成任务在落库时崩溃。
        ({'aspect_ratio': '16:0'}, None),
        ({'aspect_ratio': '0:9'}, None),
        # 语义词（landscape/auto）无法判定方向，归 None
        ({'aspect_ratio': 'landscape'}, None),
        ({'aspect_ratio': 'auto'}, None),
        # 从 size 推导宽高比
        ({'size': '1024x1024'}, '1:1'),
        ({'size': '1024x1536'}, '2:3'),
        ({'size': '1536x1024'}, '3:2'),
        ({'size': '1920x1080'}, '16:9'),
        ({'size': '1080x1920'}, '9:16'),
        # 旧有图片模型的尺寸选项会写入 resolution。
        ({'resolution': '1024x1024'}, '1:1'),
        ({'resolution': '1536x1024'}, '3:2'),
        ({'resolution': '1024x0'}, None),
        # 5:4 吸附不中任何常用档，宁缺勿错
        ({'size': '1000x800'}, None),
        (None, None),
        ({}, None),
    ],
)
def test_aspect_ratio_normalization(params, expected) -> None:
    assert aspect_ratio_from_params(params) == expected


def test_derive_media_attributes_returns_both_values() -> None:
    assert derive_media_attributes({'resolution': '2k', 'aspect_ratio': '16:9'}) == ('2k', '16:9')
    assert derive_media_attributes(None) == (None, None)


def test_tier_and_ratio_labels_are_the_documented_domains() -> None:
    # 路由 Literal 校验与前端下拉选项都以这两个元组为准，锁死取值域。
    assert CLARITY_TIERS == ('sd', 'hd', 'fhd', '2k', '4k')
    assert ASPECT_RATIOS == ('1:1', '4:3', '3:4', '3:2', '2:3', '16:9', '9:16', '21:9')
