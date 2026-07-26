from typing import Any

FAL_IMAGE_COUNTS = [1, 2, 3, 4]
FAL_OUTPUT_FORMATS = ['jpeg', 'png', 'webp']

FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES = {
    '1:1': '1024x1024',
    '16:9': '1536x864',
    '9:16': '864x1536',
    '4:3': '1024x768',
    '3:4': '768x1024',
    '3:2': '1536x1024',
    '2:3': '1024x1536',
}
FAL_OPENAI_GPT_IMAGE_2_EDIT_ASPECT_RATIO_SIZES = {
    'auto': 'auto',
    '1:1': '1024x1024',
    '16:9': '1536x864',
    '9:16': '864x1536',
    '4:3': '1024x768',
    '3:4': '768x1024',
    '3:2': '1536x1024',
    '2:3': '1024x1536',
}
FAL_OPENAI_GPT_IMAGE_SIZES = ['auto', '1024x1024', '1536x1024', '1024x1536']
FAL_OPENAI_GPT_IMAGE_15_SIZES = ['1024x1024', '1536x1024', '1024x1536']

FAL_GOOGLE_IMAGE_RATIOS = ['21:9', '16:9', '3:2', '4:3', '5:4', '1:1', '4:5', '3:4', '2:3', '9:16']
FAL_GOOGLE_AUTO_IMAGE_RATIOS = ['auto', *FAL_GOOGLE_IMAGE_RATIOS]
FAL_GOOGLE_EXTREME_IMAGE_RATIOS = [
    'auto',
    '21:9',
    '16:9',
    '3:2',
    '4:3',
    '5:4',
    '1:1',
    '4:5',
    '3:4',
    '2:3',
    '9:16',
    '4:1',
    '1:4',
    '8:1',
    '1:8',
]
FAL_GOOGLE_PRO_RESOLUTIONS = ['1K', '2K', '4K']
FAL_GOOGLE_NANO_BANANA_2_RESOLUTIONS = ['0.5K', '1K', '2K', '4K']
FAL_GOOGLE_SAFETY_TOLERANCE_OPTIONS = ['1', '2', '3', '4', '5', '6']
FAL_GOOGLE_THINKING_LEVEL_OPTIONS = ['minimal', 'high']

FAL_XAI_IMAGE_RATIOS = [
    '2:1',
    '20:9',
    '19.5:9',
    '16:9',
    '4:3',
    '3:2',
    '1:1',
    '2:3',
    '3:4',
    '9:16',
    '9:19.5',
    '9:20',
    '1:2',
]
FAL_XAI_EDIT_IMAGE_RATIOS = ['auto', *FAL_XAI_IMAGE_RATIOS]
FAL_XAI_RESOLUTIONS = ['1k', '2k']

FAL_BACKGROUND_OPTIONS = ['auto', 'transparent', 'opaque']
FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO = ['low', 'medium', 'high']
FAL_OPENAI_INPUT_FIDELITY_OPTIONS = ['low', 'high']
FAL_ALIBABA_ACCELERATION_OPTIONS = ['none', 'regular', 'high']

FAL_ALIBABA_NAMED_SIZES = [
    '1280x720',
    '1024x768',
    '720x1280',
    '768x1024',
    '1024x1024',
    '512x512',
]


