"""
积分定价初始化脚本 — 由 init_prices.py 自动生成。

共 285 条定价记录。
汇率：1 积分 = $0.001 (1000 积分 = $1 USD)
利润：在 FAL 成本基础上上浮 20%（用户售价 = 成本 × 1.2）

用法：
  cd backend
  WEBUI_SECRET_KEY=<key> PYTHONPATH=. python -m open_webui.extensions.credits.seed_prices
"""
from __future__ import annotations

import json
from time import time
from uuid import uuid4

from open_webui.extensions.credits.db import credit_session
from open_webui.extensions.credits.models import CreditPrice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


PRICES = [
  {
    "service_type": "video",
    "resource_id": "alibaba/happy-horse/video-edit",
    "action": "video-to-video",
    "base_price": "336",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bria/fibo-lite/generate",
    "action": "text-to-image",
    "base_price": "43.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bria/fibo/generate",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "bytedance/seedance-2.0/fast/image-to-video",
    "action": "image-to-video",
    "base_price": "13.44",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "bytedance/seedance-2.0/fast/text-to-video",
    "action": "text-to-video",
    "base_price": "13.44",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "bytedance/seedance-2.0/image-to-video",
    "action": "image-to-video",
    "base_price": "364.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2.248",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "bytedance/seedance-2.0/text-to-video",
    "action": "text-to-video",
    "base_price": "364.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2.248",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bytedance/seedream/v5/lite/edit",
    "action": "image-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bytedance/seedream/v5/lite/text-to-image",
    "action": "text-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bytedance/seedream/v5/pro/edit",
    "action": "image-to-image",
    "base_price": "81",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "bytedance/seedream/v5/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "81",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bitdance",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/boogu-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/boogu-image/edit",
    "action": "image-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bria/text-to-image/base",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bria/text-to-image/hd",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bytedance/seedream/v4.5/edit",
    "action": "image-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bytedance/seedream/v4.5/text-to-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bytedance/seedream/v4/edit",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/bytedance/seedream/v4/text-to-image",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/cogview4",
    "action": "text-to-image",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/dreamshaper",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/emu-3.5-image/edit-image",
    "action": "image-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/emu-3.5-image/text-to-image",
    "action": "text-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ernie-image",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ernie-image/turbo",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/dev",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/dev/image-to-image",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/krea",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/krea/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/schnell",
    "action": "text-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/srpo",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-1/srpo/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2",
    "action": "text-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-flex",
    "action": "text-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-flex/edit",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-max",
    "action": "text-to-image",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-max/edit",
    "action": "image-to-image",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-pro",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2-pro/edit",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/edit",
    "action": "image-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/flash",
    "action": "text-to-image",
    "base_price": "19.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/flash/edit",
    "action": "image-to-image",
    "base_price": "19.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/4b",
    "action": "text-to-image",
    "base_price": "10.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/4b/base",
    "action": "text-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/4b/base/edit",
    "action": "image-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/4b/edit",
    "action": "image-to-image",
    "base_price": "10.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/9b",
    "action": "text-to-image",
    "base_price": "13.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/9b/base",
    "action": "text-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/9b/base/edit",
    "action": "image-to-image",
    "base_price": "40.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/klein/9b/edit",
    "action": "image-to-image",
    "base_price": "13.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/turbo",
    "action": "text-to-image",
    "base_price": "9.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-2/turbo/edit",
    "action": "image-to-image",
    "base_price": "19.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/kontext",
    "action": "image-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/kontext/max",
    "action": "image-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/kontext/max/text-to-image",
    "action": "text-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/kontext/text-to-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/v1.1",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/v1.1-ultra",
    "action": "text-to-image",
    "base_price": "72",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux-pro/v1.1-ultra-finetuned",
    "action": "text-to-image",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/dev",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/dev/image-to-image",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/krea",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/krea/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/schnell",
    "action": "text-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/srpo",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/flux/srpo/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/glm-image",
    "action": "text-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/glm-image/image-to-image",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1-mini",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1-mini/edit",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1.5",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1.5/edit",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1/edit-image",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/gpt-image-1/text-to-image",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-i1-dev",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-i1-fast",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-i1-full",
    "action": "text-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-i1-full/image-to-image",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-o1-image",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-o1-image/dev",
    "action": "text-to-image",
    "base_price": "6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-o1-image/dev/edit",
    "action": "image-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hidream-o1-image/edit",
    "action": "image-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hunyuan-image/v2.1/text-to-image",
    "action": "text-to-image",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hunyuan-image/v3/instruct/edit",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hunyuan-image/v3/instruct/text-to-image",
    "action": "text-to-image",
    "base_price": "108",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/hunyuan-image/v3/text-to-image",
    "action": "text-to-image",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2",
    "action": "text-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2/edit",
    "action": "image-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2/turbo",
    "action": "text-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2/turbo/edit",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2a",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v2a/turbo",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v3",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ideogram/v3/edit",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/janus",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kling-image/o3/image-to-image",
    "action": "image-to-image",
    "base_price": "33.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kling-image/o3/text-to-image",
    "action": "text-to-image",
    "base_price": "33.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kling-image/v3/image-to-image",
    "action": "image-to-image",
    "base_price": "33.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kling-image/v3/text-to-image",
    "action": "text-to-image",
    "base_price": "33.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/o3/pro/video-to-video/edit",
    "action": "video-to-video",
    "base_price": "168",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/o3/standard/video-to-video/edit",
    "action": "video-to-video",
    "base_price": "168",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/pro/image-to-video",
    "action": "image-to-video",
    "base_price": "134.4",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "voice": "1.75",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/pro/text-to-video",
    "action": "text-to-video",
    "base_price": "134.4",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "voice": "1.75",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/standard/image-to-video",
    "action": "image-to-video",
    "base_price": "100.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "voice": "1.833",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/standard/text-to-video",
    "action": "text-to-video",
    "base_price": "100.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "voice": "1.833",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/turbo/pro/image-to-video",
    "action": "image-to-video",
    "base_price": "168",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/kling-video/v3/turbo/pro/text-to-video",
    "action": "text-to-video",
    "base_price": "168",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kolors",
    "action": "text-to-image",
    "base_price": "13.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/kolors/image-to-image",
    "action": "image-to-image",
    "base_price": "13.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/krea-2/turbo",
    "action": "text-to-image",
    "base_price": "9.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/longcat-image",
    "action": "text-to-image",
    "base_price": "156",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/longcat-image/edit",
    "action": "image-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/ltx-2.3/image-to-video",
    "action": "image-to-video",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/ltx-2.3/image-to-video/fast",
    "action": "image-to-video",
    "base_price": "72",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/ltx-2.3/retake-video",
    "action": "video-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/ltx-2.3/text-to-video",
    "action": "text-to-video",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/ltx-2.3/text-to-video/fast",
    "action": "text-to-video",
    "base_price": "72",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/luma-photon",
    "action": "text-to-image",
    "base_price": "22.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/luma-photon/flash",
    "action": "text-to-image",
    "base_price": "6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/luma-photon/flash/modify",
    "action": "image-to-image",
    "base_price": "6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/luma-photon/modify",
    "action": "image-to-image",
    "base_price": "22.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-02-fast/image-to-video",
    "action": "image-to-video",
    "base_price": "20.4",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-02/pro/image-to-video",
    "action": "image-to-video",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-02/pro/text-to-video",
    "action": "text-to-video",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-02/standard/image-to-video",
    "action": "image-to-video",
    "base_price": "54",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-02/standard/text-to-video",
    "action": "text-to-video",
    "base_price": "54",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3-fast/pro/image-to-video",
    "action": "image-to-video",
    "base_price": "396",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3-fast/standard/image-to-video",
    "action": "image-to-video",
    "base_price": "228",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3/pro/image-to-video",
    "action": "image-to-video",
    "base_price": "588",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3/pro/text-to-video",
    "action": "text-to-video",
    "base_price": "588",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3/standard/image-to-video",
    "action": "image-to-video",
    "base_price": "336",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/minimax/hailuo-2.3/standard/text-to-video",
    "action": "text-to-video",
    "base_price": "336",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/minimax/image-01",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana",
    "action": "text-to-image",
    "base_price": "47.76",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana-2",
    "action": "text-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana-2/edit",
    "action": "image-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana-pro",
    "action": "text-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana-pro/edit",
    "action": "image-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nano-banana/edit",
    "action": "image-to-image",
    "base_price": "47.76",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/nucleus-image",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/omnigen-v1",
    "action": "text-to-image",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/omnigen-v2",
    "action": "text-to-image",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/ovis-image",
    "action": "text-to-image",
    "base_price": "14.4",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/patina",
    "action": "image-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/patina/material",
    "action": "text-to-image",
    "base_price": "1.68",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/phota",
    "action": "text-to-image",
    "base_price": "108",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "1K": "1",
            "4K": "2",
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/phota/edit",
    "action": "image-to-image",
    "base_price": "108",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "size",
          "kind": "exact_map",
          "values": {
            "1K": "1",
            "4K": "2",
            "default": "1"
          }
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.1/image-to-video",
    "action": "image-to-video",
    "base_price": "480",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.1/text-to-video",
    "action": "text-to-video",
    "base_price": "480",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.2/image-to-video",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2.25",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.2/pikaframes",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.2/pikascenes",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2.25",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2.2/text-to-video",
    "action": "text-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "2.25",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2/turbo/image-to-video",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pika/v2/turbo/text-to-video",
    "action": "text-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/c1/image-to-video",
    "action": "image-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.333",
            "720p": "1.667",
            "1080p": "3.167",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.333",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/c1/reference-to-video",
    "action": "image-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.333",
            "720p": "1.667",
            "1080p": "3.167",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.333",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/c1/text-to-video",
    "action": "text-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.333",
            "720p": "1.667",
            "1080p": "3.167",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.333",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/c1/transition",
    "action": "image-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.333",
            "720p": "1.667",
            "1080p": "3.167",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.333",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/v6/extend",
    "action": "video-to-video",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.4",
            "720p": "1.8",
            "1080p": "3.6",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.4",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/v6/image-to-video",
    "action": "image-to-video",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.4",
            "720p": "1.8",
            "1080p": "3.6",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.4",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/v6/text-to-video",
    "action": "text-to-video",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.4",
            "720p": "1.8",
            "1080p": "3.6",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.4",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/pixverse/v6/transition",
    "action": "image-to-video",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "360p": "1",
            "540p": "1.4",
            "720p": "1.8",
            "1080p": "3.6",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.4",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image",
    "action": "text-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-2/edit",
    "action": "image-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-2/pro/edit",
    "action": "image-to-image",
    "base_price": "90",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-2/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "90",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-2/text-to-image",
    "action": "text-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-2512",
    "action": "text-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-max/edit",
    "action": "image-to-image",
    "base_price": "90",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image-max/text-to-image",
    "action": "text-to-image",
    "base_price": "90",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/qwen-image/image-to-image",
    "action": "image-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v2/text-to-image",
    "action": "text-to-image",
    "base_price": "26.28",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v3/image-to-image",
    "action": "image-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v3/text-to-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "252",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/pro/text-to-vector",
    "action": "text-to-image",
    "base_price": "360",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/text-to-image",
    "action": "text-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/text-to-vector",
    "action": "text-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/utility/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "252",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4.1/utility/text-to-image",
    "action": "text-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "300",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4/pro/text-to-vector",
    "action": "text-to-image",
    "base_price": "360",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4/text-to-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/recraft/v4/text-to-vector",
    "action": "text-to-image",
    "base_price": "96",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/sana",
    "action": "text-to-image",
    "base_price": "1.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/sana/sprint",
    "action": "text-to-image",
    "base_price": "3",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/sana/v1.5/1.6b",
    "action": "text-to-image",
    "base_price": "9",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/sana/v1.5/4.8b",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-cascade",
    "action": "text-to-image",
    "base_price": "13.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-cascade/sote-diffusion",
    "action": "text-to-image",
    "base_price": "13.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-diffusion-v15",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-diffusion-v3-medium",
    "action": "text-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-diffusion-v3-medium/image-to-image",
    "action": "image-to-image",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-diffusion-v35-large",
    "action": "text-to-image",
    "base_price": "78",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/stable-diffusion-v35-medium",
    "action": "text-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1",
    "action": "text-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "2",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/extend-video",
    "action": "video-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/fast",
    "action": "text-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "3",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/fast/extend-video",
    "action": "video-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/fast/first-last-frame-to-video",
    "action": "image-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "3",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/fast/image-to-video",
    "action": "image-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "3",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/fast/reference-to-video",
    "action": "image-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/first-last-frame-to-video",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "2",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/image-to-video",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "2",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/lite",
    "action": "text-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.67",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.67",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/lite/first-last-frame-to-video",
    "action": "image-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.67",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.67",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/lite/image-to-video",
    "action": "image-to-video",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.67",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "1.67",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/veo3.1/reference-to-video",
    "action": "image-to-video",
    "base_price": "240",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1",
            "4k": "2",
            "default": "1"
          }
        },
        {
          "key": "audio_mode",
          "kind": "exact_map",
          "values": {
            "silent": "1",
            "generate": "2",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/image-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q1/image-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q1/reference-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q1/start-end-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q1/text-to-video",
    "action": "text-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q2/image-to-video/pro",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q2/image-to-video/turbo",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q2/reference-to-video/pro",
    "action": "image-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q2/text-to-video",
    "action": "text-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q2/video-extension/pro",
    "action": "video-to-video",
    "base_price": "90",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q3/image-to-video",
    "action": "image-to-video",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q3/image-to-video/turbo",
    "action": "image-to-video",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q3/reference-to-video/mix",
    "action": "image-to-video",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q3/text-to-video",
    "action": "text-to-video",
    "base_price": "84",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/q3/text-to-video/turbo",
    "action": "text-to-video",
    "base_price": "42",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/reference-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/start-end-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/vidu/template-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan-25-preview/image-to-image",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/wan-25-preview/image-to-video",
    "action": "image-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "480p": "1",
            "720p": "2",
            "1080p": "3",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/wan-25-preview/text-to-video",
    "action": "text-to-video",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "480p": "1",
            "720p": "2",
            "1080p": "3",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan-v2.5/text-to-image",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.2-5b/text-to-image",
    "action": "text-to-image",
    "base_price": "19.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.2-a14b/image-to-image",
    "action": "image-to-image",
    "base_price": "60",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.2-a14b/text-to-image",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.7/edit",
    "action": "image-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/wan/v2.7/edit-video",
    "action": "video-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/wan/v2.7/image-to-video",
    "action": "image-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.7/pro/edit",
    "action": "image-to-image",
    "base_price": "4.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.7/pro/text-to-image",
    "action": "text-to-image",
    "base_price": "4.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/wan/v2.7/text-to-image",
    "action": "text-to-image",
    "base_price": "36",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "fal-ai/wan/v2.7/text-to-video",
    "action": "text-to-video",
    "base_price": "120",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "720p": "1",
            "1080p": "1.5",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/z-image/base",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/z-image/turbo",
    "action": "text-to-image",
    "base_price": "6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "fal-ai/z-image/turbo/image-to-image",
    "action": "image-to-image",
    "base_price": "6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "google/gemini-omni-flash",
    "action": "text-to-video",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "google/gemini-omni-flash/edit",
    "action": "video-to-video",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "google/gemini-omni-flash/image-to-video",
    "action": "image-to-video",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "video",
    "resource_id": "google/gemini-omni-flash/reference-to-video",
    "action": "image-to-video",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": []
    }
  },
  {
    "service_type": "image",
    "resource_id": "google/nano-banana-2-lite",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "google/nano-banana-lite",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "google/nano-banana-lite/edit",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "ideogram/v4",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "ideogram/v4/fast",
    "action": "text-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "ideogram/v4/image-to-image",
    "action": "image-to-image",
    "base_price": "12",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "ideogram/v4/instant",
    "action": "text-to-image",
    "base_price": "0.084",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "pixel_count",
          "kind": "proportional",
          "unit_size": "1000000"
        },
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "krea/v2/large/text-to-image",
    "action": "text-to-image",
    "base_price": "1.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "krea/v2/medium/text-to-image",
    "action": "text-to-image",
    "base_price": "1.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "krea/v2/medium/turbo/text-to-image",
    "action": "text-to-image",
    "base_price": "1.2",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "luma/agent/ray/v3.2/image-to-video",
    "action": "image-to-video",
    "base_price": "180",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "unit_blocks",
          "block_size": "5",
          "multiplier_per_block": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "540p": "1",
            "720p": "2",
            "1080p": "8",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "luma/agent/ray/v3.2/reframe",
    "action": "video-to-video",
    "base_price": "72",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "540p": "1",
            "720p": "2",
            "1080p": "6",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "luma/agent/ray/v3.2/text-to-video",
    "action": "text-to-video",
    "base_price": "600",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "unit_blocks",
          "block_size": "5",
          "multiplier_per_block": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "540p": "1",
            "720p": "2",
            "1080p": "4",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "video",
    "resource_id": "luma/agent/ray/v3.2/video-to-video",
    "action": "video-to-video",
    "base_price": "172.8",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "duration",
          "kind": "proportional",
          "unit_size": "1"
        },
        {
          "key": "resolution",
          "kind": "exact_map",
          "values": {
            "540p": "1",
            "720p": "1.5",
            "1080p": "3",
            "default": "1"
          }
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "luma/agent/uni-1/v1/edit",
    "action": "image-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "luma/agent/uni-1/v1/max",
    "action": "text-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "luma/agent/uni-1/v1/max/edit",
    "action": "image-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "luma/agent/uni-1/v1/text-to-image",
    "action": "text-to-image",
    "base_price": "3.6",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "microsoft/mai-image-2.5",
    "action": "text-to-image",
    "base_price": "1.68",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "microsoft/mai-image-2.5/edit",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "nvidia/cosmos-3-super/text-to-image",
    "action": "text-to-image",
    "base_price": "48",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "openai/gpt-image-2",
    "action": "text-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "openai/gpt-image-2/edit",
    "action": "image-to-image",
    "base_price": "1200",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "reve/2.1/edit",
    "action": "image-to-image",
    "base_price": "300",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "reve/2.1/text-to-image",
    "action": "text-to-image",
    "base_price": "300",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "rundiffusion-fal/juggernaut-flux/base",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "rundiffusion-fal/juggernaut-flux/base/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "rundiffusion-fal/juggernaut-flux/lightning",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "rundiffusion-fal/juggernaut-flux/pro",
    "action": "text-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "rundiffusion-fal/juggernaut-flux/pro/image-to-image",
    "action": "image-to-image",
    "base_price": "30",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "wan/v2.6/image-to-image",
    "action": "image-to-image",
    "base_price": "1.68",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "wan/v2.6/text-to-image",
    "action": "text-to-image",
    "base_price": "1.68",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "xai/grok-imagine-image",
    "action": "text-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "xai/grok-imagine-image/edit",
    "action": "image-to-image",
    "base_price": "24",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "xai/grok-imagine-image/quality/edit",
    "action": "image-to-image",
    "base_price": "4.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  },
  {
    "service_type": "image",
    "resource_id": "xai/grok-imagine-image/quality/text-to-image",
    "action": "text-to-image",
    "base_price": "4.08",
    "rules": {
      "schema_version": 1,
      "dimensions": [
        {
          "key": "image_count",
          "kind": "quantity"
        }
      ]
    }
  }
]


