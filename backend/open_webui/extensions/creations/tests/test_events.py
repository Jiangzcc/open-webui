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
    q1 = await bus.subscribe()
    q2 = await bus.subscribe()

    await bus.publish({'kind': 'image', 'task_id': 't1', 'status': 'succeeded', 'user_id': 'u1'})

    e1 = await asyncio.wait_for(q1.get(), timeout=1.0)
    e2 = await asyncio.wait_for(q2.get(), timeout=1.0)
    assert e1 == e2 == {'kind': 'image', 'task_id': 't1', 'status': 'succeeded', 'user_id': 'u1'}


@pytest.mark.asyncio
async def test_event_bus_unsubscribe_stops_delivery() -> None:
    bus = GenerationEventBus()
    q = await bus.subscribe()
    await bus.unsubscribe(q)

    await bus.publish({'kind': 'image', 'task_id': 't1', 'status': 'running', 'user_id': 'u1'})
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(q.get(), timeout=0.2)


@pytest.mark.asyncio
async def test_event_bus_drops_on_full_queue_without_blocking_producer() -> None:
    # 容量 1 的总线：填满后再 publish 应被丢弃，不抛、不阻塞。
    bus = GenerationEventBus()
    bus._subscribers.clear()  # reset singleton-free state

    # 直接构造一个 maxsize=1 的队列手动塞入，模拟满队列。
    small: asyncio.Queue = asyncio.Queue(maxsize=1)
    await small.put({'filler': True})
    bus._subscribers.add(small)

    # 这条事件应被丢弃（队列满），不阻塞、不抛。
    await bus.publish({'kind': 'image', 'task_id': 't2', 'status': 'failed', 'user_id': 'u2'})
    # 生产者未被阻塞到此即视为通过。
    assert small.qsize() == 1  # 仍是 filler，新事件被丢弃


def test_format_sse_event_is_single_line_data_frame() -> None:
    frame = _format_sse_event({'kind': 'video', 'task_id': 't1', 'status': 'succeeded'})
    assert frame.startswith('data: ')
    assert frame.endswith('\n\n')
    # 单行，无裸换行在 data 内。
    assert frame.count('\n') == 1 or frame.count('\n') == 2  # 结尾的 \n\n


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