def _option_field(
    field: str,
    options: list[str],
    default: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    return {
        'field': field,
        'options': options,
        **({'default': default} if default is not None else {}),
        **({'source': source} if source else {}),
    }


def _boolean_field(field: str, default: bool | None = None, source: str | None = None) -> dict[str, Any]:
    return {
        'field': field,
        **({'default': default} if default is not None else {}),
        **({'source': source} if source else {}),
    }


def _integer_field(
    field: str,
    source: str | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> dict[str, Any]:
    return {
        'field': field,
        **({'source': source} if source else {}),
        **({'min': minimum} if minimum is not None else {}),
        **({'max': maximum} if maximum is not None else {}),
    }


def _text_field(field: str, source: str | None = None) -> dict[str, Any]:
    return {'field': field, **({'source': source} if source else {})}


def _base_model(
    id: str,
    name: str,
    provider: str,
    task: str,
    generation_model: str | None = None,
    edit_model: str | None = None,
) -> dict[str, Any]:
    return {
        'id': id,
        'name': name,
        'provider': provider,
        'task': task,
        **({'generation_model': generation_model} if generation_model else {}),
        **({'edit_model': edit_model} if edit_model else {}),
        'image_counts': FAL_IMAGE_COUNTS,
        'count_field': 'num_images',
        'boolean_fields': [_boolean_field('sync_mode')],
    }


def _apply_image_input(
    model: dict[str, Any],
    task: str,
    image_input_field: str | None,
    image_input_max_count: int | None,
) -> None:
    """Attach image-input semantics to an Alibaba model descriptor in-place.

    Mirrors `_custom_size_model`'s convention: image-to-image siblings declare
    how reference images are fed to fal. Multi-image endpoints leave
    `image_input_field` unset to ride the engine default (`image_urls`);
    single-image endpoints override it to `'image_url'` and clamp
    `image_input_max_count` to 1 so the gallery caps uploads accordingly.
    """
    if task != 'image-to-image':
        return
    if image_input_field is not None:
        model['image_input_field'] = image_input_field
    elif 'image_input_field' not in model:
        model['image_input_field'] = 'image_urls'
    if image_input_max_count is not None:
        model['image_input_max_count'] = image_input_max_count


def _custom_size_model(
    id: str,
    name: str,
    provider: str,
    task: str,
    aspect_ratio_sizes: dict[str, str],
    default_aspect_ratio: str,
    generation_model: str | None = None,
    edit_model: str | None = None,
) -> dict[str, Any]:
    return {
        **_base_model(id, name, provider, task, generation_model, edit_model),
        'aspect_ratios': list(aspect_ratio_sizes),
        'aspect_ratio_sizes': aspect_ratio_sizes,
        'resolutions': [],
        'default_aspect_ratio': default_aspect_ratio,
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'png',
        'resolution_field': 'image_size',
        'custom_size_field': 'image_size',
        **({'image_input_field': 'image_urls'} if task == 'image-to-image' else {}),
    }


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
    task: str = 'text-to-image',
    generation_model: str | None = None,
    edit_model: str | None = None,
    image_input_field: str | None = None,
    image_input_max_count: int | None = None,
) -> dict[str, Any]:
    image_size_whitelist = {resolution: resolution for resolution in resolutions}
    model: dict[str, Any] = {
        **_base_model(id, name, 'alibaba', task, generation_model, edit_model),
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
    _apply_image_input(model, task, image_input_field, image_input_max_count)
    return model


def _alibaba_qwen2_model(
    id: str,
    name: str,
    default_image_size: str,
    hosting: str,
    *,
    task: str = 'text-to-image',
    generation_model: str | None = None,
    edit_model: str | None = None,
    image_input_field: str | None = None,
    image_input_max_count: int | None = None,
) -> dict[str, Any]:
    model: dict[str, Any] = {
        **_base_model(id, name, 'alibaba', task, generation_model, edit_model),
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
    _apply_image_input(model, task, image_input_field, image_input_max_count)
    return model


def _alibaba_wan_model(
    id: str,
    name: str,
    default_image_size: str,
    hosting: str,
    count_field: str | None,
    image_counts: list[int],
    output_formats: list[str],
    prompt_expansion_default: bool = True,
    *,
    task: str = 'text-to-image',
    generation_model: str | None = None,
    edit_model: str | None = None,
    image_input_field: str | None = None,
    image_input_max_count: int | None = None,
) -> dict[str, Any]:
    model: dict[str, Any] = {
        **_base_model(id, name, 'alibaba', task, generation_model, edit_model),
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
    _apply_image_input(model, task, image_input_field, image_input_max_count)
    return model


def _google_model(
    id: str,
    name: str,
    task: str,
    aspect_ratios: list[str],
    default_aspect_ratio: str,
    generation_model: str | None = None,
    edit_model: str | None = None,
    resolutions: list[str] | None = None,
    default_resolution: str | None = None,
    supports_system_prompt: bool = False,
    supports_thinking: bool = False,
    supports_web_search: bool = False,
) -> dict[str, Any]:
    option_fields = [_option_field('safety_tolerance', FAL_GOOGLE_SAFETY_TOLERANCE_OPTIONS, '6')]
    if supports_thinking:
        option_fields.append(_option_field('thinking_level', FAL_GOOGLE_THINKING_LEVEL_OPTIONS))

    boolean_fields = [_boolean_field('sync_mode'), _boolean_field('limit_generations')]
    if supports_web_search:
        boolean_fields.append(_boolean_field('enable_web_search'))

    return {
        **_base_model(id, name, 'google', task, generation_model, edit_model),
        'aspect_ratios': aspect_ratios,
        **({'resolutions': resolutions} if resolutions else {}),
        'default_aspect_ratio': default_aspect_ratio,
        **({'default_resolution': default_resolution} if default_resolution else {}),
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'png',
        'aspect_ratio_field': 'aspect_ratio',
        'resolution_field': 'resolution' if resolutions else None,
        **({'image_input_field': 'image_urls'} if task == 'image-to-image' else {}),
        'supports_system_prompt': supports_system_prompt,
        'option_fields': option_fields,
        'boolean_fields': boolean_fields,
        'integer_fields': [_integer_field('seed')],
    }


def _openai_model(
    id: str,
    name: str,
    task: str,
    image_sizes: list[str],
    default_image_size: str,
    generation_model: str | None = None,
    edit_model: str | None = None,
    quality_default: str = 'low',
    supports_background: bool = True,
    quality_options: list[str] | None = None,
    supports_input_fidelity: bool = False,
    mask_field: str | None = None,
) -> dict[str, Any]:
    option_fields = [
        _option_field('quality', quality_options or FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO, quality_default)
    ]
    if supports_background:
        option_fields.append(_option_field('background', FAL_BACKGROUND_OPTIONS, 'auto'))
    if supports_input_fidelity:
        option_fields.append(_option_field('input_fidelity', FAL_OPENAI_INPUT_FIDELITY_OPTIONS))

    return {
        **_base_model(id, name, 'openai', task, generation_model, edit_model),
        'aspect_ratios': [],
        'resolutions': image_sizes,
        'default_aspect_ratio': 'auto',
        'default_resolution': default_image_size,
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'png',
        'resolution_field': 'image_size',
        **({'image_input_field': 'image_urls'} if task == 'image-to-image' else {}),
        'option_fields': option_fields,
        **({'text_fields': [_text_field(mask_field)]} if mask_field else {}),
    }


def _xai_model(
    id: str,
    name: str,
    task: str,
    generation_model: str | None = None,
    edit_model: str | None = None,
) -> dict[str, Any]:
    is_edit = task == 'image-to-image'
    return {
        **_base_model(id, name, 'xai', task, generation_model, edit_model),
        'aspect_ratios': FAL_XAI_EDIT_IMAGE_RATIOS if is_edit else FAL_XAI_IMAGE_RATIOS,
        'resolutions': FAL_XAI_RESOLUTIONS,
        'default_aspect_ratio': 'auto' if is_edit else '1:1',
        'default_resolution': '1k',
        'output_formats': FAL_OUTPUT_FORMATS,
        'default_output_format': 'jpeg',
        'aspect_ratio_field': 'aspect_ratio',
        'resolution_field': 'resolution',
        **({'image_input_field': 'image_urls', 'image_input_max_count': 3} if is_edit else {}),
    }
