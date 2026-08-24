from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

log = logging.getLogger(__name__)

# 任务事件总线：把图片/视频生成任务的状态变更推送给所有已连接的 SSE 客户端，
# 让前端改用服务端推送替代 2s/900ms 固定轮询，降低后端 QPS、提升实时性。
#
# 设计取舍：
# - 用进程内 asyncio.Queue 订阅者集合实现广播。多 worker 部署下跨进程推送
#   不在此层处理（需 Redis pub/sub），但本层提供 publish 接口，后续可无侵入
#   替换为 Redis pub/sub 后端而不改调用方。
# - 订阅者队列有界（maxsize），慢消费者溢出时丢弃旧事件而非阻塞生产者，
#   避免一个慢客户端拖垮整个事件循环。客户端断线重连后会重新拉一次 list
#   补齐丢失的终态，因此丢弃中间过渡态是可接受的。
_SUBSCRIBER_QUEUE_MAXSIZE = 128


class GenerationEventBus:
    """进程内任务事件广播总线。

    每个连接的 SSE 端点调用 subscribe(user_id) 拿到一个 Queue，并阻塞读取。
    任务终态写入后调用 publish() 向该 user_id 的订阅者广播。subscribe() 返回的
    Queue 必须在连接关闭时通过 unsubscribe() 移除，否则会泄漏引用。
    """

    def __init__(self) -> None:
        # 按 user_id 分组的订阅者队列集合，publish 时只推送给匹配用户的队列，
        # 避免向所有订阅者广播全量事件（含其他用户的 task_id）。
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, object]]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: str) -> asyncio.Queue[dict[str, object]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=_SUBSCRIBER_QUEUE_MAXSIZE)
        async with self._lock:
            self._subscribers.setdefault(user_id, set()).add(queue)
        return queue

    async def unsubscribe(self, user_id: str, queue: asyncio.Queue[dict[str, object]]) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(user_id)
            if subscribers is not None:
                subscribers.discard(queue)
                if not subscribers:
                    del self._subscribers[user_id]

    async def publish(self, event: dict[str, object]) -> None:
        """向匹配 user_id 的订阅者非阻塞广播事件。

        仅推送给 event['user_id'] 对应的订阅者队列，避免泄露其他用户的事件。
        慢消费者（队列已满）会被跳过，不阻塞生产者；客户端重连后会拉一次
        list 补齐终态，因此过渡态丢弃是安全的。
        """
        user_id = event.get('user_id')
        if not isinstance(user_id, str):
            return
        async with self._lock:
            subscribers = list(self._subscribers.get(user_id, ()))
        for queue in subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # 保留最新状态：慢消费者真正需要的是最新任务终态，而不是最早
                # 的过渡态。淘汰一个最旧事件后立即写入当前事件，仍不阻塞生产者。
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    log.debug('generation event subscriber queue changed while replacing oldest event')
            except Exception:
                log.exception('failed to publish generation event to a subscriber')

    @property
    def subscriber_count(self) -> int:
        return sum(len(subs) for subs in self._subscribers.values())


# 全局单例。在 main.py 的 lifespan 中通过 app.state.generation_event_bus 暴露，
# 任务执行体和 SSE 端点都通过 app.state 访问，避免模块级可变状态在测试间泄漏。
_bus: GenerationEventBus | None = None


def get_generation_event_bus() -> GenerationEventBus:
    global _bus
    if _bus is None:
        _bus = GenerationEventBus()
    return _bus


def init_generation_event_bus(app: FastAPI) -> None:
    """在 lifespan 启动期把事件总线挂到 app.state。"""
    app.state.generation_event_bus = get_generation_event_bus()


async def publish_generation_event(
    app: FastAPI,
    *,
    kind: str,
    task_id: str,
    status: str,
    user_id: str,
    payload: dict[str, object] | None = None,
) -> None:
    """发布一条任务状态变更事件。

    kind: 'image' | 'video'，用于客户端按类型路由。
    status: 'queued' | 'running' | 'succeeded' | 'failed'。
    payload: 可选的额外字段（如 result/error_code），按需附加。
    """
    bus: GenerationEventBus | None = getattr(app.state, 'generation_event_bus', None)
    if bus is None:
        # 与 SSE 生成器对称：未挂载 app.state 时同样回退全局单例。原先发布侧
        # 直接丢弃而订阅侧挂全局单例，两条通道永不相交（复盘 #18 对称化）。
        bus = get_generation_event_bus()
    if bus.subscriber_count == 0:
        # 无订阅者时跳过，避免无意义的事件构造与广播。
        return
    event: dict[str, object] = {
        'kind': kind,
        'task_id': task_id,
        'status': status,
        'user_id': user_id,
    }
    if payload:
        event.update(payload)
    await bus.publish(event)


def _format_sse_event(event: dict[str, object]) -> str:
    """把事件 dict 编码为 SSE data: 帧。"""
    # SSE 不允许帧内出现裸换行，用 JSON 单行编码规避。
    data = json.dumps(event, ensure_ascii=False, separators=(',', ':'))
    return f'data: {data}\n\n'


async def sse_generation_events_generator(app: FastAPI, user_id: str):
    """SSE 事件生成器：按用户过滤推送其可见的任务事件。

    连接建立后先推送一次 hello 帧，之后阻塞等待总线事件。
    总线层已按 user_id 过滤，只推送该用户自己的任务事件，无需消费端再过滤。
    每 15s 无事件时发心跳，保持连接活跃，避免代理/负载均衡器因空闲超时断开。
    SSE 端点传入 app 以访问 app.state.generation_event_bus。
    """
    bus: GenerationEventBus | None = getattr(app.state, 'generation_event_bus', None)
    if bus is None:
        bus = get_generation_event_bus()

    queue = await bus.subscribe(user_id)
    try:
        yield _format_sse_event({'type': 'hello', 'user_id': user_id})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
            except TimeoutError:
                # 心跳：保持连接活跃，避免代理/负载均衡器因空闲超时断开。
                yield ': keepalive\n\n'
                continue
            yield _format_sse_event(event)
    except asyncio.CancelledError:
        raise
    finally:
        await bus.unsubscribe(user_id, queue)


__all__ = [
    'GenerationEventBus',
    'get_generation_event_bus',
    'init_generation_event_bus',
    'publish_generation_event',
    'sse_generation_events_generator',
]
