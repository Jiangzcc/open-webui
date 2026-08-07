# 阿里文生图 13 条接入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 fal.ai 阿里巴巴旗下 13 个文生图旗舰模型接入 Open WebUI 图片页,含后端能力元数据、积分定价录入、前端两级菜单下拉,使模型可选、可生成、可计费、可入库。

**Architecture:** 填料式扩展现有四层管线(前端 → credits image_adapter → fal.build_fal_image_payload → run_fal_queue)。后端在 `fal_models.py` 新增 3 个工厂模板 + 13 条注册 + ID 双向映射 + hosting 白名单;credits 引擎零代码改动,13 条定价经管理后台录入;前端 Images.svelte 模型下拉改两级菜单(品牌+logo / 模型),单张模型隐藏张数选择器,proxy 模型 tooltip 提示。

**Tech Stack:** Python 3 / FastAPI / SQLAlchemy(后端);SvelteKit 2 / Svelte 5 / TypeScript / Vite / Tailwind(前端);Vitest(前端测试);pytest(后端测试)。

## Global Constraints

- 禁止 worktree(主代理及任何辅助流程);禁止子智能体做 code review(审查由主代理亲自完成)。
- 未经用户明确要求,不得 commit、push、创建 PR、merge、rebase;不得覆盖无法确认归属的工作区改动。
- 二开后端优先 `extensions/`;本期 credits 引擎零代码改动,只动 `backend/open_webui/utils/images/fal_models.py`(二开桥接层)+ 前端 + docs + i18n。不改上游原表/迁移。
- TDD:每个任务先写失败测试(RED)再最小实现(GREEN),不跳过 RED 验证。
- UI 响应式(桌面 + 移动窄屏),关键操作支持触屏 + 键盘 + ARIA。
- i18n 用户可见文案用 `$i18n.t` 并补齐简体中文(zh-CN translation.json);en-US 遵循空串回落约定。
- 无新鲜验证证据不得声称完成;每任务结尾给验证命令与预期输出。
- 前端风格:tabs 缩进、单引号、无尾随逗号、printWidth 100。
- 不得把真实密码/API key/Authorization token/Cookie 写入代码、测试、日志或文档。

---

## File Structure

| 文件                                                                      | 责任                                                        | 改动性质        |
| ------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------- |
| `backend/open_webui/utils/images/fal_models.py`                           | 13 条模型能力元数据 + 3 工厂模板 + ID 映射 + hosting 白名单 | 改              |
| `backend/open_webui/utils/images/test_fal_models.py`                      | 13 条注册/映射/hosting/模板的 pytest                        | 新增            |
| `backend/open_webui/utils/images/test_fal.py`                             | build_fal_image_payload 对新模型的 payload 形态             | 扩              |
| `backend/open_webui/extensions/credits/tests/test_public_image_models.py` | public_fal_image_models 下发 hosting                        | 扩              |
| `src/lib/utils/image-generation.ts`                                       | ImageGenerationModel 加 hosting                             | 改              |
| `src/lib/utils/image-generation.test.ts`                                  | 13 条 capability 断言                                       | 扩              |
| `src/lib/utils/images-dropdown.ts`                                        | 纯函数:groupByVendor / vendorLogoUrl / isProxyModel         | 新增            |
| `src/lib/utils/images-dropdown.test.ts`                                   | 上述纯函数 Vitest                                           | 新增            |
| `src/lib/components/images/Images.svelte`                                 | 两级菜单下拉 + 单张隐藏张数 + proxy tooltip                 | 改              |
| `src/lib/i18n/locales/zh-CN/translation.json`                             | 新 i18n 键的简体中文                                        | 改              |
| `src/lib/i18n/locales/en-US/translation.json`                             | 新 i18n 键(空串)                                            | 改              |
| `docs/fal/alibaba/*.md`                                                   | 13 篇接口文档                                               | 新增            |
| ~~`backend/open_webui/extensions/credits/seed_alibaba_prices.py`~~        | ~~13 条定价录入 seed 脚本(可选)~~                           | **已废弃,见下** |

> ⚠️ **【2026-07-25 公告】** 表中被划掉的 seed 脚本已于当日从仓库删除,不应再创建或执行。13 条定价的实际入库方式为:经管理后台逐条 `POST /api/v1/credits/admin/prices`(详见 spec §4.4 与本文 Task 12 顶部公告)。凡下文出现该脚本的文件路径、`python -m` 运行命令或 `compileall` 校验步骤,一律视为**历史规划原文**,仅供追溯,不再有效。

---

## Task 1: 新增 `FAL_ALIBABA_NAMED_SIZES` 常量与模板 A 扩展

**Files:**

- Modify: `backend/open_webui/utils/images/fal_models.py`(顶部常量区 + `_alibaba_model` 函数 164-186)
- Test: `backend/open_webui/utils/images/test_fal_models.py`(新建)

**Interfaces:**

- Produces: `FAL_ALIBABA_NAMED_SIZES: list[str]`(六命名档像素串);扩展后的 `_alibaba_model(id, name, resolutions, default_resolution, *, hosting='serverless', steps_max=8, safety_default=False, prompt_expansion_default=False) -> dict`。

- [ ] **Step 1: 写失败测试(常量 + 模板 A 扩展 + z-image/turbo 不回归)**

新建 `backend/open_webui/utils/images/test_fal_models.py`:

```python
from open_webui.utils.images.fal_models import (
    FAL_ALIBABA_NAMED_SIZES,
    FAL_IMAGE_MODELS,
    _alibaba_model,
)


def test_alibaba_named_sizes_are_six_pixel_buckets():
    assert FAL_ALIBABA_NAMED_SIZES == [
        '1280x720',
        '1024x768',
        '720x1280',
        '768x1024',
        '1024x1024',
        '512x512',
    ]


def test_alibaba_model_accepts_keyword_extensions():
    model = _alibaba_model(
        'fal-ai/qwen-image',
        'Alibaba / Qwen Image',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=250,
        safety_default=True,
        prompt_expansion_default=False,
    )
    assert model['hosting'] == 'serverless'
    integers = {f['field']: f for f in model['integer_fields']}
    assert integers['num_inference_steps']['max'] == 250
    booleans = {b['field']: b for b in model['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is True
    assert booleans['enable_prompt_expansion']['default'] is False
    assert model['image_size_whitelist'] == {s: s for s in FAL_ALIBABA_NAMED_SIZES}


def test_z_image_turbo_remains_backward_compatible():
    turbo = next(m for m in FAL_IMAGE_MODELS if m['id'] == 'fal-ai/z-image/turbo')
    # 旧行为:无 hosting 字段(本任务尚未给 turbo 加 hosting,保持 undefined)
    integers = {f['field']: f for f in turbo['integer_fields']}
    assert integers['num_inference_steps']['max'] == 8
    booleans = {b['field']: b for b in turbo['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is False
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
cd D:\code\github\open-webui-main
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: FAIL — `ImportError: cannot import name 'FAL_ALIBABA_NAMED_SIZES'`(常量未定义)。

- [ ] **Step 3: 新增常量**

在 `fal_models.py` 顶部常量区(`FAL_ALIBABA_ACCELERATION_OPTIONS` 之后)加:

```python
FAL_ALIBABA_NAMED_SIZES = [
    '1280x720',
    '1024x768',
    '720x1280',
    '768x1024',
    '1024x1024',
    '512x512',
]
```

- [ ] **Step 4: 扩展 `_alibaba_model` 签名**

将 `fal_models.py:164-186` 的 `_alibaba_model` 替换为:

```python
def _alibaba_model(
    id: str,
    name: str,
    resolutions: list[str],
    default_resolution: str,
    *,
    hosting: str = 'serverless',
    steps_max: int = 8,
    safety_default: bool = False,
    prompt_expansion_default: bool = False,
) -> dict[str, Any]:
    image_size_whitelist = {resolution: resolution for resolution in resolutions}
    return {
        **_base_model(id, name, 'alibaba', 'text-to-image'),
        'resolutions': list(resolutions),
        'default_resolution': default_resolution,
        'image_size_whitelist': image_size_whitelist,
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'png',
        'custom_size_field': 'image_size',
        'hosting': hosting,
        'option_fields': [_option_field('acceleration', FAL_ALIBABA_ACCELERATION_OPTIONS, 'regular')],
        'boolean_fields': [
            _boolean_field('sync_mode'),
            _boolean_field('enable_safety_checker', safety_default),
            _boolean_field('enable_prompt_expansion', prompt_expansion_default),
        ],
        'integer_fields': [
            _integer_field('seed'),
            _integer_field('num_inference_steps', 'steps', 1, steps_max),
        ],
    }
