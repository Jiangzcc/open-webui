# fal.ai 图片模型厂商接口对比

> 仅基于本仓库 `docs/fal/**/*.md` 整理，未引入外部网页资料。  
> 覆盖目录：`alibaba`、`google`、`openai`、`xai`。  
> 共计 22 个接口文档：Alibaba 1 个、Google 9 个、OpenAI 8 个、xAI 4 个。

## 1. 全局一致点与差异点

| 维度 | 一致点 | 主要差异 |
|---|---|---|
| 调用方式 | 基本都是 `POST https://fal.run/<model-id>`，JSON 请求体，`Authorization: Key $FAL_KEY` | model id 命名空间不统一：Google 有 `fal-ai/...` 也有 `google/...`；OpenAI 目录也混有 `openai/...` 和 `fal-ai/...` |
| 核心输入 | `prompt` 基本全接口必填 | 编辑接口才有 `image_urls`；Alibaba 目录目前只有文生图，没有编辑接口 |
| 输出数量 | 大多数接口 `num_images` 默认 `1`、范围 `1..4` | Alibaba、Google、OpenAI、xAI 都基本一致 |
| 输出格式 | 基本都支持 `jpeg/png/webp` | 默认值不同：Google/OpenAI/Alibaba 多为 `png`，xAI 默认 `jpeg` |
| 同步模式 | 多数都有 `sync_mode=false`；`true` 时返回 data URI，且结果不进 request history | 各文档描述一致，但响应 schema 没有单独展开 data URI 模式 |
| 尺寸/比例 | 都能控制图像尺寸或比例 | Alibaba 用 `image_size`；Google 用 `aspect_ratio` + 部分接口 `resolution`；OpenAI 用 `image_size`；xAI 用 `aspect_ratio` + `resolution` |
| 可复现性 | 部分支持 `seed` | 只有 Alibaba、Google 文档里有 `seed`；OpenAI、xAI 未见 |
| 扩散控制 | 大多不暴露底层扩散参数 | `steps` 只在 Alibaba 的 Z Image Turbo 里出现；全目录未见 `guidance/CFG`、`negative_prompt` |
| 安全控制 | 有些接口暴露安全参数 | Alibaba 有 `enable_safety_checker` 和 `has_nsfw_concepts`；Google 有 `safety_tolerance`；OpenAI/xAI 文档未见显式 safety 参数 |
| 计费 | 所有 22 个文档都见到价格信息 | 差异最大：有按百万像素、按张、按 token、按输入图、按分辨率倍率、按附加能力收费等 |

## 2. 厂商接口与价格总表

### 2.1 Alibaba

来源目录：`docs/fal/alibaba/`

| 接口 | 用途 | Endpoint / Model ID | 必填参数 | 关键可选参数 | 响应字段 | 价格 | 差异点 |
|---|---|---|---|---|---|---|---|
| Z Image Turbo | 文生图 | `https://fal.run/fal-ai/z-image/turbo` / `fal-ai/z-image/turbo` | `prompt` | `image_size`、`num_inference_steps`、`seed`、`sync_mode`、`num_images`、`enable_safety_checker`、`output_format`、`acceleration`、`enable_prompt_expansion` | `images`、`timings`、`seed`、`has_nsfw_concepts`、`prompt` | **$0.005 / megapixel**；开启 `enable_prompt_expansion` 额外 **0.0025 credits/request** | 唯一按“百万像素”计费；唯一明确暴露 `num_inference_steps`，范围 `1..8`；无编辑接口 |

来源文件：

- `docs/fal/alibaba/z-image/fal-ai@z-image@turbo.md`

### 2.2 Google

来源目录：`docs/fal/google/`

