from open_webui.utils.images.fal_models import (
    FAL_ALIBABA_NAMED_SIZES,
    FAL_IMAGE_MODELS,
    FAL_OUTPUT_FORMATS,
    _alibaba_model,
    _alibaba_qwen2_model,
    _alibaba_wan_model,
    _base_model,
    internal_fal_image_model_id,
    normalize_fal_image_model_id,
    public_fal_image_model_id,
    public_fal_image_models,
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
    integers = {f['field']: f for f in turbo['integer_fields']}
    assert integers['num_inference_steps']['max'] == 8
    booleans = {b['field']: b for b in turbo['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is False
    assert turbo['edit_model'] == 'fal-ai/z-image/turbo/image-to-image'


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


# --- Task #10: factories gain i2i-aware keyword extension ---------------------
#
# 阿里三条工厂此前只能产 text-to-image 元数据块;为了让同一套构造器也能注册
# image-to-image 兄弟条目,我们给它们加上统一的 keyword-only 扩展:
#   task                 默认 'text-to-image',传 'image-to-image' 即产出 i2i 块
#   generation_model     仅 i2i 用,指向同名 t2i 端点(供 get_fal_generation_model 反解)
#   edit_model           通常 t2i 用,指向配套 i2i 端点(_base_model 已支持,_alibaba_* 需贯通)
#   image_input_field    单图派 'image_url'(单数字符串),多图派省略走默认 'image_urls'
#   image_input_max_count 单图派强制 1,防止前端塞多张参考图撑爆端点
# 下面三组用例分别锁定每种工厂的单图/多图两类产物形状。


def test_alibaba_factory_emits_i2i_block_for_multi_image_endpoint():
    # 代表 qwen-image-2 系列:image_urls(list),i2i 端点形如 '<t2i>/edit'
    model = _alibaba_qwen2_model(
        'fal-ai/qwen-image-2/edit',
        'Alibaba / Qwen Image 2 Edit',
        '1024x1024',
        'proxy',
        task='image-to-image',
        generation_model='fal-ai/qwen-image-2/text-to-image',
        image_input_field='image_urls',
    )
    assert model['task'] == 'image-to-image'
    assert model['generation_model'] == 'fal-ai/qwen-image-2/text-to-image'
    assert model['image_input_field'] == 'image_urls'
    # 多图派不应强制压低上限,沿用 _base_model 不下发 image_input_max_count
    assert 'image_input_max_count' not in model
    # 解析度/计数/hosting 这些能力维度应当与同名 t2i 保持一致,便于共用 UI 报价
    assert model['image_size_whitelist'] == {s: s for s in FAL_ALIBABA_NAMED_SIZES}


def test_alibaba_factory_emits_i2i_block_for_single_image_endpoint():
    # 代表 qwen-image:v1 代,image_url(单数字符串),i2i 端点 '/image-to-image'
    model = _alibaba_model(
        'fal-ai/qwen-image/image-to-image',
        'Alibaba / Qwen Image Edit',
        FAL_ALIBABA_NAMED_SIZES,
        '1024x768',
        hosting='serverless',
        steps_max=250,
        safety_default=True,
        prompt_expansion_default=False,
        task='image-to-image',
        generation_model='fal-ai/qwen-image',
        image_input_field='image_url',
        image_input_max_count=1,
    )
    assert model['task'] == 'image-to-image'
    assert model['generation_model'] == 'fal-ai/qwen-image'
    assert model['image_input_field'] == 'image_url'
    assert model['image_input_max_count'] == 1
    # 其余能力维度继承同名 t2i(steps_max/safety/format),不被 i2i 化打乱
    integers = {f['field']: f for f in model['integer_fields']}
    assert integers['num_inference_steps']['max'] == 250
    booleans = {b['field']: b for b in model['boolean_fields']}
    assert booleans['enable_safety_checker']['default'] is True


def test_alibaba_wan_factory_supports_i2i_extension():
    # 代表 wan-v2.7:max_images/count 异构,output_formats 不同,但仍要走同一套 i2i 扩展
    model = _alibaba_wan_model(
        'fal-ai/wan/v2.7/edit',
        'Alibaba / Wan 2.7 Edit',
        '512x512',
        'proxy',
        count_field='num_images',
        image_counts=[1, 2, 3, 4, 5],
        output_formats=FAL_OUTPUT_FORMATS,
        prompt_expansion_default=True,
        task='image-to-image',
        generation_model='fal-ai/wan/v2.7/text-to-image',
        image_input_field='image_urls',
    )
    assert model['task'] == 'image-to-image'
    assert model['generation_model'] == 'fal-ai/wan/v2.7/text-to-image'
    assert model['image_input_field'] == 'image_urls'
    assert model['count_field'] == 'num_images'


def test_factories_keep_t2i_defaults_when_i2i_kwargs_absent():
    # 回归保护:不加 i2i 扩展时,工厂依旧产出原有 text-to-image 块,不带任何残留字段
    t2i = _alibaba_qwen2_model(
        'fal-ai/qwen-image-2/text-to-image',
        'Alibaba / Qwen Image 2',
        '1024x1024',
        'proxy',
    )
    assert t2i['task'] == 'text-to-image'
    assert 'generation_model' not in t2i
    assert 'image_input_field' not in t2i
    assert 'image_input_max_count' not in t2i


def test_base_model_already_propagates_relations_but_not_image_inputs():
    # _base_model 早就有 edit_model/generation_model 通路;此测试固化它不会越界塞
    # image_input_field,从而保证图像输入语义只在各 *_factory 层显式声明。
    block = _base_model(
        'demo/id-edit',
        'Demo Edit',
        'alibaba',
        'image-to-image',
        generation_model='demo/id',
    )
    assert block['generation_model'] == 'demo/id'
    assert 'edit_model' not in block
    assert 'image_input_field' not in block
    assert 'image_input_max_count' not in block


# --- Shared truth table for Tasks #11/#12/#13 ---------------------------------
#
# 这是阿里文生图 i2i 接入的唯一事实源:每行列出一条 t2i 及其配套 i2i 端点、
# 参考图字段形态(单图 image_url / 多图 image_urls)。三类断言从这里推导:
#   - t2i 条目必须挂 edit_model 指向同行 i2i (#11)
#   - i2i 兄弟条目必须注册,task=image-to-image,反指 t2i 作 generation_model (#12)
#   - 两组内部 id 都要在 _FAL_INTERNAL_TO_PUBLIC_ID 里登记 (#13)
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


# --- Task #11: supported t2i twins advertise their edit_model -----------------
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


# --- Task #12: register the i2i sibling descriptors ----------------------------
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
        assert sibling['image_size_whitelist'] == twin['image_size_whitelist']


def test_no_extra_phantom_alibaba_i2i_registrations_exist():
    # 除了 ALIBABA_I2I_PAIRS 列出的条目,不许冒出额外的阿里 i2i 条目,
    # 以免有人日后随手加了一条却忘了同步映射/定价。
    by_provider_task = [
        m['id'] for m in FAL_IMAGE_MODELS if m.get('provider') == 'alibaba' and m.get('task') == 'image-to-image'
    ]
    expected = {edit_id for _, edit_id, _ in ALIBABA_I2I_PAIRS}
    assert set(by_provider_task) == expected, (
        f'alibaba i2i registrations drift: {sorted(set(by_provider_task) ^ expected)}'
    )


# --- Task #13: bidirectional public-id mappings for the i2i siblings -----------
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


def test_each_alibaba_i2i_sibling_has_bidirectional_public_id_mapping():
    for internal_id, expected_public in ALIBABA_I2I_PUBLIC_IDS.items():
        assert public_fal_image_model_id(internal_id) == expected_public, (
            f'public_fal_image_model_id({internal_id!r}) expected {expected_public!r}'
        )
        assert internal_fal_image_model_id(expected_public) == internal_id, (
            f'internal_fal_image_model_id({expected_public!r}) expected {internal_id!r}'
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
