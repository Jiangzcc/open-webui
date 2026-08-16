#!/usr/bin/env python
"""
初始化积分定价：为所有图片和视频模型生成 CreditPrice 记录。

定价规则：
  - 汇率：1 积分 = $0.001（1000 积分 = $1 USD）
  - 利润：在 FAL 成本基础上上浮 20%（用户售价 = 成本 × 1.2）
  - 图片模型：
      megapixels / processed megapixels → base_price = unit_price×100,
        dimensions: [size exact_map(各分辨率的兆像素倍率), image_count quantity]
      images / generations / credits / units(图片) → base_price = unit_price×100,
        dimensions: [image_count quantity]
      compute seconds → base_price = unit_price×100×20(估算 20s 计算),
        dimensions: [image_count quantity]
  - 视频模型：
      seconds → base_price = unit_price×100,
        dimensions: [duration proportional 1]
      5 seconds → base_price = unit_price×100,
        dimensions: [duration unit_blocks 5]
      videos / units(按次) / credits / 空 unit → base_price = unit_price×100,
        dimensions: []
      units(seedance 按秒) → base_price = unit_price×100,
        dimensions: [duration proportional 1]
      分层定价模型（A 类兼容）：FAL 文档按 resolution/audio_mode 分层定价的模型，
        base_price 取文档最低档（最低分辨率 × silent）真实 USD 单价（非 API unit_price，
        后者常对应非最低档），dimensions 额外挂 resolution/audio_mode exact_map（含
        'default' 键兜底）。见 _VIDEO_TIER_BASE / _VIDEO_RESOLUTION_TIERS / _VIDEO_AUDIO_TIERS。

用法：
  cd backend
  WEBUI_SECRET_KEY=<key> PYTHONPATH=. python -m open_webui.extensions.credits.init_prices
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from uuid import uuid4

# ── 常量 ──────────────────────────────────────────────────────────────
CREDITS_PER_USD = 1000  # 1 积分 = $0.001
PROFIT_MARGIN = 1.2  # 在 FAL 成本基础上上浮 20%（用户售价 = 成本 × 1.2）
COMPUTE_SECONDS_ESTIMATE = 20  # compute seconds 模型的估算计算时长
MEGA_PIXEL_UNIT = 1_000_000  # pixel_count 维度的 unit_size：1 兆像素 = 1,000,000 像素

_CATALOG_DIR = Path(__file__).resolve().parent.parent / 'fal_catalog' / 'catalog'

# seedance 系列按秒计费（units 实际含义为 per second）
_PER_SECOND_UNITS_VIDEO = {
    'bytedance/seedance-2.0/text-to-video',
    'bytedance/seedance-2.0/image-to-video',
    'bytedance/seedance-2.0/fast/text-to-video',
    'bytedance/seedance-2.0/fast/image-to-video',
}

# 按次计费的 video units 模型（units 实际含义为 per video generation）
_PER_VIDEO_UNITS_VIDEO = {
    'fal-ai/minimax/hailuo-2.3/pro/text-to-video',
    'fal-ai/minimax/hailuo-2.3/pro/image-to-video',
    'fal-ai/minimax/hailuo-2.3/standard/text-to-video',
    'fal-ai/minimax/hailuo-2.3/standard/image-to-video',
    'fal-ai/minimax/hailuo-2.3-fast/pro/image-to-video',
    'fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video',
    'google/gemini-omni-flash',
    'google/gemini-omni-flash/edit',
    'google/gemini-omni-flash/image-to-video',
    'google/gemini-omni-flash/reference-to-video',
    'google/nano-banana-2-lite',
}

# ideogram/v4 实际按 megapixel 计费，但有模式倍率
_IDEOGRAM_V4_MODELS = {
    'ideogram/v4',
    'ideogram/v4/fast',
    'ideogram/v4/instant',
    'ideogram/v4/image-to-image',
}

# krea/v2 按兆像素计费
_KREA_V2_MODELS = {
    'krea/v2/large/text-to-image',
    'krea/v2/medium/text-to-image',
    'krea/v2/medium/turbo/text-to-image',
}

# phota 按 1K/4K 区分
_PHOTA_MODELS = {
    'fal-ai/phota',
    'fal-ai/phota/edit',
}

# ── 视频分层定价基准（A 类兼容）──────────────────────────────────────
# FAL API 返回的 unit_price 对分层模型常不对应最低档（如 veo3.1 API 返回
# generate 价 $0.4，seedance API 返回 token 价 $0.014 而非 per-second 价）。
# 直接用 API 价作 base 会让分层倍率与基准错位（silent 被多收、低档被高估）。
# 故分层模型必须用文档最低档（最低分辨率 × silent）真实 USD 单价作 base_price。
# 数据来源：docs/fal 各模型 Pricing 章节。
# 值为 (base_usd, duration_kind)：duration_kind 决定 duration 维度类型。
_VIDEO_TIER_BASE: dict[str, tuple[float, str]] = {
    # happy-horse: 720p $0.28/s（$0.14 input + $0.14 output 双边总价）
    'alibaba/happy-horse/video-edit': (0.28, 'per_second'),
    # wan v2.7: 720p $0.10/s
    'fal-ai/wan/v2.7/text-to-video': (0.10, 'per_second'),
    'fal-ai/wan/v2.7/image-to-video': (0.10, 'per_second'),
    # wan-25-preview: 480p $0.05/s
    'fal-ai/wan-25-preview/text-to-video': (0.05, 'per_second'),
    'fal-ai/wan-25-preview/image-to-video': (0.05, 'per_second'),
    # luma ray t2v/i2v: 540p 5s flat 价（unit='5 seconds'）
    'luma/agent/ray/v3.2/text-to-video': (0.50, '5s_blocks'),
    'luma/agent/ray/v3.2/image-to-video': (0.15, '5s_blocks'),
    # luma ray reframe/v2v: 540p per-source-second（API 为 compute seconds，改用文档 per-second 价）
    'luma/agent/ray/v3.2/reframe': (0.06, 'per_second'),
    'luma/agent/ray/v3.2/video-to-video': (0.144, 'per_second'),
    # pika v2.2: 720p 5s flat（unit='videos'，按次，duration 不参与 A 类）
    'fal-ai/pika/v2.2/text-to-video': (0.20, 'flat'),
    'fal-ai/pika/v2.2/image-to-video': (0.20, 'flat'),
    'fal-ai/pika/v2.2/pikaframes': (0.20, 'flat'),
    'fal-ai/pika/v2.2/pikascenes': (0.20, 'flat'),
    # pixverse c1: 360p silent $0.03/s
    'fal-ai/pixverse/c1/image-to-video': (0.03, 'per_second'),
    'fal-ai/pixverse/c1/text-to-video': (0.03, 'per_second'),
    'fal-ai/pixverse/c1/reference-to-video': (0.03, 'per_second'),
    'fal-ai/pixverse/c1/transition': (0.03, 'per_second'),
    # pixverse v6: 360p silent $0.025/s
    'fal-ai/pixverse/v6/image-to-video': (0.025, 'per_second'),
    'fal-ai/pixverse/v6/text-to-video': (0.025, 'per_second'),
    'fal-ai/pixverse/v6/extend': (0.025, 'per_second'),
    'fal-ai/pixverse/v6/transition': (0.025, 'per_second'),
    # seedance-2.0: 720p $0.3034/s（API 返回 token 价 $0.014，此处用 per-second 价）
    'bytedance/seedance-2.0/text-to-video': (0.3034, 'per_second'),
    'bytedance/seedance-2.0/image-to-video': (0.3034, 'per_second'),
    # kling v3 pro: silent $0.112/s（无 resolution 分层，仅 audio）
    'fal-ai/kling-video/v3/pro/text-to-video': (0.112, 'per_second'),
    'fal-ai/kling-video/v3/pro/image-to-video': (0.112, 'per_second'),
    # kling v3 standard: silent $0.084/s
    'fal-ai/kling-video/v3/standard/text-to-video': (0.084, 'per_second'),
    'fal-ai/kling-video/v3/standard/image-to-video': (0.084, 'per_second'),
    # veo3.1: 720p silent $0.20/s
    'fal-ai/veo3.1': (0.20, 'per_second'),
    'fal-ai/veo3.1/image-to-video': (0.20, 'per_second'),
    'fal-ai/veo3.1/first-last-frame-to-video': (0.20, 'per_second'),
    'fal-ai/veo3.1/reference-to-video': (0.20, 'per_second'),
    'fal-ai/veo3.1/extend-video': (0.20, 'per_second'),
    # veo3.1/fast: 720p silent $0.10/s
    'fal-ai/veo3.1/fast': (0.10, 'per_second'),
    'fal-ai/veo3.1/fast/image-to-video': (0.10, 'per_second'),
    'fal-ai/veo3.1/fast/first-last-frame-to-video': (0.10, 'per_second'),
    'fal-ai/veo3.1/fast/extend-video': (0.10, 'per_second'),
    'fal-ai/veo3.1/fast/reference-to-video': (0.10, 'per_second'),
    # veo3.1/lite: 720p silent $0.03/s
    'fal-ai/veo3.1/lite': (0.03, 'per_second'),
    'fal-ai/veo3.1/lite/image-to-video': (0.03, 'per_second'),
    'fal-ai/veo3.1/lite/first-last-frame-to-video': (0.03, 'per_second'),
}

# FAL 文档明确按 resolution 分层定价的视频模型。
# 倍率相对最低档（通常是 catalog.default 或最低分辨率）= 1。
# 数据来源：docs/fal 各模型 Pricing 章节（见 workflow 调研结果）。
# 每个 exact_map 都含 'default' 键兜底：catalog 无 resolution_field 的模型
# 或老任务 params 无 resolution 时，video_quote_dimensions 返回 'default'，
# 必须能命中，否则报价端 price_rule_incomplete（pricing.py:106-108）。
_VIDEO_RESOLUTION_TIERS: dict[str, dict[str, str]] = {
    # happy-horse: 720p $0.14/s → 1080p $0.28/s（×2）
    'alibaba/happy-horse/video-edit': {'720p': '1', '1080p': '2', 'default': '1'},
    # wan v2.7: 720p $0.10/s → 1080p $0.15/s（×1.5）
    'fal-ai/wan/v2.7/text-to-video': {'720p': '1', '1080p': '1.5', 'default': '1'},
    'fal-ai/wan/v2.7/image-to-video': {'720p': '1', '1080p': '1.5', 'default': '1'},
    # wan-25-preview: 480p $0.05 → 720p $0.10 → 1080p $0.15
    'fal-ai/wan-25-preview/text-to-video': {'480p': '1', '720p': '2', '1080p': '3', 'default': '1'},
    'fal-ai/wan-25-preview/image-to-video': {'480p': '1', '720p': '2', '1080p': '3', 'default': '1'},
    # luma ray v3.2: 540p 最低档
    'luma/agent/ray/v3.2/text-to-video': {'540p': '1', '720p': '2', '1080p': '4', 'default': '1'},
    'luma/agent/ray/v3.2/image-to-video': {'540p': '1', '720p': '2', '1080p': '8', 'default': '1'},
    'luma/agent/ray/v3.2/reframe': {'540p': '1', '720p': '2', '1080p': '6', 'default': '1'},
    'luma/agent/ray/v3.2/video-to-video': {'540p': '1', '720p': '1.5', '1080p': '3', 'default': '1'},
    # pika v2.2: 720p $0.04 → 1080p $0.09（×2.25）；pikaframes 1080p×1.5
    'fal-ai/pika/v2.2/text-to-video': {'720p': '1', '1080p': '2.25', 'default': '1'},
    'fal-ai/pika/v2.2/image-to-video': {'720p': '1', '1080p': '2.25', 'default': '1'},
    'fal-ai/pika/v2.2/pikaframes': {'720p': '1', '1080p': '1.5', 'default': '1'},
    'fal-ai/pika/v2.2/pikascenes': {'720p': '1', '1080p': '2.25', 'default': '1'},
    # pixverse c1: 360p 最低档
    'fal-ai/pixverse/c1/image-to-video': {'360p': '1', '540p': '1.333', '720p': '1.667', '1080p': '3.167', 'default': '1'},
    'fal-ai/pixverse/c1/text-to-video': {'360p': '1', '540p': '1.333', '720p': '1.667', '1080p': '3.167', 'default': '1'},
    'fal-ai/pixverse/c1/reference-to-video': {'360p': '1', '540p': '1.333', '720p': '1.667', '1080p': '3.167', 'default': '1'},
    'fal-ai/pixverse/c1/transition': {'360p': '1', '540p': '1.333', '720p': '1.667', '1080p': '3.167', 'default': '1'},
    # pixverse v6
    'fal-ai/pixverse/v6/image-to-video': {'360p': '1', '540p': '1.4', '720p': '1.8', '1080p': '3.6', 'default': '1'},
    'fal-ai/pixverse/v6/text-to-video': {'360p': '1', '540p': '1.4', '720p': '1.8', '1080p': '3.6', 'default': '1'},
    'fal-ai/pixverse/v6/extend': {'360p': '1', '540p': '1.4', '720p': '1.8', '1080p': '3.6', 'default': '1'},
    'fal-ai/pixverse/v6/transition': {'360p': '1', '540p': '1.4', '720p': '1.8', '1080p': '3.6', 'default': '1'},
    # seedance-2.0: 720p $0.3034 → 1080p $0.682（×2.248）
    # 注：480p/4k 在 FAL 按纯 token 计费（无 per-second 价），本次 A 类未支持 token，
    # 故只在文档有 per-second 价的 720p/1080p 间分层；480p/4k 走 default=1 占位。
    'bytedance/seedance-2.0/text-to-video': {'720p': '1', '1080p': '2.248', 'default': '1'},
    'bytedance/seedance-2.0/image-to-video': {'720p': '1', '1080p': '2.248', 'default': '1'},
    # veo3.1: 720p/1080p 同价，4k ×2
    'fal-ai/veo3.1': {'720p': '1', '1080p': '1', '4k': '2', 'default': '1'},
    'fal-ai/veo3.1/image-to-video': {'720p': '1', '1080p': '1', '4k': '2', 'default': '1'},
    'fal-ai/veo3.1/first-last-frame-to-video': {'720p': '1', '1080p': '1', '4k': '2', 'default': '1'},
    'fal-ai/veo3.1/reference-to-video': {'720p': '1', '1080p': '1', '4k': '2', 'default': '1'},
    # veo3.1/fast: 720p/1080p 同价，4k ×3
    'fal-ai/veo3.1/fast': {'720p': '1', '1080p': '1', '4k': '3', 'default': '1'},
    'fal-ai/veo3.1/fast/image-to-video': {'720p': '1', '1080p': '1', '4k': '3', 'default': '1'},
    'fal-ai/veo3.1/fast/first-last-frame-to-video': {'720p': '1', '1080p': '1', '4k': '3', 'default': '1'},
    # veo3.1/fast/reference-to-video: 文档为平价（无分层），不在此表
    # veo3.1/lite: 720p $0.03 → 1080p $0.05（×1.67）
    'fal-ai/veo3.1/lite': {'720p': '1', '1080p': '1.67', 'default': '1'},
    'fal-ai/veo3.1/lite/image-to-video': {'720p': '1', '1080p': '1.67', 'default': '1'},
    'fal-ai/veo3.1/lite/first-last-frame-to-video': {'720p': '1', '1080p': '1.67', 'default': '1'},
}

# FAL 文档明确按 audio_mode 分层定价的视频模型。
# kling v3 pro/standard: silent/generate/voice 三档（voice 档 FAL 按 voice_control 计价，
# 本次作为 audio_mode 的第三档兼容，前端选 voice 即按该倍率计费）。
# veo3.1: silent/generate 两档（audio off/on）。
# pixverse c1/v6: silent/generate 两档。
# 倍率相对最低档（silent）= 1。default 取 silent（与各模型 default_audio_mode 多为 generate 不同，
# 但 default 键是"请求缺失时"的兜底，取 1 保证不会因缺失而抬价）。
_VIDEO_AUDIO_TIERS: dict[str, dict[str, str]] = {
    # kling v3 pro: silent $0.112 → generate $0.168 → voice $0.196
    'fal-ai/kling-video/v3/pro/text-to-video': {'silent': '1', 'generate': '1.5', 'voice': '1.75', 'default': '1'},
    'fal-ai/kling-video/v3/pro/image-to-video': {'silent': '1', 'generate': '1.5', 'voice': '1.75', 'default': '1'},
    # kling v3 standard: silent $0.084 → generate $0.126 → voice $0.154
    'fal-ai/kling-video/v3/standard/text-to-video': {'silent': '1', 'generate': '1.5', 'voice': '1.833', 'default': '1'},
    'fal-ai/kling-video/v3/standard/image-to-video': {'silent': '1', 'generate': '1.5', 'voice': '1.833', 'default': '1'},
    # veo3.1: silent $0.20 → generate $0.40（×2）
    'fal-ai/veo3.1': {'silent': '1', 'generate': '2', 'default': '1'},
    'fal-ai/veo3.1/image-to-video': {'silent': '1', 'generate': '2', 'default': '1'},
    'fal-ai/veo3.1/first-last-frame-to-video': {'silent': '1', 'generate': '2', 'default': '1'},
    'fal-ai/veo3.1/reference-to-video': {'silent': '1', 'generate': '2', 'default': '1'},
    'fal-ai/veo3.1/extend-video': {'silent': '1', 'generate': '2', 'default': '1'},
    # veo3.1/fast: silent $0.10 → generate $0.15（×1.5）
    'fal-ai/veo3.1/fast': {'silent': '1', 'generate': '1.5', 'default': '1'},
    'fal-ai/veo3.1/fast/image-to-video': {'silent': '1', 'generate': '1.5', 'default': '1'},
    'fal-ai/veo3.1/fast/first-last-frame-to-video': {'silent': '1', 'generate': '1.5', 'default': '1'},
    'fal-ai/veo3.1/fast/extend-video': {'silent': '1', 'generate': '1.5', 'default': '1'},
    'fal-ai/veo3.1/fast/reference-to-video': {'silent': '1', 'generate': '1.5', 'default': '1'},
    # veo3.1/lite: silent $0.03 → generate $0.05（×1.67）
    'fal-ai/veo3.1/lite': {'silent': '1', 'generate': '1.67', 'default': '1'},
    'fal-ai/veo3.1/lite/image-to-video': {'silent': '1', 'generate': '1.67', 'default': '1'},
    'fal-ai/veo3.1/lite/first-last-frame-to-video': {'silent': '1', 'generate': '1.67', 'default': '1'},
    # pixverse c1: silent $0.03(360p) → generate $0.04(360p)（×1.333）
    'fal-ai/pixverse/c1/image-to-video': {'silent': '1', 'generate': '1.333', 'default': '1'},
    'fal-ai/pixverse/c1/text-to-video': {'silent': '1', 'generate': '1.333', 'default': '1'},
    'fal-ai/pixverse/c1/reference-to-video': {'silent': '1', 'generate': '1.333', 'default': '1'},
    'fal-ai/pixverse/c1/transition': {'silent': '1', 'generate': '1.333', 'default': '1'},
    # pixverse v6: silent $0.025(360p) → generate $0.035(360p)（×1.4）
    'fal-ai/pixverse/v6/image-to-video': {'silent': '1', 'generate': '1.4', 'default': '1'},
    'fal-ai/pixverse/v6/text-to-video': {'silent': '1', 'generate': '1.4', 'default': '1'},
    'fal-ai/pixverse/v6/extend': {'silent': '1', 'generate': '1.4', 'default': '1'},
    'fal-ai/pixverse/v6/transition': {'silent': '1', 'generate': '1.4', 'default': '1'},
}


def _usd_to_credits(usd: float) -> str:
    """将 USD 金额转换为积分数（在 FAL 成本基础上上浮 20% 利润）。"""
    credits = usd * CREDITS_PER_USD * PROFIT_MARGIN
    # 保留 6 位小数，去掉尾零
    s = f'{credits:.6f}'.rstrip('0').rstrip('.')
    return s if s else '0'


def _megapixels(width: int, height: int) -> str:
    """计算兆像素倍率（width×height / 1,000,000）。"""
    mp = (width * height) / 1_000_000
    s = f'{mp:.6f}'.rstrip('0').rstrip('.')
    return s if s else '0'


def _parse_resolution(res: str) -> tuple[int, int] | None:
    """解析 '1024x1024' 格式的分辨率为 (width, height)。"""
    parts = res.lower().split('x')
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return None


def _load_catalog_models() -> dict[str, dict]:
    """加载目录中所有模型定义，返回 {model_id: definition}。"""
    models = {}

    # 图片目录
    img_manifest = json.loads((_CATALOG_DIR / 'image' / 'manifest.json').read_text(encoding='utf-8'))
    for filename in img_manifest['files']:
        path = _CATALOG_DIR / 'image' / filename
        for m in json.loads(path.read_text(encoding='utf-8')):
            models[m['id']] = m

    # 视频目录
    vid_manifest = json.loads((_CATALOG_DIR / 'video' / 'manifest.json').read_text(encoding='utf-8'))
    for filename in vid_manifest['files']:
        path = _CATALOG_DIR / 'video' / filename
        for m in json.loads(path.read_text(encoding='utf-8')):
            models[m['id']] = m

    return models


def _load_fal_prices() -> dict[str, dict]:
    """加载 FAL API 返回的价格，返回 {endpoint_id: {unit_price, unit, currency}}。"""
    prices = {}
    for p in json.loads(Path('/tmp/fal_prices.json').read_text(encoding='utf-8')):
        prices[p['endpoint_id']] = p
    return prices


def _image_megapixel_rules(definition: dict) -> dict:
    """为按兆像素计费的图片模型生成规则。

    关键：支持自定义尺寸的模型用 pixel_count 的 proportional 规则，
    按 (宽×高)/1,000,000 计算实际兆像素，而非枚举所有分辨率。
    这样任意 WxH 尺寸都能正确计价。不支持自定义尺寸的模型
    用 size 的 exact_map 枚举其固定分辨率。
    """
    has_custom_size = bool(definition.get('custom_size_field') or definition.get('custom_size'))

    if has_custom_size:
        # 支持自定义尺寸：用 pixel_count proportional(÷1,000,000) 计费
        # image_adapter._dimensions() 会在 size/resolution 为 WxH 时
        # 自动计算 pixel_count 并加入计费维度。
        return {
            'schema_version': 1,
            'dimensions': [
                {'key': 'pixel_count', 'kind': 'proportional', 'unit_size': str(MEGA_PIXEL_UNIT)},
                {'key': 'image_count', 'kind': 'quantity'},
            ],
        }

    # 不支持自定义尺寸：枚举固定分辨率做 exact_map
    resolutions = definition.get('resolutions', [])
    default_res = definition.get('default_resolution', '')

    values: dict[str, str] = {}
    for res in resolutions:
        wh = _parse_resolution(res)
        if wh:
            values[res] = _megapixels(wh[0], wh[1])

    # default 使用默认分辨率的兆像素，或回退到 1.0
    if default_res:
        wh = _parse_resolution(default_res)
        if wh:
            values['default'] = _megapixels(wh[0], wh[1])
        else:
            values['default'] = '1'
    elif values:
        values['default'] = next(iter(values.values()))
    else:
        values['default'] = '1'

    return {
        'schema_version': 1,
        'dimensions': [
            {'key': 'size', 'kind': 'exact_map', 'values': values},
            {'key': 'image_count', 'kind': 'quantity'},
        ],
    }


def _image_flat_rules() -> dict:
    """为按次/按图计费的图片模型生成规则（仅 image_count）。"""
    return {
        'schema_version': 1,
        'dimensions': [
            {'key': 'image_count', 'kind': 'quantity'},
        ],
    }


def _video_per_second_rules(
    resolution_multipliers: dict[str, str] | None = None,
    audio_mode_multipliers: dict[str, str] | None = None,
) -> dict:
    """为按秒计费的视频模型生成规则。

    可选附加 resolution / audio_mode 的 exact_map 分层维度（A 类兼容）。
    exact_map 必须含 'default' 键：video_quote_dimensions 在请求缺失该维度时
    归一为 'default'（billing.py:52-54），需命中兜底否则 price_rule_incomplete。
    duration 维度始终在前，exact_map 在后，保持现有因子顺序与快照哈希稳定。
    """
    dimensions: list[dict] = [{'key': 'duration', 'kind': 'proportional', 'unit_size': '1'}]
    if resolution_multipliers:
        values = dict(resolution_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'resolution', 'kind': 'exact_map', 'values': values})
    if audio_mode_multipliers:
        values = dict(audio_mode_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'audio_mode', 'kind': 'exact_map', 'values': values})
    return {'schema_version': 1, 'dimensions': dimensions}


def _video_5second_blocks_rules(
    resolution_multipliers: dict[str, str] | None = None,
    audio_mode_multipliers: dict[str, str] | None = None,
) -> dict:
    """为按 5 秒块计费的视频模型生成规则（可选分层维度，同 _video_per_second_rules）。"""
    dimensions: list[dict] = [
        {'key': 'duration', 'kind': 'unit_blocks', 'block_size': '5', 'multiplier_per_block': '1'}
    ]
    if resolution_multipliers:
        values = dict(resolution_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'resolution', 'kind': 'exact_map', 'values': values})
    if audio_mode_multipliers:
        values = dict(audio_mode_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'audio_mode', 'kind': 'exact_map', 'values': values})
    return {'schema_version': 1, 'dimensions': dimensions}


def _video_flat_rules(
    resolution_multipliers: dict[str, str] | None = None,
    audio_mode_multipliers: dict[str, str] | None = None,
) -> dict:
    """为按次计费的视频模型生成规则（可选分层维度，无 duration）。

    按次模型（pika v2.2 / minimax 等）若文档按 resolution 分层，也用 exact_map。
    """
    dimensions: list[dict] = []
    if resolution_multipliers:
        values = dict(resolution_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'resolution', 'kind': 'exact_map', 'values': values})
    if audio_mode_multipliers:
        values = dict(audio_mode_multipliers)
        values.setdefault('default', '1')
        dimensions.append({'key': 'audio_mode', 'kind': 'exact_map', 'values': values})
    return {'schema_version': 1, 'dimensions': dimensions}


def _phota_rules() -> dict:
    """phota 模型按 1K/4K 区分。"""
    return {
        'schema_version': 1,
        'dimensions': [
            {'key': 'size', 'kind': 'exact_map', 'values': {'1K': '1', '4K': '2', 'default': '1'}},
            {'key': 'image_count', 'kind': 'quantity'},
        ],
    }


def _ideogram_v4_rules(definition: dict) -> dict:
    """ideogram/v4 按兆像素计费，支持自定义尺寸 → 用 pixel_count proportional。"""
    has_custom_size = bool(definition.get('custom_size_field') or definition.get('custom_size'))
    if has_custom_size:
        return {
            'schema_version': 1,
            'dimensions': [
                {'key': 'pixel_count', 'kind': 'proportional', 'unit_size': str(MEGA_PIXEL_UNIT)},
                {'key': 'image_count', 'kind': 'quantity'},
            ],
        }

    resolutions = ['512x512', '1024x1024', '768x1024', '1024x768', '576x1024', '1024x576',
                   '1536x1024', '1024x1536', '2048x2048']
    values: dict[str, str] = {}
    for res in resolutions:
        wh = _parse_resolution(res)
        if wh:
            values[res] = _megapixels(wh[0], wh[1])
    values['default'] = '1.048576'

    return {
        'schema_version': 1,
        'dimensions': [
            {'key': 'size', 'kind': 'exact_map', 'values': values},
            {'key': 'image_count', 'kind': 'quantity'},
        ],
    }


def _classify_and_build(
    model_id: str,
    definition: dict,
    fal_price: dict | None,
) -> tuple[str, str, dict, str] | None:
    """
    为单个模型生成 (service_type, resource_id, rules, base_price) 元组。
    返回 None 表示无法定价。
    """
    task = definition.get('task', '')
    is_image = task in ('text-to-image', 'image-to-image')
    is_video = task in ('text-to-video', 'image-to-video', 'video-to-video')

    if not is_image and not is_video:
        return None

    service_type = 'image' if is_image else 'video'
    action = task

    # 特殊模型处理
    if model_id in _PHOTA_MODELS:
        if fal_price is None:
            return None
        base_price = _usd_to_credits(float(fal_price['unit_price']))
        return service_type, model_id, _phota_rules(), base_price

    if model_id in _IDEOGRAM_V4_MODELS:
        if fal_price is None:
            return None
        # ideogram/v4 API 返回 $0.01/unit，实际是 TURBO 模式每兆像素价格
        base_price = _usd_to_credits(float(fal_price['unit_price']))
        return service_type, model_id, _ideogram_v4_rules(definition), base_price

    if model_id in _KREA_V2_MODELS:
        if fal_price is None:
            return None
        # krea/v2 无 custom_size 且无 resolutions，实际按兆像素但尺寸由服务端决定；
        # 无 pixel_count 维度可挂（image_adapter 在 size 非默认 WxH 时才填），用 flat 兜底。
        base_price = _usd_to_credits(float(fal_price['unit_price']))
        return service_type, model_id, _image_flat_rules(), base_price

    if fal_price is None:
        # fal-ai/wan-v2.5/text-to-image: API 404，使用 wan/v2.7/text-to-image 的价格
        if model_id == 'fal-ai/wan-v2.5/text-to-image':
            base_price = _usd_to_credits(0.03)  # $0.03/image
            return service_type, model_id, _image_flat_rules(), base_price
        return None

    unit = fal_price.get('unit', '')
    unit_price = float(fal_price['unit_price'])

    if is_image:
        if unit in ('megapixels', 'processed megapixels'):
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _image_megapixel_rules(definition), base_price
        elif unit in ('images', 'generations', 'credits', 'units'):
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _image_flat_rules(), base_price
        elif unit == 'compute seconds':
            # 估算 20 秒计算时间
            base_price = _usd_to_credits(unit_price * COMPUTE_SECONDS_ESTIMATE)
            return service_type, model_id, _image_flat_rules(), base_price
        elif unit == '':
            # 空 unit，按次计费
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _image_flat_rules(), base_price
        else:
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _image_flat_rules(), base_price

    if is_video:
        # 分层定价模型（A 类）：base_price 取文档最低档真实 USD 单价，
        # 而非 API unit_price（后者常对应非最低档，会导致基准错位）。
        tier_base = _VIDEO_TIER_BASE.get(model_id)
        if tier_base is not None:
            base_usd, duration_kind = tier_base
            base_price = _usd_to_credits(base_usd)
            res_mult = _VIDEO_RESOLUTION_TIERS.get(model_id)
            audio_mult = _VIDEO_AUDIO_TIERS.get(model_id)
            if duration_kind == 'per_second':
                rules = _video_per_second_rules(res_mult, audio_mult)
            elif duration_kind == '5s_blocks':
                rules = _video_5second_blocks_rules(res_mult, audio_mult)
            else:  # flat（pika 按次，duration 不参与）
                rules = _video_flat_rules(res_mult, audio_mult)
            return service_type, model_id, rules, base_price

        if unit == 'seconds':
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_per_second_rules(), base_price
        elif unit == '5 seconds':
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_5second_blocks_rules(), base_price
        elif unit == 'videos':
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_flat_rules(), base_price
        elif unit == 'units':
            if model_id in _PER_SECOND_UNITS_VIDEO:
                base_price = _usd_to_credits(unit_price)
                return service_type, model_id, _video_per_second_rules(), base_price
            elif model_id in _PER_VIDEO_UNITS_VIDEO:
                base_price = _usd_to_credits(unit_price)
                return service_type, model_id, _video_flat_rules(), base_price
            else:
                # 默认按次
                base_price = _usd_to_credits(unit_price)
                return service_type, model_id, _video_flat_rules(), base_price
        elif unit == 'credits':
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_flat_rules(), base_price
        elif unit == '':
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_flat_rules(), base_price
        else:
            base_price = _usd_to_credits(unit_price)
            return service_type, model_id, _video_flat_rules(), base_price

    return None


def _rule_description(rules: dict) -> str:
    """生成规则的人类可读描述。"""
    dims = rules.get('dimensions', [])
    if not dims:
        return '固定价格（无维度）'
    parts = []
    for d in dims:
        kind = d['kind']
        key = d['key']
        if kind == 'exact_map':
            vals = d['values']
            sample = ', '.join(f'{k}→{v}' for k, v in list(vals.items())[:4])
            parts.append(f'{key}=exact_map({sample}...)' if len(vals) > 4 else f'{key}=exact_map({sample})')
        elif kind == 'quantity':
            parts.append(f'{key}=quantity(×N)')
        elif kind == 'proportional':
            parts.append(f'{key}=proportional(÷{d["unit_size"]})')
        elif kind == 'unit_blocks':
            parts.append(f'{key}=unit_blocks(block={d["block_size"]},×{d["multiplier_per_block"]})')
        elif kind == 'numeric_tier':
            tiers = ', '.join(f'≤{t["max"]}→{t["multiplier"]}' for t in d['tiers'])
            parts.append(f'{key}=numeric_tier({tiers})')
    return ', '.join(parts)


def generate_prices() -> list[dict]:
    """生成所有模型的定价记录。"""
    models = _load_catalog_models()
    fal_prices = _load_fal_prices()

    records = []
    for model_id in sorted(models.keys()):
        definition = models[model_id]
        fal_price = fal_prices.get(model_id)

        result = _classify_and_build(model_id, definition, fal_price)
        if result is None:
            records.append({
                'model_id': model_id,
                'service_type': 'image' if definition.get('task', '') in ('text-to-image', 'image-to-image') else 'video',
                'action': definition.get('task', ''),
                'base_price': None,
                'rules': None,
                'enabled': False,
                'fal_unit_price': fal_price.get('unit_price') if fal_price else None,
                'fal_unit': fal_price.get('unit', '') if fal_price else None,
                'note': 'FAL API 未返回价格' if fal_price is None else '',
            })
            continue

        service_type, resource_id, rules, base_price = result
        records.append({
            'model_id': model_id,
            'service_type': service_type,
            'action': definition.get('task', ''),
            'resource_id': resource_id,
            'base_price': base_price,
            'rules': rules,
            'enabled': True,
            'fal_unit_price': fal_price.get('unit_price') if fal_price else None,
            'fal_unit': fal_price.get('unit', '') if fal_price else None,
            'rule_description': _rule_description(rules),
            'note': '',
        })

    return records


def generate_init_script(records: list[dict], output_path: Path) -> None:
    """生成可执行的初始化脚本。"""
    # 只保留 seed_prices 脚本实际使用的字段，避免 json.dumps 的 true/false/null
    # 在 Python 字面量中无法解析（true → NameError）。
    _slim_records = [
        {
            'service_type': r['service_type'],
            'resource_id': r['resource_id'],
            'action': r['action'],
            'base_price': r['base_price'],
            'rules': r['rules'],
        }
        for r in records
        if r.get('base_price')
    ]
    lines = [
        '"""',
        '积分定价初始化脚本 — 由 init_prices.py 自动生成。',
        '',
        f'共 {len(_slim_records)} 条定价记录。',
        '汇率：1 积分 = $0.001 (1000 积分 = $1 USD)',
        '利润：在 FAL 成本基础上上浮 20%（用户售价 = 成本 × 1.2）',
        '',
        '用法：',
        '  cd backend',
        '  WEBUI_SECRET_KEY=<key> PYTHONPATH=. python -m open_webui.extensions.credits.seed_prices',
        '"""',
        'from __future__ import annotations',
        '',
        'import json',
        'from time import time',
        'from uuid import uuid4',
        '',
        'from open_webui.extensions.credits.db import credit_session',
        'from open_webui.extensions.credits.models import CreditPrice',
        'from sqlalchemy import select',
        'from sqlalchemy.ext.asyncio import AsyncSession',
        '',
        '',
        f'PRICES = {json.dumps(_slim_records, indent=2, ensure_ascii=False)}',
        '',
        '',
        'async def seed_prices() -> None:',
        '    """插入或更新所有定价记录。已存在的 (service_type, resource_id, action) 会被更新。"""',
        '    now = int(time())',
        '    async with credit_session() as session:',
        '        # 查询已存在的定价',
        '        existing = (',
        '            await session.scalars(',
        '                select(CreditPrice).where(CreditPrice.service_type.in_([\'image\', \'video\']))',
        '            )',
        '        ).all()',
        '        existing_map = {(r.service_type, r.resource_id, r.action): r for r in existing}',
        '',
        '        for item in PRICES:',
        '            key = (item[\'service_type\'], item[\'resource_id\'], item[\'action\'])',
        '            row = existing_map.get(key)',
        '            if row is None:',
        '                session.add(CreditPrice(',
        '                    id=uuid4().hex,',
        '                    service_type=item[\'service_type\'],',
        '                    resource_id=item[\'resource_id\'],',
        '                    action=item[\'action\'],',
        '                    base_price=item[\'base_price\'],',
        '                    rules=item[\'rules\'],',
        '                    enabled=True,',
        '                    updated_by_id=\'system\',',
        '                    updated_by_name_snapshot=\'System\',',
        '                    created_at=now,',
        '                    updated_at=now,',
        '                ))',
        '            else:',
        '                row.base_price = item[\'base_price\']',
        '                row.rules = item[\'rules\']',
        '                row.enabled = True',
        '                row.updated_by_id = \'system\'',
        '                row.updated_by_name_snapshot = \'System\'',
        '                row.updated_at = now',
        '        await session.commit()',
        '        print(f\'Seeded {len(PRICES)} credit prices\')',
        '',
        '',
        'if __name__ == \'__main__\':',
        '    import asyncio',
        '    asyncio.run(seed_prices())',
        '',
    ]

    output_path.write_text('\n'.join(lines), encoding='utf-8')