| 接口 | 用途 | Endpoint / Model ID | 必填参数 | 关键可选参数 | 响应字段 | 价格 | 差异点 |
|---|---|---|---|---|---|---|---|
| Nano Banana | 文生图 | `https://fal.run/fal-ai/nano-banana` / `fal-ai/nano-banana` | `prompt` | `num_images`、`seed`、`aspect_ratio`、`output_format`、`safety_tolerance`、`sync_mode`、`limit_generations` | `images`、`description` | **$0.039 / image**；约 `$1 = 25` 次 | 基础版，参数较少；无 `system_prompt`、`resolution`、`web_search`、`thinking_level` |
| Nano Banana Edit | 图像编辑 | `https://fal.run/fal-ai/nano-banana/edit` / `fal-ai/nano-banana/edit` | `prompt`、`image_urls` | 同上；`aspect_ratio` 默认 `auto` | `images`、`description` | **$0.039 / image** | 基础编辑版，`image_urls` 必填 |
| Nano Banana Pro | 文生图 | `https://fal.run/fal-ai/nano-banana-pro` / `fal-ai/nano-banana-pro` | `prompt` | `system_prompt`、`resolution`、`enable_web_search`、其它通用参数 | `images`、`description` | **$0.15 / image**；`4K` 按 **2x**；`web_search` 额外 **+$0.015** | 支持 `1K/2K/4K`，强调写实和文字排版 |
| Nano Banana Pro Edit | 图像编辑 | `https://fal.run/fal-ai/nano-banana-pro/edit` / `fal-ai/nano-banana-pro/edit` | `prompt`、`image_urls` | `system_prompt`、`resolution`、`enable_web_search`、其它通用参数 | `images`、`description` | **$0.15 / image**；`4K` **2x**；`web_search` **+$0.015** | Pro 编辑版，`image_urls` 必填 |
| Nano Banana 2 | 文生图 | `https://fal.run/fal-ai/nano-banana-2` / `fal-ai/nano-banana-2` | `prompt` | `system_prompt`、`resolution`、`enable_web_search`、`thinking_level`、其它通用参数 | `images`、`description` | **$0.08 / image**；`0.5K` **0.75x**；`2K` **1.5x**；`4K` **2x**；`web_search` **+$0.015**；`thinking_level=high` **+$0.002** | 功能更全，支持极端比例和 thinking |
| Nano Banana 2 Edit | 图像/多模态编辑 | `https://fal.run/fal-ai/nano-banana-2/edit` / `fal-ai/nano-banana-2/edit` | `prompt` | `image_urls`、`video_url`、`audio_url`、`pdf_url`、`system_prompt`、`resolution`、`enable_web_search`、`thinking_level` | `images`、`description` | 同 Nano Banana 2 | 最特殊：可接视频、音频、PDF 上下文；`image_urls` 可不是唯一输入 |
| Nano Banana Lite | 文生图 | `https://fal.run/google/nano-banana-lite` / `google/nano-banana-lite` | `prompt` | `system_prompt`、`aspect_ratio`、`num_images`、`seed`、`safety_tolerance`、`thinking_level` | `images`、`description` | 文本输入 **$0.3125/1M tokens**；文本输出 **$1.875/1M tokens**；图像输入 **$0.3125/1M tokens**；图像输出 **$37.50/1M tokens** | Lite 路线，token 计费；文档称输出固定 `1K (1024x1024px)` |
| Nano Banana Lite Edit | 图像编辑 | `https://fal.run/google/nano-banana-lite/edit` / `google/nano-banana-lite/edit` | `prompt` | `image_urls` 可选、`system_prompt`、`aspect_ratio`、`thinking_level` 等 | `images`、`description` | 同 Lite token 计费 | `image_urls` 在文档中是可选，不像基础/Pro edit 那样必填 |
| Nano Banana 2 Lite | 文生图 | `https://fal.run/google/nano-banana-2-lite` / `google/nano-banana-2-lite` | `prompt` | `system_prompt`、`aspect_ratio`、`num_images`、`seed`、`safety_tolerance`、`thinking_level` | `images`、`description` | 同 Lite token 计费 | 目录中只见文生图文档，未见 edit 文档 |

来源文件：

- `docs/fal/google/nano-banana/nano-banana.md`
- `docs/fal/google/nano-banana/nano-banana@edit.md`
- `docs/fal/google/nano-banana-pro/nano-banana-pro.md`
- `docs/fal/google/nano-banana-pro/nano-banana-pro@edit.md`
- `docs/fal/google/nano-banana-2/nano-banana-2.md`
- `docs/fal/google/nano-banana-2/nano-banana-2@edit.md`
- `docs/fal/google/nano-banana-lite/nano-banana-lite.md`
- `docs/fal/google/nano-banana-lite/nano-banana-lite@edit.md`
- `docs/fal/google/nano-banana-lite/nano-banana-2-lite.md`

### 2.3 OpenAI

来源目录：`docs/fal/openai/`

