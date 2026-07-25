# fal.ai 文生图(text-to-image)接入决策表


> **用途**:本文是为「拍板要不要、接哪些 fal 文生图模型」准备的决策材料,**尚未动任何代码**。你阅毕圈定范围后,我再依此制定实现计划。

> **数据来源**:线上 explore 共 194 条 → 逐条抓 `https://fal.ai/models/<id>/llms.txt` 机器解析得到入参/出参;再按 `hostingType + modelLab` 分为四档:旗舰(serverless 58)、旗舰(proxy 67)、衍生 LoRA 风格包 30、社区/无名 39。

> **覆盖范围**:按你的选择,只展开 **旗舰两档共 125 条** 的详表;余 69 条仅在 §C 一览,不入接入考量。


---


## 怎么读这张表


| 列 | 含义 |
|---|---|
| `id` | fal 真实 model id,即 `fal.run/<id>` 的请求路径 |
| ★ | 我们仓库 `docs/fal/**` 已为该 id 本人或其 gen/edit 兄弟建过档案(≠ 已在前端开放) |
| 托管 | serverless = fal 自管 GPU 推荐;proxy = 第三方代理路由,偶有冷启动 |
| 尺寸参数 | 控制画幅所用字段:`image_size`=显式像素枚举;`aspect_ratio`=比例枚举;`resolution`=分辨率档 |
| 张数 | `num_images` 取值范围(全员另必有 `prompt` 必填、`sync_mode` 开关,表中不再赘述) |
| 入参要点 | 除去上述两者以外的可调旋钮,`「…」` 内为枚举/范围/默认值的精简形 |
| 出参字段 | 响应顶层字段名集合;`images[]` 是全体共有主载体 |
| 价位 | 取自 llms.txt 原文的美元数额,仅供横向比较,以 fal 控制台为准 |

> ⚠️ 几乎所有模型都用 `image_size` 或 `aspect_ratio` 中的一个来表达画幅,但两者的**枚举内涵各异**(Flux 系多是 `landscape_4_3`/`portrait_16_9`/`square_hd` 这类命名档;Google/xAI 是数值比例串;OpenAI 是像素串)。接入时每种模型需各自维护一套合法值,这也是我们 `fal_models.py` 至今只能逐条手写的根本原因。


---


## §A 旗舰候选详表(125 条,按实验室分组)