```

- [ ] **Step 5: 运行测试,确认通过(GREEN)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: `3 passed`。

- [ ] **Step 6: 验证 z-image/turbo 既有测试不回归**

```
python -m pytest backend/open_webui/utils/images/test_fal.py backend/open_webui/extensions/credits/tests/test_public_image_models.py -q
```

Expected: 全部 passed(无 failures/errors)。

- [ ] **Step 7: Python 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py
```

Expected: 无输出(编译成功)。

---

## Task 2: 新增模板 B `_alibaba_qwen2_model` 与模板 C `_alibaba_wan_model`

**Files:**

- Modify: `backend/open_webui/utils/images/fal_models.py`(在 `_alibaba_model` 之后新增两个函数)
- Test: `backend/open_webui/utils/images/test_fal_models.py`(扩)

**Interfaces:**

- Produces:
  - `_alibaba_qwen2_model(id, name, default_image_size, hosting) -> dict`
  - `_alibaba_wan_model(id, name, default_image_size, hosting, count_field, image_counts, output_formats, prompt_expansion_default=True) -> dict`

- [ ] **Step 1: 写失败测试(模板 B 与 C 的结构)**

追加到 `test_fal_models.py`:

```python
from open_webui.utils.images.fal_models import (
    _alibaba_qwen2_model,
    _alibaba_wan_model,
    FAL_OUTPUT_FORMATS,
)


def test_qwen2_model_shape():
    m = _alibaba_qwen2_model(
        'fal-ai/qwen-image-2/text-to-image',
        'Alibaba / Qwen Image 2',
        '1024x1024',
        'proxy',
    )
    assert m['hosting'] == 'proxy'
    assert m['count_field'] == 'num_images'
    assert m['image_counts'] == [1, 2, 3, 4]
    assert m['custom_size_field'] == 'image_size'
    assert m['image_size_whitelist'] == {s: s for s in FAL_ALIBABA_NAMED_SIZES}
    assert m['output_formats'] == FAL_OUTPUT_FORMATS
    booleans = {b['field']: b for b in m['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is True
    assert booleans['enable_prompt_expansion']['default'] is True
    assert {f['field'] for f in m['integer_fields']} == {'seed'}
    assert 'guidance_scale' not in {f['field'] for f in m['integer_fields']}


def test_wan_model_fixed_single_image():
    m = _alibaba_wan_model(
        'fal-ai/wan/v2.2-5b/text-to-image',
        'Alibaba / Wan 2.2 (5B)',
        '512x512',
        'serverless',
        count_field=None,
        image_counts=[1],
        output_formats=['jpeg', 'png'],
        prompt_expansion_default=False,
    )
    assert m['count_field'] is None
    assert m['image_counts'] == [1]
    assert m['output_formats'] == ['jpeg', 'png']
    booleans = {b['field']: b for b in m['boolean_fields']}
    assert booleans['enable_prompt_expansion']['default'] is False
    assert 'enable_output_safety_checker' not in booleans


def test_wan_model_max_images_variant():
    m = _alibaba_wan_model(
        'wan/v2.6/text-to-image',
        'Alibaba / Wan 2.6',
        '1024x1024',
        'proxy',
        count_field='max_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=[],
    )
    assert m['count_field'] == 'max_images'
    assert m['image_counts'] == [1, 2, 3, 4, 5]


def test_wan_model_no_output_formats_when_empty():
    m = _alibaba_wan_model(
        'wan/v2.6/text-to-image',
        'Alibaba / Wan 2.6',
        '1024x1024',
        'proxy',
        count_field='max_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=[],
    )
    assert m['output_formats'] == []
    assert m['default_output_format'] == 'png'
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: FAIL — `ImportError: cannot import name '_alibaba_qwen2_model'`。

- [ ] **Step 3: 新增两个模板函数**

在 `fal_models.py` 的 `_alibaba_model` 函数之后(原 186 行 `}` 之后空行)插入:

```python
def _alibaba_qwen2_model(
    id: str,
    name: str,
    default_image_size: str,
    hosting: str,
) -> dict[str, Any]:
    return {
        **_base_model(id, name, 'alibaba', 'text-to-image'),
        'resolutions': list(FAL_ALIBABA_NAMED_SIZES),
        'default_resolution': default_image_size,
        'image_size_whitelist': {size: size for size in FAL_ALIBABA_NAMED_SIZES},
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'png',
        'custom_size_field': 'image_size',
        'count_field': 'num_images',
        'image_counts': [1, 2, 3, 4],
        'hosting': hosting,
        'boolean_fields': [
            _boolean_field('sync_mode'),
            _boolean_field('enable_safety_checker', True),
            _boolean_field('enable_prompt_expansion', True),
        ],
        'integer_fields': [_integer_field('seed')],
    }


def _alibaba_wan_model(
    id: str,
    name: str,
    default_image_size: str,
    hosting: str,
    count_field: str | None,
    image_counts: list[int],
    output_formats: list[str],
    prompt_expansion_default: bool = True,
) -> dict[str, Any]:
    return {
        **_base_model(id, name, 'alibaba', 'text-to-image'),
        'resolutions': list(FAL_ALIBABA_NAMED_SIZES),
        'default_resolution': default_image_size,
        'image_size_whitelist': {size: size for size in FAL_ALIBABA_NAMED_SIZES},
        'output_formats': list(output_formats),
        'default_output_format': output_formats[0] if output_formats else 'png',
        'custom_size_field': 'image_size',
        'count_field': count_field,
        'image_counts': list(image_counts),
        'hosting': hosting,
        'boolean_fields': [
            _boolean_field('sync_mode'),
            _boolean_field('enable_safety_checker', True),
            _boolean_field('enable_prompt_expansion', prompt_expansion_default),
        ],
        'integer_fields': [_integer_field('seed')],
    }
