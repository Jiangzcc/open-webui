# 阿里文生图 13 条接入设计

> **状态**:设计稿,待用户审阅。审阅通过后移交 writing-plans 产出 TDD 实施计划。
> **日期**:2026-07-25。
> **作者**:主代理(与用户 brainstorming 共创)。
> **范围**:将 fal.ai 阿里巴巴旗下 13 个文生图旗舰模型接入 Open WebUI 图片页,含后端能力元数据、积分定价、前端两级菜单下拉。

## 1. 目标与非目标

### 目标
- 接入 13 条阿里旗舰文生图(清单见 §3.1),使其在图片页可选择、可生成、可计费、可入库。
- 积分定价按 $0.005 = 1 积分 配置,ceil 自然取整。
- 模型下拉从平铺改为两级菜单(品牌 + logo / 模型),响应式支持桌面与移动。
- 单张模型隐藏张数选择器;proxy 模型提示"可能较慢"。

### 非目标(YAGNI 边界)
- **不接 LoRA**:`qwen-image`、`qwen-image-2512/lora` 暴露的 `loras` 入参不开放,请求时不传,走默认 `[]`。`qwen-image-2512/lora` 作为普通 2512 接入。
- **不接 tiling**:`fal-ai/z-image/turbo/tiling` 整条不进注册表(身兼文生图与无缝贴图编辑,本期略)。
- **不接 4 条 derivative LoRA 变体**(`qwen-image-2512/lora` 除外,它被视为 2512 同款):`wan/v2.2-a14b/.../lora`、`z-image/base/lora`、`z-image/turbo/lora`、`z-image/turbo/tiling/lora` 不接。
- **不改 credits 引擎代码**:13 条定价是运行时数据,经管理后台录入;引擎零改动。
- **不开放 wan v2.2 的扩散旋钮**(guidance_scale/shift/num_inference_steps):走 fal 默认。理由:`CreateImageForm` 无 guidance/shift 字段,`_set_integer_fields` 滤 float;开放需改表单+setter+前端,成本与普通用户场景收益不匹配。
- **不做出参额外字段留存**:`timings/seed/has_nsfw_concepts/generated_text/actual_prompt` 丢弃,只取 url(保持现状)。
- **不预热 proxy**:仅 UI 提示,后端不新增定时任务。
- **不做品牌 logo 兜底**:无自备 logo 的厂商不上线该品牌。

### 遗留备忘:per-megapixel 计费维度缺口
用户指出 credits 引擎缺少真正的 per-megapixel(按输出百万像素连续计费)维度。当前 z-image/turbo 与本期 qwen-image-2512 均用 `exact_map(key='size')` 离散近似(每档尺寸一个倍率),非连续兆帕计费。
**决定**:此项**单独立项**(独立 spec → plan → 实施),不纳入本批次。本批 credits 引擎零代码改动;qwen-2512 暂用 exact_map;未来独立立项完成后,qwen-2512 与 z-image/turbo 平滑迁移到真正的 per-megapixel 维度(届时为纯定价数据迁移,不动本批代码)。

## 2. 接入链路与代码事实(已勘查)

13 条新品沿现有四层管线"填料式"扩展,前三层代码零改动(数据驱动):

```
前端 Images.svelte (两级菜单选模型+尺寸+张数)
   │  发 {model(public_id), prompt, size, n, ...}
   ▼
routers/images.py → credits image_adapter._prepare
   │  normalize → resolve_provider_model(public_id→internal) → dimensions → billing context
   ▼
fal.build_fal_image_payload(CreateImageForm, internal_model)
   │  按 model_info 的 count_field/custom_size_field/option_fields 拼 payload
   ▼
fal.run_fal_queue → extract_fal_image_urls → 作品库 capture
```