### Alibaba(15 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/qwen-image` | Qwen Image | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=" "」; guidance_scale=「`0` to `20`」; num_inference_steps=「`2` to `250`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」; +loras=「def=[]」; +use_turbo=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.02 |  |
| `fal-ai/qwen-image-2512` | Qwen Image 2512 | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | 0.02 per megapixel (rounded up to the nearest me |  |
| `fal-ai/qwen-image-2512/lora` | Qwen Image 2512 | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」; +loras=「def=[]」 | images,timings,seed,has_nsfw_concepts,prompt | $0.035 |  |
| `fal-ai/wan/v2.2-5b/text-to-image` | Wan | serverless | commercial | image_size | — | image_size=「def="square_hd"」; seed; negative_prompt=「def=""」; guidance_scale=「`1` to `10`」; num_inference_steps=「`2` to `50`」; enable_safety_checker=「def=false」; +enable_output_safety_checker=「def=false」; +enable_prompt_expansion=「def=false」; +shift=「`1` to `10`」 | image,seed | $0.016 |  |
| `fal-ai/wan/v2.2-a14b/text-to-image` | Wan | serverless | commercial | image_size | — | image_size=「def="square_hd"」; seed; negative_prompt=「def=""」; guidance_scale=「`1` to `10`」; num_inference_steps=「`2` to `40`」; enable_safety_checker=「def=false」; +enable_output_safety_checker=「def=false」; +enable_prompt_expansion=「def=false」; +acceleration=「"none"/"regular"」 | image,seed | $0.025 |  |
| `fal-ai/z-image/base` | Z Image Base | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.01 |  |
| `fal-ai/z-image/turbo` | Z Image Turbo | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; num_inference_steps=「`1` to `8`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」; +enable_prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.005 | ★ |
| `fal-ai/z-image/turbo/tiling` | Z-Image Turbo Seamless Tili… | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; num_inference_steps=「`1` to `8`」; strength=「def=0.6」; enable_safety_checker=「def=true」; mask_image_url; image_url; +acceleration=「"none"/"regular"/"high"」; +enable_prompt_expansion=「def=false」; +tile_size=「`32` to `256`, step: `2`」 | images,timings,seed,has_nsfw_concepts,prompt | $0.02 |  |
| `fal-ai/qwen-image-2/pro/text-to-image` | Qwen Image 2 | proxy | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」 | images,seed | $0.075 |  |
| `fal-ai/qwen-image-2/text-to-image` | Qwen Image 2 | proxy | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」 | images,seed | $0.035 |  |
| `fal-ai/qwen-image-max/text-to-image` | Qwen Image Max | proxy | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」 | images,seed | $0.075 |  |
| `fal-ai/wan-25-preview/text-to-image` | Wan 2.5 Text to Image | proxy | commercial | image_size | `1` to `4` | image_size=「def="square"」; num_images=「`1` to `4`」; seed; negative_prompt; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」 | images,seeds,actual_prompt | $0.05 |  |
| `wan/v2.6/text-to-image` | Wan v2.6 Text to Image | proxy | commercial | image_size | — | image_size; seed; negative_prompt=「def=""」; enable_safety_checker=「def=true」; image_url; +max_images=「`1` to `5`」 | images,generated_text,seed | $0.03 |  |
| `fal-ai/wan/v2.7/pro/text-to-image` | Wan | proxy | commercial | image_size | `1` to `5` | image_size=「def="square_hd"」; num_images=「`1` to `5`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; enable_safety_checker=「def=true」 | images,generated_text,seed | $0.075 |  |
| `fal-ai/wan/v2.7/text-to-image` | Wan | proxy | commercial | image_size | `1` to `5` | image_size=「def="square_hd"」; num_images=「`1` to `5`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; enable_safety_checker=「def=true」 | images,generated_text,seed | $0.03 |  |

### Baidu(2 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/ernie-image` | Ernie Image | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `100`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,seed,prompt,timings | $0.03 |  |
| `fal-ai/ernie-image/turbo` | Ernie Image Turbo | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `20`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,seed,prompt,timings | $0.01 |  |

### Black Forest Labs(23 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/flux-1/dev` | FLUX.1 [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux-1/krea` | FLUX.1 Krea [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux-1/schnell` | FLUX.1 [schnell] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `12`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.003 |  |
| `fal-ai/flux-2` | FLUX 2 | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; guidance_scale=「`0` to `20`」; num_inference_steps=「`4` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」; +enable_prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.012 |  |
| `fal-ai/flux-2/flash` | FLUX 2 Flash | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; guidance_scale=「`0` to `20`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.005 |  |
| `fal-ai/flux-2/klein/4b` | FLUX.2 [klein] 4B | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; num_inference_steps=「`4` to `8`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.005 |  |
| `fal-ai/flux-2/klein/4b/base` | FLUX.2 [klein] 4B Base | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`4` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.009 |  |
| `fal-ai/flux-2/klein/9b` | FLUX.2 [klein] 9B | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; num_inference_steps=「`4` to `8`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.006 |  |
| `fal-ai/flux-2/klein/9b/base` | FLUX.2 [klein] 9B Base | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`4` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.011 |  |
| `fal-ai/flux-2/turbo` | FLUX 2 Turbo | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; guidance_scale=「`0` to `20`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.008 |  |
| `fal-ai/flux/dev` | FLUX.1 [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux/krea` | FLUX.1 Krea [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux/schnell` | FLUX.1 [schnell] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `12`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.003 |  |
| `fal-ai/flux-1/srpo` | FLUX.1 SRPO [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux-subject` | FLUX.1 Subject | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; image_url | images,timings,seed,has_nsfw_concepts,prompt | $0.04 |  |
| `fal-ai/flux/srpo` | FLUX.1 SRPO [dev] | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.025 |  |
| `fal-ai/flux-2-flex` | Flux 2 Flex | proxy | commercial | image_size | — | image_size=「def="landscape_4_3"」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1.5` to `10`」; num_inference_steps=「`2` to `50`」; enable_safety_checker=「def=true」; safety_tolerance=「"1"/"2"/"3"/"4" …(+1)」 | images,seed | $0.05 $0.06 $0.10 |  |
| `fal-ai/flux-2-max` | Flux 2 Max | proxy | commercial | image_size | — | image_size=「def="landscape_4_3"」; seed; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」; safety_tolerance=「"1"/"2"/"3"/"4" …(+1)」 | images,seed | $0.07 |  |
| `fal-ai/flux-2-pro` | Flux 2 Pro | proxy | commercial | image_size | — | image_size=「def="landscape_4_3"」; seed; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」; safety_tolerance=「"1"/"2"/"3"/"4" …(+1)」 | images,seed | $0.015 $0.03 $0.045 |  |
| `fal-ai/flux-pro/v1.1` | FLUX1.1 [pro] | proxy | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; enhance_prompt=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.04 |  |
| `fal-ai/flux-pro/v1.1-ultra` | FLUX1.1 [pro] ultra | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「def="16:9"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; enhance_prompt=「def=false」; image_url; image_prompt_strength=「`0` to `1`」; +raw=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.06 |  |
| `fal-ai/flux-pro/kontext/max/text-to-image` | FLUX.1 Kontext [max] | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"21:9"/"16:9"/"4:3"/"3:2" …(+5)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; enhance_prompt=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.08 |  |
| `fal-ai/flux-pro/kontext/text-to-image` | FLUX.1 Kontext [pro] | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"21:9"/"16:9"/"4:3"/"3:2" …(+5)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; enhance_prompt=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt | $0.04 |  |

### Bria AI(6 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `bria/fibo-lite/generate` | Fibo Lite | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; seed=「def=7」; negative_prompt=「def=""」; image_url; +structured_prompt; +steps_num=「`4` to `30`」 | image,images,structured_prompt | $0.036 |  |
| `bria/fibo/generate` | Fibo | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; resolution=「"1MP"/"4MP"」; seed=「def=5555」; negative_prompt=「def=""」; image_url; +structured_prompt; +steps_num=「`20` to `50`」 | image,images,structured_prompt | $0.04 |  |
| `bria/fibo-bbq-preview/generate` | Fibo Bbq Preview | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; seed=「def=5555」; negative_prompt=「def=""」; guidance_scale=「`3` to `5`」; image_url; +structured_prompt; +steps_num=「`20` to `50`」 | image,images,structured_prompt | $0.04 |  |
| `fal-ai/bria/text-to-image/base` | Bria Text-to-Image Base | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; num_images=「`1` to `4`」; seed=「`0` to `2147483647`」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`20` to `50`」; +prompt_enhancement=「def=false」; +medium=「"photography"/"art"」; +guidance=「def=[]」 | images,seed | $0.04 |  |
| `fal-ai/bria/text-to-image/fast` | Bria Text-to-Image Fast | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; num_images=「`1` to `4`」; seed=「`0` to `2147483647`」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`4` to `10`」; +prompt_enhancement=「def=false」; +medium=「"photography"/"art"」; +guidance=「def=[]」 | images,seed | $0.028 |  |
| `fal-ai/bria/text-to-image/hd` | Bria Text-to-Image HD | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"1:1"/"2:3"/"3:2"/"3:4" …(+5)」; num_images=「`1` to `4`」; seed=「`0` to `2147483647`」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`20` to `50`」; +prompt_enhancement=「def=false」; +medium=「"photography"/"art"」; +guidance=「def=[]」 | images,seed | $0.04 |  |

### Fal(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/patina/material` | PATINA | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; num_inference_steps=「`1` to `8`」; strength=「def=0.6」; enable_safety_checker=「def=true」; mask_url; image_url; +enable_prompt_expansion=「def=true」; +tiling_mode=「"both"/"horizontal"/"vertical"」; +tile_size=「`32` to `256`」 | images,seed,prompt,timings | $0.004 $0.01 $0.016 $0.02 $0.08 $0.61 |  |

### Hidream(4 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/hidream-i1-dev` | Hidream I1 Dev | serverless | commercial | image_size | `1` to `4` | image_size=「def={"width":1024,"height":1024}」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.03 |  |
| `fal-ai/hidream-i1-fast` | Hidream I1 Fast | serverless | commercial | image_size | `1` to `4` | image_size=「def={"width":1024,"height":1024}」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.01 |  |
| `fal-ai/hidream-i1-full` | Hidream I1 Full | serverless | commercial | image_size | `1` to `4` | image_size=「def={"height":1024,"width":1024}」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +loras=「def=[]」 | images,timings,seed,has_nsfw_concepts,prompt | $0.05 |  |
| `fal-ai/hidream-o1-image` | Hidream O1 Image | serverless | commercial | image_size | `1` to `4` | image_size=「def={"width":1024,"height":1024}」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +reference_image_urls=「def=[]」; +keep_original_aspect=「def=false」 | images,seed,has_nsfw_concepts,prompt,timings | $0.01 |  |

### Ideogram(10 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `ideogram/v4` | Ideogram V4.0 Text to Image | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; rendering_speed=「"TURBO"/"BALANCED"/"QUALITY"」; enable_safety_checker=「def=true」; +expansion_model=「"None"/"Medium"/"Large"」; +acceleration=「"none"/"low"/"regular"/"high"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.0075 $0.015 $0.025 $0.03 $0.06 $0.10 |  |
| `ideogram/v4/fast` | V4.0q [fast] | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; rendering_speed=「"TURBO"/"BALANCED"/"QUALITY"」; enable_safety_checker=「def=true」; +expansion_model=「"None"/"Medium"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.00525 $0.0105 $0.0175 $0.021 $0.042 $0.07 |  |
| `ideogram/v4/instant` | V4.0q [instant] | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」; +expansion_model=「"None"/"Medium"」 | images,timings,seed,has_nsfw_concepts,prompt | $0.0075 $0.03 |  |
| `fal-ai/ideogram/v2` | Ideogram V2 | proxy | commercial | aspect_ratio | — | aspect_ratio=「"10:16"/"16:10"/"9:16"/"16:9" …(+7)」; seed; negative_prompt=「def=""」; style=「"auto"/"general"/"realistic"/"design" …(+2)」; expand_prompt=「def=true」 | images,seed | $0.08 |  |
| `fal-ai/ideogram/v2/turbo` | Ideogram V2 Turbo | proxy | commercial | aspect_ratio | — | aspect_ratio=「"10:16"/"16:10"/"9:16"/"16:9" …(+7)」; seed; negative_prompt=「def=""」; style=「"auto"/"general"/"realistic"/"design" …(+2)」; expand_prompt=「def=true」 | images,seed | $0.05 |  |
| `fal-ai/ideogram/v2a` | Ideogram V2A | proxy | commercial | aspect_ratio | — | aspect_ratio=「"10:16"/"16:10"/"9:16"/"16:9" …(+7)」; seed; style=「"auto"/"general"/"realistic"/"design" …(+2)」; expand_prompt=「def=true」 | images,seed | $0.04 |  |
| `fal-ai/ideogram/v2a/turbo` | Ideogram V2A Turbo | proxy | commercial | aspect_ratio | — | aspect_ratio=「"10:16"/"16:10"/"9:16"/"16:9" …(+7)」; seed; style=「"auto"/"general"/"realistic"/"design" …(+2)」; expand_prompt=「def=true」 | images,seed | $0.025 |  |
| `fal-ai/ideogram/v3` | Ideogram Text to Image | proxy | commercial | image_size | `1` to `8` | image_size=「def="square_hd"」; num_images=「`1` to `8`」; seed; negative_prompt=「def=""」; rendering_speed=「"TURBO"/"BALANCED"/"QUALITY"」; style=「"AUTO"/"GENERAL"/"REALISTIC"/"DESIGN"」; style_preset=「"80S_ILLUSTRATION"/"90S_NOSTALGIA"/"ABSTRACT_ORGANIC"/"ANALOG_NOSTALGIA" …(+58)」; expand_prompt=「def=true」; image_urls; +color_palette; +style_codes | images,seed | $0.03 $0.06 $0.09 |  |
| `fal-ai/ideogram/custom-models/generate` | Ideogram | proxy | commercial | aspect_ratio | `1` to `8` | aspect_ratio=「"1:3"/"3:1"/"1:2"/"2:1" …(+11)」; num_images=「`1` to `8`」; seed; negative_prompt=「def=""」; rendering_speed=「"TURBO"/"BALANCED"/"QUALITY"」; expand_prompt=「def=true」; +model_id | images,seed | $0.03 $0.06 $0.09 |  |
| `fal-ai/ideogram/v3/generate-transparent` | Ideogram Transparent | proxy | commercial | aspect_ratio | `1` to `8` | aspect_ratio=「"1:3"/"3:1"/"1:2"/"2:1" …(+11)」; num_images=「`1` to `8`」; seed; negative_prompt=「def=""」; rendering_speed=「"TURBO"/"BALANCED"/"QUALITY"」; expand_prompt=「def=true」 | images,seed | $0.03 $0.06 $0.09 |  |

### ImagineArt(3 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `imagineart/imagineart-2.0-preview/text-to-image` | Imagineart 2.0 Preview | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"16:9"/"9:16"/"4:3" …(+10)」; resolution=「"1K"/"2K"」; seed; +reasoning=「"high"/"low"」 | images | $0.03 $0.05 |  |
| `imagineart/imagineart-1.5-preview/text-to-image` | Imagineart 1.5 Preview | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"3:1"/"1:3"/"16:9" …(+5)」; seed | images | $0.03 |  |
| `imagineart/imagineart-1.5-pro-preview/text-to-image` | ImagineArt 1.5 Pro Preview | serverless | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"3:1"/"1:3"/"16:9" …(+5)」; seed | images | $0.045 |  |

### Krea(4 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/krea-2/turbo` | Krea 2 Turbo | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"」; +enable_prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt,actual_prompt | $0.008 |  |
| `krea/v2/large/text-to-image` | Krea 2 Large | proxy | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"4:3"/"3:2"/"16:9" …(+4)」; seed; +creativity=「"raw"/"low"/"medium"/"high"」; +image_style_references=「def=[]」; +styles=「def=[]」 | images,seed | $0.060 $0.065 |  |
| `krea/v2/medium/text-to-image` | Krea 2 Medium | proxy | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"4:3"/"3:2"/"16:9" …(+4)」; seed; +creativity=「"raw"/"low"/"medium"/"high"」; +image_style_references=「def=[]」; +styles=「def=[]」 | images,seed | $0.030 $0.035 |  |
| `krea/v2/medium/turbo/text-to-image` | Krea 2 Medium Text to Image… | proxy | commercial | aspect_ratio | — | aspect_ratio=「"1:1"/"4:3"/"3:2"/"16:9" …(+4)」; seed; +creativity=「"raw"/"low"/"medium"/"high"」; +image_style_references=「def=[]」; +styles=「def=[]」 | images,seed | $0.015 $0.0175 |  |

### Krea 2(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/krea-2/turbo/style` | Krea 2 Text to Image Turbo … | None | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」; +acceleration=「"none"/"regular"」; +enable_prompt_expansion=「def=false」; +reference_image_urls | images,timings,seed,has_nsfw_concepts,prompt,actual_prompt | $0.01 |  |

### NVIDIA(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `nvidia/cosmos-3-super/text-to-image` | Cosmos 3 Super | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=false」; +enable_agentic_generation=「def=false」; +agentic_max_iterations=「`1` to `3`」 | images,seed,has_nsfw_concepts | $0.02 $0.04 |  |

### Recraft(12 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/recraft-20b` | Recraft 20b | serverless | commercial | image_size | — | image_size=「def="square_hd"」; style=「"any"/"realistic_image"/"digital_illustration"/"vector_illustration" …(+33)」; enable_safety_checker=「def=false」; +colors=「def=[]」; +style_id | images | $0.022 $0.044 $1 |  |
| `fal-ai/recraft/v4/pro/text-to-image` | Recraft V4 Pro | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.25 |  |
| `fal-ai/recraft/v4/pro/text-to-vector` | Recraft V4 Pro (Vector) | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.3 |  |
| `fal-ai/recraft/v4/text-to-image` | Recraft V4 | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.04 |  |
| `fal-ai/recraft/v4/text-to-vector` | Recraft V4 (Vector) | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.08 |  |
| `fal-ai/recraft/v4.1/pro/text-to-image` | Recraft V4.1 Text to Image … | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.21 |  |
| `fal-ai/recraft/v4.1/pro/text-to-vector` | Recraft V4.1 Text to Vector… | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.3 |  |
| `fal-ai/recraft/v4.1/text-to-image` | Recraft V4.1 Text to Image | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.035 |  |
| `fal-ai/recraft/v4.1/text-to-vector` | Recraft V4.1 Text to Vector | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.08 |  |
| `fal-ai/recraft/v4.1/utility/pro/text-to-image` | Recraft V4.1 Utility Text t… | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.21 |  |
| `fal-ai/recraft/v4.1/utility/text-to-image` | Recraft V4.1 Text to Image … | proxy | commercial | image_size | — | image_size=「def="square_hd"」; enable_safety_checker=「def=true」; +colors=「def=[]」; +background_color | images | $0.035 |  |
| `fal-ai/recraft/v3/text-to-image` | Recraft V3 | proxy | commercial | image_size | — | image_size=「def="square_hd"」; style=「"any"/"realistic_image"/"digital_illustration"/"vector_illustration" …(+81)」; enable_safety_checker=「def=false」; +colors=「def=[]」; +style_id | images | $0.04 $0.08 $1 |  |

### Rundiffusion(4 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `rundiffusion-fal/juggernaut-flux/base` | Juggernaut Flux Base | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.035 |  |
| `rundiffusion-fal/juggernaut-flux/lightning` | Juggernaut Flux Lightning | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; num_inference_steps=「`1` to `12`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.006 |  |
| `rundiffusion-fal/juggernaut-flux/pro` | Juggernaut Flux Pro | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.055 |  |
| `rundiffusion-fal/rundiffusion-photo-flux` | Rundiffusion Photo Flux | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`0` to `35`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +photo_lora_scale=「def=0.75」; +loras=「def=[]」 | images,timings,seed,has_nsfw_concepts,prompt | $0.045 |  |

### Stability AI(7 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/fast-lcm-diffusion` | Latent Consistency Models (… | serverless | commercial | image_size | `1` to `8` | image_size=「def="square_hd"」; num_images=「`1` to `8`」; seed=「def=null」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `32`」; expand_prompt=「def=false」; enable_safety_checker=「def=true」; +safety_checker_version=「"v1"/"v2"」; +format=「"jpeg"/"png"」; +request_id=「def=""」 | images,timings,seed,has_nsfw_concepts,prompt | $0 |  |
| `fal-ai/stable-cascade` | Stable Cascade | serverless | research | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; enable_safety_checker=「def=true」; +first_stage_steps=「`4` to `40`」; +second_stage_steps=「`4` to `24`」; +second_stage_guidance_scale=「`0` to `20`」 | images,timings,seed,has_nsfw_concepts,prompt | $0 |  |
| `fal-ai/stable-cascade/sote-diffusion` | SoteDiffusion | serverless | research | image_size | `1` to `4` | image_size=「def={"width":1024,"height":1536}」; num_images=「`1` to `4`」; seed; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; enable_safety_checker=「def=true」; +first_stage_steps=「`4` to `50`」; +second_stage_steps=「`4` to `24`」; +second_stage_guidance_scale=「`0` to `20`」 | images,timings,seed,has_nsfw_concepts,prompt | $0 |  |
| `fal-ai/stable-diffusion-v15` | Stable Diffusion v1.5 | serverless | commercial | image_size | `1` to `8` | image_size=「def="square"」; num_images=「`1` to `8`」; seed=「def=null」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; expand_prompt=「def=false」; enable_safety_checker=「def=true」; +loras=「def=[]」; +embeddings=「def=[]」; +request_id=「def=""」 | images,timings,seed,has_nsfw_concepts,prompt | $0 |  |
| `fal-ai/stable-diffusion-v3-medium` | Stable Diffusion V3 | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +prompt_expansion=「def=false」 | images,timings,seed,has_nsfw_concepts,prompt,num_images | $0.035 |  |
| `fal-ai/stable-diffusion-v35-large` | Stable Diffusion 3.5 Large | serverless | commercial | image_size | `1` to `4` | image_size; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +controlnet; +loras=「def=[]」; +ip_adapter | images,timings,seed,has_nsfw_concepts,prompt | $0.065 |  |
| `fal-ai/stable-diffusion-v35-medium` | Stable Diffusion 3.5 Medium | serverless | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`0` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +auto_fix=「def=true」 | images,timings,seed,has_nsfw_concepts,prompt | $0.02 |  |

### Tencent(3 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/hunyuan-image/v2.1/text-to-image` | Hunyuan Image | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +use_reprompt=「def=true」; +use_refiner=「def=false」 | images,seed | $0.1 |  |
| `fal-ai/hunyuan-image/v3/instruct/text-to-image` | Hunyuan Image 3.0 Instruct | serverless | commercial | image_size | `1` to `4` | image_size=「def="auto"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; guidance_scale=「`2` to `20`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=true」 | images,seed | $0.09 |  |
| `fal-ai/hunyuan-image/v3/text-to-image` | Hunyuan Image | serverless | commercial | image_size | `1` to `4` | image_size=「def="square_hd"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"」; negative_prompt=「def=""」; guidance_scale=「`1` to `20`」; num_inference_steps=「`1` to `50`」; enable_safety_checker=「def=true」; +enable_prompt_expansion=「def=false」 | images,seed | $0.1 |  |

### Bytedance(5 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/bytedance/dreamina/v3.1/text-to-image` | Bytedance Dreamina V3.1 Tex… | proxy | commercial | image_size | `1` to `4` | image_size=「def={"height":1536,"width":2048}」; num_images=「`1` to `4`」; seed; enhance_prompt=「def=false」 | images,seed | $0.03 |  |
| `fal-ai/bytedance/seedream/v4/text-to-image` | Bytedance Seedream V4 Text … | proxy | commercial | image_size | `1` to `6` | image_size=「def={"height":2048,"width":2048}」; num_images=「`1` to `6`」; seed; enable_safety_checker=「def=true」; +max_images=「`1` to `6`」; +enhance_prompt_mode=「"standard"/"fast"」 | images,seed | $0.03 |  |
| `fal-ai/bytedance/seedream/v4.5/text-to-image` | Bytedance Seedream V4.5 Tex… | proxy | commercial | image_size | `1` to `6` | image_size=「def={"height":2048,"width":2048}」; num_images=「`1` to `6`」; seed; enable_safety_checker=「def=true」; +max_images=「`1` to `6`」 | images,seed | $0.04 |  |
| `bytedance/seedream/v5/pro/text-to-image` | Seedream 5.0 Pro Text to Im… | proxy | commercial | image_size | `1` to `6` | image_size=「def="auto_2K"」; num_images=「`1` to `6`」; output_format=「"jpeg"/"png"」; enable_safety_checker=「def=true」 | images | $0.0675 $0.135 |  |
| `bytedance/seedream/v5/lite/text-to-image` | Seedream | proxy | commercial | image_size | `1` to `6` | image_size=「def="auto_2K"」; num_images=「`1` to `6`」; enable_safety_checker=「def=true」; +max_images=「`1` to `6`」; +return_byteplus_urls=「def=false」 | images,seed | $0.035 |  |

### Google(8 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/gemini-25-flash-image` | Gemini 2.5 Flash Image | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"21:9"/"16:9"/"3:2"/"4:3" …(+6)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; +limit_generations=「def=true」 | images,description | $0.039 $1.00 |  |
| `fal-ai/nano-banana` | Nano Banana | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"21:9"/"16:9"/"3:2"/"4:3" …(+6)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; +limit_generations=「def=true」 | images,description | $0.039 $1.00 | ★ |
| `fal-ai/gemini-3.1-flash-image-preview` | Gemini 3.1 Flash Image Prev… | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+11)」; resolution=「"0.5K"/"1K"/"2K"/"4K"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; enable_web_search=「def=false」; thinking_level=「"minimal"/"high"」; +limit_generations=「def=true」 | images,description | $0.015 $0.08 $1.00 |  |
| `fal-ai/nano-banana-2` | Nano Banana 2 | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+11)」; resolution=「"0.5K"/"1K"/"2K"/"4K"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; enable_web_search=「def=false」; thinking_level=「"minimal"/"high"」; +limit_generations=「def=true」 | images,description | $0.002 $0.015 $0.08 $1.00 | ★ |
| `google/nano-banana-2-lite` | Nano Banana 2 Lite | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+11)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; thinking_level=「"minimal"/"high"」; +limit_generations=「def=true」 | images,description | $0.3125 $1.875 $37.50 | ★ |
| `google/nano-banana-lite` | Nano Banana Lite | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+11)」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; thinking_level=「"minimal"/"high"」; +limit_generations=「def=true」 | images,description | $0.3125 $1.875 $37.50 | ★ |
| `fal-ai/gemini-3-pro-image-preview` | Gemini 3 Pro Image Preview | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+7)」; resolution=「"1K"/"2K"/"4K"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; enable_web_search=「def=false」; +limit_generations=「def=true」 | images,description | $0.15 $1.00 |  |
| `fal-ai/nano-banana-pro` | Nano Banana Pro | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"21:9"/"16:9"/"3:2" …(+7)」; resolution=「"1K"/"2K"/"4K"」; num_images=「`1` to `4`」; seed; output_format=「"jpeg"/"png"/"webp"」; safety_tolerance=「"1"/"2"/"3"/"4" …(+2)」; system_prompt=「def=""」; enable_web_search=「def=false」; +limit_generations=「def=true」 | images,description | $0.015 $0.15 $1.00 | ★ |