| 接口 | 用途 | Endpoint / Model ID | 必填参数 | 关键可选参数 | 响应字段 | 价格 | 差异点 |
|---|---|---|---|---|---|---|---|
| GPT Image 2 | 文生图 | `https://fal.run/openai/gpt-image-2` / `openai/gpt-image-2` | `prompt` | `image_size`、`quality`、`num_images`、`output_format`、`sync_mode` | `images` | 文本 token：输入 **$5/1M**、缓存 **$1.25/1M**、输出 **$10/1M**；图像 token：输入 **$8/1M**、缓存 **$2/1M**、输出 **$30/1M** | token 计费；`image_size` 最灵活，可 preset、显式宽高或 `auto` |
| GPT Image 2 Edit | 图像编辑 | `https://fal.run/openai/gpt-image-2/edit` / `openai/gpt-image-2/edit` | `prompt`、`image_urls` | `image_size`、`quality`、`num_images`、`output_format`、`sync_mode`、`mask_url` | `images` | 同 GPT Image 2 token 计费 | 支持 `mask_url` 蒙版编辑 |
| GPT-Image 1.5 | 文生图 | `https://fal.run/fal-ai/gpt-image-1.5` / `fal-ai/gpt-image-1.5` | `prompt` | `image_size`、`background`、`quality`、`num_images`、`output_format`、`sync_mode` | `images` | 文本输入 **$0.005/1K tokens**；文本输出 **$0.010/1K tokens**；输出图按质量/尺寸收费，见下表 | 有 reasoning/output text token 成本 |
| GPT-Image 1.5 Edit | 图像编辑 | `https://fal.run/fal-ai/gpt-image-1.5/edit` / `fal-ai/gpt-image-1.5/edit` | `prompt`、`image_urls` | `image_size`、`background`、`quality`、`input_fidelity`、`mask_image_url` 等 | `images` | 文本同 1.5；输入图 **$0.008/1K image tokens**；1024² 图约 `135` tokens low fidelity 或 `3050` tokens high fidelity；输出图同 1.5 | 支持 `input_fidelity` 和 `mask_image_url` |
| GPT Image 1 Mini | 文生图 | `https://fal.run/fal-ai/gpt-image-1-mini` / `fal-ai/gpt-image-1-mini` | `prompt` | `image_size`、`background`、`quality`、`num_images`、`output_format`、`sync_mode` | `images` | 文本输入 **$0.002/1K tokens**；输出图按质量/尺寸收费，见下表；总价向上取整到最近 1 美分 | 低价 mini 版 |
| GPT Image 1 Mini Edit | 图像编辑 | `https://fal.run/fal-ai/gpt-image-1-mini/edit` / `fal-ai/gpt-image-1-mini/edit` | `prompt`、`image_urls` | `image_size`、`background`、`quality`、`num_images`、`output_format`、`sync_mode` | `images` | 文本输入 **$0.002/1K tokens**；输入图 **$0.0025/1K image tokens**；1024² 图约 `135` tokens；输出图同 Mini | 编辑版无 mask 字段 |
| gpt-image-1 text-to-image | 文生图 | `https://fal.run/fal-ai/gpt-image-1/text-to-image` / `fal-ai/gpt-image-1/text-to-image` | `prompt` | `image_size`、`background`、`quality`、`num_images`、`output_format`、`sync_mode` | `images` | 文本输入 **$0.002/1K tokens**；输出图按质量/尺寸收费，见下表；总价向上取整到最近 1 美分 | 基础 GPT Image 1 文生图 |
| gpt-image-1 edit-image | 图像编辑 | `https://fal.run/fal-ai/gpt-image-1/edit-image` / `fal-ai/gpt-image-1/edit-image` | `prompt`、`image_urls` | `image_size`、`background`、`quality`、`input_fidelity`、`num_images`、`output_format`、`sync_mode` | `images` | 文本输入 **$0.002/1K tokens**；输入图 **$0.005/1K image tokens**；1024² 图约 `135` tokens low fidelity 或 `3050` tokens high fidelity；输出图同 gpt-image-1 | 路径是 `edit-image`，不是常见的 `/edit` |

OpenAI 目录下几个按输出图质量/尺寸计费的明细：

| 模型族 | Quality | `1024x1024` | `1024x1536` | `1536x1024` / 其它同类尺寸 |
|---|---:|---:|---:|---:|
| GPT-Image 1.5 | low | `$0.009` | `$0.013` | `$0.013` |
| GPT-Image 1.5 | medium | `$0.034` | `$0.051` | `$0.050` |
| GPT-Image 1.5 | high | `$0.133` | `$0.200` | `$0.199` |
| GPT Image 1 Mini | low | `$0.005` | `$0.006` | `$0.006` |
| GPT Image 1 Mini | medium | `$0.011` | `$0.015` | `$0.015` |
| GPT Image 1 Mini | high | `$0.036` | `$0.052` | `$0.052` |
| gpt-image-1 | low | `$0.011` | `$0.016` | `$0.016` |
| gpt-image-1 | medium | `$0.042` | `$0.063` | `$0.063` |
| gpt-image-1 | high | `$0.167` | `$0.25` | `$0.25` |