### 关键代码事实
- **`build_fal_image_payload` 的 `form_data` 是 `routers/images.py:CreateImageForm`**(Pydantic),非 `CompatImageInput`。带前端全部字段;`_get_field_value` 用 getattr 直取。
- **`CreateImageForm` 已有字段**:`seed(int)`、`negative_prompt`、`enable_safety_checker`、`enable_prompt_expansion`、`acceleration`、`output_format`、`steps(int,作 num_inference_steps 的 source)`、`safety_tolerance`、`thinking_level`、`enable_web_search`、`quality`、`background`、`system_prompt`。
- **`CreateImageForm` 无字段**:`guidance_scale`、`shift`、`num_inference_steps`(靠 steps+source 映射)、`enable_output_safety_checker`(实施时核对,若需则补)。
- **`_set_integer_fields` 严 `isinstance(value,int)`**,float 被滤 → guidance/shift 无法经此通路(故 wan v2.2 不开放)。
- **`_safe_image_size`(fal.py:120)**:白名单校验 `value not in sizes.values()` 严格匹配;`"1024x768"` 解析为 `{'width':1024,'height':768}` 发给 fal。fal OpenAPI 确认 13 条均接受 `{width,height}` 对象。
- **`count_field` 动态**(fal.py:346):`model_info.get('count_field','num_images')`,按模型 dict 决定发 `num_images`/`max_images`/不发。异构 count 已被架构吸收。
- **`extract_fal_image_urls`(fal.py:482)**:兼容 `images[]`/`image`(单数)/`url`;item 可为 str 或 `{url}`。出参三态无碍。
- **`MAX_IMAGE_COUNT=100`**(constants.py:39):wan v2.7 的 5 张完全合规。
- **`resolve_provider_model`(compat.py:367)**:对 fal,`requested` 经 `normalize_fal_image_model_id` 翻 internal_id;`resource_id == transport_model == model`。`validate_provider_resolution` 要求 ≤128 字符(13 条最长 39,无忧)。**接入通行证 = 进入 `_FAL_INTERNAL_TO_PUBLIC_ID`**。
- **`public_fal_image_models`(fal_models.py:581)**:投影 `_FAL_PUBLIC_MODEL_FIELDS` 白名单下发前端,自动剥内部字段、提升 quality_options。
- **`_dimensions`(image_adapter.py:205)**:产出 context key = `{size, resolution, aspect_ratio, quality, image_count}`,均为字符串/int。无"兆帕"数值 key → per-megapixel 只能 exact_map 离散(见 §4.3 与 §1 遗留备忘)。
- **定价引擎**(pricing.py):`charged_credits = ceil(base_price × ∏ 倍率)`,min 1。`base_price` 即积分单位,无 USD 汇率层。`$0.005=1 积分` 靠配 base_price 时人工换算。

## 3. 后端能力元数据

### 3.1 13 条清单

| # | internal id | public id | 模板 | hosting | $口径 | base_price | count_field | image_counts |
|---|---|---|---|---|---|---|---|---|
| 1 | fal-ai/qwen-image | qwen-image | A | serverless | $0.02/图 | 4 | num_images | [1,2,3,4] |
| 2 | fal-ai/qwen-image-2512 | qwen-image-2512 | A | serverless | $0.02/MP | 1(exact_map) | num_images | [1,2,3,4] |
| 3 | fal-ai/qwen-image-2512/lora | qwen-image-2512-lora | A | serverless | $0.035/图 | 7 | num_images | [1,2,3,4] |
| 4 | fal-ai/z-image/base | z-image-base | A | serverless | $0.01/图 | 2 | num_images | [1,2,3,4] |
| 5 | fal-ai/qwen-image-2/text-to-image | qwen-image-2 | B | proxy | $0.035/图 | 7 | num_images | [1,2,3,4] |
| 6 | fal-ai/qwen-image-2/pro/text-to-image | qwen-image-2-pro | B | proxy | $0.075/图 | 15 | num_images | [1,2,3,4] |
| 7 | fal-ai/qwen-image-max/text-to-image | qwen-image-max | B | proxy | $0.075/图 | 15 | num_images | [1,2,3,4] |
| 8 | fal-ai/wan/v2.2-5b/text-to-image | wan-2.2-5b | C | serverless | $0.016/图 | 3.2 | None | [1] |
| 9 | fal-ai/wan/v2.2-a14b/text-to-image | wan-2.2-a14b | C | serverless | $0.025/图 | 5 | None | [1] |
| 10 | wan/v2.6/text-to-image | wan-2.6 | C | proxy | $0.03/图 | 6 | max_images | [1,2,3,4,5] |
| 11 | fal-ai/wan/v2.7/text-to-image | wan-2.7 | C | proxy | $0.03/图 | 6 | num_images | [1,2,3,4,5] |
| 12 | fal-ai/wan/v2.7/pro/text-to-image | wan-2.7-pro | C | proxy | $0.075/图 | 15 | num_images | [1,2,3,4,5] |
| 13 | fal-ai/wan-25-preview/text-to-image | wan-2.5-preview | C | proxy | $0.05/图 | 10 | num_images | [1,2,3,4] |

