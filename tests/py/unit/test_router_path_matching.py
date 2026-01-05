"""Tests for router path matching."""

from trellis.routing.path_matching import match_path


class TestExactMatch:
    """Test exact path matching without params."""

    def test_root_path_matches(self) -> None:
        matched, params = match_path("/", "/")
        assert matched is True
        assert params == {}

    def test_simple_path_matches(self) -> None:
        matched, params = match_path("/users", "/users")
        assert matched is True
        assert params == {}

    def test_nested_path_matches(self) -> None:
        matched, params = match_path("/users/settings", "/users/settings")
        assert matched is True
        assert params == {}

    def test_different_paths_no_match(self) -> None:
        matched, params = match_path("/users", "/posts")
        assert matched is False
        assert params == {}

    def test_partial_path_no_match(self) -> None:
        """Pattern /users should not match /users/123 (exact matching)."""
        matched, params = match_path("/users", "/users/123")
        assert matched is False
        assert params == {}

    def test_longer_pattern_no_match(self) -> None:
        """Pattern /users/settings should not match /users."""
        matched, params = match_path("/users/settings", "/users")
        assert matched is False
        assert params == {}


class TestParamExtraction:
    """Test parameter extraction from paths."""

    def test_single_param(self) -> None:
        matched, params = match_path("/users/:id", "/users/123")
        assert matched is True
        assert params == {"id": "123"}

    def test_multiple_params(self) -> None:
        matched, params = match_path("/users/:userId/posts/:postId", "/users/42/posts/99")
        assert matched is True
        assert params == {"userId": "42", "postId": "99"}

    def test_param_with_static_segments(self) -> None:
        matched, params = match_path("/api/v1/users/:id/profile", "/api/v1/users/abc/profile")
        assert matched is True
        assert params == {"id": "abc"}

    def test_param_preserves_special_chars(self) -> None:
        """Params should preserve URL-safe special characters."""
        matched, params = match_path("/files/:name", "/files/my-file_v2.txt")
        assert matched is True
        assert params == {"name": "my-file_v2.txt"}


class TestTrailingSlashNormalization:
    """Test that trailing slashes are normalized."""

    def test_pattern_with_trailing_matches_path_without(self) -> None:
        matched, params = match_path("/users/", "/users")
        assert matched is True
        assert params == {}

    def test_pattern_without_trailing_matches_path_with(self) -> None:
        matched, params = match_path("/users", "/users/")
        assert matched is True
        assert params == {}

    def test_both_with_trailing_slashes(self) -> None:
        matched, params = match_path("/users/", "/users/")
        assert matched is True
        assert params == {}

    def test_root_with_no_trailing(self) -> None:
        """Empty string path should match root."""
        matched, params = match_path("/", "")
        assert matched is True
        assert params == {}


class TestWildcardPattern:
    """Test wildcard (*) pattern matching."""

    def test_wildcard_matches_any_path(self) -> None:
        matched, params = match_path("*", "/any/path/here")
        assert matched is True
        assert params == {}

    def test_wildcard_matches_root(self) -> None:
        matched, params = match_path("*", "/")
        assert matched is True
        assert params == {}


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_param_segment(self) -> None:
        """Double slash in path should not match param pattern."""
        matched, params = match_path("/users/:id", "/users/")
        assert matched is False
        assert params == {}

    def test_case_sensitive_matching(self) -> None:
        """Paths should be case-sensitive."""
        matched, params = match_path("/Users", "/users")
        assert matched is False
        assert params == {}

    def test_numeric_param_as_string(self) -> None:
        """Params should always be strings."""
        matched, params = match_path("/items/:id", "/items/42")
        assert matched is True
        assert params == {"id": "42"}
        assert isinstance(params["id"], str)
