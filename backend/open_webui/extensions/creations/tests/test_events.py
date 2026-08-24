from __future__ import annotations

import asyncio

import pytest
from open_webui.extensions.creations.events import (
    GenerationEventBus,
    _format_sse_event,
)


@pytest.mark.asyncio
async def test_event_bus_broadcasts_to_all_subscribers() -> None:
    bus = GenerationEventBus()
    q1 = await bus.subscribe('u1')
    q2 = await bus.subscribe('u1')

    await bus.publish({'kind': 'image', 'task_id': 't1', 'status': 'succeeded', 'user_id': 'u1'})

    e1 = await asyncio.wait_for(q1.get(), timeout=1.0)
    e2 = await asyncio.wait_for(q2.get(), timeout=1.0)
    assert e1 == e2 == {'kind': 'image', 'task_id': 't1', 'status': 'succeeded', 'user_id': 'u1'}


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_stops_delivery() -> None:
    bus = GenerationEventBus()
    q = await bus.subscribe('u1')
    await bus.unsubscribe('u1', q)

    await bus.publish({'kind': 'image', 'task_id': 't1', 'status': 'running', 'user_id': 'u1'})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q.get(), timeout=0.2)


@pytest.mark.asyncio
async def test_event_bus_only_delivers_to_matching_user() -> None:
    # user_id 过滤：user A 的事件不应推送给 user B 的队列。
    bus = GenerationEventBus()
    q_a = await bus.subscribe('user-a')
    q_b = await bus.subscribe('user-b')

    await bus.publish({'kind': 'image', 'task_id': 't1', 'status': 'running', 'user_id': 'user-a'})

    e_a = await asyncio.wait_for(q_a.get(), timeout=1.0)
    assert e_a['task_id'] == 't1'
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q_b.get(), timeout=0.2)


@pytest.mark.asyncio
async def test_event_bus_replaces_oldest_on_full_queue_without_blocking_producer() -> None:
    # 容量 1 的总线：填满后再 publish 应保留最新状态，不抛、不阻塞。
    bus = GenerationEventBus()

    # 直接构造一个 maxsize=1 的队列手动塞入，模拟满队列。
    small: asyncio.Queue = asyncio.Queue(maxsize=1)
    await small.put({'filler': True})
    bus._subscribers.setdefault('u2', set()).add(small)

    latest = {'kind': 'image', 'task_id': 't2', 'status': 'failed', 'user_id': 'u2'}
    await bus.publish(latest)

    assert small.qsize() == 1
    assert small.get_nowait() == latest


def test_format_sse_event_is_single_line_data_frame() -> None:
    frame = _format_sse_event({'kind': 'video', 'task_id': 't1', 'status': 'succeeded'})
    assert frame.startswith('data: ')
    assert frame.endswith('\n\n')
    # 单行，无裸换行在 data 内。
    # SSE 帧格式为 "data: ...\n\n"，始终恰好 2 个换行。
    assert frame.count('\n') == 2


@pytest.mark.asyncio
async def test_publish_generation_event_skips_when_no_subscribers() -> None:
    # 无订阅者时 publish 应直接跳过，不构造事件、不抛错。
    from open_webui.extensions.creations.events import (
        GenerationEventBus,
        publish_generation_event,
    )

    class _FakeApp:
        class state:
            generation_event_bus = GenerationEventBus()  # 无订阅者

    # 不应抛出
    await publish_generation_event(
        _FakeApp(),
        kind='image',
        task_id='t3',
        status='running',
        user_id='u3',
    )


@pytest.mark.asyncio
async def test_publish_and_sse_fallback_channels_are_symmetric(monkeypatch) -> None:
    """复盘 #18：发布侧与 SSE 侧在 app.state 未挂载总线时都回退全局单例——
    不对称时发布侧丢弃、订阅侧挂全局单例，两条通道永不相交。"""
    from types import SimpleNamespace

    import open_webui.extensions.creations.events as events
    from open_webui.extensions.creations.events import (
        get_generation_event_bus,
        publish_generation_event,
        sse_generation_events_generator,
    )

    # 重置全局单例，隔离其他测试的影响。
    monkeypatch.setattr(events, '_bus', None)
    bus = get_generation_event_bus()
    queue = await bus.subscribe('user-a')

    # 无 app.state.generation_event_bus 的 app：两侧都应回退全局单例。
    app = SimpleNamespace(state=SimpleNamespace())
    generator = sse_generation_events_generator(app, 'user-a')
    hello = await asyncio.wait_for(generator.__anext__(), timeout=1)

    # 生成器订阅建立后再发布：全局单例的订阅者（手动 queue + 生成器 queue）
    # 都应收到。若发布侧不回退全局单例，第二个 __anext__ 会等到 keepalive
    # 超时（wait_for 1s 先失败）。
    await publish_generation_event(
        app, kind='video', task_id='t1', status='succeeded', user_id='user-a'
    )
    event_frame = await asyncio.wait_for(generator.__anext__(), timeout=1)
    await generator.aclose()

    assert hello.startswith('data: {"type":"hello"')
    assert '"task_id":"t1"' in event_frame
    assert queue.qsize() == 1
