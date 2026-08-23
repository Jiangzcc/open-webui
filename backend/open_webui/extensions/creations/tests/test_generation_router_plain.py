from __future__ import annotations

import asyncio
from types import SimpleNamespace

from open_webui.extensions.creations import router
from open_webui.extensions.creations.schemas import ImageGenerationTaskSubmitForm


def _submission() -> ImageGenerationTaskSubmitForm:
    # prompt 是用户输入的纯文本：标签点击时已直接插入 insert_text，
    # 提交/落库/调度全程同一份文本，无任何 token 展开层。
    return ImageGenerationTaskSubmitForm(
        kind='text-to-image',
        payload={
            'prompt': 'a girl, cinematic lighting',
            'negative_prompt': 'black and white, blurry',
            'model': 'fal/model',
        },
    )


def _install_collaborators(monkeypatch):  # type: ignore[no-untyped-def]
    """记录 create/schedule 收到的参数，并放行限流/槽位与调度。"""
    created_payloads: list[dict[str, object]] = []
    scheduled_forms: list[object] = []

    async def fake_create(_session, **_kwargs):  # type: ignore[no-untyped-def]
        created_payloads.append(dict(_kwargs['payload']))
        return SimpleNamespace(id='task-1'), True

    monkeypatch.setattr(router, 'create_generation_task', fake_create)
    monkeypatch.setattr(router, 'enforce_image_generation_rate', lambda *_args: None)

    async def fake_acquire(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(router, 'acquire_image_generation_slot', fake_acquire)
    monkeypatch.setattr(router, 'release_image_generation_slot', lambda *_args: None)

    def fake_schedule(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        scheduled_forms.append(_kwargs.get('form'))

    monkeypatch.setattr(router, 'schedule_generation_task', fake_schedule)
    return created_payloads, scheduled_forms


def test_plain_prompt_stored_and_forwarded(monkeypatch) -> None:
    """纯文本直传：任务行落库的 prompt 与调度器收到的表单都是用户
    输入的同一份纯文本。"""

    async def scenario() -> None:
        created_payloads, scheduled_forms = _install_collaborators(monkeypatch)

        result = await router.create_image_generation_task(
            SimpleNamespace(),
            _submission(),
            'key-1',
            SimpleNamespace(id='user-1'),
            object(),
        )

        assert result.id == 'task-1'
        assert len(created_payloads) == 1
        assert created_payloads[0]['prompt'] == 'a girl, cinematic lighting'
        assert created_payloads[0]['negative_prompt'] == 'black and white, blurry'
        assert created_payloads[0]['model'] == 'fal/model'
        assert len(scheduled_forms) == 1

    asyncio.run(scenario())
