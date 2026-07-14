from typing import Any

FAL_DEFAULT_IMAGE_MODEL = 'fal-ai/z-image/turbo'
FAL_DEFAULT_IMAGE_EDIT_MODEL = 'fal-ai/nano-banana/edit'

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
FAL_COMMON_IMAGE_RATIOS = list(FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES)
FAL_OPENAI_GPT_IMAGE_2_EDIT_ASPECT_RATIO_SIZES = {
    'auto': 'auto',
    **FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES,
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
FAL_OPENAI_QUALITY_OPTIONS = ['auto', 'low', 'medium', 'high']
FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO = ['low', 'medium', 'high']
FAL_OPENAI_INPUT_FIDELITY_OPTIONS = ['low', 'high']
FAL_ALIBABA_ACCELERATION_OPTIONS = ['none', 'regular', 'high']


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
) -> dict[str, Any]:
    return {
        **_custom_size_model(
            id,
            name,
            'alibaba',
            'text-to-image',
            FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES,
            '4:3',
        ),
        'option_fields': [_option_field('acceleration', FAL_ALIBABA_ACCELERATION_OPTIONS, 'regular')],
        'boolean_fields': [
            _boolean_field('sync_mode'),
            _boolean_field('enable_safety_checker', True),
            _boolean_field('enable_prompt_expansion'),
        ],
        'integer_fields': [_integer_field('seed'), _integer_field('num_inference_steps', 'steps', 1, 8)],
    }


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
    option_fields = [_option_field('safety_tolerance', FAL_GOOGLE_SAFETY_TOLERANCE_OPTIONS, '4')]
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
    quality_default: str = 'auto',
    supports_background: bool = True,
    quality_options: list[str] | None = None,
    supports_input_fidelity: bool = False,
    mask_field: str | None = None,
) -> dict[str, Any]:
    option_fields = [_option_field('quality', quality_options or FAL_OPENAI_QUALITY_OPTIONS, quality_default)]
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