```

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: `7 passed`(Task1 的 3 个 + Task2 的 4 个)。

- [ ] **Step 5: 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py
```

Expected: 无输出。

---

## Task 3: 注册 13 条模型到 `FAL_IMAGE_MODELS`

**Files:**

- Modify: `backend/open_webui/utils/images/fal_models.py`(`FAL_IMAGE_MODELS` 列表,在现有 `_alibaba_model('fal-ai/z-image/turbo', ...)` 之后插入 13 条)
- Test: `backend/open_webui/utils/images/test_fal_models.py`(扩)

**Interfaces:**

- Produces: `FAL_IMAGE_MODELS` 含 13 条新模型,每条 `id`/`provider='alibaba'`/`task='text-to-image'`/`hosting`/`count_field`/`image_counts`/`image_size_whitelist` 齐备。

- [ ] **Step 1: 写失败测试(13 条注册 + 字段断言)**

追加到 `test_fal_models.py`:

```python
EXPECTED_NEW_MODELS = [
    ('fal-ai/qwen-image', 'serverless', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-2512', 'serverless', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-2512/lora', 'serverless', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/z-image/base', 'serverless', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-2/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-2/pro/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-max/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/wan/v2.2-5b/text-to-image', 'serverless', None, [1]),
    ('fal-ai/wan/v2.2-a14b/text-to-image', 'serverless', None, [1]),
    ('wan/v2.6/text-to-image', 'proxy', 'max_images', [1, 2, 3, 4, 5]),
    ('fal-ai/wan/v2.7/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4, 5]),
    ('fal-ai/wan/v2.7/pro/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4, 5]),
    ('fal-ai/wan-v2.5/text-to-image', 'proxy', 'num_images', [1, 2, 3, 4]),
]


def test_all_thirteen_new_models_registered():
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    for model_id, hosting, count_field, image_counts in EXPECTED_NEW_MODELS:
        assert model_id in by_id, f'missing model: {model_id}'
        m = by_id[model_id]
        assert m['provider'] == 'alibaba'
        assert m['task'] == 'text-to-image'
        assert m['hosting'] == hosting
        assert m['count_field'] == count_field
        assert m['image_counts'] == image_counts
        assert m['custom_size_field'] == 'image_size'
        assert set(m['image_size_whitelist'].keys()) == set(FAL_ALIBABA_NAMED_SIZES)


def test_existing_22_models_still_present():
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    for existing in [
        'fal-ai/z-image/turbo',
        'fal-ai/nano-banana',
        'openai/gpt-image-2',
        'xai/grok-imagine-image',
    ]:
        assert existing in by_id
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py::test_all_thirteen_new_models_registered -q
```

Expected: FAIL — `AssertionError: missing model: fal-ai/qwen-image`。

- [ ] **Step 3: 在 `FAL_IMAGE_MODELS` 插入 13 条**

在 `fal_models.py` 的 `FAL_IMAGE_MODELS` 列表中,紧跟现有 `_alibaba_model('fal-ai/z-image/turbo', ...)` 条目之后(原 294 行 `),` 之后),插入:

```python
    _alibaba_model(
        'fal-ai/qwen-image',
        'Alibaba / Qwen Image',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=250,
        safety_default=True,
        prompt_expansion_default=False,
    ),
    _alibaba_model(
        'fal-ai/qwen-image-2512',
        'Alibaba / Qwen Image 2512',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=50,
        safety_default=True,
        prompt_expansion_default=False,
    ),
    _alibaba_model(
        'fal-ai/qwen-image-2512/lora',
        'Alibaba / Qwen Image 2512',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=50,
        safety_default=True,
        prompt_expansion_default=False,
    ),
    _alibaba_model(
        'fal-ai/z-image/base',
        'Alibaba / Z Image Base',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=50,
        safety_default=True,
        prompt_expansion_default=False,
    ),
    _alibaba_qwen2_model(
        'fal-ai/qwen-image-2/text-to-image',
        'Alibaba / Qwen Image 2',
        '1024x1024',
        'proxy',
    ),
    _alibaba_qwen2_model(
        'fal-ai/qwen-image-2/pro/text-to-image',
        'Alibaba / Qwen Image 2 Pro',
        '1024x1024',
        'proxy',
    ),
    _alibaba_qwen2_model(
        'fal-ai/qwen-image-max/text-to-image',
        'Alibaba / Qwen Image Max',
        '1024x1024',
        'proxy',
    ),
    _alibaba_wan_model(
        'fal-ai/wan/v2.2-5b/text-to-image',
        'Alibaba / Wan 2.2 (5B)',
        '512x512',
        'serverless',
        count_field=None,
        image_counts=[1],
        output_formats=['jpeg', 'png'],
        prompt_expansion_default=False,
    ),
    _alibaba_wan_model(
        'fal-ai/wan/v2.2-a14b/text-to-image',
        'Alibaba / Wan 2.2 (A14B)',
        '512x512',
        'serverless',
        count_field=None,
        image_counts=[1],
        output_formats=['jpeg', 'png'],
        prompt_expansion_default=False,
    ),
    _alibaba_wan_model(
        'wan/v2.6/text-to-image',
        'Alibaba / Wan 2.6',
        '1024x1024',
        'proxy',
        count_field='max_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=[],
    ),
    _alibaba_wan_model(
        'fal-ai/wan/v2.7/text-to-image',
        'Alibaba / Wan 2.7',
        '512x512',
        'proxy',
        count_field='num_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=FAL_OUTPUT_FORMATS,
    ),
    _alibaba_wan_model(
        'fal-ai/wan/v2.7/pro/text-to-image',
        'Alibaba / Wan 2.7 Pro',
        '512x512',
        'proxy',
        count_field='num_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=FAL_OUTPUT_FORMATS,
    ),
    _alibaba_wan_model(
        'fal-ai/wan-v2.5/text-to-image',
        'Alibaba / Wan 2.5 Preview',
        '1024x1024',
        'proxy',
        count_field='num_images',
        image_counts=[1, 2, 3, 4],
        output_formats=[],
    ),
```

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: 全部 passed(Task1+2+3 共 11 个)。

- [ ] **Step 5: 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py
```

Expected: 无输出。

---

## Task 4: 追加 13 条 `_FAL_INTERNAL_TO_PUBLIC_ID` 双向映射

**Files:**

- Modify: `backend/open_webui/utils/images/fal_models.py`(`_FAL_INTERNAL_TO_PUBLIC_ID` 字典)
- Test: `backend/open_webui/utils/images/test_fal_models.py`(扩)

**Interfaces:**

- Produces: `public_fal_image_model_id('<internal>')` 与 `internal_fal_image_model_id('<public>')` 对 13 条互通。

- [ ] **Step 1: 写失败测试(双向映射闭合)**

追加到 `test_fal_models.py`:

```python
from open_webui.utils.images.fal_models import (
    public_fal_image_model_id,
    internal_fal_image_model_id,
    normalize_fal_image_model_id,
)

