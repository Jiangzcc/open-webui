import pytest
from open_webui.extensions import url_security


def test_https_url_guard_rejects_non_strings_confusing_characters_and_bad_ports() -> None:
    for value in (None, '', 'https://safe.test\n/path', 'https://safe.test:bad/path'):
        with pytest.raises(ValueError, match='invalid HTTPS URL'):
            url_security.require_https_url(value)