### 3.2 三个工厂模板

**模板 A — 复用 `_alibaba_model`**(4 条:qwen-image/2512/2512-lora/z-image-base)
现有签名 `_alibaba_model(id, name, resolutions, default_resolution)`,硬编码 `steps 1-8`、`enable_safety_checker` 默认 False、`enable_prompt_expansion` 默认 False、`acceleration` 默认 'regular'、无 `hosting`。需扩为:
```python
def _alibaba_model(id, name, resolutions, default_resolution, *,
                   hosting='serverless', steps_max=8,
                   safety_default=False, prompt_expansion_default=False):
```
- `hosting` 产出 `'hosting': hosting`。
- `steps_max`:`_integer_field('num_inference_steps','steps',1,steps_max)`(qwen-image 250、2512/base 50、turbo 8)。
- `safety_default`:qwen-image 系默认 True,z-image/turbo 默认 False。
- `prompt_expansion_default`:按模型差异(qwen-image-2512 默认 False,qwen-image 默认 False——实施时按 llms.txt 核对各条)。
- `resolutions` 用 `FAL_ALIBABA_NAMED_SIZES`;`image_size_whitelist = {s:s for s in FAL_ALIBABA_NAMED_SIZES}`。
- `acceleration` 沿用现有(qwen-image 系有,z-image/base 亦有)。
- **向后兼容**:新增参数均 keyword-only 且有默认值,现有 `z-image/turbo` 调用不传这些参数时行为不变(safety False/prompt_expansion False/steps 1-8/hosting serverless)——需 TDD 断言 z-image/turbo 旧行为不回归。

**模板 B — `_alibaba_qwen2_model`**(3 条:qwen-image-2/-2-pro/-max)
```python
def _alibaba_qwen2_model(id, name, default_image_size, hosting):
    return {
        **_base_model(id, name, 'alibaba', 'text-to-image'),
        'resolutions': FAL_ALIBABA_NAMED_SIZES,
        'default_resolution': default_image_size,
        'image_size_whitelist': {s: s for s in FAL_ALIBABA_NAMED_SIZES},
        'output_formats': FAL_OUTPUT_FORMATS, 'default_output_format': 'png',
        'custom_size_field': 'image_size',
        'count_field': 'num_images', 'image_counts': [1,2,3,4],
        'hosting': hosting,
        'boolean_fields': [_boolean_field('sync_mode'),
                           _boolean_field('enable_safety_checker', True),
                           _boolean_field('enable_prompt_expansion', True)],
        'integer_fields': [_integer_field('seed')],
    }
```

**模板 C — `_alibaba_wan_model`**(6 条:wan v2.2-5b/a14b/v2.6/v2.7/v2.7-pro/wan-2.5)
```python
def _alibaba_wan_model(id, name, default_image_size, hosting,
                       count_field, image_counts, output_formats,
                       prompt_expansion_default=True):
    booleans = [_boolean_field('sync_mode'),
                _boolean_field('enable_safety_checker', True),
                _boolean_field('enable_prompt_expansion', prompt_expansion_default)]
    return {
        **_base_model(id, name, 'alibaba', 'text-to-image'),
        'resolutions': FAL_ALIBABA_NAMED_SIZES,
        'default_resolution': default_image_size,
        'image_size_whitelist': {s: s for s in FAL_ALIBABA_NAMED_SIZES},
        'output_formats': output_formats,
        'default_output_format': output_formats[0] if output_formats else 'png',
        'custom_size_field': 'image_size',
        'count_field': count_field, 'image_counts': image_counts,
        'hosting': hosting,
        'boolean_fields': booleans,
        'integer_fields': [_integer_field('seed')],
    }
```
> `count_field=None` 用于 v2.2(固 1 张,不发 count);`image_counts=[1]` 让前端隐藏张数选择器。
> ~~`has_output_safety_checker`~~ **已移除**:`enable_output_safety_checker` 不在 `CreateImageForm`(已核实,仅 `enable_safety_checker`/`enable_prompt_expansion` 在),该布尔发不出,故模板 C 不暴露此字段,wan v2.2 走 fal 默认。
> `prompt_expansion_default`:v2.2 为 False,其余 True。
> `output_formats`:v2.2 `['jpeg','png']`;v2.7/v2.7-pro `FAL_OUTPUT_FORMATS`;v2.6/wan-2.5 `[]`(不暴露)。

