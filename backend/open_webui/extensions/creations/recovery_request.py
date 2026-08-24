from __future__ import annotations

from fastapi import FastAPI
from starlette.requests import Request


def recovery_request(app: FastAPI) -> Request:
    """Build the minimal internal request shared by persisted media recovery."""
    return Request(
        {
            'type': 'http',
            'app': app,
            'method': 'GET',
            'path': '/',
            'headers': [],
            'query_string': b'',
            'scheme': 'http',
            'server': ('localhost', 80),
            'client': None,
        }
    )


__all__ = ['recovery_request']