来源文件：

- `docs/fal/openai/gpt-image-2/gpt-image-2.md`
- `docs/fal/openai/gpt-image-2/gpt-image-2@edit.md`
- `docs/fal/openai/gpt-image-1.5/gpt-image-1.5.md`
- `docs/fal/openai/gpt-image-1.5/gpt-image-1.5@edit.md`
- `docs/fal/openai/gpt-image-1/gpt-image-1-mini.md`
- `docs/fal/openai/gpt-image-1/gpt-image-1-mini@edit.md`
- `docs/fal/openai/gpt-image-1/gpt-image-1@text-to-image.md`
- `docs/fal/openai/gpt-image-1/gpt-image-1@edit-image.md`

### 2.4 xAI

来源目录：`docs/fal/xai/`

| 接口 | 用途 | Endpoint / Model ID | 必填参数 | 关键可选参数 | 响应字段 | 价格 | 差异点 |
|---|---|---|---|---|---|---|---|
| Grok Imagine Image | 文生图 | `https://fal.run/xai/grok-imagine-image` / `xai/grok-imagine-image` | `prompt` | `num_images`、`aspect_ratio`、`resolution`、`output_format`、`sync_mode` | `images`、`revised_prompt?` | **$0.02 / image** | 标准版，参数克制 |
| Grok Imagine Image Edit | 图像编辑 | `https://fal.run/xai/grok-imagine-image/edit` / `xai/grok-imagine-image/edit` | `prompt`；`image_urls` 文档标为可选但编辑语义上通常需要 | `image_urls` 最多 3 张、其它通用参数 | `images`、`revised_prompt?` | **$0.022 / image**，其中 `$0.02` 输出图 + `$0.002` 输入图 | 编辑输入最多 3 张 URL；无 mask |
| Grok Imagine Pro / Quality Text-to-Image | 高质量文生图 | `https://fal.run/xai/grok-imagine-image/quality/text-to-image` / `xai/grok-imagine-image/quality/text-to-image` | `prompt` | 同标准文生图 | `images`、`revised_prompt?` | `1K`: **$0.05 / image**；`2K`: **$0.07 / image** | Pro/quality 版，按分辨率阶梯收费 |
| Grok Imagine Pro / Quality Edit | 高质量图像编辑 | `https://fal.run/xai/grok-imagine-image/quality/edit` / `xai/grok-imagine-image/quality/edit` | `prompt`；`image_urls` 文档标为可选 | `image_urls` 最多 3 张、其它通用参数 | `images`、`revised_prompt?` | `1K`: **$0.05 / output image + $0.01 / input image**；`2K`: **$0.07 / output image + $0.01 / input image** | 同时按输出图和输入图计费 |

来源文件：

- `docs/fal/xai/grok-imagine/grok-imagine-image.md`
- `docs/fal/xai/grok-imagine/grok-imagine-image@edit.md`
- `docs/fal/xai/grok-imagine/grok-imagine-image@quality@text-to-image.md`
- `docs/fal/xai/grok-imagine/grok-imagine-image@quality@edit.md`

## 3. 参数能力矩阵