FAL_IMAGE_MODELS: list[dict[str, Any]] = [
    _alibaba_model(
        'fal-ai/z-image/turbo',
        'Alibaba / Z Image Turbo',
    ),
    _google_model(
        'fal-ai/nano-banana',
        'Google / Nano Banana',
        'text-to-image',
        FAL_GOOGLE_IMAGE_RATIOS,
        '1:1',
        edit_model='fal-ai/nano-banana/edit',
    ),
    _google_model(
        'fal-ai/nano-banana/edit',
        'Google / Nano Banana Edit',
        'image-to-image',
        FAL_GOOGLE_AUTO_IMAGE_RATIOS,
        'auto',
        generation_model='fal-ai/nano-banana',
    ),
    _google_model(
        'fal-ai/nano-banana-pro',
        'Google / Nano Banana Pro',
        'text-to-image',
        FAL_GOOGLE_AUTO_IMAGE_RATIOS,
        '1:1',
        edit_model='fal-ai/nano-banana-pro/edit',
        resolutions=FAL_GOOGLE_PRO_RESOLUTIONS,
        default_resolution='1K',
        supports_system_prompt=True,
        supports_web_search=True,
    ),
    _google_model(
        'fal-ai/nano-banana-pro/edit',
        'Google / Nano Banana Pro Edit',
        'image-to-image',
        FAL_GOOGLE_AUTO_IMAGE_RATIOS,
        'auto',
        generation_model='fal-ai/nano-banana-pro',
        resolutions=FAL_GOOGLE_PRO_RESOLUTIONS,
        default_resolution='1K',
        supports_system_prompt=True,
        supports_web_search=True,
    ),
    _google_model(
        'fal-ai/nano-banana-2',
        'Google / Nano Banana 2',
        'text-to-image',
        FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
        'auto',
        edit_model='fal-ai/nano-banana-2/edit',
        resolutions=FAL_GOOGLE_NANO_BANANA_2_RESOLUTIONS,
        default_resolution='1K',
        supports_system_prompt=True,
        supports_thinking=True,
        supports_web_search=True,
    ),
    _google_model(
        'fal-ai/nano-banana-2/edit',
        'Google / Nano Banana 2 Edit',
        'image-to-image',
        FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
        'auto',
        generation_model='fal-ai/nano-banana-2',
        resolutions=FAL_GOOGLE_NANO_BANANA_2_RESOLUTIONS,
        default_resolution='1K',
        supports_system_prompt=True,
        supports_thinking=True,
        supports_web_search=True,
    ),
    _google_model(
        'google/nano-banana-lite',
        'Google / Nano Banana Lite',
        'text-to-image',
        FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
        'auto',
        edit_model='google/nano-banana-lite/edit',
        supports_system_prompt=True,
        supports_thinking=True,
    ),
    _google_model(
        'google/nano-banana-lite/edit',
        'Google / Nano Banana Lite Edit',
        'image-to-image',
        FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
        'auto',
        generation_model='google/nano-banana-lite',
        supports_system_prompt=True,
        supports_thinking=True,
    ),
    _google_model(
        'google/nano-banana-2-lite',
        'Google / Nano Banana 2 Lite',
        'text-to-image',
        FAL_GOOGLE_EXTREME_IMAGE_RATIOS,
        'auto',
        supports_system_prompt=True,
        supports_thinking=True,
    ),
    {
        **_custom_size_model(
            'openai/gpt-image-2',
            'OpenAI / GPT Image 2',
            'openai',
            'text-to-image',
            FAL_COMMON_IMAGE_ASPECT_RATIO_SIZES,
            '4:3',
            edit_model='openai/gpt-image-2/edit',
        ),
        'option_fields': [_option_field('quality', FAL_OPENAI_QUALITY_OPTIONS, 'high')],
    },
    {
        **_custom_size_model(
            'openai/gpt-image-2/edit',
            'OpenAI / GPT Image 2 Edit',
            'openai',
            'image-to-image',
            FAL_OPENAI_GPT_IMAGE_2_EDIT_ASPECT_RATIO_SIZES,
            'auto',
            generation_model='openai/gpt-image-2',
        ),
        'option_fields': [_option_field('quality', FAL_OPENAI_QUALITY_OPTIONS, 'high')],
        'text_fields': [_text_field('mask_url')],
    },
    _openai_model(
        'fal-ai/gpt-image-1.5',
        'OpenAI / GPT Image 1.5',
        'text-to-image',
        FAL_OPENAI_GPT_IMAGE_15_SIZES,
        '1024x1024',
        edit_model='fal-ai/gpt-image-1.5/edit',
        quality_default='high',
        quality_options=FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO,
    ),
    _openai_model(
        'fal-ai/gpt-image-1.5/edit',
        'OpenAI / GPT Image 1.5 Edit',
        'image-to-image',
        FAL_OPENAI_GPT_IMAGE_SIZES,
        'auto',
        generation_model='fal-ai/gpt-image-1.5',
        quality_default='high',
        quality_options=FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO,
        supports_input_fidelity=True,
        mask_field='mask_image_url',
    ),
    _openai_model(
        'fal-ai/gpt-image-1-mini',
        'OpenAI / GPT Image 1 Mini',
        'text-to-image',
        FAL_OPENAI_GPT_IMAGE_SIZES,
        'auto',
        edit_model='fal-ai/gpt-image-1-mini/edit',
    ),
    _openai_model(
        'fal-ai/gpt-image-1-mini/edit',
        'OpenAI / GPT Image 1 Mini Edit',
        'image-to-image',
        FAL_OPENAI_GPT_IMAGE_SIZES,
        'auto',
        generation_model='fal-ai/gpt-image-1-mini',
    ),
    _openai_model(
        'fal-ai/gpt-image-1/text-to-image',
        'OpenAI / GPT Image 1',
        'text-to-image',
        FAL_OPENAI_GPT_IMAGE_SIZES,
        'auto',
        edit_model='fal-ai/gpt-image-1/edit-image',
        quality_options=FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO,
    ),
    _openai_model(
        'fal-ai/gpt-image-1/edit-image',
        'OpenAI / GPT Image 1 Edit',
        'image-to-image',
        FAL_OPENAI_GPT_IMAGE_SIZES,
        'auto',
        generation_model='fal-ai/gpt-image-1/text-to-image',
        quality_options=FAL_OPENAI_QUALITY_OPTIONS_WITHOUT_AUTO,
        supports_input_fidelity=True,
    ),
    _xai_model(
        'xai/grok-imagine-image',
        'xAI / Grok Imagine',
        'text-to-image',
        edit_model='xai/grok-imagine-image/edit',
    ),
    _xai_model(
        'xai/grok-imagine-image/edit',
        'xAI / Grok Imagine Edit',
        'image-to-image',
        generation_model='xai/grok-imagine-image',
    ),
    _xai_model(
        'xai/grok-imagine-image/quality/text-to-image',
        'xAI / Grok Imagine Pro',
        'text-to-image',
        edit_model='xai/grok-imagine-image/quality/edit',
    ),
    _xai_model(
        'xai/grok-imagine-image/quality/edit',
        'xAI / Grok Imagine Pro Edit',
        'image-to-image',
        generation_model='xai/grok-imagine-image/quality/text-to-image',
    ),
]
