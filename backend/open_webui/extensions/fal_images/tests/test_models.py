"""fal_images 静态模型注册表（目录驱动外观）的数据契约测试。

旧的 legacy_builders 构造器及其单测已随声明式目录（fal_catalog）迁移删除；
此处仅锁定对外注册表 ``FAL_IMAGE_MODELS`` 与公共 id 映射的数据契约。
"""

from __future__ import annotations

from open_webui.extensions.fal_images.models import (
    FAL_IMAGE_MODELS,
    normalize_fal_image_model_id,
    public_fal_image_model_id,
    public_fal_image_models,
)

# 阿里系模型统一的比例档（原六档像素枚举转换而来；512x512 与 1024x1024
# 同为 1:1，按「1K 级隐藏分辨率、同比例取大档」规则合并为 1024x1024）
ALIBABA_NAMED_SIZES = [
    '1280x720',
    '1024x768',
    '720x1280',
    '768x1024',
    '1024x1024',
    '512x512',
]
ALIBABA_RATIO_SIZES = {
    '1:1': '1024x1024',
    '16:9': '1280x720',
    '9:16': '720x1280',
    '4:3': '1024x768',
    '3:4': '768x1024',
}


def test_z_image_turbo_remains_backward_compatible():
    turbo = next(m for m in FAL_IMAGE_MODELS if m['id'] == 'fal-ai/z-image/turbo')
    integers = {f['field']: f for f in turbo['integer_fields']}
    assert integers['num_inference_steps']['max'] == 8
    booleans = {b['field']: b for b in turbo['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is False
    assert turbo['edit_model'] == 'fal-ai/z-image/turbo/image-to-image'


EXPECTED_NEW_MODELS = [
    ('fal-ai/qwen-image', 'serverless', 'num_images', [1, 2, 3, 4]),
    ('fal-ai/qwen-image-2512', 'serverless', 'num_images', [1, 2, 3, 4]),
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


def test_all_twelve_new_models_registered():
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
        assert m['aspect_ratio_sizes'] == ALIBABA_RATIO_SIZES
        assert m['default_aspect_ratio'] in m['aspect_ratios']


def test_existing_22_models_still_present():
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    for existing in [
        'fal-ai/z-image/turbo',
        'fal-ai/nano-banana',
        'openai/gpt-image-2',
        'xai/grok-imagine-image',
    ]:
        assert existing in by_id


INTERNAL_TO_PUBLIC = {
    'fal-ai/qwen-image': 'qwen-image',
    'fal-ai/qwen-image-2512': 'qwen-image-2512',
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


def test_internal_ids_map_to_public_ids():
    # 复盘：internal_fal_image_model_id（public→internal 方向）无生产调用方，
    # 已删；这里只锁 public 方向映射。
    for internal, public in INTERNAL_TO_PUBLIC.items():
        assert public_fal_image_model_id(internal) == public


def test_normalize_accepts_both_forms():
    for internal, public in INTERNAL_TO_PUBLIC.items():
        assert normalize_fal_image_model_id(public) == internal
        assert normalize_fal_image_model_id(internal) == internal


def test_every_registered_model_has_public_id():
    registered = {m['id'] for m in FAL_IMAGE_MODELS}
    unmapped = [i for i in registered if public_fal_image_model_id(i) is None]
    assert unmapped == [], f'unmapped internal ids: {unmapped}'


# --- 阿里文生图 i2i 接入的事实源 -------------------------------------------
#
# 每行列出一条 t2i 及其配套 i2i 端点、参考图字段形态(单图 image_url / 多图
# image_urls)。三类断言从这里推导:
#   - t2i 条目必须挂 edit_model 指向同行 i2i
#   - i2i 兄弟条目必须注册,task=image-to-image,反指 t2i 作 generation_model
#   - 两组内部 id 都要在内部↔公共 id 映射里登记
ALIBABA_I2I_PAIRS = [
    ('fal-ai/z-image/turbo', 'fal-ai/z-image/turbo/image-to-image', 'image_url'),
    ('fal-ai/qwen-image', 'fal-ai/qwen-image/image-to-image', 'image_url'),
    ('fal-ai/qwen-image-2/text-to-image', 'fal-ai/qwen-image-2/edit', 'image_urls'),
    ('fal-ai/qwen-image-2/pro/text-to-image', 'fal-ai/qwen-image-2/pro/edit', 'image_urls'),
    ('fal-ai/qwen-image-max/text-to-image', 'fal-ai/qwen-image-max/edit', 'image_urls'),
    ('fal-ai/wan/v2.2-a14b/text-to-image', 'fal-ai/wan/v2.2-a14b/image-to-image', 'image_url'),
    ('wan/v2.6/text-to-image', 'wan/v2.6/image-to-image', 'image_urls'),
    ('fal-ai/wan/v2.7/text-to-image', 'fal-ai/wan/v2.7/edit', 'image_urls'),
    ('fal-ai/wan/v2.7/pro/text-to-image', 'fal-ai/wan/v2.7/pro/edit', 'image_urls'),
    ('fal-ai/wan-v2.5/text-to-image', 'fal-ai/wan-25-preview/image-to-image', 'image_urls'),
]

# 多图派 i2i 端点参考图上限,取自 fal 文档("1-3 images required" 等)。
# 单图派固定为 1(下面按 image_input_field=='image_url' 分支断言),不在此表登记。
ALIBABA_I2I_MAX_COUNT = {
    'fal-ai/qwen-image-2/edit': 3,
    'fal-ai/qwen-image-2/pro/edit': 3,
    'fal-ai/qwen-image-max/edit': 3,
    'wan/v2.6/image-to-image': 3,
    'fal-ai/wan/v2.7/edit': 4,
    'fal-ai/wan/v2.7/pro/edit': 4,
    'fal-ai/wan-25-preview/image-to-image': 2,
}


def test_each_supported_alibaba_t2i_declares_edit_model_pointing_to_real_sibling():
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    for t2i_id, edit_id, _field in ALIBABA_I2I_PAIRS:
        assert t2i_id in by_id, f'missing t2i registration: {t2i_id}'
        declared = by_id[t2i_id].get('edit_model')
        assert declared == edit_id, f'{t2i_id} edit_model expected {edit_id!r}, got {declared!r}'


def test_three_alibaba_t2i_without_i2i_do_not_pretend_an_edit_model():
    # qwen-image-2512 / z-image/base / wan v2.2-5b 没有面向终端的 i2i 端点,
    # 它们绝不允许携带 edit_model,否则前端会把用户导向一个并不存在的 edit 路径。
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    unsupported = [
        'fal-ai/qwen-image-2512',
        'fal-ai/z-image/base',
        'fal-ai/wan/v2.2-5b/text-to-image',
    ]
    for model_id in unsupported:
        assert model_id in by_id, f'missing t2i baseline: {model_id}'
        assert 'edit_model' not in by_id[model_id], (
            f'{model_id} unexpectedly advertises edit_model {by_id[model_id]["edit_model"]!r}'
        )


def test_each_alibaba_i2i_sibling_is_registered_with_correct_shape():
    by_id = {m['id']: m for m in FAL_IMAGE_MODELS}
    for t2i_id, edit_id, image_input_field in ALIBABA_I2I_PAIRS:
        assert edit_id in by_id, f'missing i2i registration: {edit_id}'
        sibling = by_id[edit_id]
        assert sibling['task'] == 'image-to-image', f'{edit_id} task expected image-to-image, got {sibling["task"]!r}'
        # i2i 必须反指自己的 t2i twin,使 get_fal_generation_model 能回路翻转
        assert sibling['generation_model'] == t2i_id, (
            f'{edit_id} generation_model expected {t2i_id!r}, got {sibling.get("generation_model")!r}'
        )
        assert sibling['image_input_field'] == image_input_field, (
            f'{edit_id} image_input_field expected {image_input_field!r}, got {sibling.get("image_input_field")!r}'
        )
        if image_input_field == 'image_url':
            # 单图派强制最多一张参考图,杜绝前端灌入第二张撞坏端点契约
            assert sibling['image_input_max_count'] == 1, (
                f'{edit_id} image_input_max_count expected 1, got {sibling.get("image_input_max_count")!r}'
            )
        else:
            # 多图派按 fal 文档声明的参考图上限收紧上传器,避免用户上传第 N+1
            # 张时被 fal 端拒绝(qwen "1-3 images"、wan v2.7 "1-4 images" 等)。
            expected = ALIBABA_I2I_MAX_COUNT[edit_id]
            assert sibling['image_input_max_count'] == expected, (
                f'{edit_id} image_input_max_count expected {expected}, got {sibling.get("image_input_max_count")!r}'
            )
        # 能力维度(hosting/resolutions/output_formats)应当与 t2i twin 对齐
        twin = by_id[t2i_id]
        assert sibling['hosting'] == twin['hosting'], (
            f'{edit_id} hosting diverges from {t2i_id}: {sibling["hosting"]!r} vs {twin["hosting"]!r}'
        )
        if 'aspect_ratio_field' in sibling:
            # wan v2.2-a14b i2i：fal 端点原生 aspect_ratio 参数（文档 Options
            # auto/16:9/9:16/1:1），比例直传而非像素映射，与 t2i 的 image_size 机制不同。
            assert sibling['aspect_ratio_field'] == 'aspect_ratio'
        else:
            assert sibling['aspect_ratio_sizes'] == twin['aspect_ratio_sizes']


def test_known_alibaba_i2i_registrations_remain_available():
    # 这张表只锁定已有端点的兼容契约；后续新增且已完整声明关系的阿里 i2i
    # 不应仅因没有同步扩充历史基准表而导致目录测试失败。
    registered = {
        m['id'] for m in FAL_IMAGE_MODELS if m.get('provider') == 'alibaba' and m.get('task') == 'image-to-image'
    }
    expected = {edit_id for _, edit_id, _ in ALIBABA_I2I_PAIRS}

    assert registered >= expected, f'missing known alibaba i2i registrations: {sorted(expected - registered)}'


# --- 双向公共 id 映射 --------------------------------------------------------
# 公共 id 统一规整为 "<对应 t2i 公共 id>/edit",与 Google/OpenAI 的 nano-banana/edit
# 惯例对齐,屏蔽 fal 端混乱的 "/image-to-image" 与 "/edit" 双后缀以及 wan-2.5 ↔
# wan-v2.5 的拼写漂移。下表是与 ALIBABA_I2I_PAIRS 一一对应的公共 id。
ALIBABA_I2I_PUBLIC_IDS = {
    'fal-ai/z-image/turbo/image-to-image': 'z-image-turbo/edit',
    'fal-ai/qwen-image/image-to-image': 'qwen-image/edit',
    'fal-ai/qwen-image-2/edit': 'qwen-image-2/edit',
    'fal-ai/qwen-image-2/pro/edit': 'qwen-image-2-pro/edit',
    'fal-ai/qwen-image-max/edit': 'qwen-image-max/edit',
    'fal-ai/wan/v2.2-a14b/image-to-image': 'wan-2.2-a14b/edit',
    'wan/v2.6/image-to-image': 'wan-2.6/edit',
    'fal-ai/wan/v2.7/edit': 'wan-2.7/edit',
    'fal-ai/wan/v2.7/pro/edit': 'wan-2.7-pro/edit',
    'fal-ai/wan-25-preview/image-to-image': 'wan-2.5-preview/edit',
}


def test_each_alibaba_i2i_sibling_has_public_id_mapping():
    for internal_id, expected_public in ALIBABA_I2I_PUBLIC_IDS.items():
        assert public_fal_image_model_id(internal_id) == expected_public, (
            f'public_fal_image_model_id({internal_id!r}) expected {expected_public!r}'
        )


def test_alibaba_i2i_public_catalog_translates_relations_to_valid_public_ids():
    # public_fal_image_models 会把 t2i 的 edit_model 翻成公共 id;映射补齐后,
    # 每个 t2i 的 edit_model 必须落在公共目录里真实存在的另一条目上。
    pub_by_id = {m['id']: m for m in public_fal_image_models(None)}
    for t2i_id, _edit_id, _field in ALIBABA_I2I_PAIRS:
        t2i_pub_id = public_fal_image_model_id(t2i_id)
        assert t2i_pub_id is not None and t2i_pub_id in pub_by_id, f'{t2i_id} lacks a public catalog entry'
        declared = pub_by_id[t2i_pub_id].get('edit_model')
        assert declared is not None and declared in pub_by_id, (
            f'{t2i_pub_id}.edit_model={declared!r} is not a reachable public model'
        )