| 参数/能力 | Alibaba | Google | OpenAI | xAI |
|---|---|---|---|---|
| `prompt` | 有，必填 | 有，必填 | 有，必填 | 有，必填 |
| 输入图 | 未见 | 编辑接口用 `image_urls`；部分必填，部分可选 | 编辑接口用 `image_urls`，必填 | 编辑接口用 `image_urls`，最多 3 张；文档标 optional |
| 文生图 | 有 | 有 | 有 | 有 |
| 图像编辑 | 未见 | 有 | 有 | 有 |
| 多图参考 | 未见 | 有，编辑接口 | 有，编辑接口 | 有，最多 3 张 |
| 视频/音频/PDF 上下文 | 未见 | 仅 `nano-banana-2/edit` 有 `video_url`、`audio_url`、`pdf_url` | 未见 | 未见 |
| 尺寸/比例字段 | `image_size` | `aspect_ratio`，部分接口有 `resolution` | `image_size` | `aspect_ratio` + `resolution` |
| `num_images` | 有，`1..4` | 有，`1..4` | 有，`1..4` | 有，`1..4` |
| `seed` | 有 | 有 | 未见 | 未见 |
| `steps` | 有，`num_inference_steps`，`1..8` | 未见 | 未见 | 未见 |
| `guidance/CFG` | 未见 | 未见 | 未见 | 未见 |
| `negative_prompt` | 未见 | 未见 | 未见 | 未见 |
| 安全控制 | `enable_safety_checker` | `safety_tolerance`，`1..6` | 未见 | 未见 |
| 安全结果 | `has_nsfw_concepts` | 未见专门字段 | 未见 | 未见 |
| 输出格式 | `jpeg/png/webp` | `jpeg/png/webp` | `jpeg/png/webp` | `jpeg/png/webp` |
| `sync_mode` | 有 | 有 | 有 | 有 |
| Web search | 未见 | Pro / Nano Banana 2 有 `enable_web_search` | 未见 | 未见 |
| Thinking/reasoning | 未见 | Nano Banana 2 / Lite 有 `thinking_level` | 1.5 价格说明里有 output text/reasoning token，但无 `thinking_level` 参数 | 未见 |
| `system_prompt` | 未见 | Pro / Nano Banana 2 / Lite 系列有 | 未见 | 未见 |
| 蒙版编辑 | 未见 | 未见 | GPT Image 2 Edit 有 `mask_url`；GPT-Image 1.5 Edit 有 `mask_image_url` | 未见 |
| 背景/透明背景 | 未见 | 未见 | 1.5 / 1 Mini / gpt-image-1 有 `background=auto/transparent/opaque` | 未见 |
| 输入保真度 | 未见 | 未见 | 1.5 Edit / gpt-image-1 Edit 有 `input_fidelity=low/high` | 未见 |
| Prompt 扩展 | `enable_prompt_expansion`，额外收费 | 未见同名参数 | 未见 | `revised_prompt` 输出提示词改写结果，但请求无同名开关 |

## 4. 响应结构对比

| 厂商 | 顶层响应字段 | `images[]` 子字段 | 特殊字段 | 注意点 |
|---|---|---|---|---|
| Alibaba | `images`、`timings`、`seed`、`has_nsfw_concepts`、`prompt` | 示例含 `url`、`height`、`width`、`content_type` | `has_nsfw_concepts`、`seed`、`timings` | schema 说这些字段必填，但示例响应没完整展示 |
| Google | `images`、`description` | 示例含 `file_name`、`url`、`content_type` | `description` | 统一性最好，9 个接口输出基本一致 |
| OpenAI | `images` | 示例含 `url`、`file_name`、`content_type`、`width`、`height` | 无顶层 `description`/`seed` | SDK 示例可能有 `requestId`，但输出 schema 未列为 API 响应字段 |
| xAI | `images`、`revised_prompt?` | 示例主要展示 `url` | `revised_prompt` | 可拿到被模型改写后的 prompt，方便审计/复现 |

## 5. 价格模型横向对比

| 价格模型 | 对应厂商/接口 | 价格表达 | 适合怎么理解 |
|---|---|---|---|
| 按百万像素 | Alibaba Z Image Turbo | `$0.005 / megapixel` | 分辨率越高越贵；1MP 左右大约 `$0.005` 级别，但要按实际像素算 |
| 固定按张 | Google Nano Banana、xAI 标准版 | Google 基础 `$0.039/image`；xAI 标准 `$0.02/image` | 最容易预算，生成几张乘几张 |
| 按分辨率倍率 | Google Pro / Nano Banana 2、xAI quality | Google Pro `$0.15/image` 且 4K `2x`；Nano Banana 2 `$0.08/image`，0.5K/2K/4K 有倍率；xAI quality 1K/2K 不同单价 | 输出分辨率是成本关键 |
| 按 token | Google Lite、OpenAI GPT Image 2 | Google Lite 文本/图像 token 分别计费；OpenAI GPT Image 2 文本 token + 图像 token + cached token | 需要结合 prompt、输入图、输出图 token 量估算，不适合直接按张比较 |
| 混合：文本 token + 输出图价格 | OpenAI 1.5 / 1 Mini / gpt-image-1 | 文本输入 token 另算，输出图按质量和尺寸收费 | 既要看 prompt token，也要看 `quality` 和 `image_size` |
| 输入图额外收费 | OpenAI 编辑、xAI 编辑 | OpenAI 按 image tokens；xAI 标准编辑 `$0.002/input image`，quality 编辑 `$0.01/input image` | 编辑接口预算要同时算输入图和输出图 |
| 附加能力额外收费 | Alibaba、Google | Alibaba prompt expansion `+0.0025 credits/request`；Google web search `+$0.015`；Nano Banana 2 high thinking `+$0.002` | 功能开关会改变成本，不能只看基础单价 |