### Kling(2 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/kling-image/o3/text-to-image` | Kling Image | proxy | commercial | aspect_ratio | `1` to `9` | aspect_ratio=「"16:9"/"9:16"/"1:1"/"4:3" …(+4)」; resolution=「"1K"/"2K"/"4K"」; num_images=「`1` to `9`」; output_format=「"jpeg"/"png"/"webp"」; +elements; +result_type=「"single"/"series"」; +series_amount=「`2` to `9`」 | images | $0.028 |  |
| `fal-ai/kling-image/v3/text-to-image` | Kling Image | proxy | commercial | aspect_ratio | `1` to `9` | aspect_ratio=「"16:9"/"9:16"/"1:1"/"4:3" …(+4)」; resolution=「"1K"/"2K"」; num_images=「`1` to `9`」; output_format=「"jpeg"/"png"/"webp"」; negative_prompt; +elements | images | $0.028 |  |

### Luma AI(4 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/luma-photon` | Luma Photon | proxy | commercial | aspect_ratio | — | aspect_ratio=「"16:9"/"9:16"/"1:1"/"4:3" …(+3)」 | images | $0.019 |  |
| `fal-ai/luma-photon/flash` | Luma Photon Flash | proxy | commercial | aspect_ratio | — | aspect_ratio=「"16:9"/"9:16"/"1:1"/"4:3" …(+3)」 | images | $0.005 |  |
| `luma/agent/uni-1/v1/max` | Luma Uni-1 Text to Image Max | proxy | commercial | aspect_ratio | — | aspect_ratio=「"3:1"/"2:1"/"16:9"/"3:2" …(+5)」; output_format=「"png"/"jpeg"」; style=「"auto"/"manga"」; enable_web_search=「def=false」; +reference_image_urls | images | $0.102 $1 |  |
| `luma/agent/uni-1/v1/text-to-image` | Luma Uni-1 Text to Image | proxy | commercial | aspect_ratio | — | aspect_ratio=「"3:1"/"2:1"/"16:9"/"3:2" …(+5)」; output_format=「"png"/"jpeg"」; style=「"auto"/"manga"」; enable_web_search=「def=false」; +reference_image_urls | images | $0.042 $1 |  |

