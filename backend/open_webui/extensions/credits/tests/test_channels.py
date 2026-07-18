from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('function_name', 'form_kwargs', 'action'),
    [
        ('generate_image', {'prompt': 'Draw a tree'}, 'text-to-image'),
        ('edit_image', {'prompt': 'Turn it blue', 'image_urls': ['image-1']}, 'image-to-image'),
    ],
)
async def test_builtin_image_tools_forward_stable_tool_metadata(
    monkeypatch, function_name, form_kwargs, action
) -> None:
    import open_webui.tools.builtin as builtin

    invoke = AsyncMock(return_value=[{'url': '/api/v1/files/result/content'}])
    monkeypatch.setattr(builtin, 'image_generations' if action == 'text-to-image' else 'image_edits', invoke)
    function = getattr(builtin, function_name)
    metadata = {
        'chat_id': 'chat-1',
        'message_id': 'message-1',
        'call_instance_id': 'tool-call-1',
        'credit_channel': 'untrusted',
    }

    await function(
        **form_kwargs,
        __request__=SimpleNamespace(),
        __metadata__=metadata,
    )

    assert invoke.await_args.kwargs['metadata'] == {
        'credit_channel': 'tool',
        'chat_id': 'chat-1',
        'message_id': 'message-1',
        'call_instance_id': 'tool-call-1',
    }
    assert metadata['credit_channel'] == 'untrusted'


@pytest.mark.asyncio
async def test_builtin_image_tools_return_sanitized_domain_error(monkeypatch) -> None:
    import open_webui.tools.builtin as builtin

    monkeypatch.setattr(builtin, 'image_generations', AsyncMock(side_effect=RuntimeError('provider-api-key-secret')))

    result = await builtin.generate_image(prompt='Draw a tree', __request__=SimpleNamespace())

    assert json.loads(result) == {
        'error': {
            'code': 'credit_service_unavailable',
            'message': 'Credit service is unavailable',
            'context': {},
        }
    }
    assert 'provider-api-key-secret' not in result


@pytest.mark.asyncio
async def test_builtin_image_tools_return_domain_error_without_request_context() -> None:
    import open_webui.tools.builtin as builtin

    result = await builtin.generate_image(prompt='Draw a tree')

    assert json.loads(result) == {
        'error': {
            'code': 'credit_service_unavailable',
            'message': 'Credit service is unavailable',
            'context': {},
        }
    }


@pytest.mark.asyncio
async def test_tool_execution_rebinds_builtin_metadata_with_tool_call_id() -> None:
    from open_webui.tools import builtin
    from open_webui.utils import tools

    async def original(*, __metadata__: dict | None = None):
        return __metadata__

    bound = await tools.get_async_tool_function_and_apply_extra_params(
        original,
        {'__metadata__': {'chat_id': 'chat-1', 'message_id': 'message-1'}},
    )
    rebound = await tools.get_updated_tool_function(
        bound,
        {
            '__metadata__': builtin._image_credit_metadata(
                {
                    'chat_id': 'chat-1',
                    'message_id': 'message-1',
                    'call_instance_id': 'tool-call-1',
                },
                None,
                None,
            )
        },
    )

    assert await rebound() == {
        'credit_channel': 'tool',
        'chat_id': 'chat-1',
        'message_id': 'message-1',
        'call_instance_id': 'tool-call-1',
    }


def test_tool_call_metadata_uses_tool_call_id_without_mutating_request_metadata() -> None:
    from open_webui.utils import middleware

    request_metadata = {
        'chat_id': 'chat-1',
        'message_id': 'message-1',
        'credit_channel': 'untrusted',
    }

    first = middleware.build_tool_credit_metadata(request_metadata, 'tool-call-1')
    replay = middleware.build_tool_credit_metadata(request_metadata, 'tool-call-1')
    second = middleware.build_tool_credit_metadata(request_metadata, 'tool-call-2')

    assert (
        first
        == replay
        == {
            'chat_id': 'chat-1',
            'message_id': 'message-1',
            'credit_channel': 'tool',
            'call_instance_id': 'tool-call-1',
        }
    )
    assert second['call_instance_id'] == 'tool-call-2'
    assert request_metadata['credit_channel'] == 'untrusted'


def test_tool_call_metadata_omits_unstable_call_instance_id() -> None:
    from open_webui.utils import middleware

    metadata = middleware.build_tool_credit_metadata({'chat_id': 'chat-1', 'message_id': 'message-1'}, '')

    assert metadata == {
        'chat_id': 'chat-1',
        'message_id': 'message-1',
        'credit_channel': 'tool',
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('has_images', 'expected_action'),
    [(False, 'text-to-image'), (True, 'image-to-image')],
)
async def test_chat_image_handler_forwards_stable_action_sequence_metadata(
    monkeypatch, has_images, expected_action
) -> None:
    from open_webui.utils import middleware

    image_call = AsyncMock(return_value=[{'url': '/api/v1/files/result/content'}])
    monkeypatch.setattr(
        middleware,
        'image_edits' if has_images else 'image_generations',
        image_call,
    )
    monkeypatch.setattr(middleware, 'get_last_user_message', lambda _messages: 'Draw a tree')
    monkeypatch.setattr(middleware, 'get_images_from_messages', lambda _messages: [['image-1']] if has_images else [])

    async def config_get(key, *_args):
        return key == 'images.edit.enable' if has_images else False

    monkeypatch.setattr(middleware.Config, 'get', config_get)
    event_emitter = AsyncMock()
    form_data = {'model': 'model-1', 'messages': [{'role': 'user', 'content': 'Draw a tree'}]}

    await middleware.chat_image_generation_handler(
        SimpleNamespace(),
        form_data,
        {
            '__metadata__': {'chat_id': 'local:chat-1', 'message_id': 'message-1'},
            '__event_emitter__': event_emitter,
        },
        SimpleNamespace(id='user-1'),
    )

    assert image_call.await_args.kwargs['metadata'] == {
        'credit_channel': 'chat',
        'chat_id': 'local:chat-1',
        'message_id': 'message-1',
        'call_instance_id': f'{expected_action}:1',
    }


def test_chat_metadata_uses_explicit_stable_action_sequence() -> None:
    from open_webui.utils import middleware

    counters: dict[str, int] = {}
    first = middleware.build_chat_image_credit_metadata('chat-1', 'message-1', 'text-to-image', counters)
    second = middleware.build_chat_image_credit_metadata('chat-1', 'message-1', 'text-to-image', counters)
    replay_counters: dict[str, int] = {}
    replay = middleware.build_chat_image_credit_metadata(
        'chat-1',
        'message-1',
        'text-to-image',
        replay_counters,
    )

    assert first == replay
    assert first['call_instance_id'] == 'text-to-image:1'
    assert second['call_instance_id'] == 'text-to-image:2'
    assert counters == {'text-to-image': 2}


def test_chat_metadata_without_message_id_leaves_idempotency_to_request_scope() -> None:
    from open_webui.utils import middleware

    metadata = middleware.build_chat_image_credit_metadata('chat-1', None, 'text-to-image')

    assert metadata == {
        'credit_channel': 'chat',
        'chat_id': 'chat-1',
    }
