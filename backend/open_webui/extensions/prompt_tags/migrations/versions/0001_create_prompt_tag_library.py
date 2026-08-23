"""Create the independent prompt-tag library and its built-in catalog.

Revision ID: 0001_create_prompt_tag_library
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from open_webui.internal.db import JSONField

revision: str = '0001_create_prompt_tag_library'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEEDED_AT = 1_776_556_800

_CATEGORIES = (
    ('lighting', '光影', 'Lighting'),
    ('composition', '构图', 'Composition'),
    ('style', '风格', 'Style'),
    ('camera', '镜头', 'Camera'),
    ('quality', '画质', 'Quality'),
    ('people', '人物', 'People'),
    ('scene', '场景', 'Scene'),
    ('motion', '运动', 'Motion'),
    ('negative', '负面约束', 'Negative constraints'),
)

# category, slug, zh label, en label, insert text, negative, media kinds
_TAGS = (
    (
        'lighting',
        'cinematic-lighting',
        '电影感光效',
        'Cinematic lighting',
        'cinematic lighting',
        False,
        ('image', 'video'),
    ),
    (
        'lighting',
        'soft-diffused-lighting',
        '柔和漫射光',
        'Soft diffused light',
        'soft diffused lighting',
        False,
        ('image', 'video'),
    ),
    ('lighting', 'golden-hour-lighting', '黄金时刻', 'Golden hour', 'golden hour lighting', False, ('image', 'video')),
    (
        'lighting',
        'volumetric-lighting',
        '体积光',
        'Volumetric lighting',
        'volumetric lighting',
        False,
        ('image', 'video'),
    ),
    ('lighting', 'rim-lighting', '轮廓光', 'Rim lighting', 'rim lighting', False, ('image', 'video')),
    (
        'lighting',
        'dramatic-chiaroscuro',
        '明暗对照',
        'Dramatic chiaroscuro',
        'dramatic chiaroscuro',
        False,
        ('image', 'video'),
    ),
    (
        'composition',
        'rule-of-thirds',
        '三分法构图',
        'Rule of thirds',
        'rule of thirds composition',
        False,
        ('image', 'video'),
    ),
    (
        'composition',
        'centered-symmetry',
        '中心对称',
        'Centered symmetry',
        'centered symmetrical composition',
        False,
        ('image', 'video'),
    ),
    ('composition', 'leading-lines', '引导线', 'Leading lines', 'leading lines', False, ('image', 'video')),
    (
        'composition',
        'foreground-framing',
        '前景框景',
        'Foreground framing',
        'foreground framing',
        False,
        ('image', 'video'),
    ),
    ('composition', 'layered-depth', '层次景深', 'Layered depth', 'layered depth', False, ('image', 'video')),
    (
        'composition',
        'negative-space',
        '负空间',
        'Negative space',
        'negative space composition',
        False,
        ('image', 'video'),
    ),
    ('style', 'cinematic-realism', '电影写实', 'Cinematic realism', 'cinematic realism', False, ('image', 'video')),
    (
        'style',
        'editorial-photography',
        '杂志摄影',
        'Editorial photography',
        'editorial photography',
        False,
        ('image', 'video'),
    ),
    (
        'style',
        'watercolor-illustration',
        '水彩插画',
        'Watercolor illustration',
        'watercolor illustration',
        False,
        ('image', 'video'),
    ),
    ('style', 'anime-style', '动漫风格', 'Anime style', 'anime style', False, ('image', 'video')),
    ('style', 'minimalist-design', '极简主义', 'Minimalist design', 'minimalist design', False, ('image', 'video')),
    ('style', 'retro-futurism', '复古未来主义', 'Retro-futurism', 'retro-futurism', False, ('image', 'video')),
    ('camera', 'wide-angle-shot', '广角镜头', 'Wide-angle shot', 'wide-angle shot', False, ('image', 'video')),
    ('camera', 'close-up-shot', '特写镜头', 'Close-up shot', 'close-up shot', False, ('image', 'video')),
    ('camera', 'macro-shot', '微距镜头', 'Macro shot', 'macro shot', False, ('image', 'video')),
    ('camera', 'low-angle-shot', '低角度镜头', 'Low-angle shot', 'low-angle shot', False, ('image', 'video')),
    ('camera', 'aerial-view', '航拍视角', 'Aerial view', 'aerial view', False, ('image', 'video')),
    (
        'camera',
        'shallow-depth-of-field',
        '浅景深',
        'Shallow depth of field',
        'shallow depth of field',
        False,
        ('image', 'video'),
    ),
    ('quality', 'highly-detailed', '高细节', 'Highly detailed', 'highly detailed', False, ('image', 'video')),
    ('quality', 'sharp-focus', '清晰对焦', 'Sharp focus', 'sharp focus', False, ('image', 'video')),
    ('quality', 'natural-textures', '自然纹理', 'Natural textures', 'natural textures', False, ('image', 'video')),
    (
        'quality',
        'high-dynamic-range',
        '高动态范围',
        'High dynamic range',
        'high dynamic range',
        False,
        ('image', 'video'),
    ),
    (
        'quality',
        'professional-color-grading',
        '专业调色',
        'Professional color grading',
        'professional color grading',
        False,
        ('image', 'video'),
    ),
    ('quality', 'film-grain', '电影颗粒', 'Film grain', 'subtle film grain', False, ('image', 'video')),
    (
        'people',
        'natural-expression',
        '自然表情',
        'Natural expression',
        'natural facial expression',
        False,
        ('image', 'video'),
    ),
    (
        'people',
        'realistic-skin-texture',
        '真实皮肤纹理',
        'Realistic skin texture',
        'realistic skin texture',
        False,
        ('image', 'video'),
    ),
    ('people', 'expressive-eyes', '传神眼神', 'Expressive eyes', 'expressive eyes', False, ('image', 'video')),
    ('people', 'dynamic-pose', '动态姿态', 'Dynamic pose', 'dynamic pose', False, ('image', 'video')),
    ('people', 'candid-moment', '抓拍感', 'Candid moment', 'candid moment', False, ('image', 'video')),
    ('scene', 'urban-night-scene', '都市夜景', 'Urban night scene', 'urban night scene', False, ('image', 'video')),
    ('scene', 'misty-forest', '薄雾森林', 'Misty forest', 'misty forest', False, ('image', 'video')),
    ('scene', 'futuristic-city', '未来城市', 'Futuristic city', 'futuristic city', False, ('image', 'video')),
    (
        'scene',
        'minimalist-studio',
        '极简影棚',
        'Minimalist studio',
        'minimalist studio setting',
        False,
        ('image', 'video'),
    ),
    ('scene', 'vast-landscape', '辽阔风景', 'Vast landscape', 'vast landscape', False, ('image', 'video')),
    ('scene', 'cozy-interior', '温馨室内', 'Cozy interior', 'cozy interior', False, ('image', 'video')),
    ('motion', 'slow-push-in', '缓慢推进', 'Slow push-in', 'slow cinematic push-in', False, ('video',)),
    ('motion', 'smooth-tracking-shot', '平滑跟拍', 'Smooth tracking shot', 'smooth tracking shot', False, ('video',)),
    (
        'motion',
        'gentle-handheld-motion',
        '轻微手持',
        'Gentle handheld motion',
        'gentle handheld motion',
        False,
        ('video',),
    ),
    ('motion', 'slow-motion', '慢动作', 'Slow motion', 'slow motion', False, ('video',)),
    ('motion', 'time-lapse', '延时摄影', 'Time-lapse', 'time-lapse sequence', False, ('video',)),
    ('motion', 'seamless-loop', '无缝循环', 'Seamless loop', 'seamless looping motion', False, ('video',)),
    (
        'negative',
        'blurry-low-quality',
        '模糊低质',
        'Blurry or low quality',
        'blurry, low quality',
        True,
        ('image', 'video'),
    ),
    ('negative', 'distorted-anatomy', '解剖畸形', 'Distorted anatomy', 'distorted anatomy', True, ('image', 'video')),
    ('negative', 'extra-limbs', '多余肢体', 'Extra limbs', 'extra limbs', True, ('image', 'video')),
    (
        'negative',
        'malformed-hands',
        '手指异常',
        'Malformed hands',
        'malformed hands, extra fingers',
        True,
        ('image', 'video'),
    ),
    (
        'negative',
        'watermark-text-logo',
        '水印文字',
        'Watermark, text, or logo',
        'watermark, text, logo',
        True,
        ('image', 'video'),
    ),
    (
        'negative',
        'oversaturated-colors',
        '过度饱和',
        'Oversaturated colors',
        'oversaturated colors',
        True,
        ('image', 'video'),
    ),
    (
        'negative',
        'flicker-jitter',
        '闪烁抖动',
        'Flicker or jitter',
        'flicker, jitter, unstable motion',
        True,
        ('video',),
    ),
)


def _current_schema() -> str | None:
    from alembic import context

    return context.config.attributes.get('prompt_tag_schema')


def _category_id(slug: str) -> str:
    return f'builtin-category-{slug}'


def upgrade() -> None:
    schema = _current_schema()
    category_reference = f'{schema}.ext_prompt_tag_category.id' if schema else 'ext_prompt_tag_category.id'
    op.create_table(
        'ext_prompt_tag_category',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('name_zh', sa.String(128), nullable=False),
        sa.Column('name_en', sa.String(128), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default=sa.text('1000'), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_by_id', sa.String(128), nullable=True),
        sa.Column('updated_by_name_snapshot', sa.String(256), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_ext_prompt_tag_category_slug'),
        sa.CheckConstraint('sort_order >= 0', name='ck_ext_prompt_tag_category_sort_order'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_prompt_tag_category_visibility_order',
        'ext_prompt_tag_category',
        ['enabled', 'sort_order', 'id'],
        schema=schema,
    )
    op.create_table(
        'ext_prompt_tag',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('slug', sa.String(64), nullable=False),
        sa.Column('category_id', sa.String(64), nullable=False),
        sa.Column('label_zh', sa.String(128), nullable=False),
        sa.Column('label_en', sa.String(128), nullable=False),
        sa.Column('insert_text', sa.String(500), nullable=False),
        sa.Column('is_negative', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('media_kinds_json', JSONField(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('model_refs_json', JSONField(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default=sa.text('1000'), nullable=False),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.Column('updated_by_id', sa.String(128), nullable=True),
        sa.Column('updated_by_name_snapshot', sa.String(256), nullable=True),
        sa.ForeignKeyConstraint(
            ['category_id'],
            [category_reference],
            name='fk_ext_prompt_tag_category',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_ext_prompt_tag_slug'),
        sa.CheckConstraint('sort_order >= 0', name='ck_ext_prompt_tag_sort_order'),
        schema=schema,
    )
    op.create_index(
        'ix_ext_prompt_tag_category_enabled_order',
        'ext_prompt_tag',
        ['category_id', 'enabled', 'sort_order', 'id'],
        schema=schema,
    )
    op.create_index(
        'ix_ext_prompt_tag_enabled_order',
        'ext_prompt_tag',
        ['enabled', 'sort_order', 'id'],
        schema=schema,
    )

    category_table = sa.Table(
        'ext_prompt_tag_category',
        sa.MetaData(),
        sa.Column('id', sa.String(64)),
        sa.Column('slug', sa.String(64)),
        sa.Column('name_zh', sa.String(128)),
        sa.Column('name_en', sa.String(128)),
        sa.Column('enabled', sa.Boolean()),
        sa.Column('sort_order', sa.Integer()),
        sa.Column('created_at', sa.BigInteger()),
        sa.Column('updated_at', sa.BigInteger()),
        schema=schema,
    )
    tag_table = sa.Table(
        'ext_prompt_tag',
        sa.MetaData(),
        sa.Column('id', sa.String(64)),
        sa.Column('slug', sa.String(64)),
        sa.Column('category_id', sa.String(64)),
        sa.Column('label_zh', sa.String(128)),
        sa.Column('label_en', sa.String(128)),
        sa.Column('insert_text', sa.String(500)),
        sa.Column('is_negative', sa.Boolean()),
        sa.Column('media_kinds_json', JSONField()),
        sa.Column('model_refs_json', JSONField()),
        sa.Column('enabled', sa.Boolean()),
        sa.Column('sort_order', sa.Integer()),
        sa.Column('created_at', sa.BigInteger()),
        sa.Column('updated_at', sa.BigInteger()),
        schema=schema,
    )
    op.bulk_insert(
        category_table,
        [
            {
                'id': _category_id(slug),
                'slug': slug,
                'name_zh': name_zh,
                'name_en': name_en,
                'enabled': True,
                'sort_order': index * 10,
                'created_at': _SEEDED_AT,
                'updated_at': _SEEDED_AT,
            }
            for index, (slug, name_zh, name_en) in enumerate(_CATEGORIES, start=1)
        ],
    )
    category_positions = {slug: index for index, (slug, _zh, _en) in enumerate(_CATEGORIES)}
    counters: dict[str, int] = {}
    tag_rows = []
    for category, slug, label_zh, label_en, insert_text, is_negative, media_kinds in _TAGS:
        counters[category] = counters.get(category, 0) + 1
        tag_rows.append(
            {
                'id': f'builtin-tag-{slug}',
                'slug': slug,
                'category_id': _category_id(category),
                'label_zh': label_zh,
                'label_en': label_en,
                'insert_text': insert_text,
                'is_negative': is_negative,
                'media_kinds_json': list(media_kinds),
                'model_refs_json': [],
                'enabled': True,
                'sort_order': category_positions[category] * 100 + counters[category] * 10,
                'created_at': _SEEDED_AT,
                'updated_at': _SEEDED_AT,
            }
        )
    op.bulk_insert(tag_table, tag_rows)


def downgrade() -> None:
    schema = _current_schema()
    op.drop_table('ext_prompt_tag', schema=schema)
    op.drop_table('ext_prompt_tag_category', schema=schema)