### Microsoft(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `microsoft/mai-image-2.5` | Mai Image 2.5 Text to Image | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"auto"/"1:1"/"4:3"/"3:4" …(+4)」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」 | images,description | $0.0001 $0.05 $5.00 |  |

### Minimax(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/minimax/image-01` | MiniMax (Hailuo AI) Text to… | proxy | commercial | aspect_ratio | `1` to `9` | aspect_ratio=「"1:1"/"16:9"/"4:3"/"3:2" …(+4)」; num_images=「`1` to `9`」; +prompt_optimizer=「def=false」 | images | $1 |  |

### OpenAI(4 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/gpt-image-1-mini` | GPT Image 1 Mini | proxy | commercial | image_size | `1` to `4` | image_size=「"auto"/"1024x1024"/"1536x1024"/"1024x1536"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」; quality=「"auto"/"low"/"medium"/"high"」; background=「"auto"/"transparent"/"opaque"」 | images | $0.002 $0.005 $0.006 $0.011 $0.015 $0.036 $0.052 | ★ |
| `fal-ai/gpt-image-1/text-to-image` | gpt-image-1 | proxy | commercial | image_size | `1` to `4` | image_size=「"auto"/"1024x1024"/"1536x1024"/"1024x1536"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」; quality=「"auto"/"low"/"medium"/"high"」; background=「"auto"/"transparent"/"opaque"」 | images | $0.002 $0.011 $0.016 $0.042 $0.063 $0.167 $0.25 | ★ |
| `fal-ai/gpt-image-1.5` | GPT-Image 1.5 | proxy | commercial | image_size | `1` to `4` | image_size=「"1024x1024"/"1536x1024"/"1024x1536"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」; quality=「"low"/"medium"/"high"」; background=「"auto"/"transparent"/"opaque"」 | images | $0.005 $0.009 $0.010 $0.013 $0.034 $0.050 $0.05… | ★ |
| `openai/gpt-image-2` | GPT Image 2 API | proxy | commercial | image_size | `1` to `4` | image_size=「def="landscape_4_3"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」; quality=「"auto"/"low"/"medium"/"high"」 | images | $0.0001 $1.25 $10.00 $2.00 $30.00 $5.00 $8.00 | ★ |