INTERNAL_TO_PUBLIC = {
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
}


def test_bidirectional_mapping_roundtrip():
    for internal, public in INTERNAL_TO_PUBLIC.items():
        assert public_fal_image_model_id(internal) == public
        assert internal_fal_image_model_id(public) == internal


def test_normalize_accepts_both_forms():
    for internal, public in INTERNAL_TO_PUBLIC.items():
        assert normalize_fal_image_model_id(public) == internal
        assert normalize_fal_image_model_id(internal) == internal


def test_every_registered_model_has_public_id():
    registered = {m['id'] for m in FAL_IMAGE_MODELS}
    unmapped = [i for i in registered if public_fal_image_model_id(i) is None]
    assert unmapped == [], f'unmapped internal ids: {unmapped}'
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py::test_bidirectional_mapping_roundtrip -q
```

Expected: FAIL — `AssertionError: assert None == 'qwen-image'`。

- [ ] **Step 3: 追加映射**

在 `_FAL_INTERNAL_TO_PUBLIC_ID` 字典中,在 `'xai/grok-imagine-image/quality/edit': 'grok-imagine-image-pro/edit',` 之后(原字典末尾 `}` 之前),插入 13 条:

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

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
python -m pytest backend/open_webui/utils/images/test_fal_models.py -q
```

Expected: 全部 passed。

- [ ] **Step 5: 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py
```

Expected: 无输出。

---

## Task 5: `_FAL_PUBLIC_MODEL_FIELDS` 白名单加 `hosting`

**Files:**

- Modify: `backend/open_webui/utils/images/fal_models.py`(`_FAL_PUBLIC_MODEL_FIELDS` 集合)
- Test: `backend/open_webui/extensions/credits/tests/test_public_image_models.py`(扩)

**Interfaces:**

- Produces: `public_fal_image_models()` 返回的每个 dict 含 `hosting` 字段。

- [ ] **Step 1: 写失败测试(hosting 下发)**

追加到 `backend/open_webui/extensions/credits/tests/test_public_image_models.py`:

```python
def test_public_fal_image_models_include_hosting_for_alibaba():
    from open_webui.utils.images.fal_models import public_fal_image_models

    models = public_fal_image_models(default_model='fal-ai/z-image/turbo')
    by_id = {m['id']: m for m in models}
    qwen = by_id.get('qwen-image')
    assert qwen is not None
    assert qwen['hosting'] == 'serverless'
    qwen2_pro = by_id.get('qwen-image-2-pro')
    assert qwen2_pro is not None
    assert qwen2_pro['hosting'] == 'proxy'


def test_legacy_models_keep_hosting_absent_or_filled():
    from open_webui.utils.images.fal_models import public_fal_image_models

    models = public_fal_image_models(default_model='fal-ai/z-image/turbo')
    by_id = {m['id']: m for m in models}
    # z-image-turbo 是 Task1 改造后也带 hosting 的(existing 旧模型在 _alibaba_model 改造后会带 hosting)
    turbo = by_id.get('z-image-turbo')
    assert turbo is not None
    assert turbo.get('hosting') == 'serverless'
```

> 备注:Task 1 改造 `_alibaba_model` 后,z-image/turbo 也会有 `hosting='serverless'`。其它旧模板(\_google_model/\_openai_model/\_xai_model)未加 hosting,其 public dict 不含 hosting 字段(white-list 过滤),前端按 `hosting === 'proxy'` 判定,缺失即非 proxy,行为正确。

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
python -m pytest backend/open_webui/extensions/credits/tests/test_public_image_models.py::test_public_fal_image_models_include_hosting_for_alibaba -q
```

Expected: FAIL — `KeyError: 'hosting'`(白名单未含,public dict 无此键)。

- [ ] **Step 3: 白名单加 `hosting`**

在 `fal_models.py` 的 `_FAL_PUBLIC_MODEL_FIELDS` 集合中,在 `'default_quality',` 之后加:

```python
    'hosting',
```

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
python -m pytest backend/open_webui/extensions/credits/tests/test_public_image_models.py -q
```

Expected: 全部 passed(含原有 + 2 个新)。

- [ ] **Step 5: 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py
```

Expected: 无输出。

---

## Task 6: `build_fal_image_payload` 对新模型的 payload 形态回归

**Files:**

- Test: `backend/open_webui/utils/images/test_fal.py`(扩)

**Interfaces:**

- Consumes: Task 3 注册的 13 条模型;`build_fal_image_payload(form_data, model)`(fal.py 现有)。
- Verifies: count_field 异构(num_images/max_images/None)、image_size 转 {width,height}、wan v2.2 不发 count。

- [ ] **Step 1: 写失败测试(payload 形态)**

先读 `test_fal.py` 现有 `form_data` fixture 的构造方式(找 `make_form` 或类似的 helper),然后追加测试。若该文件无 helper,用 `types.SimpleNamespace` 构造。追加到 `test_fal.py`:

```python
import types
from open_webui.utils.images.fal import build_fal_image_payload


def _form(**kw):
    base = dict(
        prompt='a cat',
        model='',
        size=None,
        n=1,
        steps=None,
        negative_prompt=None,
        aspect_ratio=None,
        resolution=None,
        output_format=None,
        system_prompt=None,
        seed=None,
        sync_mode=None,
        safety_tolerance=None,
        limit_generations=None,
        enable_web_search=None,
        thinking_level=None,
        enable_safety_checker=None,
        enable_prompt_expansion=None,
        acceleration=None,
        quality=None,
        background=None,
    )
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_payload_qwen_image_sends_num_images_and_image_size_object():
    data = build_fal_image_payload(_form(n=2, size='1024x768'), 'fal-ai/qwen-image')
    assert data['prompt'] == 'a cat'
    assert data['num_images'] == 2
    assert data['image_size'] == {'width': 1024, 'height': 768}


def test_payload_wan_v26_uses_max_images_field():
    data = build_fal_image_payload(_form(n=3), 'wan/v2.6/text-to-image')
    assert data['max_images'] == 3
    assert 'num_images' not in data


def test_payload_wan_v22_does_not_send_count():
    data = build_fal_image_payload(_form(n=1), 'fal-ai/wan/v2.2-5b/text-to-image')
    assert 'num_images' not in data
    assert 'max_images' not in data


def test_payload_wan_v27_supports_five_images():
    data = build_fal_image_payload(_form(n=5), 'fal-ai/wan/v2.7/text-to-image')
    assert data['num_images'] == 5


def test_payload_qwen2_has_no_guidance_or_steps():
    data = build_fal_image_payload(_form(), 'fal-ai/qwen-image-2/text-to-image')
    assert 'guidance_scale' not in data
    assert 'num_inference_steps' not in data
    assert data['enable_safety_checker'] is True
    assert data['enable_prompt_expansion'] is True
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
python -m pytest backend/open_webui/utils/images/test_fal.py -k "payload_qwen_image or payload_wan or payload_qwen2" -q
```