### 3.3 新常量

```python
FAL_ALIBABA_NAMED_SIZES = [
    '1280x720',   # landscape_16_9
    '1024x768',   # landscape_4_3
    '720x1280',   # portrait_16_9
    '768x1024',   # portrait_4_3
    '1024x1024',  # square
    '512x512',    # square_hd
]
```
13 条共享。前端 UI 给用户选人脑比例,后端按 `default_resolution` 兜底,`_safe_image_size` 转 `{width,height}` 发 fal。

### 3.4 `_FAL_INTERNAL_TO_PUBLIC_ID` 追加 13 条

```python
'fal-ai/qwen-image': 'qwen-image',
'fal-ai/qwen-image-2512': 'qwen-image-2512',
'fal-ai/qwen-image-2512/lora': 'qwen-image-2512-lora',
'fal-ai/z-image/base': 'z-image-base',
'fal-ai/qwen-image-2/text-to-image': 'qwen-image-2',
'fal-ai/qwen-image-2/pro/text-to-image': 'qwen-image-2-pro',
'fal-ai/qwen-image-max/text-to-image': 'qwen-image-max',
'fal-ai/wan/v2.2-5b/text-to-image': 'wan-2.2-5b',
'fal-ai/wan/v2.2-a14b/text-to-image': 'wan-2.2-a14b',
'wan/v2.6/text-to-image': 'wan-2.6',
'fal-ai/wan/v2.7/text-to-image': 'wan-2.7',
'fal-ai/wan/v2.7/pro/text-to-image': 'wan-2.7-pro',
'fal-ai/wan-v2.5/text-to-image': 'wan-2.5-preview',
```

### 3.5 `_FAL_PUBLIC_MODEL_FIELDS` 白名单加 `hosting`

```python
_FAL_PUBLIC_MODEL_FIELDS = {
    ..., 'image_input_max_count', 'quality_options', 'default_quality',
    'hosting',  # 新增
}
```
前端 `ImageGenerationModel` 类型对应加 `hosting?: string`。

## 4. 积分定价

### 4.1 汇率与取整
- `$0.005 = 1 积分`。`base_price = 美元价 ÷ 0.005`(原值,可小数)。
- `charged_credits = ceil(base_price × ∏ 倍率)`,min 1(pricing.py 现有)。
- 小额模型(如 wan v2.2 $0.016→3.2)ceil 自然溢价,接受。

### 4.2 per-image 模型(12 条)
结构:`base_price = $/0.005`,`dimensions = [quantity(key='image_count')]`。
```jsonc
{
  "service_type": "image", "resource_id": "<internal_id>", "action": "text-to-image",
  "base_price": "<N>",
  "rules": { "schema_version": 1, "dimensions": [
    { "key": "image_count", "kind": "quantity" }
  ]}
}
```
> `quantity` 倍率 = 张数,故 `base_price × image_count` = 单张 × 张数。`image_count` 与 `_dimensions` 产的 context key 对齐。
> wan v2.2 两款 `image_counts=[1]`,quantity 倍率恒 1,计费 = ceil(base_price)。

12 条 base_price:qwen-image 4 / 2512-lora 7 / wan-2.2-5b 3.2 / wan-2.2-a14b 5 / z-image-base 2 / qwen-image-2 7 / qwen-image-2-pro 15 / qwen-image-max 15 / wan-2.5-preview 10 / wan-2.6 6 / wan-2.7 6 / wan-2.7-pro 15。

### 4.3 per-megapixel 模型(1 条:qwen-image-2512)
结构:`base_price=1`,`exact_map(key='size', values={<像素串>:<倍率>})`。
```jsonc
{
  "service_type": "image", "resource_id": "fal-ai/qwen-image-2512", "action": "text-to-image",
  "base_price": "1",
  "rules": { "schema_version": 1, "dimensions": [
    { "key": "size", "kind": "exact_map", "values": {
      "default": 4,
      "512x512": 4, "1024x1024": 4, "1024x768": 4, "768x1024": 4, "1280x720": 4, "720x1280": 4
    }}
  ]}
}
```
> 六档均 ≤1MP,ceil 兆帕 = 1,×4 积分 = 4。`default=4` 为 exact_map 校验所需(admintool 校验要求 values 含 'default'),白名单封闭故 default 实不命中。
> 此为 discrete 近似(见 §1 遗留备忘),未来 per-megapixel 维度立项后迁移。

