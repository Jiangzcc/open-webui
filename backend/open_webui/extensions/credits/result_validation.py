import re
from collections.abc import Sequence
from urllib.parse import urlsplit

from .constants import MAX_USAGE_RESULT_URL_LENGTH, MAX_USAGE_RESULT_URLS
from .errors import CreditError


def safe_result_urls(urls: Sequence[str]) -> list[str]:
    if isinstance(urls, (str, bytes)) or not 1 <= len(urls) <= MAX_USAGE_RESULT_URLS:
        raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
    normalized: list[str] = []
    for url in urls:
        if not isinstance(url, str) or not url or len(url) > MAX_USAGE_RESULT_URL_LENGTH:
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        if any(ord(char) < 32 or ord(char) == 127 for char in url) or '\\' in url or url.startswith('//'):
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        parsed = urlsplit(url)
        file_id = url.removeprefix('/api/v1/files/').removesuffix('/content')
        if (
            not url.startswith('/api/v1/files/')
            or not url.endswith('/content')
            or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', file_id) is None
            or parsed.scheme
            or parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise CreditError(code='provider_failed', context={'reason': 'invalid_provider_result'})
        normalized.append(url)
    return normalized


__all__ = ['safe_result_urls']
