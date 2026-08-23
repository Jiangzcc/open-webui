"""二开共享：图片/视频生成任务的状态枚举单一事实源。

复盘 P2：任务状态原先散落 6+ 处（两份 schemas Literal、两条 ORM CHECK 字面量、
generation_tasks 的活跃子集、前端类型）——收敛到本模块，SQL CHECK 从 Literal
派生，保证 ORM、迁移校验与 Pydantic 校验永远指向同一集合。
"""

from __future__ import annotations

from typing import Literal, get_args

GenerationTaskStatus = Literal['queued', 'running', 'succeeded', 'failed']

GENERATION_TASK_STATUSES: tuple[str, ...] = get_args(GenerationTaskStatus)

# 仍在执行中的任务（未终态）；与终态核对、恢复扫描的过滤条件共用。
ACTIVE_GENERATION_TASK_STATUSES: tuple[str, ...] = ('queued', 'running')

# 与迁移 0001 手写的 CHECK 文本逐字符一致（registration 指纹校验依赖）。
GENERATION_TASK_STATUS_CHECK_SQL = f"status IN ({', '.join(repr(value) for value in GENERATION_TASK_STATUSES)})"


__all__ = [
    'ACTIVE_GENERATION_TASK_STATUSES',
    'GENERATION_TASK_STATUSES',
    'GENERATION_TASK_STATUS_CHECK_SQL',
    'GenerationTaskStatus',
]