### 4.4 录入方式
- **不在代码种子**(遵循惯例,credits 引擎零代码改动,定价是运行时数据)。
- 经管理后台逐条 POST `createCreditPrice`,13 条 = 13 次。
- `resource_id` 必须用**内部 id**(如 `fal-ai/qwen-image`),非 public id——credits 用 internal 计费。
- 可选:写一次性 seed 脚本 `backend/open_webui/extensions/credits/seed_alibaba_prices.py`,作为 admin 录入 SOP;是否纳入由用户定。

> ⚠️ **【2026-07-25 更新·本条已废弃】** 该 seed 脚本已于当日从仓库删除。实际录入遵照本节主线(第 227–229 行):经管理后台逐条 `POST /api/v1/credits/admin/prices` 完成,13 条已全部入库(enabled=true)。脚本被弃用的技术与流程原因见 plan 文档 Task 12 顶部公告。本文保留下方历史原文不作改写。

## 5. 前端

### 5.1 模型下拉:两级菜单
- **现状**:`showModelSelector` 触发单层 listbox,`{#each models}` 平铺。
- **改造**:展开后双栏。
  - 左栏(品牌级):按 `model.provider` 分组,每行 = logo `<img src="/assets/vendors/{provider}.webp" class="size-4">` + 品牌名。点击选中品牌。
  - 右栏(模型级):`{#each models.filter(m => m.provider === selectedVendor)}`,每行 = 模型名 + proxy tooltip。`selectModel(model.id)` 选中并关闭。
  - **始终两级**,无双模态分支。
- **键盘**:左栏 ↑↓ 选品牌,→ 进右栏,↑↓ 选模型,Enter 确认,Esc 关闭。role="listbox"/"option" 沿用。
- **窄屏(<640px)**:左右栏**上下堆叠**——品牌栏在上(横向滚动 chips),模型栏在下(纵向列表)。不做 drill-down,无额外状态。
- 新增状态:`selectedVendor: string`(默认第一个品牌)。

### 5.2 品牌 logo
- 资产已位于 `static/assets/vendors/*.webp`(16 枚,含 alibaba=qwen 别名,96×96,均值 <1KB)。
- 渲染:`<img src={`/assets/vendors/${provider}.webp`} alt={vendorName} class="size-4 rounded-sm" />`。
- `VENDOR_LABELS: Record<string,string>`(alibaba→Alibaba, google→Google, openai→OpenAI, xai→xAI),带 i18n key。
- 无 logo 的厂商不上线下拉(前置校验)。本期只 Alibaba,alibaba.webp 已在。
- **版权备注**:logo 归各厂商,取自 fal 平台公开 CDN(fal.ai/explore/labs),用于本产品模型下拉的指示性标识,属合理使用惯例;如涉商业化/合规审查需法务再评。

### 5.3 单张模型隐藏张数选择器
- 张数选择器渲染处外包 `{#if capability.imageCounts.length > 1}`。
- `imageCounts=[1]`(wan v2.2)→ 不渲染,`imageCount` 保 1。
- `imageCounts=[1,2,3,4,5]`(wan v2.7)→ 正常 5 选项。
- `getImageModelCapability`(image-generation.ts:405)已支持 `imageCounts` 字段,无需改。

### 5.4 proxy 提示
- `ImageGenerationModel` 加 `hosting?: string`(§3.5)。
- 模型 option 右侧,若 `model.hosting === 'proxy'`,显示小时钟图标 + Tooltip「首张可能较慢」。
- i18n key `proxyHostingSlowHint`(en-US 空,zh-CN「首张可能较慢」)。

### 5.5 i18n 新增键(zh-CN 补齐,en-US 空串回落)
| key | zh-CN |
|---|---|
| vendor.alibaba | 阿里巴巴 |
| vendor.google | 谷歌 |
| vendor.openai | OpenAI |
| vendor.xai | xAI |
| proxyHostingSlowHint | 首张可能较慢 |
| selectVendor | 选择品牌 |

### 5.6 前端测试(Vitest)
- `image-generation.test.ts`(扩):`getImageModelCapability` 对 13 条返回正确 imageCounts/aspects/resolutions。
- `images-dropdown.test.ts`(新增,纯函数):`groupByVendor(models)`、`vendorLogoUrl(provider)`、`isProxyModel(model)`。
- Svelte markup 渲染不测(脆弱,靠手动+集成)。