## 6. 关键差异总结

| 主题 | 最明显的差异 |
|---|---|
| 最轻量的参数体系 | xAI：基本就是 `prompt`、`num_images`、`aspect_ratio`、`resolution`、`output_format`、`sync_mode`，编辑再加 `image_urls` |
| 最多高级能力 | Google Nano Banana 2 Edit：支持图像、视频、音频、PDF，上下文输入最丰富 |
| 最接近传统扩散参数 | Alibaba Z Image Turbo：有 `num_inference_steps`、`seed`、安全检查、加速档位 |
| 最复杂的计费 | OpenAI：尤其 GPT Image 2 token 计费，以及 1.5/1/mini 的 token + 输出图质量/尺寸组合 |
| 最明确的安全参数 | Google 和 Alibaba：Google 用 `safety_tolerance`，Alibaba 用 `enable_safety_checker` 并返回 `has_nsfw_concepts` |
| 最明确的蒙版编辑 | OpenAI：GPT Image 2 Edit 的 `mask_url`，GPT-Image 1.5 Edit 的 `mask_image_url` |
| 最适合统一抽象的响应 | 所有厂商都可以抽象成 `images[]`；但附加字段要保留 vendor-specific metadata |
| 最需要注意的字段命名差异 | `size` 概念在不同厂商分别叫 `image_size`、`aspect_ratio`、`resolution`；OpenAI 的 mask 字段还有 `mask_url` / `mask_image_url` 两种 |

## 7. 建议的统一适配层字段

| 统一字段 | Alibaba | Google | OpenAI | xAI |
|---|---|---|---|---|
| `provider` | `alibaba` | `google` | `openai` | `xai` |
| `model` | `fal-ai/z-image/turbo` | `fal-ai/nano-banana*` / `google/nano-banana*` | `openai/gpt-image-2` / `fal-ai/gpt-image-*` | `xai/grok-imagine-image*` |
| `mode` | `text-to-image` | `text-to-image` / `edit` | `text-to-image` / `edit` | `text-to-image` / `edit` |
| `prompt` | `prompt` | `prompt` | `prompt` | `prompt` |
| `input_images` | 无 | `image_urls` | `image_urls` | `image_urls` |
| `aspect_or_size` | `image_size` | `aspect_ratio` | `image_size` | `aspect_ratio` |
| `resolution` | 部分包含在 `image_size` | `resolution` | 部分包含在 `image_size` | `resolution` |
| `count` | `num_images` | `num_images` | `num_images` | `num_images` |
| `format` | `output_format` | `output_format` | `output_format` | `output_format` |
| `seed` | `seed` | `seed` | 不支持 | 不支持 |
| `safety` | `enable_safety_checker` | `safety_tolerance` | 不支持 | 不支持 |
| `sync` | `sync_mode` | `sync_mode` | `sync_mode` | `sync_mode` |
| `vendor_options` | `num_inference_steps`、`acceleration`、`enable_prompt_expansion` | `system_prompt`、`enable_web_search`、`thinking_level`、`video_url/audio_url/pdf_url` | `quality`、`background`、`input_fidelity`、`mask_url/mask_image_url` | 无太多高级字段 |

## 8. 实现注意事项

如果这些接口要接入统一图片生成 UI/API，不建议强行把所有字段压平成同一套固定表单。更稳妥的做法是：

1. 通用字段：`prompt`、`mode`、`input_images`、`aspect_ratio/image_size`、`num_images`、`output_format`、`sync_mode`。
2. 能力探测字段：`supports_seed`、`supports_safety`、`supports_mask`、`supports_resolution`、`supports_web_search`、`supports_multimodal_context`。
3. 厂商扩展字段：每个 provider/model 保留自己的 `vendor_options`。
4. 价格模型字段：不要只存 `price_per_image`，应支持 `per_image`、`per_megapixel`、`token_based`、`resolution_multiplier`、`addon`、`input_image_fee` 等类型。
