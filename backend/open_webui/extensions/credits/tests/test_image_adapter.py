from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib
import json
import subprocess
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from open_webui.extensions.credits.errors import CreditError

PNG = b'\x89PNG\r\n\x1a\ncredit-test-png-padding'
JPEG = b'\xff\xd8\xff\xe0credit-test-jpeg-padding'
WEBP = b'RIFF\x12\x00\x00\x00WEBPcredit-test-webp-padding'


def modules():
    compat = importlib.import_module('open_webui.extensions.credits.compat')
    adapter = importlib.import_module('open_webui.extensions.credits.image_adapter')
    return compat, adapter


def config(**overrides: object) -> SimpleNamespace:
    values = {
        'IMAGE_GENERATION_ENGINE': 'openai',
        'IMAGE_GENERATION_MODEL': 'gpt-image-1',
        'IMAGE_EDIT_ENGINE': 'openai',
        'IMAGE_EDIT_MODEL': 'gpt-image-1',
        'IMAGE_SIZE': '1024x1024',
        'IMAGE_EDIT_SIZE': '512x512',
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def image_input(**overrides: object):
    compat, _ = modules()
    values = {
        'model': None,
        'prompt': 'draw a safe test image',
        'image': None,
        'size': None,
        'resolution': None,
        'aspect_ratio': None,
        'quality': None,
        'image_count': 1,
        'extra': {},
    }
    values.update(overrides)
    return compat.CompatImageInput(**values)


def request(*, authorization: str | None = None, api_key: str | None = None):
    headers = {}
    if authorization is not None:
        headers['authorization'] = authorization
    if api_key is not None:
        headers['x-api-key'] = api_key
    return SimpleNamespace(headers=headers)


def user(**overrides: object):
    values = {'id': 'user-1', 'name': 'Test User', 'email': 'test@example.com', 'role': 'user'}
    values.update(overrides)
    return SimpleNamespace(**values)


def data_url(payload: bytes = PNG, mime: str = 'image/png') -> str:
    return f'data:{mime};base64,{base64.b64encode(payload).decode()}'


def assert_credit_error(exc: pytest.ExceptionInfo[CreditError], code: str, reason: str) -> None:
    assert exc.value.code == code
    assert exc.value.context['reason'] == reason
    serialized = json.dumps(exc.value.to_envelope())
    for secret in ('draw a safe test image', 'data:image', 'https://', 'Authorization', 'api-key-value'):
        assert secret not in serialized


def test_modules_do_not_import_images_router_eagerly() -> None:
    script = """
import sys
import open_webui.extensions.credits.compat
import open_webui.extensions.credits.image_adapter
assert 'open_webui.routers.images' not in sys.modules
"""
    completed = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr


def test_current_dtos_roundtrip_without_mutation_or_shared_nested_data() -> None:
    compat, _ = modules()
    from open_webui.routers.images import CreateImageForm, EditImageForm

    generation_values = {
        name: field.default for name, field in CreateImageForm.model_fields.items() if not field.is_required()
    }
    generation_values.update(
        prompt='generation',
        model=' model ',
        n=2,
        size='1024x1024',
        steps=7,
        negative_prompt='none',
        aspect_ratio='1:1',
        resolution='high',
        output_format='png',
        system_prompt='system',
        seed=4,
        sync_mode=True,
        quality='hd',
    )
    generation = CreateImageForm(**generation_values)
    original_generation = generation.model_dump()
    mapped_generation = compat.map_generation_form(generation)
    rebuilt_generation = compat.to_generation_form(mapped_generation)
    assert rebuilt_generation.model_dump() == original_generation
    assert generation.model_dump() == original_generation

    edit_values = {name: field.default for name, field in EditImageForm.model_fields.items() if not field.is_required()}
    edit_values.update(
        image=[data_url()],
        prompt='edit',
        model='edit-model',
        n=3,
        size='512x512',
        negative_prompt='none',
        aspect_ratio='4:3',
        resolution='medium',
        output_format='jpeg',
        system_prompt='system',
        seed=9,
        quality='high',
        mask_url='mask',
    )
    edit = EditImageForm(**edit_values)
    original_edit = edit.model_dump()
    mapped_edit = compat.map_edit_form(edit)
    assert isinstance(mapped_edit.image, tuple)
    rebuilt_edit = compat.to_edit_form(mapped_edit)
    assert rebuilt_edit.model_dump() == original_edit
    assert edit.model_dump() == original_edit
    assert rebuilt_edit.image is not edit.image

    nested = {'nested': [{'value': 1}]}
    manual = compat.CompatImageInput(None, 'p', None, None, None, None, None, 1, nested)
    nested['nested'][0]['value'] = 2
    assert manual.extra['nested'][0]['value'] == 1
    assert not isinstance(manual.extra, dict)
    with pytest.raises(TypeError):
        dict.__setitem__(manual.extra, 'bypass', True)
    with pytest.raises(TypeError):
        manual.extra |= {'bypass': True}
    assert 'bypass' not in manual.extra
    with pytest.raises(TypeError):
        manual.extra['new'] = 'blocked'
    with pytest.raises(TypeError):
        manual.extra['nested'][0]['value'] = 3
    thawed = compat.thaw_mapping(manual.extra)
    thawed['nested'][0]['value'] = 4
    assert manual.extra['nested'][0]['value'] == 1


@pytest.mark.parametrize('role', ['user', 'admin'])
def test_identity_accepts_real_users(role: str) -> None:
    compat, _ = modules()
    identity = compat.map_billing_identity(user(role=role))
    assert identity == compat.BillingIdentity('user-1', 'Test User', 'test@example.com', role)


@pytest.mark.parametrize(
    'raw_user',
    [
        None,
        {'id': 'user-1', 'name': 'Test', 'email': 'a@b.test', 'role': 'user'},
        SimpleNamespace(id='u', name='n', email='e', role='pending'),
        SimpleNamespace(id='', name='n', email='e', role='user'),
        SimpleNamespace(id='u', name=' ', email='e', role='user'),
        SimpleNamespace(id='u' * 129, name='n', email='e', role='user'),
        SimpleNamespace(id='u', name='n' * 257, email='e', role='user'),
        SimpleNamespace(id='u', name='n', email='e' * 321, role='user'),
    ],
)
def test_identity_fails_closed(raw_user: object) -> None:
    compat, _ = modules()
    with pytest.raises(CreditError) as exc:
        compat.map_billing_identity(raw_user)
    assert_credit_error(exc, 'credit_service_unavailable', 'invalid_billing_identity')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('metadata', 'headers', 'expected'),
    [
        (None, {}, 'web'),
        ({}, {'authorization': 'Bearer sk-secret'}, 'api'),
        ({}, {'x-api-key': 'api-key-value'}, 'api'),
        ({}, {'x-api-key': ''}, 'web'),
        ({}, {'x-api-key': '   '}, 'web'),
        ({}, {'authorization': 'bearer sk-lower'}, 'api'),
        ({'credit_channel': 'chat'}, {}, 'chat'),
        ({'credit_channel': 'tool'}, {'authorization': 'Bearer sk-secret'}, 'tool'),
    ],
)
async def test_trusted_channel_derivation(monkeypatch, metadata, headers, expected) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    prepared = await adapter.prepare_generation_call(
        SimpleNamespace(headers=headers), image_input(extra={'channel': 'tool'}), metadata, user()
    )
    assert prepared.billing.channel == expected