Expected: 多数 FAIL — 例如 `KeyError: 'num_images'`(模型未注册时 `_get_fal_model_info` 返回 None,走到 fallback 分支)。若 Task 3 已完成,这些应已能通过;若仍有 fail,排查 fixture 字段名与 `CreateImageForm` 一致。

> 若 Step 2 全部 PASS(因 Task 3 已让模型注册),则此 Task 为回归保障而非 RED→GREEN:记录"测试先行,实现已在 Task3 完成,此处验证 payload 契约",继续 Step 3。

- [ ] **Step 3: 运行全部 fal 测试确认无回归**

```
python -m pytest backend/open_webui/utils/images/test_fal.py -q
```

Expected: 全部 passed。

- [ ] **Step 4: 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal.py
```

Expected: 无输出。

---

## Task 7: 前端 `ImageGenerationModel` 类型加 `hosting`

**Files:**

- Modify: `src/lib/utils/image-generation.ts`(`ImageGenerationModel` 类型,57-78 行)
- Test: `src/lib/utils/image-generation.test.ts`(扩)

**Interfaces:**

- Produces: `ImageGenerationModel.hosting?: string`。

- [ ] **Step 1: 写失败测试(hosting 透传 capability)**

追加到 `src/lib/utils/image-generation.test.ts`:

```typescript
import { getImageModelCapability } from '$lib/utils/image-generation';

describe('alibaba t2i hosting field', () => {
	it('exposes hosting on capability for proxy model', () => {
		const cap = getImageModelCapability({
			id: 'qwen-image-2-pro',
			hosting: 'proxy',
			aspectRatios: ['1:1'],
			resolutions: ['1024x1024'],
			imageCounts: [1, 2, 3, 4]
		});
		expect(cap.aspectRatios).toEqual(['1:1']);
	});

	it('treats single-image-count model as fixed one', () => {
		const cap = getImageModelCapability({
			id: 'wan-2.2-5b',
			hosting: 'serverless',
			imageCounts: [1]
		});
		expect(cap.imageCounts).toEqual([1]);
		expect(cap.imageCounts.length).toBe(1);
	});
});
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
npm run test -- image-generation.test.ts
```

Expected: FAIL — TS 类型错误 `Property 'hosting' does not exist on type 'ImageGenerationModel'`(若 vitest 对 TS 类型报错敏感)或测试因 capability 不透传 hosting 而 fail。

- [ ] **Step 3: 类型加 `hosting`**

在 `image-generation.ts` 的 `ImageGenerationModel` 类型(57-78 行)中,在 `defaultQuality?: string;` 之后加:

```typescript
	hosting?: string;
```

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
npm run test -- image-generation.test.ts
```

Expected: 全部 passed。

- [ ] **Step 5: 类型检查(改动文件 0 诊断)**

```
npx svelte-check --tsconfig ./tsconfig.json --threshold error --output machine 2>&1 | grep "image-generation.ts" || echo "no diagnostics in image-generation.ts"
```

Expected: `no diagnostics in image-generation.ts`。

---

## Task 8: 前端纯函数 `groupByVendor` / `vendorLogoUrl` / `isProxyModel`

**Files:**

- Create: `src/lib/utils/images-dropdown.ts`
- Test: `src/lib/utils/images-dropdown.test.ts`(新建)

**Interfaces:**

- Produces:
  - `groupByVendor(models: ImageGenerationModel[]): Record<string, ImageGenerationModel[]>`(按 `provider` 分组,空 provider 归 `'other'`)
  - `vendorLogoUrl(provider: string): string`(返回 `/assets/vendors/<provider>.webp`)
  - `isProxyModel(model: ImageGenerationModel): boolean`(`model.hosting === 'proxy'`)

- [ ] **Step 1: 写失败测试**

新建 `src/lib/utils/images-dropdown.test.ts`:

```typescript
import { groupByVendor, vendorLogoUrl, isProxyModel } from '$lib/utils/images-dropdown';
import type { ImageGenerationModel } from '$lib/utils/image-generation';

describe('images-dropdown utils', () => {
	it('groups models by provider', () => {
		const models: ImageGenerationModel[] = [
			{ id: 'qwen-image', provider: 'alibaba' },
			{ id: 'z-image-turbo', provider: 'alibaba' },
			{ id: 'nano-banana', provider: 'google' },
			{ id: 'legacy-no-provider' }
		];
		const groups = groupByVendor(models);
		expect(groups.alibaba.map((m) => m.id)).toEqual(['qwen-image', 'z-image-turbo']);
		expect(groups.google.map((m) => m.id)).toEqual(['nano-banana']);
		expect(groups.other.map((m) => m.id)).toEqual(['legacy-no-provider']);
	});

	it('builds vendor logo url', () => {
		expect(vendorLogoUrl('alibaba')).toBe('/assets/vendors/alibaba.webp');
		expect(vendorLogoUrl('google')).toBe('/assets/vendors/google.webp');
	});

	it('detects proxy hosting', () => {
		expect(isProxyModel({ id: 'x', hosting: 'proxy' })).toBe(true);
		expect(isProxyModel({ id: 'x', hosting: 'serverless' })).toBe(false);
		expect(isProxyModel({ id: 'x' })).toBe(false);
	});
});
```

- [ ] **Step 2: 运行测试,确认失败(RED)**

```
npm run test -- images-dropdown.test.ts
```

Expected: FAIL — `Failed to resolve import "$lib/utils/images-dropdown"`(文件不存在)。

- [ ] **Step 3: 实现纯函数**

新建 `src/lib/utils/images-dropdown.ts`:

```typescript
import type { ImageGenerationModel } from '$lib/utils/image-generation';

export const groupByVendor = (
	models: ImageGenerationModel[]
): Record<string, ImageGenerationModel[]> => {
	const groups: Record<string, ImageGenerationModel[]> = {};
	for (const model of models) {
		const vendor = model.provider ?? 'other';
		(groups[vendor] ??= []).push(model);
	}
	return groups;
};

export const vendorLogoUrl = (provider: string): string => `/assets/vendors/${provider}.webp`;

export const isProxyModel = (model: ImageGenerationModel): boolean => model.hosting === 'proxy';
```

- [ ] **Step 4: 运行测试,确认通过(GREEN)**

```
npm run test -- images-dropdown.test.ts
```

Expected: `3 passed`。

- [ ] **Step 5: Prettier 格式检查**

```
npx prettier --check "src/lib/utils/images-dropdown.ts" "src/lib/utils/images-dropdown.test.ts"
```

Expected: `All matched files use Prettier code style!`。

- [ ] **Step 6: 类型检查**

```
npx svelte-check --tsconfig ./tsconfig.json --threshold error --output machine 2>&1 | grep "images-dropdown" || echo "no diagnostics"
```

Expected: `no diagnostics`。

---

## Task 9: Images.svelte 模型下拉改两级菜单 + 单张隐藏张数 + proxy tooltip

**Files:**