### Reve(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `reve/2.1/text-to-image` | Reve 2.1 | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"4:1"/"3:1"/"21:9"/"2:1" …(+14)」; num_images=「`1` to `4`」; output_format=「"png"/"jpeg"/"webp"」 | images | $0.25 |  |

### Vidu(1 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `fal-ai/vidu/q2/text-to-image` | Vidu | proxy | commercial | aspect_ratio | — | aspect_ratio=「"16:9"/"9:16"/"1:1"」; seed | image | $0.1 |  |

### xAI(2 条)

| id | 名称 | 托管 | 许可 | 尺寸参数 | 张数 | 入参要点 | 出参字段 | 价位 | ★ |
|---|---|---|---|---|---|---|---|---|---|
| `xai/grok-imagine-image` | Grok Imagine Image | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"2:1"/"20:9"/"19.5:9"/"16:9" …(+9)」; resolution=「"1k"/"2k"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」 | images,revised_prompt | $0.02 | ★ |
| `xai/grok-imagine-image/quality/text-to-image` | Grok Imagine Image | proxy | commercial | aspect_ratio | `1` to `4` | aspect_ratio=「"2:1"/"20:9"/"19.5:9"/"16:9" …(+9)」; resolution=「"1k"/"2k"」; num_images=「`1` to `4`」; output_format=「"jpeg"/"png"/"webp"」 | images,revised_prompt | $0.05 $0.07 | ★ |

