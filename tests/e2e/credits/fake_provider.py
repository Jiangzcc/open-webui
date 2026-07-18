"""Loopback-only OpenAI-compatible image provider for the credits Cypress suite."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Final

LOOPBACK_HOST: Final = '127.0.0.1'
SUCCESS_MODE: Final = 'success'
FAILURE_MODE: Final = 'failure'
VALID_MODES: Final = frozenset({SUCCESS_MODE, FAILURE_MODE})
FIXTURES_DIRECTORY: Final = Path(__file__).parent / 'fixtures'


@dataclass
class ProviderState:
    """Mutable state is isolated behind a lock for concurrent backend requests."""

    mode: str = SUCCESS_MODE
    calls: Counter[str] = field(default_factory=Counter)
    lock: Lock = field(default_factory=Lock)

    def reset(self) -> None:
        with self.lock:
            self.calls.clear()

    def record(self, action: str) -> str:
        with self.lock:
            self.calls[action] += 1
            return self.mode

    def set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f'Unsupported provider mode: {mode}')
        with self.lock:
            self.mode = mode

    def snapshot(self) -> dict[str, object]:
        with self.lock:
            return {'mode': self.mode, 'total': sum(self.calls.values()), 'by_action': dict(self.calls)}


class FakeProviderHandler(BaseHTTPRequestHandler):
    """Serve only the two OpenAI image endpoints and local test controls."""

    state: ProviderState
    fixtures: dict[str, bytes]

    def do_GET(self) -> None:  # noqa: N802
        if self.path == '/__calls':
            self._send_json(HTTPStatus.OK, self.state.snapshot())
            return
        self._send_json(HTTPStatus.NOT_FOUND, {'error': {'message': 'Unknown local fake provider route'}})

    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split('?', maxsplit=1)[0]
        if route == '/__reset':
            self.state.reset()
            self._send_json(HTTPStatus.OK, self.state.snapshot())
            return
        if route == '/__mode':
            self._set_mode()
            return
        if route in {'/images/generations', '/images/edits'}:
            self._serve_image_request('text-to-image' if route.endswith('generations') else 'image-to-image')
            return
        self._send_json(HTTPStatus.NOT_FOUND, {'error': {'message': 'Unknown local fake provider route'}})

    def _set_mode(self) -> None:
        try:
            payload = self._read_json()
            mode = payload.get('mode')
            if not isinstance(mode, str):
                raise ValueError('mode must be a string')
            self.state.set_mode(mode)
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {'error': {'message': str(error)}})
            return
        self._send_json(HTTPStatus.OK, self.state.snapshot())

    def _serve_image_request(self, action: str) -> None:
        mode = self.state.record(action)
        if mode == SUCCESS_MODE:
            self._send_bytes(HTTPStatus.OK, self.fixtures[SUCCESS_MODE])
            return
        self._send_bytes(HTTPStatus.INTERNAL_SERVER_ERROR, self.fixtures[FAILURE_MODE])

    def _read_json(self) -> dict[str, object]:
        content_length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(content_length).decode('utf-8'))
        if not isinstance(payload, dict):
            raise ValueError('request body must be a JSON object')
        return payload

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        self._send_bytes(status, json.dumps(payload).encode('utf-8'))

    def _send_bytes(self, status: HTTPStatus, payload: bytes) -> None:
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep expected test traffic out of the terminal output."""


def read_fixture(name: str) -> bytes:
    return (FIXTURES_DIRECTORY / f'provider-{name}.json').read_bytes()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18080)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    FakeProviderHandler.state = ProviderState()
    FakeProviderHandler.fixtures = {mode: read_fixture(mode) for mode in VALID_MODES}
    server = ThreadingHTTPServer((LOOPBACK_HOST, args.port), FakeProviderHandler)
    print(f'Fake image provider listening on http://{LOOPBACK_HOST}:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
