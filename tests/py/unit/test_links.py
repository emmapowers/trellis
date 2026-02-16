"""Unit tests for trellis.html.links module."""

from trellis.html.links import _is_relative_url


def test_relative_path_is_relative() -> None:
    """Simple relative paths return True."""
    assert _is_relative_url("/users") is True
    assert _is_relative_url("/users/123") is True
    assert _is_relative_url("/") is True


def test_relative_path_with_query_is_relative() -> None:
    """Relative paths with query strings return True."""
    assert _is_relative_url("/search?q=test") is True
    assert _is_relative_url("/users?page=1&sort=name") is True


def test_relative_path_with_hash_is_relative() -> None:
    """Relative paths with hash fragments return True."""
    assert _is_relative_url("/docs#section") is True
    assert _is_relative_url("/#top") is True


def test_http_url_is_not_relative() -> None:
    """HTTP URLs return False."""
    assert _is_relative_url("http://example.com") is False
    assert _is_relative_url("http://example.com/path") is False


def test_https_url_is_not_relative() -> None:
    """HTTPS URLs return False."""
    assert _is_relative_url("https://example.com") is False
    assert _is_relative_url("https://example.com/path") is False


def test_protocol_relative_url_is_not_relative() -> None:
    """Protocol-relative URLs (//) return False."""
    assert _is_relative_url("//example.com") is False
    assert _is_relative_url("//example.com/path") is False


def test_mailto_scheme_is_not_relative() -> None:
    """mailto: URLs return False - browser should handle email links."""
    assert _is_relative_url("mailto:user@example.com") is False
    assert _is_relative_url("mailto:user@example.com?subject=Hello") is False


def test_tel_scheme_is_not_relative() -> None:
    """tel: URLs return False - browser should handle phone links."""
    assert _is_relative_url("tel:+1234567890") is False
    assert _is_relative_url("tel:555-1234") is False


def test_javascript_scheme_is_not_relative() -> None:
    """javascript: URLs return False - prevents security issues."""
    assert _is_relative_url("javascript:alert(1)") is False
    assert _is_relative_url("javascript:void(0)") is False


def test_data_scheme_is_not_relative() -> None:
    """data: URLs return False - browser should handle data URIs."""
    assert _is_relative_url("data:text/html,<h1>Test</h1>") is False
    assert _is_relative_url("data:image/png;base64,iVBORw0KGgo=") is False


def test_file_scheme_is_not_relative() -> None:
    """file: URLs return False - browser should handle file links."""
    assert _is_relative_url("file:///path/to/file") is False
    assert _is_relative_url("file://localhost/path") is False


def test_other_absolute_schemes_are_not_relative() -> None:
    """Any absolute URI scheme should bypass router navigation."""
    assert _is_relative_url("ftp://example.com/file.txt") is False
    assert _is_relative_url("tauri://localhost/path") is False


def test_bare_path_is_relative() -> None:
    """Paths without leading slash are still relative."""
    assert _is_relative_url("path/to/resource") is True
    assert _is_relative_url("relative") is True


def test_empty_string_is_relative() -> None:
    """Empty string is considered relative."""
    assert _is_relative_url("") is True


def test_fragment_only_is_not_relative() -> None:
    """Fragment-only URLs (#section) should use browser navigation.

    These scroll to an element on the current page and shouldn't
    go through the router.
    """
    assert _is_relative_url("#section") is False
    assert _is_relative_url("#top") is False
    assert _is_relative_url("#") is False


def test_query_only_is_not_relative() -> None:
    """Query-only URLs (?foo=bar) should use browser navigation.

    These modify query params on the current page and shouldn't
    go through the router.
    """
    assert _is_relative_url("?search=test") is False
    assert _is_relative_url("?page=1&sort=name") is False
    assert _is_relative_url("?") is False
