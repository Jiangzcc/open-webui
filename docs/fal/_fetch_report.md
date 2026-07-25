# fal.ai 文生图 llms.txt 归档抓取报告
> 由自动化脚本生成（stage2_download.py），对应 `docs/fal/**` 本次新增/覆盖。
> 内容均为 fal 官方 `llms.txt` 原文整篇照存，未做人为篡改。

## 概况

| 项目 | 数值 |
|---|---|
| API 大盘总计(endpoint) | 1394 |
| 翻页采集到的行 | 1394 |
| text-to-image 主入口 | 194 |
| edit 兄弟候选(image-to-image 且有血缘) | 85 |
| 无血缘 image-to-image(已排除) | 295 |
| 本次目标 endpoint(unique) | 279 |
| 成功·新增 | 271 |
| 成功·覆盖既有 | 8 |
| 失败 | 0 |

## 各品牌落地分布(新增为主,覆盖另计)

| 品牌(slug) | 新增 | 覆盖既有 |
|---|---|---|
| `alibaba` | 29 | 0 |
| `baidu` | 4 | 0 |
| `black-forest-labs` | 69 | 0 |
| `bria-ai` | 6 | 0 |
| `bytedance` | 9 | 0 |
| `fal` | 2 | 0 |
| `google` | 9 | 6 |
| `hidream` | 7 | 0 |
| `ideogram` | 15 | 0 |
| `imagineart` | 3 | 0 |
| `kling` | 4 | 0 |
| `krea` | 4 | 0 |
| `krea-2` | 2 | 0 |
| `luma-ai` | 6 | 0 |
| `microsoft` | 2 | 0 |
| `minimax` | 1 | 0 |
| `misc` | 52 | 0 |
| `nvidia` | 1 | 0 |
| `openai` | 6 | 2 |
| `phota` | 1 | 0 |
| `recraft` | 13 | 0 |
| `reve` | 1 | 0 |
| `rundiffusion` | 7 | 0 |
| `stability-ai` | 9 | 0 |
| `tencent` | 4 | 0 |
| `vidu` | 1 | 0 |
| `xai` | 4 | 0 |

## 命名与目录约定

- 一级目录=`docs/fal/<brand-slug>/`,`brand-slug` 由 `modelLab` 小写化并以连字符规整而来,缺失者为 `misc/`。
- 二级目录=`<series-slug>/`,为去除厂商前缀后的 id(`/`坍缩为 `-`),尾部 `/edit`、`/edit-image`、`/image-to-image` 等编辑标记先行剥离。
- 叶子文件:t2i 主线为 `<series-slug>.md`;edit 兄弟追加 `@edit` 得 `<series-slug>@edit.md`。
- 保证任一路径最深三层(`docs/fal/brand/series/file.md`)。

## edit 兄弟匹配明细(供你复核血缘判定)

`via=strip->t2i-stem` 表示剥掉 `/edit`/`/image-to-image` 等尾段后恰为已知 t2i;
`via=prefix` 表示其为某 t2i 的父前缀(常见于家族容器或 LoRA 包),宽松起见一并纳入,如觉不当可指示剔除。

