"""Source-tree Windows server entry point.

Uvicorn's Windows loop factory selects ProactorEventLoop, which psycopg cannot
use asynchronously. Importing the app first installs the Selector policy; the
none loop setting then prevents Uvicorn from replacing it.
"""

import os

import uvicorn


def main() -> None:
    import open_webui.main  # noqa: F401
    from open_webui.env import UVICORN_WORKERS

    forwarded_allow_ips = os.getenv('FORWARDED_ALLOW_IPS', '*').strip("'\"")
    uvicorn.run(
        'open_webui.main:app',
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', '8080')),
        forwarded_allow_ips=forwarded_allow_ips,
        workers=UVICORN_WORKERS,
        loop='none',
        ws='auto',
    )


if __name__ == '__main__':
    main()