_旗舰合计 125 条_


---


## §B 我们已注册的 22 条(基准锚,源自 `fal_models.py`)

以下是本仓库 `backend/open_webui/utils/images/fal_models.py` 已构造能力元数据的模型;其在 §A 中出现的 text-to-image 主入口以 ★ 标出,此处补齐与之绑定的 `/edit` 兄弟。


| 公开 id | 厂商 | 任务 | 比例档数 | 分辨率档 | 默认比例 | 默认分辨率 | 选项字段 | 布尔字段 |
|---|---|---|---|---|---|---|---|---|
| `z-image-turbo` | alibaba | text-to-image | 0 | 6 | — | 1024x768 | acceleration | sync_mode,enable_safety_checker,enable_prompt_expansion |
| `nano-banana` | google | text-to-image | 10 | 0 | 1:1 | — | safety_tolerance | sync_mode,limit_generations |
| `nano-banana/edit` | google | image-to-image | 11 | 0 | auto | — | safety_tolerance | sync_mode,limit_generations |
| `nano-banana-pro` | google | text-to-image | 11 | 3 | 1:1 | 1K | safety_tolerance | sync_mode,limit_generations,enable_web_search |
| `nano-banana-pro/edit` | google | image-to-image | 11 | 3 | auto | 1K | safety_tolerance | sync_mode,limit_generations,enable_web_search |
| `nano-banana-2` | google | text-to-image | 15 | 4 | auto | 1K | safety_tolerance,thinking_level | sync_mode,limit_generations,enable_web_search |
| `nano-banana-2/edit` | google | image-to-image | 15 | 4 | auto | 1K | safety_tolerance,thinking_level | sync_mode,limit_generations,enable_web_search |
| `nano-banana-lite` | google | text-to-image | 15 | 0 | auto | — | safety_tolerance,thinking_level | sync_mode,limit_generations |
| `nano-banana-lite/edit` | google | image-to-image | 15 | 0 | auto | — | safety_tolerance,thinking_level | sync_mode,limit_generations |
| `nano-banana-2-lite` | google | text-to-image | 15 | 0 | auto | — | safety_tolerance,thinking_level | sync_mode,limit_generations |
| `gpt-image-2` | openai | text-to-image | 7 | 0 | 4:3 | — | quality | sync_mode |
| `gpt-image-2/edit` | openai | image-to-image | 8 | 0 | auto | — | quality | sync_mode |
| `gpt-image-1.5` | openai | text-to-image | 0 | 3 | auto | 1024x1024 | quality,background | sync_mode |
| `gpt-image-1.5/edit` | openai | image-to-image | 0 | 4 | auto | auto | quality,background,input_fidelity | sync_mode |
| `gpt-image-1-mini` | openai | text-to-image | 0 | 4 | auto | auto | quality,background | sync_mode |
| `gpt-image-1-mini/edit` | openai | image-to-image | 0 | 4 | auto | auto | quality,background | sync_mode |
| `gpt-image-1` | openai | text-to-image | 0 | 4 | auto | auto | quality,background | sync_mode |
| `gpt-image-1/edit-image` | openai | image-to-image | 0 | 4 | auto | auto | quality,background,input_fidelity | sync_mode |
| `grok-imagine-image` | xai | text-to-image | 13 | 2 | 1:1 | 1k | — | sync_mode |
| `grok-imagine-image/edit` | xai | image-to-image | 14 | 2 | auto | 1k | — | sync_mode |
| `grok-imagine-image-pro` | xai | text-to-image | 13 | 2 | 1:1 | 1k | — | sync_mode |
| `grok-imagine-image-pro/edit` | xai | image-to-image | 14 | 2 | auto | 1k | — | sync_mode |

