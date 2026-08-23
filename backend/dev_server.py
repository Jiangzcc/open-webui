"""Windows 开发启动入口。

直接用 uvicorn 命令行启动时，uvicorn 在 reload 子进程里会先创建 Windows
默认的 ProactorEventLoop，再 import 应用；而 PostgreSQL 异步引擎
（psycopg v3）不兼容 Proactor 循环，启动即报
"Psycopg cannot use the 'ProactorEventLoop' to run in async mode"。
官方 CLI ``open-webui serve`` 的做法是先 import 应用再以 ``loop='none'``
启动（见 open_webui/__init__.py），本入口等效之并保留 --reload 开发模式：

- 主模块顶层设置 WindowsSelectorEventLoopPolicy：主进程立即生效；reload
  以 spawn 方式启动的子进程会重新执行主模块顶层，同样早于 uvicorn 创建
  事件循环。
- ``loop='none'`` 让 uvicorn 完全不碰事件循环，asyncio.run() 遵循已
  设置的策略。
"""

import asyncio
import os
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _forwarded_allow_ips() -> str:
    # start_windows.bat 里的值带字面单引号（SET "FORWARDED_ALLOW_IPS='*'"），剥掉。
    raw = os.environ.get('FORWARDED_ALLOW_IPS', "'*'").strip()
    return raw.strip("'\"")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'open_webui.main:app',
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', '9000')),
        loop='none' if sys.platform == 'win32' else 'auto',
        reload=True,
        reload_dirs=['open_webui'],
        forwarded_allow_ips=_forwarded_allow_ips(),
        ws='auto',
    )