## 6. 文档归档
- `docs/fal/alibaba/` 下为 13 条各建一篇接口文档(沿袭现有 22 条体例,源自各自 llms.txt)。
- 文档含:endpoint、model id、入参 schema、出参 schema、价位、能力差异备注。

## 7. 错误处理与边界
- **后端**:13 条不引入新错误路径,所有边界已被现有防线覆盖(size 不在白名单→走默认;count 超域→不发;image_count>100→拒;proxy 超时→报错;id 未登记→拒;定价未配→拒)。
- **前端**:无 logo 的厂商不下拉;选中品牌模型空→空提示;报价失败→badge 失败态不阻断输入。
- **数据一致性**:`FAL_IMAGE_MODELS` 与 `_FAL_INTERNAL_TO_PUBLIC_ID` 双侧同步(TDD 覆盖);`image_size_whitelist` 统一用 `FAL_ALIBABA_NAMED_SIZES`;定价 `resource_id` ∈ 注册表 id 集合(TDD 断言)。

## 8. 测试策略(TDD,先红后绿)
### 后端 pytest(定向)
- `test_fal_models.py`:13 条注册;双向映射闭合;每条有 hosting/custom_size_field/image_size_whitelist(六档);count_field 与 image_counts 匹配。
- `test_fal.py`:`build_fal_image_payload` 对 qwen-image-2(num_images)、wan v2.6(max_images)、wan v2.2(不发 count)、qwen-image(image_size→{w,h})的 payload 形态。
- `test_public_image_models.py`:13 条下发含 hosting;public_id 正确;z-image-turbo 不回归。
- credits 定价**不纳自动化测试**(运行时数据,录入 SOP 即可)。

### 前端 Vitest
- 见 §5.6。

### 验证命令(新鲜证据)
- 后端:`python -m pytest backend/open_webui/utils/images/test_fal_models.py backend/open_webui/utils/images/test_fal.py backend/open_webui/extensions/credits/tests/test_public_image_models.py -q`
- 前端:`npm run test -- image-generation images-dropdown`
- 类型:`npm run check`(改动文件路径筛选 0 诊断)
- 格式:`npx prettier --check <改动文件>`
- 编译:`python -m compileall backend/open_webui/utils/images/fal_models.py`

### 浏览器运行时验收
- `npm run dev`(5173)+ 后端(8080)。
- 桌面 + 移动窄屏各一:
  - 下拉两级菜单,品牌 logo 可见,切换品牌模型列表随之变;窄屏上下堆叠。
  - 选 wan v2.2 → 张数选择器消失;选 wan v2.7 → 1-5;选 qwen-image-2(proxy)→ tooltip「可能较慢」。
  - 生成一张 qwen-image,Network 无 `fal-ai/`(公开 id 隔离),作品库出现该图。
  - 报价 badge 显示 4 积分(qwen-image 一张)。

## 9. 已落实的实施细节(pre-plan 勘查)
- `_alibaba_model` 现签名 `(id, name, resolutions, default_resolution)`,硬编码 steps 1-8/safety False/prompt_expansion False。扩为 keyword-only 参数 `hosting='serverless', steps_max=8, safety_default=False, prompt_expansion_default=False`,向后兼容 z-image/turbo(TDD 断言不回归)。
- `enable_output_safety_checker` **不在** `CreateImageForm`(已核实,仅有 enable_safety_checker/enable_prompt_expansion)。模板 C 不暴露此字段,wan v2.2 走 fal 默认。
- `enable_prompt_expansion` 在 `CreateImageForm`(line 503),通路 OK。
- 前端张数选择器 each 块在 `Images.svelte:1062`(`{#each imageCountOptions as count}`,外层 section 在 1056,“Quantity” 标题 1059);触发按钮在 958-961(显示 `{imageCount}`)。两处均需 `{#if imageCountOptions.length > 1}` 守卫包裹。reactive 守卫已在 163-169(切换模型时重置 imageCount)。

## 10. 约束遵守
- 不用 worktree;不由子智能体做 code review;未经用户明确要求不 commit。
- 二开后端优先 `extensions/`,本期 credits 零代码改动,只动 `fal_models.py`(utils/images,已属二开桥接层)。
- 不改上游原表/迁移。
- UI 响应式(桌面+移动),关键操作支持触屏+键盘,语义化+ARIA。
- i18n 补齐简体中文。
- 新鲜验证证据后方可声称完成。