> 这 22 条构成目前的「已接入基准」。它们的能力表是逐条手写的——这也预示着:即便只新增 30 条新模型,也需要同等量级的手写能力元数据 + 公开/内部 ID 双向映射 + `docs/fal/**` 文档归档 + 积分定价录入。这是衡量「接多少」时的隐性成本坐标。


---


## §C 暂不推荐的 69 条(一览,不入详表)


**① LoRA 风格包(30 条)** —— 本质是在父模型上叠加审美滤镜(Ballpoint Pen Sketch、Sepia Vintage、HDR Style、Realism、Digital Comic Art 等)。建议将来以「父模型 + 风格选择器」的单一通道统一承接,而非逐条建账。


代表:id 包括 `fal-ai/wan/v2.2-a14b/text-to-image/lora`, `fal-ai/z-image/base/lora`, `fal-ai/z-image/turbo/lora`, `fal-ai/z-image/turbo/tiling/lora`, `fal-ai/ernie-image/lora`, `fal-ai/ernie-image/lora/turbo`, `fal-ai/flux-2/klein/4b/base/lora`, `fal-ai/flux-2/klein/4b/lora`, `fal-ai/flux-2/klein/9b/base/lora`, `fal-ai/flux-2/klein/9b/lora`, `fal-ai/flux-2-lora-gallery/ballpoint-pen-sketch`, `fal-ai/flux-2-lora-gallery/digital-comic-art`, `fal-ai/flux-2-lora-gallery/hdr-style`, `fal-ai/flux-2-lora-gallery/realism`, `fal-ai/flux-2-lora-gallery/satellite-view-style`, `fal-ai/flux-2-lora-gallery/sepia-vintage`, `fal-ai/flux-2/lora`, `fal-ai/flux-general`, `fal-ai/flux-kontext-lora/text-to-image`, `fal-ai/flux-krea-lora` …