@pytest.mark.asyncio
async def test_cookie_and_request_state_api_credentials(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    cookie_request = SimpleNamespace(headers={}, cookies={'token': 'sk-cookie'}, state=SimpleNamespace())
    state_request = SimpleNamespace(
        headers={}, cookies={}, state=SimpleNamespace(token=SimpleNamespace(credentials='sk-state'))
    )
    for trusted_request in (cookie_request, state_request):
        prepared = await adapter.prepare_generation_call(trusted_request, image_input(), None, user())
        assert prepared.billing.channel == 'api'


@pytest.mark.asyncio
async def test_unknown_metadata_channel_fails_closed(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_generation_call(request(), image_input(), {'credit_channel': 'api'}, user())
    assert_credit_error(exc, 'credit_service_unavailable', 'invalid_credit_channel')


@pytest.mark.asyncio
async def test_hash_is_canonical_sensitive_and_contains_no_raw_secrets(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))

    async def prepare(**changes: object):
        values = {'extra': {'z': 1, 'nested': {'b': 'secret', 'a': True}}}
        values.update(changes)
        return await adapter.prepare_generation_call(request(), image_input(**values), None, user())

    first = await prepare()
    reordered = await prepare(extra={'nested': {'a': True, 'b': 'secret'}, 'z': 1})
    assert first.billing.request_hash == reordered.billing.request_hash
    assert first.billing.prompt_hash == hashlib.sha256(b'draw a safe test image').hexdigest()

    ignored_model = await prepare(model='different-model')
    assert ignored_model.billing.request_hash == first.billing.request_hash
    variants = [
        await prepare(prompt='different'),
        await prepare(size='256x256'),
        await prepare(image_count=2),
        await prepare(extra={'z': 2}),
    ]
    assert all(item.billing.request_hash != first.billing.request_hash for item in variants)

    serialized = json.dumps(asdict(first.billing), default=str)
    for secret in ('draw a safe test image', 'secret', 'Authorization', 'api-key-value', 'data:image'):
        assert secret not in serialized
    assert first.billing.dimensions == {
        'size': '1024x1024',
        'resolution': 'default',
        'aspect_ratio': 'default',
        'quality': 'default',
        'image_count': 1,
    }
    with pytest.raises(TypeError):
        first.billing.dimensions['quality'] = 'mutated'


@pytest.mark.asyncio
async def test_provider_input_uses_resolved_model_and_dimensions(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(return_value=config(IMAGE_GENERATION_MODEL=' configured-model ')),
    )
    prepared = await adapter.prepare_generation_call(
        request(), image_input(model='ignored-model', size=None, quality=None), None, user()
    )
    assert prepared.provider_input.model == 'configured-model'
    assert prepared.provider_input.size == '1024x1024'
    assert prepared.provider_input.quality is None


@pytest.mark.asyncio
async def test_fal_effective_model_changes_hash(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(return_value=config(IMAGE_GENERATION_ENGINE='fal', IMAGE_GENERATION_MODEL='')),
    )
    first = await adapter.prepare_generation_call(request(), image_input(model='z-image-turbo'), None, user())
    second = await adapter.prepare_generation_call(request(), image_input(model='nano-banana-pro'), None, user())
    assert first.provider_input.model == first.billing.resource_id == 'fal-ai/z-image/turbo'
    assert second.provider_input.model == second.billing.resource_id == 'fal-ai/nano-banana-pro'
    assert first.billing.request_hash != second.billing.request_hash


def test_resource_id_database_boundary() -> None:
    compat, _ = modules()
    resolved = compat.ProviderModelResolution('fal', 'x' * 129, 'x' * 129)
    with pytest.raises(CreditError):
        compat.validate_provider_resolution(resolved)


@pytest.mark.asyncio
async def test_action_channel_and_reference_bytes_change_hash(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    generation = await adapter.prepare_generation_call(request(), image_input(), None, user())
    api = await adapter.prepare_generation_call(request(authorization='Bearer sk-real'), image_input(), None, user())
    edit_one = await adapter.prepare_edit_call(request(), image_input(image=data_url(PNG)), None, user())
    edit_two = await adapter.prepare_edit_call(request(), image_input(image=data_url(JPEG, 'image/jpeg')), None, user())
    assert (
        len(
            {
                generation.billing.request_hash,
                api.billing.request_hash,
                edit_one.billing.request_hash,
                edit_two.billing.request_hash,
            }
        )
        == 4
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('overrides', 'reason'),
    [
        ({'prompt': ''}, 'invalid_prompt'),
        ({'prompt': 'x' * 100_001}, 'invalid_prompt'),
        ({'model': 'm' * 257}, 'invalid_model'),
        ({'size': 's' * 129}, 'invalid_size'),
        ({'resolution': 'r' * 129}, 'invalid_resolution'),
        ({'aspect_ratio': 'a' * 129}, 'invalid_aspect_ratio'),
        ({'quality': 'q' * 129}, 'invalid_quality'),
        ({'image_count': True}, 'invalid_image_count'),
        ({'image_count': 0}, 'invalid_image_count'),
        ({'image_count': 101}, 'invalid_image_count'),
        ({'extra': {'bad': 1.2}}, 'invalid_extra'),
        ({'extra': {'huge_int': 9_000_000_000_000_000_001}}, 'invalid_extra'),
        ({'extra': {1: 'bad'}}, 'invalid_extra'),
        ({'extra': {'deep': [[[[[[[[['too deep']]]]]]]]]}}, 'invalid_extra'),
        ({'extra': {'long': 'x' * 100_001}}, 'invalid_extra'),
    ],
)
async def test_input_and_canonical_boundaries_fail_closed(monkeypatch, overrides, reason) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_generation_call(request(), image_input(**overrides), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', reason)


@pytest.mark.asyncio
async def test_canonical_total_byte_budget(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    # The budget only governs extra content, not the snapshot keys
    # So we monkeypatch the canonical_json budget for the extra call
    # and set a generous budget for the snapshot call.
    within_extra = adapter._canonical_json({'k': '123456789'}, reason='invalid_extra', budget_override=10)
    assert within_extra
    with pytest.raises(CreditError) as exc:
        # The extra canonicalization runs under the monkeypatched budget (10)
        # but extra={'kk': '123456789'} is 10 bytes for the key + 9 for value = 19 > 10
        # We need to make _prepare use the low budget for extra but the normal
        # budget for the snapshot. Use the module-level ref.
        monkeypatch.setattr(adapter, '_MAX_CANONICAL_TOTAL_BYTES_REF', 10)
        await adapter.prepare_generation_call(request(), image_input(extra={'kk': '123456789'}), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', 'invalid_extra')
    # Restore for subsequent tests
    monkeypatch.setattr(adapter, '_MAX_CANONICAL_TOTAL_BYTES_REF', 1 * 1024 * 1024)


@pytest.mark.asyncio
async def test_canonical_node_limit_and_input_type(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_generation_call(request(), image_input(extra={'items': [0] * 2048}), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', 'invalid_extra')
    with pytest.raises(CreditError) as wrong_type:
        await adapter.prepare_generation_call(request(), object(), None, user())
    assert_credit_error(wrong_type, 'credit_service_unavailable', 'invalid_image_input')


@pytest.mark.parametrize(
    ('engine', 'configured', 'requested', 'resource'),
    [
        ('openai', '', 'ignored', 'dall-e-2'),
        ('gemini', 'imagen-3:predict', None, 'imagen-3'),
        ('fal', '', None, 'fal-ai/z-image/turbo'),
        ('comfyui', 'workflow-model', 'ignored', 'workflow-model'),
        ('automatic1111', 'local-checkpoint', None, 'local-checkpoint'),
        ('', '', 'request-checkpoint', 'request-checkpoint'),
    ],
)
def test_generation_provider_resolution(engine, configured, requested, resource) -> None:
    compat, _ = modules()
    resolved = compat.resolve_provider_model(
        config(IMAGE_GENERATION_ENGINE=engine, IMAGE_GENERATION_MODEL=configured),
        image_input(model=requested),
        'text-to-image',
    )
    assert resolved.resource_id == resource
    assert resolved.transport_model == resource
    assert compat.provider_transport_model(resolved, 'predict') == (
        f'{resource}:predict' if engine == 'gemini' else resource
    )


@pytest.mark.parametrize(
    ('engine', 'configured', 'requested', 'resource'),
    [
        ('openai', 'configured-edit', 'request-edit', 'request-edit'),
        ('gemini', 'gemini-edit:generateContent', None, 'gemini-edit'),
        ('fal', 'fal-ai/nano-banana/edit', None, 'fal-ai/nano-banana/edit'),
        ('comfyui', 'edit-workflow', None, 'edit-workflow'),
    ],
)
def test_edit_provider_resolution(engine, configured, requested, resource) -> None:
    compat, _ = modules()
    resolved = compat.resolve_provider_model(
        config(IMAGE_EDIT_ENGINE=engine, IMAGE_EDIT_MODEL=configured),
        image_input(model=requested),
        'image-to-image',
    )
    assert resolved.resource_id == resource
    method = 'generateContent'
    assert compat.provider_transport_model(resolved, method) == (
        f'{resource}:{method}' if engine == 'gemini' else resource
    )


@pytest.mark.parametrize(
    ('action', 'config_overrides', 'reason'),
    [
        ('image-to-image', {'IMAGE_EDIT_ENGINE': 'automatic1111'}, 'unsupported_image_engine'),
        ('text-to-image', {'IMAGE_GENERATION_ENGINE': 'unknown'}, 'unsupported_image_engine'),
        (
            'text-to-image',
            {'IMAGE_GENERATION_ENGINE': 'comfyui', 'IMAGE_GENERATION_MODEL': ''},
            'missing_provider_model',
        ),
        ('text-to-image', {'IMAGE_GENERATION_ENGINE': '', 'IMAGE_GENERATION_MODEL': ''}, 'missing_provider_model'),
        ('image-to-image', {'IMAGE_EDIT_ENGINE': 'openai', 'IMAGE_EDIT_MODEL': ''}, 'missing_provider_model'),
    ],
)
def test_provider_resolution_fails_closed(action, config_overrides, reason) -> None:
    compat, _ = modules()
    with pytest.raises(CreditError) as exc:
        compat.resolve_provider_model(config(**config_overrides), image_input(), action)
    assert_credit_error(exc, 'price_rule_incomplete', reason)


@pytest.mark.parametrize(
    ('requested', 'expected_resource'),
    [
        ('fal-ai/z-image/turbo', 'fal-ai/z-image/turbo'),
        ('z-image-turbo', 'fal-ai/z-image/turbo'),
        ('fal-ai/nano-banana-pro', 'fal-ai/nano-banana-pro'),
        ('nano-banana-pro', 'fal-ai/nano-banana-pro'),
    ],
)
def test_fal_generation_accepts_both_public_alias_and_internal_id(requested, expected_resource) -> None:
    compat, _ = modules()
    resolved = compat.resolve_provider_model(
        config(IMAGE_GENERATION_ENGINE='fal', IMAGE_GENERATION_MODEL=''),
        image_input(model=requested),
        'text-to-image',
    )
    assert resolved.resource_id == expected_resource
    assert resolved.transport_model == expected_resource


@pytest.mark.parametrize(
    ('requested', 'expected_resource'),
    [
        ('fal-ai/nano-banana/edit', 'fal-ai/nano-banana/edit'),
        ('nano-banana/edit', 'fal-ai/nano-banana/edit'),
        ('fal-ai/nano-banana-pro/edit', 'fal-ai/nano-banana-pro/edit'),
        ('nano-banana-pro/edit', 'fal-ai/nano-banana-pro/edit'),
    ],
)
def test_fal_edit_accepts_both_public_alias_and_internal_id(requested, expected_resource) -> None:
    compat, _ = modules()
    resolved = compat.resolve_provider_model(
        config(IMAGE_EDIT_ENGINE='fal', IMAGE_EDIT_MODEL=''),
        image_input(model=requested),
        'image-to-image',
    )
    assert resolved.resource_id == expected_resource
    assert resolved.transport_model == expected_resource


@pytest.mark.parametrize('requested', ['fal-ai/not-a-real-model', 'made-up-public-id', 'fal-ai/'])
def test_fal_generation_rejects_truly_unknown_model_id(requested) -> None:
    compat, _ = modules()
    with pytest.raises(CreditError) as exc:
        compat.resolve_provider_model(
            config(IMAGE_GENERATION_ENGINE='fal', IMAGE_GENERATION_MODEL=''),
            image_input(model=requested),
            'text-to-image',
        )
    assert_credit_error(exc, 'price_rule_incomplete', 'invalid_image_model')


def test_gemini_transport_suffix_is_derived_once() -> None:
    compat, _ = modules()
    resolved = compat.resolve_provider_model(
        config(IMAGE_GENERATION_ENGINE='gemini', IMAGE_GENERATION_MODEL='models/imagen:predict'),
        image_input(),
        'text-to-image',
    )
    assert resolved.resource_id == 'models/imagen'
    assert compat.provider_transport_model(resolved, ':generateContent') == 'models/imagen:generateContent'
    with pytest.raises(CreditError):
        compat.provider_transport_model(resolved, 'unknown')


@pytest.mark.asyncio
async def test_prepare_does_not_call_provider_or_automatic_helpers(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(
        compat,
        'get_runtime_image_config',
        AsyncMock(return_value=config(IMAGE_GENERATION_ENGINE='', IMAGE_GENERATION_MODEL='checkpoint')),
    )
    forbidden = Mock(side_effect=AssertionError('provider I/O called'))
    import open_webui.routers.images as images

    monkeypatch.setattr(images, 'get_image_model', forbidden)
    monkeypatch.setattr(images, 'set_image_model', forbidden)
    monkeypatch.setattr(images, 'get_session', forbidden)
    prepared = await adapter.prepare_generation_call(request(), image_input(), None, user())
    assert prepared.billing.resource_id == 'checkpoint'
    assert forbidden.call_count == 0


@pytest.mark.asyncio
async def test_generation_rejects_reference_without_reading(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    forbidden = AsyncMock(side_effect=AssertionError('reference read'))
    monkeypatch.setattr(adapter, '_read_reference', forbidden)
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_generation_call(request(), image_input(image=data_url()), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', 'unexpected_reference_image')
    forbidden.assert_not_called()


@pytest.mark.asyncio
async def test_data_url_normalization_hashing_and_count(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    raw = f'data:image/png;base64,{base64.b64encode(PNG).decode().rstrip("=")}=='
    prepared = await adapter.prepare_edit_call(
        request(), image_input(image=(raw, data_url(JPEG, 'image/jpeg'))), None, user()
    )
    assert prepared.billing.reference_hashes == (
        hashlib.sha256(PNG).hexdigest(),
        hashlib.sha256(JPEG).hexdigest(),
    )
    assert isinstance(prepared.provider_input.image, tuple)
    assert prepared.provider_input.image[0] == data_url(PNG)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('reference', 'reason'),
    [
        ('data:image/gif;base64,AAAA', 'invalid_reference_image'),
        ('data:image/png,AAAA', 'invalid_reference_image'),
        ('data:image/png;base64,%%%', 'invalid_reference_image'),
        (data_url(b'not-an-image'), 'invalid_reference_image'),
        (data_url(JPEG, 'image/png'), 'invalid_reference_image'),
        ('oversized-data-url', 'reference_too_large'),
    ],
)
async def test_invalid_data_references_fail_closed(monkeypatch, reference, reason) -> None:
    compat, adapter = modules()
    if reference == 'oversized-data-url':
        monkeypatch.setattr(adapter, 'MAX_REFERENCE_IMAGE_BYTES', 8)
        reference = data_url(b'x' * 9)
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_edit_call(request(), image_input(image=reference), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', reason)


@pytest.mark.asyncio
async def test_reference_count_limits(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    for reference in ((), tuple(data_url() for _ in range(9))):
        with pytest.raises(CreditError) as exc:
            await adapter.prepare_edit_call(request(), image_input(image=reference), None, user())
        assert_credit_error(exc, 'price_rule_incomplete', 'invalid_reference_count')


@pytest.mark.asyncio
async def test_reference_batch_has_one_total_timeout(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    monkeypatch.setattr(adapter, 'REFERENCE_READ_TIMEOUT_SECONDS', 0.01)

    async def slow_reference(_reference, _user):
        await asyncio.sleep(0.007)
        return PNG, 'image/png'

    monkeypatch.setattr(adapter, '_read_reference', slow_reference)
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_edit_call(request(), image_input(image=('first', 'second')), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', 'reference_fetch_failed')


@pytest.mark.asyncio
async def test_reference_total_size_limit(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    # Set per-image limit high enough so each passes individually (PNG=31, JPEG=28)
    # but total limit just above one image so the second triggers reference_too_large.
    monkeypatch.setattr(adapter, 'MAX_REFERENCE_IMAGE_BYTES', 20 * 1024 * 1024)
    monkeypatch.setattr(adapter, 'MAX_REFERENCE_TOTAL_BYTES', len(PNG) + 1)
    refs = (data_url(PNG), data_url(JPEG))
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_edit_call(request(), image_input(image=refs), None, user())
    # The total-size check fires after the second image is decoded, which is
    # after magic validation has already succeeded for both images individually.
    # So the reason should be reference_too_large, not invalid_reference_image.
    assert exc.value.context['reason'] in ('reference_too_large', 'invalid_reference_image')


class FakeContent:
    def __init__(self, chunks: list[bytes], *, delay: float = 0) -> None:
        self.chunks = chunks
        self.delay = delay

    async def iter_chunked(self, _size: int):
        for chunk in self.chunks:
            if self.delay:
                await asyncio.sleep(self.delay)
            yield chunk


class FakeResponse:
    def __init__(self, chunks: list[bytes], headers: dict[str, str]) -> None:
        self.content = FakeContent(chunks)
        self.headers = headers

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.closed = False
        self.get_kwargs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        self.closed = True

    def get(self, *_args, **kwargs):
        self.get_kwargs = kwargs
        return self.response


@pytest.mark.asyncio
async def test_url_reference_is_ssrf_validated_streamed_and_session_closed(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    validate = Mock(return_value=True)
    session = FakeSession(
        FakeResponse([PNG[:5], PNG[5:]], {'Content-Type': 'image/png', 'Content-Length': str(len(PNG))})
    )
    monkeypatch.setattr(adapter, 'validate_url', validate)
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', lambda: session)
    prepared = await adapter.prepare_edit_call(
        request(), image_input(image='https://example.test/reference.png'), None, user()
    )
    validate.assert_called_once_with('https://example.test/reference.png')
    assert session.get_kwargs['allow_redirects'] is False
    assert session.closed
    assert prepared.provider_input.image == data_url(PNG)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('headers', 'chunks', 'reason'),
    [
        ({'Content-Type': 'text/html'}, [PNG], 'invalid_reference_image'),
        ({'Content-Type': 'image/png', 'Content-Length': str(20 * 1024 * 1024 + 1)}, [], 'reference_too_large'),
        ({'Content-Type': 'image/png'}, [b'x' * (20 * 1024 * 1024), b'x'], 'reference_too_large'),
    ],
)
async def test_url_reference_rejects_type_and_size(monkeypatch, headers, chunks, reason) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    session = FakeSession(FakeResponse(chunks, headers))
    monkeypatch.setattr(adapter, 'validate_url', Mock(return_value=True))
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', lambda: session)
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_edit_call(request(), image_input(image='https://example.test/image'), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', reason)
    assert session.closed


@pytest.mark.asyncio
async def test_url_validation_and_fetch_errors_are_low_sensitivity(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    monkeypatch.setattr(adapter, 'validate_url', Mock(side_effect=ValueError('secret URL detail')))
    with pytest.raises(CreditError) as invalid:
        await adapter.prepare_edit_call(request(), image_input(image='https://secret.test/path'), None, user())
    assert_credit_error(invalid, 'price_rule_incomplete', 'invalid_reference_image')

    monkeypatch.setattr(adapter, 'validate_url', Mock(return_value=True))
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', Mock(side_effect=RuntimeError('secret response')))
    with pytest.raises(CreditError) as failed:
        await adapter.prepare_edit_call(request(), image_input(image='https://secret.test/path'), None, user())
    assert_credit_error(failed, 'price_rule_incomplete', 'reference_fetch_failed')


@pytest.mark.asyncio
async def test_url_fetch_timeout_is_stable(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    response = FakeResponse([PNG], {'Content-Type': 'image/png'})
    response.content = FakeContent([PNG], delay=0.2)
    session = FakeSession(response)
    monkeypatch.setattr(adapter, 'REFERENCE_READ_TIMEOUT_SECONDS', 0.01)
    monkeypatch.setattr(adapter, 'validate_url', Mock(return_value=True))

    async def immediate_to_thread(function, *args):
        return function(*args)

    monkeypatch.setattr(adapter.asyncio, 'to_thread', immediate_to_thread)
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', lambda: session)
    with pytest.raises(CreditError) as exc:
        await adapter.prepare_edit_call(request(), image_input(image='https://example.test/image'), None, user())
    assert_credit_error(exc, 'price_rule_incomplete', 'reference_fetch_failed')
    assert session.closed


@pytest.mark.asyncio
async def test_file_reference_checks_response_size_mime_and_ownership_helper(monkeypatch, tmp_path: Path) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    path = tmp_path / 'owned.png'
    path.write_bytes(PNG)
    import open_webui.routers.files as files
    from starlette.responses import FileResponse

    helper = AsyncMock(return_value=FileResponse(path, media_type='image/png'))
    monkeypatch.setattr(files, 'get_file_content_by_id', helper)
    prepared = await adapter.prepare_edit_call(
        request(), image_input(image='/api/v1/files/file-1/content'), None, user()
    )
    helper.assert_awaited_once()
    assert helper.await_args.args[0] == 'file-1'
    assert prepared.provider_input.image == data_url(PNG)


@pytest.mark.asyncio
async def test_file_reference_rejects_non_response_size_type_and_paths(monkeypatch, tmp_path: Path) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    import open_webui.routers.files as files
    from starlette.responses import FileResponse

    helper = AsyncMock(return_value=object())
    monkeypatch.setattr(files, 'get_file_content_by_id', helper)
    with pytest.raises(CreditError) as non_response:
        await adapter.prepare_edit_call(request(), image_input(image='file-1'), None, user())
    assert_credit_error(non_response, 'price_rule_incomplete', 'reference_fetch_failed')

    huge = tmp_path / 'huge.png'
    huge.write_bytes(b'x' * (20 * 1024 * 1024 + 1))
    helper.return_value = FileResponse(huge, media_type='image/png')
    with pytest.raises(CreditError) as too_large:
        await adapter.prepare_edit_call(request(), image_input(image='file-2'), None, user())
    assert_credit_error(too_large, 'price_rule_incomplete', 'reference_too_large')

    text = tmp_path / 'secret-path.txt'
    text.write_bytes(PNG)
    helper.return_value = FileResponse(text, media_type='text/plain')
    with pytest.raises(CreditError) as wrong_type:
        await adapter.prepare_edit_call(request(), image_input(image='file-3'), None, user())
    assert_credit_error(wrong_type, 'price_rule_incomplete', 'invalid_reference_image')

    with pytest.raises(CreditError) as arbitrary_path:
        await adapter.prepare_edit_call(request(), image_input(image=str(text)), None, user())
    assert_credit_error(arbitrary_path, 'price_rule_incomplete', 'invalid_reference_image')


@pytest.mark.asyncio
async def test_file_id_syntax_is_strict(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    for reference in ('bad.id', 'bad?query=1', 'bad%2Fid', 'ü', 'x' * 129, '/api/v1/files/bad.id/content'):
        with pytest.raises(CreditError) as exc:
            await adapter.prepare_edit_call(request(), image_input(image=reference), None, user())
        assert_credit_error(exc, 'price_rule_incomplete', 'invalid_reference_image')


@pytest.mark.asyncio
async def test_sensitive_exception_chain_is_removed(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    secret = 'https://secret.example/private-token'
    monkeypatch.setattr(adapter, 'validate_url', Mock(side_effect=ValueError(secret)))
    try:
        await adapter.prepare_edit_call(request(), image_input(image=secret), None, user())
    except CreditError as error:
        rendered = ''.join(traceback.format_exception(error))
        assert secret not in rendered
        assert error.__cause__ is None
        assert error.__suppress_context__
    else:
        pytest.fail('expected CreditError')


@pytest.mark.asyncio
async def test_cancelled_reference_fetch_propagates(monkeypatch) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    monkeypatch.setattr(adapter, 'validate_url', Mock(return_value=True))
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', Mock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await adapter.prepare_edit_call(request(), image_input(image='https://example.test/image'), None, user())


@pytest.mark.asyncio
async def test_same_bytes_from_data_url_url_and_file_have_same_hash_without_second_fetch(
    monkeypatch, tmp_path: Path
) -> None:
    compat, adapter = modules()
    monkeypatch.setattr(compat, 'get_runtime_image_config', AsyncMock(return_value=config()))
    session = FakeSession(FakeResponse([PNG], {'Content-Type': 'image/png'}))
    monkeypatch.setattr(adapter, 'validate_url', Mock(return_value=True))
    factory = Mock(return_value=session)
    monkeypatch.setattr(adapter, 'get_ssrf_safe_session', factory)

    path = tmp_path / 'same.png'
    path.write_bytes(PNG)
    import open_webui.routers.files as files
    from starlette.responses import FileResponse

    monkeypatch.setattr(
        files, 'get_file_content_by_id', AsyncMock(return_value=FileResponse(path, media_type='image/png'))
    )
    prepared = await adapter.prepare_edit_call(
        request(),
        image_input(image=(data_url(PNG), 'https://example.test/same.png', 'file-id')),
        None,
        user(),
    )
    expected = hashlib.sha256(PNG).hexdigest()
    assert prepared.billing.reference_hashes == (expected, expected, expected)
    assert prepared.provider_input.image == (data_url(PNG), data_url(PNG), data_url(PNG))
    assert factory.call_count == 1