| id | 品牌 | via | 命中 stems |
|---|---|---|---|
| `bytedance/seedream/v5/lite/edit` | `bytedance` | prefix | bytedance/seedream/v5/lite/text-to-image |
| `bytedance/seedream/v5/pro/edit` | `bytedance` | prefix | bytedance/seedream/v5/pro/text-to-image |
| `fal-ai/bagel/edit` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/boogu-image/edit` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/bytedance/seedream/v4.5/edit` | `bytedance` | prefix | fal-ai/bytedance/seedream/v4.5/text-to-image |
| `fal-ai/bytedance/seedream/v4/edit` | `bytedance` | prefix | fal-ai/bytedance/seedream/v4/text-to-image |
| `fal-ai/emu-3.5-image/edit-image` | `misc` | prefix | fal-ai/emu-3.5-image/text-to-image |
| `fal-ai/fast-lcm-diffusion/image-to-image` | `stability-ai` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/fast-lightning-sdxl/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/fast-sdxl-controlnet-canny/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/fast-sdxl/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-1/dev/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-1/krea/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-1/srpo/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2-flex/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2-max/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2-pro/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/flash/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/klein/4b/base/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/klein/4b/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/klein/9b/base/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/klein/9b/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/lora/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-2/turbo/edit` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-control-lora-canny/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-control-lora-depth/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-general/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-kontext-lora` | `black-forest-labs` | prefix | fal-ai/flux-kontext-lora/text-to-image |
| `fal-ai/flux-krea-lora/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-lora/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux-pro/kontext` | `black-forest-labs` | prefix | fal-ai/flux-pro/kontext/max/text-to-image, fal-ai/flux-pro/kontext/text-to-image |
| `fal-ai/flux-pro/kontext/max` | `black-forest-labs` | prefix | fal-ai/flux-pro/kontext/max/text-to-image |
| `fal-ai/flux/dev/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux/krea/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/flux/srpo/image-to-image` | `black-forest-labs` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gemini-25-flash-image/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gemini-3-pro-image-preview/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gemini-3.1-flash-image-preview/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/glm-image/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gpt-image-1-mini/edit` | `openai` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gpt-image-1.5/edit` | `openai` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/gpt-image-1/edit-image` | `openai` | prefix | fal-ai/gpt-image-1/text-to-image |
| `fal-ai/hidream-i1-full/image-to-image` | `hidream` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/hidream-o1-image/dev/edit` | `hidream` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/hidream-o1-image/edit` | `hidream` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/hunyuan-image/v3/instruct/edit` | `tencent` | prefix | fal-ai/hunyuan-image/v3/instruct/text-to-image |
| `fal-ai/ideogram/v2/edit` | `ideogram` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/ideogram/v2/turbo/edit` | `ideogram` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/ideogram/v3/edit` | `ideogram` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/kling-image/o3/image-to-image` | `kling` | prefix | fal-ai/kling-image/o3/text-to-image |
| `fal-ai/kling-image/v3/image-to-image` | `kling` | prefix | fal-ai/kling-image/v3/text-to-image |
| `fal-ai/kolors/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/longcat-image/edit` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/lora/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/nano-banana-2/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/nano-banana-pro/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/nano-banana/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/patina` | `fal` | prefix | fal-ai/patina/material |
| `fal-ai/phota/edit` | `phota` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/playground-v25/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/qwen-image-2/edit` | `alibaba` | prefix | fal-ai/qwen-image-2/text-to-image, fal-ai/qwen-image-2/pro/text-to-image |
| `fal-ai/qwen-image-2/pro/edit` | `alibaba` | prefix | fal-ai/qwen-image-2/pro/text-to-image |
| `fal-ai/qwen-image-max/edit` | `alibaba` | prefix | fal-ai/qwen-image-max/text-to-image |
| `fal-ai/qwen-image/image-to-image` | `alibaba` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/recraft/v3/image-to-image` | `recraft` | prefix | fal-ai/recraft/v3/text-to-image |
| `fal-ai/sdxl-controlnet-union/image-to-image` | `misc` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/stable-diffusion-v3-medium/image-to-image` | `stability-ai` | strip->t2i-stem | (stripped→t2i) |
| `fal-ai/wan-25-preview/image-to-image` | `alibaba` | prefix | fal-ai/wan-25-preview/text-to-image |
| `fal-ai/wan/v2.2-a14b/image-to-image` | `alibaba` | prefix | fal-ai/wan/v2.2-a14b/text-to-image/lora, fal-ai/wan/v2.2-a14b/text-to-image |
| `fal-ai/wan/v2.7/edit` | `alibaba` | prefix | fal-ai/wan/v2.7/pro/text-to-image, fal-ai/wan/v2.7/text-to-image |
| `fal-ai/wan/v2.7/pro/edit` | `alibaba` | prefix | fal-ai/wan/v2.7/pro/text-to-image |
| `fal-ai/z-image/turbo/image-to-image` | `alibaba` | strip->t2i-stem | (stripped→t2i) |
| `google/nano-banana-lite/edit` | `google` | strip->t2i-stem | (stripped→t2i) |
| `ideogram/v4/image-to-image` | `ideogram` | strip->t2i-stem | (stripped→t2i) |
| `luma/agent/uni-1/v1/edit` | `luma-ai` | prefix | luma/agent/uni-1/v1/max, luma/agent/uni-1/v1/text-to-image |
| `luma/agent/uni-1/v1/max/edit` | `luma-ai` | strip->t2i-stem | (stripped→t2i) |
| `microsoft/mai-image-2.5/edit` | `microsoft` | strip->t2i-stem | (stripped→t2i) |
| `openai/gpt-image-2/edit` | `openai` | strip->t2i-stem | (stripped→t2i) |
| `reve/2.1/edit` | `misc` | prefix | reve/2.1/text-to-image |
| `rundiffusion-fal/juggernaut-flux/base/image-to-image` | `rundiffusion` | strip->t2i-stem | (stripped→t2i) |
| `rundiffusion-fal/juggernaut-flux/pro/image-to-image` | `rundiffusion` | strip->t2i-stem | (stripped→t2i) |
| `wan/v2.6/image-to-image` | `alibaba` | prefix | wan/v2.6/text-to-image |
| `xai/grok-imagine-image/edit` | `xai` | strip->t2i-stem | (stripped→t2i) |
| `xai/grok-imagine-image/quality/edit` | `xai` | prefix | xai/grok-imagine-image/quality/text-to-image |

## 被覆盖的既有文件清单

- `fal-ai/nano-banana-2`
- `fal-ai/nano-banana-pro`
- `fal-ai/nano-banana`
- `fal-ai/gpt-image-1.5`
- `fal-ai/nano-banana-2/edit`
- `fal-ai/nano-banana-pro/edit`
- `fal-ai/nano-banana/edit`
- `fal-ai/gpt-image-1.5/edit`

## 失败明细

_(全部成功,无失败)_