- Modify: `src/lib/components/images/Images.svelte`(模型选择器 893-931 区域;张数触发按钮 958-961;张数 section 1056-1079)
- Test: `src/lib/components/images/Images.test.ts`(扩,若存在;否则靠手动验收)

**Interfaces:**

- Consumes: Task 8 的 `groupByVendor`/`vendorLogoUrl`/`isProxyModel`;Task 7 的 `ImageGenerationModel.hosting`。
- Produces: 两级菜单 UI(左品牌+logo / 右模型,窄屏上下堆叠);单张模型隐藏张数;proxy tooltip。

> 本任务是纯 Svelte markup 改造,Vitest 对 markup 脆弱。按项目约定(markdown 不强测 Svelte 渲染),以手动 + 浏览器验收为准(Task 14)。先做类型/Prettier 守护,再手动验收。

- [ ] **Step 1: 引入纯函数与状态**

在 `Images.svelte` `<script>` 顶部 import 区(34 行附近)加:

```typescript
import { groupByVendor, vendorLogoUrl, isProxyModel } from '$lib/utils/images-dropdown';
```

在状态变量区(`let showModelSelector = false;` 附近,64 行)加:

```typescript
let selectedVendor = '';
```

在 reactive 区(`$: view = ...` 附近)加:

```typescript
$: vendorGroups = groupByVendor(models);
$: vendorList = Object.keys(vendorGroups).sort((a, b) =>
	a === 'other' ? 1 : b === 'other' ? -1 : a.localeCompare(b)
);
$: if (selectedVendor === '' && vendorList.length > 0) {
	selectedVendor = vendorList[0];
}
$: vendorModels = vendorGroups[selectedVendor] ?? [];
```

- [ ] **Step 2: 改造模型下拉为两级菜单**

将 `Images.svelte` 现有模型下拉(893-931 区域,`{#if showModelSelector}` 块)替换为两级菜单。保留外层容器与定位 class,内部改为:

```svelte
{#if showModelSelector}
	<div
		class="absolute z-40 mt-2 flex flex-col gap-2 rounded-2xl border border-gray-100 bg-white p-2 shadow-xl sm:flex-row sm:min-w-[28rem] dark:border-gray-800 dark:bg-gray-900"
		role="listbox"
		aria-label={$i18n.t('Select a model')}
	>
		<!-- 品牌级(左/上)-->
		<ul
			class="flex snap-x snap-mandatory gap-1 overflow-x-auto sm:w-40 sm:flex-col sm:overflow-visible sm:border-r sm:border-gray-100 sm:pr-1 dark:sm:border-gray-800"
			role="group"
			aria-label={$i18n.t('Brands')}
		>
			{#each vendorList as vendor}
				<li class="snap-start">
					<button
						type="button"
						class="flex w-full shrink-0 items-center gap-2 rounded-xl px-2 py-1.5 text-sm transition {selectedVendor ===
						vendor
							? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
							: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
						on:click={() => (selectedVendor = vendor)}
						aria-pressed={selectedVendor === vendor}
					>
						<img
							src={vendorLogoUrl(vendor)}
							alt={vendor}
							class="size-4 rounded-sm"
							loading="lazy"
							decoding="async"
						/>
						<span class="capitalize">{vendor}</span>
					</button>
				</li>
			{/each}
		</ul>
		<!-- 模型级(右/下)-->
		<ul class="max-h-72 overflow-y-auto sm:flex-1" role="group" aria-label={$i18n.t('Models')}>
			{#each vendorModels as model}
				<li>
					<button
						type="button"
						class="flex w-full items-center justify-between gap-2 rounded-xl px-2 py-1.5 text-sm transition {selectedModel ===
						model.id
							? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
							: 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-850'}"
						on:click={() => selectModel(model.id)}
						role="option"
						aria-selected={selectedModel === model.id}
					>
						<span class="truncate">{model.name ?? model.id}</span>
						{#if isProxyModel(model)}
							<Tooltip content={$i18n.t('First image may be slower')}>
								<span class="shrink-0 text-xs text-gray-400 dark:text-gray-500" aria-hidden="true"
									>⏱</span
								>
							</Tooltip>
						{/if}
					</button>
				</li>
			{/each}
		</ul>
	</div>
{/if}
```

- [ ] **Step 3: 单张模型隐藏张数(触发按钮 + section)**

在 `Images.svelte` 张数触发按钮(958-961 区域,`<span class="inline-flex items-center gap-1">` 含 `{imageCount}`)外面加守卫。将该按钮所在的整个数量触发块用 `{#if imageCountOptions.length > 1}...{/if}` 包裹。

在张数 section(1056-1079,`<section>` 含“Quantity”标题与 each 块)外面加 `{#if imageCountOptions.length > 1}...{/if}` 守卫。

> 具体:找到 `<span class="inline-flex items-center gap-1">` 紧邻的上级按钮(显示 imageCount 那个),在最外层按钮前加 `{#if imageCountOptions.length > 1}`,其后加 `{/if}`。同样包裹 1056 起的 `<section>...</section>`。

- [ ] **Step 4: 类型检查(改动文件 0 诊断)**

```
npx svelte-check --tsconfig ./tsconfig.json --threshold error --output machine 2>&1 | grep "images/Images.svelte" || echo "no diagnostics in Images.svelte"
```

Expected: `no diagnostics in Images.svelte`。

- [ ] **Step 5: Prettier 格式检查**

```
npx prettier --check "src/lib/components/images/Images.svelte"
```

Expected: `All matched files use Prettier code style!`。

- [ ] **Step 6: 既有前端测试不回归**

```
npm run test -- Images.test.ts
```

Expected: 既有用例全部 passed(若 Images.test.ts 不存在则跳过,记为 N/A)。

---

## Task 10: i18n 新增键(zh-CN 补齐,en-US 空串)

**Files:**

- Modify: `src/lib/i18n/locales/zh-CN/translation.json`
- Modify: `src/lib/i18n/locales/en-US/translation.json`
- Test: 手动 + 现有 i18n 测试不回归

**Interfaces:**

- Produces: `Brands`/`Models`/`Select a model`/`First image may be slower` 的 zh-CN 翻译;en-US 空串回落。

- [ ] **Step 1: zh-CN 加键**

在 `zh-CN/translation.json` 中合适的字母位置插入:

```json
	"Brands": "品牌",
	"Models": "模型",
	"Select a model": "选择模型",
	"First image may be slower": "首张可能较慢",
```

> 插入位置:跟随文件既有习惯(不强制排序,Prettier 不重排 JSON key)。插在相邻 key 附近即可。

- [ ] **Step 2: en-US 加空串键**

在 `en-US/translation.json` 对应位置插入:

```json
	"Brands": "",
	"Models": "",
	"Select a model": "",
	"First image may be slower": "",
```

- [ ] **Step 3: Prettier 格式检查**

```
npx prettier --check "src/lib/i18n/locales/zh-CN/translation.json" "src/lib/i18n/locales/en-US/translation.json"
```

Expected: `All matched files use Prettier code style!`。

- [ ] **Step 4: 既有 i18n 测试不回归**