**② 社区/无名实验室(39 条)** —— 多为早期 SDXL / ControlNet / Fooocus 生态遗物,商业价值与稳定性不足,不建议接入。

代表:id 包括 `fal-ai/aura-flow`, `fal-ai/bagel`, `fal-ai/bitdance`, `fal-ai/boogu-image`, `fal-ai/cogview4`, `fal-ai/dreamshaper`, `fal-ai/emu-3.5-image/text-to-image`, `fal-ai/fast-fooocus-sdxl/image-to-image`, `fal-ai/fast-lightning-sdxl`, `fal-ai/fast-sdxl`, `fal-ai/fast-sdxl-controlnet-canny`, `fal-ai/fooocus`, `fal-ai/fooocus/image-prompt`, `fal-ai/fooocus/inpaint`, `fal-ai/fooocus/upscale-or-vary`, `fal-ai/glm-image`, `fal-ai/hidream-o1-image/dev`, `fal-ai/illusion-diffusion`, `fal-ai/janus`, `fal-ai/kolors` …

---


## 附:对接实现的几点前置认知(供你权衡「接多少」时参考)


1. **没有自动 manifest**:`fal_models.py` 是逐条手写的能力字典,不存在「读 schema 自动上线」的快捷方式。每接一条 = 手写一条能力元数据 + 双向 ID 映射 + 文档归档 + 定价录入 + 前端可见性裁决。

2. **入参异构严重**:同样是「画幅」,Flux 用命名档(`landscape_4_3`…),Google/xAI 用比例串(`16:9`…),OpenAI 用像素串(`1024x1024`…),Z-Image 用白名单像素。我们的统一适配层([[testable-import-seams]])已具备容纳多种 `*_FIELD` 的能力,但仍需为新成员逐一定义。

3. **出参相对收敛**:绝大部分返回 `images[](url[,content_type][,file_name])` + 可选 `seed`/`timings`/`has_nsfw_concepts`/`prompt`/`description`/`revised_prompt`。规范化压力小于入参。

4. **proxy vs serverless**:同为旗舰,proxy 类(如 Flux Pro/Kontext、Recraft、Google Nano Banana、ByteDance Seedream)走第三方路由,首发可能冷启动;serverless 类(Flux schnell/dev、Z-Image、Stability、Bria、HiDream)延迟更可控。对用户体验而言,前者需要在 UI 上容忍更长等待或在后端预热。

5. **价格梯度极大**:从 \$0.003/图(FLUX schnell)到 \$0.15+/图(Nano Banana Pro、高质量 GPT Image)再到按 megapixel/token 计费,跨度近 50 倍。「接哪些」本质上也是在划定你愿意承担的积分定价区间。