async def seed_prices() -> None:
    """插入或更新所有定价记录。已存在的 (service_type, resource_id, action) 会被更新。"""
    now = int(time())
    async with credit_session() as session:
        # 查询已存在的定价
        existing = (
            await session.scalars(
                select(CreditPrice).where(CreditPrice.service_type.in_(['image', 'video']))
            )
        ).all()
        existing_map = {(r.service_type, r.resource_id, r.action): r for r in existing}

        for item in PRICES:
            key = (item['service_type'], item['resource_id'], item['action'])
            row = existing_map.get(key)
            if row is None:
                session.add(CreditPrice(
                    id=uuid4().hex,
                    service_type=item['service_type'],
                    resource_id=item['resource_id'],
                    action=item['action'],
                    base_price=item['base_price'],
                    rules=item['rules'],
                    enabled=True,
                    updated_by_id='system',
                    updated_by_name_snapshot='System',
                    created_at=now,
                    updated_at=now,
                ))
            else:
                row.base_price = item['base_price']
                row.rules = item['rules']
                row.enabled = True
                row.updated_by_id = 'system'
                row.updated_by_name_snapshot = 'System'
                row.updated_at = now
        await session.commit()
        print(f'Seeded {len(PRICES)} credit prices')


if __name__ == '__main__':
    import asyncio
    asyncio.run(seed_prices())