```
npm run test -- i18n
```

Expected: 既有用例 passed(若无 i18n 专项测试则跳过)。

---

## Task 11: 13 篇 fal 接口文档归档

**Files:**

- Create: `docs/fal/alibaba/qwen-image.md`、`qwen-image-2512.md`、`qwen-image-2512-lora.md`、`z-image-base.md`、`qwen-image-2.md`、`qwen-image-2-pro.md`、`qwen-image-max.md`、`wan-2.2-5b.md`、`wan-2.2-a14b.md`、`wan-2.6.md`、`wan-2.7.md`、`wan-2.7-pro.md`、`wan-2.5-preview.md`

**Interfaces:**

- Consumes: 每条对应的 `https://fal.ai/models/<id>/llms.txt`(已在 Temp 缓存,见 findings)。

- [ ] **Step 1: 为每条模型新建文档**

对 13 条逐一创建 `docs/fal/alibaba/<public-id>.md`,内容源自该模型的 llms.txt(概述、Endpoint、Model ID、Pricing、Input Schema、Output Schema、cURL/Python/JS 示例)。沿袭现有 `docs/fal/alibaba/z-image/fal-ai@z-image@turbo.md` 的体例。

> llms.txt 缓存位置:`~/.claude/projects/.../Temp/llms_full/<slug>.txt`(slug = internal id 的 `/` 替换为 `__`)。读取后转为 markdown,保留 schema 字段表。

- [ ] **Step 2: 更新 `docs/fal/fal-provider-comparison.md`**

在 Alibaba 小节(2.1)追加 13 条新接口的行,沿用现有表格列(接口/用途/Endpoint/必填/可选/响应/价格/差异)。

- [ ] **Step 3: 验证文档无占位符**

```
grep -rE "TBD|TODO|占位" docs/fal/alibaba/ || echo "no placeholders"
```

Expected: `no placeholders`。

---

## Task 12: 积分定价录入 seed 脚本(可选)

> 🛑 **【2026-07-25 整任务废弃公告】**
>
> 本任务规划的 seed 脚本 `backend/open_webui/extensions/credits/seed_alibaba_prices.py` **已于当日从仓库删除,永不创建**。以下整个 Task 12 正文(Steps 1–3、脚本源码、运行/编译命令)一律作为**历史规划原文保留**,仅供溯源,不再具有执行力。
>
> **实际录入已完成**,走的是 spec §4.4 的主线路径:经管理后台逐条 `POST /api/v1/credits/admin/prices`,13 条定价全部入库(`service_type=image`、`action=text-to-image`、`enabled=true`),经只读对账 0 mismatch。
>
> **该脚本被弃用的客观原因**(供未来回顾,勿再蹈辙):
>
> 1. `CreditPrice` 表的 `id` / `created_at` / `updated_at` 三列为 `nullable=False` 且无 `server_default`,credits 代码内**无任何 `before_insert` ORM 钩子**为其兜底;脚本构造 `CreditPrice(...)` 时遗漏这三列,flush 时必然 `IntegrityError`,整个 `session.begin()` 事务回滚,一条都进不去。Task 12 当年仅以 `compileall` + AST 静态校验宣告 DONE,未能揭示此运行期缺陷。
> 2. `ExactMapRule.values` 要求 `dict[str, PositivePrice]`,后者经 `BeforeValidator(parse_decimal_string)` 仅接受字符串形态的价格;脚本中以裸整数 `4` 充当 value 会被后端 422 拒绝。
> 3. 脚本不带存在性检查,与 `uq_ext_credit_price_service` 唯一约束结合后不具备幂等性,重复执行会产生 409/回滚。
>
> 如未来确需批量种子能力,应以"调用管理路由"的形式重写(让路由自动填补 id/时间戳/审计字段并处理冲突),切勿沿袭本任务的直接 `session.add` 范式。

**Files:**

- Create: `backend/open_webui/extensions/credits/seed_alibaba_prices.py`

**Interfaces:**

- Produces: 13 条 `CreditPrice` 的 seed 脚本,供管理员一次性导入(非自动运行;需 admin 手动执行)。

> 本任务**可选**。若用户倾向管理后台逐条手录,可跳过本任务。

- [ ] **Step 1: 写 seed 脚本**

新建 `backend/open_webui/extensions/credits/seed_alibaba_prices.py`:

```python
"""一次性 seed:为阿里 13 条文生图模型录入积分定价。

用法(需 admin 环境):
    python -m open_webui.extensions.credits.seed_alibaba_prices

汇率:$0.005 = 1 积分,base_price = 美元价 / 0.005,ceil 取整(min 1)。
"""
from __future__ import annotations

from open_webui.extensions.credits.models import CreditPrice

# (resource_id, base_price, rules)
# resource_id 必须用内部 id(credits 用 internal 计费)
PER_IMAGE_PRICE_RULES = {'schema_version': 1, 'dimensions': [{'key': 'image_count', 'kind': 'quantity'}]}
PER_MEGAPIXEL_QWEN_2512 = {
    'schema_version': 1,
    'dimensions': [
        {
            'key': 'size',
            'kind': 'exact_map',
            'values': {
                'default': 4,
                '512x512': 4,
                '1024x1024': 4,
                '1024x768': 4,
                '768x1024': 4,
                '1280x720': 4,
                '720x1280': 4,
            },
        }
    ],
}

PRICES = [
    ('fal-ai/qwen-image', '4', PER_IMAGE_PRICE_RULES),
    ('fal-ai/qwen-image-2512', '1', PER_MEGAPIXEL_QWEN_2512),
    ('fal-ai/qwen-image-2512/lora', '7', PER_IMAGE_PRICE_RULES),
    ('fal-ai/z-image/base', '2', PER_IMAGE_PRICE_RULES),
    ('fal-ai/qwen-image-2/text-to-image', '7', PER_IMAGE_PRICE_RULES),
    ('fal-ai/qwen-image-2/pro/text-to-image', '15', PER_IMAGE_PRICE_RULES),
    ('fal-ai/qwen-image-max/text-to-image', '15', PER_IMAGE_PRICE_RULES),
    ('fal-ai/wan/v2.2-5b/text-to-image', '3.2', PER_IMAGE_PRICE_RULES),
    ('fal-ai/wan/v2.2-a14b/text-to-image', '5', PER_IMAGE_PRICE_RULES),
    ('wan/v2.6/text-to-image', '6', PER_IMAGE_PRICE_RULES),
    ('fal-ai/wan/v2.7/text-to-image', '6', PER_IMAGE_PRICE_RULES),
    ('fal-ai/wan/v2.7/pro/text-to-image', '15', PER_IMAGE_PRICE_RULES),
    ('fal-ai/wan-v2.5/text-to-image', '10', PER_IMAGE_PRICE_RULES),
]


async def seed(session) -> None:
    for resource_id, base_price, rules in PRICES:
        session.add(
            CreditPrice(
                service_type='image',
                resource_id=resource_id,
                action='text-to-image',
                base_price=base_price,
                rules=rules,
                enabled=True,
            )
        )


if __name__ == '__main__':
    import asyncio

    from open_webui.extensions.credits.database import get_session_factory

    async def main():
        factory = get_session_factory()
        async with factory() as session, session.begin():
            await seed(session)

    asyncio.run(main())
```