def generate_excel(records: list[dict], output_path: Path) -> None:
    """生成 Excel 明细表。"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    # ── Sheet 1: 定价总览 ──
    ws = wb.active
    ws.title = '定价总览'

    headers = [
        '序号', '服务类型', '模型 ID (resource_id)', '任务类型 (action)',
        'FAL 单价 (USD)', 'FAL 计费单位', '积分 base_price', '积分规则类型',
        '规则详情', '规则 JSON', '参考依据', '备注',
    ]

    # 样式
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin'),
    )

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    for i, r in enumerate(records, 2):
        row_data = [
            i - 1,
            r.get('service_type', ''),
            r.get('model_id', ''),
            r.get('action', ''),
            r.get('fal_unit_price', ''),
            r.get('fal_unit', ''),
            r.get('base_price', ''),
            r.get('rule_description', '').split('(')[0].strip() if r.get('rule_description') else '',
            r.get('rule_description', ''),
            json.dumps(r.get('rules'), ensure_ascii=False) if r.get('rules') else '',
            f"FAL API: ${r.get('fal_unit_price', 'N/A')}/{r.get('fal_unit', 'N/A')}" if r.get('fal_unit_price') else 'FAL API 未返回',
            r.get('note', ''),
        ]
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=i, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(vertical='top', wrap_text=True)

    # 列宽
    col_widths = [6, 10, 45, 18, 14, 16, 16, 18, 50, 60, 35, 25]
    for col, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # 冻结首行
    ws.freeze_panes = 'A2'

    # ── Sheet 2: 按类型统计 ──
    ws2 = wb.create_sheet('按类型统计')
    from collections import Counter

    stats_headers = ['计费单位', '模型数量', '示例模型', '定价方式']
    for col, header in enumerate(stats_headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    unit_counts = Counter(r.get('fal_unit', 'N/A') for r in records)
    unit_examples: dict[str, list[str]] = {}
    for r in records:
        u = r.get('fal_unit', 'N/A')
        unit_examples.setdefault(u, []).append(r.get('model_id', ''))

    pricing_methods = {
        'megapixels': 'base_price=单价×100, size=exact_map(兆像素倍率), image_count=quantity',
        'processed megapixels': '同 megapixels',
        'images': 'base_price=单价×100, image_count=quantity',
        'generations': 'base_price=单价×100, image_count=quantity',
        'credits': 'base_price=单价×100, image_count=quantity (图片) / 无维度 (视频)',
        'compute seconds': 'base_price=单价×100×20(估算20s), image_count=quantity',
        'units': '按模型分类：图片→image_count=quantity, 视频→duration=proportional 或无维度',
        'seconds': 'base_price=单价×100, duration=proportional(÷1)',
        '5 seconds': 'base_price=单价×100, duration=unit_blocks(block=5)',
        'videos': 'base_price=单价×100, 无维度',
        '': 'base_price=单价×100, 无维度',
        'N/A': 'FAL API 未返回价格',
    }

    for i, (unit, count) in enumerate(sorted(unit_counts.items(), key=lambda x: str(x[0])), 2):
        examples = ', '.join(unit_examples[unit][:3])
        if len(unit_examples[unit]) > 3:
            examples += f'... (共{len(unit_examples[unit])}个)'
        row_data = [unit or '(空)', count, examples, pricing_methods.get(unit, '未知')]
        for col, value in enumerate(row_data, 1):
            cell = ws2.cell(row=i, column=col, value=value)
            cell.border = thin_border
            cell.alignment = Alignment(vertical='top', wrap_text=True)

    for col, width in enumerate([16, 10, 50, 60], 1):
        ws2.column_dimensions[get_column_letter(col)].width = width
    ws2.freeze_panes = 'A2'

    # ── Sheet 3: 说明 ──
    ws3 = wb.create_sheet('说明')
    notes = [
        ['积分定价说明', ''],
        ['', ''],
        ['汇率', '1 积分 = $0.001 USD (1000 积分 = $1)'],
        ['利润率', '在 FAL 成本基础上上浮 20%（用户售价 = 成本 × 1.2）'],
        ['', ''],
        ['定价公式', 'charged_credits = ceil(base_price × ∏(各维度倍率))'],
        ['', ''],
        ['维度类型', ''],
        ['exact_map', '离散值映射：每个选项对应一个倍率（如分辨率→兆像素倍率）'],
        ['quantity', '数量倍率：倍率 = 传入值（如 image_count=2 → 倍率=2）'],
        ['proportional', '比例倍率：倍率 = 值 / unit_size（如 duration=5, unit_size=1 → 倍率=5）'],
        ['unit_blocks', '块计费：倍率 = ceil(值 / block_size) × multiplier_per_block'],
        ['numeric_tier', '阶梯倍率：按值匹配 tier，返回对应倍率'],
        ['', ''],
        ['图片维度', ''],
        ['size', '分辨率字符串（如 1024x1024），exact_map 映射到兆像素倍率'],
        ['image_count', '生成图片数量（1-4），quantity 倍率'],
        ['', ''],
        ['视频维度', ''],
        ['duration', '视频时长（秒），proportional 或 unit_blocks'],
        ['resolution', '分辨率档位（720p/1080p/4k 等），exact_map 映射到相对最低档的倍率'],
        ['audio_mode', '音频档位（silent/generate/voice），exact_map 映射到相对 silent 的倍率'],
        ['', ''],
        ['特殊模型', ''],
        ['compute seconds', '按估算 20 秒计算时间定价（实际可能不同）'],
        ['ideogram/v4', 'API 返回 $0.01/unit，实际按兆像素×模式倍率计费'],
        ['phota', '按 1K/4K 区分，1K=1倍率，4K=2倍率'],
        ['seedance-2.0', 'units 实际为按秒计费（分层定价取文档 720p per-second 价）'],
        ['minimax/gemini', 'units 实际为按次计费'],
        ['wan-v2.5/text-to-image', 'FAL API 404，参考 wan/v2.7 定价 $0.03/image'],
        ['', ''],
        ['分层定价模型（A 类）', ''],
        ['happy-horse/wan/wan-25-preview', '按 resolution 分层，base 取最低分辨率档 USD 单价'],
        ['luma ray v3.2', 'reframe/video-to-video 改用文档 per-source-second 价（API 为 compute seconds）'],
        ['pika v2.2', '按次计费，duration 不参与，仅 resolution exact_map'],
        ['pixverse c1/v6', 'resolution + audio_mode 双维度分层'],
        ['kling v3 pro/standard', 'audio_mode 三档（silent/generate/voice），无 resolution 分层'],
        ['veo3.1 系列', 'resolution + audio_mode 双维度分层，base 取 720p silent 价'],
        ['', ''],
        ['数据来源', 'FAL API https://api.fal.ai/v1/models/pricing'],
        ['生成时间', f'{__import__("datetime").datetime.now().isoformat()}'],
    ]
    for i, (key, value) in enumerate(notes, 1):
        ws3.cell(row=i, column=1, value=key).font = Font(bold=(i == 1 or key in ('汇率', '定价公式', '维度类型', '图片维度', '视频维度', '特殊模型', '数据来源')))
        ws3.cell(row=i, column=2, value=value)
    ws3.column_dimensions['A'].width = 25
    ws3.column_dimensions['B'].width = 80

    wb.save(str(output_path))


def main() -> None:
    records = generate_prices()

    priced = [r for r in records if r.get('base_price')]
    unpriced = [r for r in records if not r.get('base_price')]

    print(f'总计 {len(records)} 个模型')
    print(f'  已定价: {len(priced)}')
    print(f'  未定价: {len(unpriced)}')
    if unpriced:
        print('\n未定价模型:')
        for r in unpriced:
            print(f'  {r["model_id"]}')

    output_dir = Path(__file__).resolve().parent

    # 生成初始化脚本
    script_path = output_dir / 'seed_prices.py'
    generate_init_script(records, script_path)
    print(f'\n初始化脚本已生成: {script_path}')

    # 生成 Excel
    excel_path = output_dir / 'credit_prices.xlsx'
    generate_excel(records, excel_path)
    print(f'Excel 明细表已生成: {excel_path}')


if __name__ == '__main__':
    main()
