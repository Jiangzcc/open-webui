"""Small URL syntax guards shared by provider extensions.

Network-level SSRF protection belongs to the connect-time safe resolver. These
helpers enforce the separate invariant needed for provider credentials: an URL
that receives an API key must stay on the exact configured HTTPS origin.
"""

from __future__ import annotations

from urllib.parse import SplitResult, urlsplit

_CONFUSING_URL_CHARACTERS = frozenset({'\\', '\t', '\r', '\n'})


def _https_parts(value: str) -> SplitResult:
    if not isinstance(value, str) or not value or any(char in value for char in _CONFUSING_URL_CHARACTERS):
        raise ValueError('invalid HTTPS URL')
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError('invalid HTTPS URL') from error
    if (
        parsed.scheme.lower() != 'https'
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or port is not None and not 1 <= port <= 65535
    ):
        raise ValueError('invalid HTTPS URL')
    return parsed


def require_https_url(value: str) -> str:
    _https_parts(value)
    return value


def normalize_https_base_url(value: str, *, allow_empty: bool = False) -> str:
    normalized = value.strip().rstrip('/')
    if allow_empty and not normalized:
        return ''
    parsed = _https_parts(normalized)
    if parsed.query or parsed.fragment:
        raise ValueError('HTTPS base URL must not contain a query or fragment')
    return normalized


def require_same_https_origin(value: str, trusted_base_url: str) -> str:
    parsed = _https_parts(value)
    trusted = _https_parts(trusted_base_url)
    origin = (parsed.hostname.rstrip('.').lower(), parsed.port or 443)
    trusted_origin = (trusted.hostname.rstrip('.').lower(), trusted.port or 443)
    if origin != trusted_origin:
        raise ValueError('provider URL origin does not match configured origin')
    return value


__all__ = ['normalize_https_base_url', 'require_https_url', 'require_same_https_origin']