- [ ] **Step 2: 编译检查**

```
python -m compileall backend/open_webui/extensions/credits/seed_alibaba_prices.py
```

Expected: 无输出。

- [ ] **Step 3: 验证 PRICES 清单与 spec §4 一致**

```
python -c "from open_webui.extensions.credits.seed_alibaba_prices import PRICES; print(len(PRICES))"
```

Expected: `13`。

> 注意:此脚本不自动运行,需 admin 在部署环境手动执行。录制后应在管理后台或 `/api/v1/credits/admin/prices` 核对 13 条已存在。

---

## Task 13: 全量新鲜验证

**Files:** 无(仅运行验证)

- [ ] **Step 1: 后端合并定向测试**

```
cd D:\code\github\open-webui-main
python -m pytest backend/open_webui/utils/images/test_fal_models.py backend/open_webui/utils/images/test_fal.py backend/open_webui/extensions/credits/tests/test_public_image_models.py -q
```

Expected: 全部 passed,0 failures。

- [ ] **Step 2: credits 全套不回归**

```
python -m pytest backend/open_webui/extensions/credits/tests/ -q
```

Expected: 全部 passed(预期 547 passed / 8 skipped 量级,以实际基线为准)。

- [ ] **Step 3: Python 编译检查**

```
python -m compileall backend/open_webui/utils/images/fal_models.py backend/open_webui/utils/images/fal.py backend/open_webui/extensions/credits/seed_alibaba_prices.py
```

Expected: 无输出。

> ℹ️ 【2026-07-25 更新】`seed_alibaba_prices.py` 已删除,执行时应将该文件名从命令中去掉,仅编译 `fal_models.py` 与 `fal.py` 两项。

- [ ] **Step 4: 前端 Vitest**

```
npm run test -- image-generation images-dropdown
```

Expected: 全部 passed。

- [ ] **Step 5: 前端类型检查(改动文件 0 诊断)**

```
npx svelte-check --tsconfig ./tsconfig.json --threshold error --output machine 2>&1 | grep -E "images.Images.svelte|image-generation.ts|images-dropdown" || echo "no diagnostics in changed files"
```

Expected: `no diagnostics in changed files`(全量既有错误不计)。

- [ ] **Step 6: Prettier**

```
npx prettier --check "src/lib/utils/images-dropdown.ts" "src/lib/utils/images-dropdown.test.ts" "src/lib/utils/image-generation.ts" "src/lib/utils/image-generation.test.ts" "src/lib/components/images/Images.svelte" "src/lib/i18n/locales/zh-CN/translation.json" "src/lib/i18n/locales/en-US/translation.json"
```

Expected: `All matched files use Prettier code style!`。

- [ ] **Step 7: git diff 格式检查**

```
git diff --check
```

Expected: 无输出(无行尾空白/冲突标记)。

- [ ] **Step 8: 报告**

汇总上述 7 步的实际输出给用户,等待验收。**不 commit**(用户未授权)。

---

## Task 14: 浏览器运行时验收

**Files:** 无(浏览器手动)

- [ ] **Step 1: 起服务**

前端:`npm run dev`(端口 5173)。后端:按项目既有方式(如 `backend/dev.sh`,端口 8080)。确认两侧均 200。

- [ ] **Step 2: 桌面端验收**

访问 `/images`，使用本地测试管理员账号登录（凭据从开发环境安全配置读取，不写入仓库）：

- 点击模型按钮,下拉为两级菜单:左栏品牌(Alibaba 带 logo),右栏该品牌模型。
- 点 Alibaba → 右栏出现 13 条新模型 + z-image-turbo。
- 选 `Wan 2.2 (5B)` → 张数选择器消失(单张)。
- 选 `Wan 2.7` → 张数选择器出现 1-5。
- 选 `Qwen Image 2 Pro`(proxy)→ 模型名右侧出现 ⏱ tooltip「首张可能较慢」。
- 输入 prompt,选 `Qwen Image`,报价 badge 显示 4 积分(一张)。
- 生成一张,Network 里 `/images/generations` 请求 body 的 `model` 字段为 `qwen-image`(无 `fal-ai/`),响应成功,作品库出现该图。

- [ ] **Step 3: 移动端窄屏验收**

DevTools 切到 375px 宽:

- 下拉两级菜单变为上下堆叠:品牌栏在上(横向滚动 chips),模型栏在下。
- 品牌芯片可横向滑动选择,模型栏随之切换。
- 张数选择器、proxy tooltip 在窄屏下可见且不溢出。

- [ ] **Step 4: 深浅色主题**

切换暗色主题,下拉、logo、tooltip 均可读,无明显对比度问题。

- [ ] **Step 5: 报告验收结果**

汇总桌面/移动/深浅色的观察给用户。发现问题则回到对应 Task 修复。**不 commit**。

---

## Self-Review

**1. Spec coverage:**

- §3.1 13 条清单 → Task 3(EXPECTED_NEW_MODELS 表逐一对应)✅
- §3.2 三模板 → Task 1(A)/Task 2(B,C)✅
- §3.3 FAL_ALIBABA_NAMED_SIZES → Task 1 ✅
- §3.4 双向映射 → Task 4 ✅
- §3.5 hosting 白名单 → Task 5 ✅
- §4 积分定价 → Task 12(seed 脚本)+ Task 14(浏览器验收报价)✅
- §5.1 两级菜单 → Task 9 ✅
- §5.2 品牌 logo → Task 8(vendorLogoUrl)+ Task 9(img 渲染)✅
- §5.3 单张隐藏张数 → Task 9 Step 3 ✅
- §5.4 proxy tooltip → Task 9 Step 2(isProxyModel + Tooltip)✅
- §5.5 i18n → Task 10 ✅
- §5.6 前端测试 → Task 7/8 ✅
- §6 文档归档 → Task 11 ✅
- §8 测试策略 → Task 6/13 ✅
- §9 已落实细节 → Task 1(safety_default/promption_expansion_default)+ Task 2(去 has_output_safety_checker)+ Task 9(张数守卫位置)✅

**2. Placeholder scan:** 已扫,无 TBD/TODO/"适当处理";每步含全代码或确切命令。Task 11 文档生成依赖 llms.txt 缓存读取,给出了确切路径与体例参照,非占位。

**3. Type consistency:**

- `hosting` 在 Task 5(后端 white-list)→ Task 7(TS 类型)→ Task 8(isProxyModel)→ Task 9(渲染)贯穿一致 ✅
- `count_field`/`image_counts` 在 Task 2(模板)→ Task 3(注册)→ Task 6(payload)一致 ✅
- `FAL_ALIBABA_NAMED_SIZES` 在 Task 1(定义)→ Task 2/3(引用)一致 ✅
- `groupByVendor`/`vendorLogoUrl`/`isProxyModel` 在 Task 8(定义)→ Task 9(import 与使用)一致 ✅
