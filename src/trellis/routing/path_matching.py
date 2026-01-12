"""Path matching for router patterns."""


def match_path(pattern: str, path: str) -> tuple[bool, dict[str, str]]:
    """Match path against pattern, extract params.

    Args:
        pattern: Route pattern (e.g., "/users/:id")
        path: Actual path to match (e.g., "/users/123")

    Returns:
        Tuple of (matched, params) where params is dict of extracted values
    """
    # Handle wildcard pattern
    if pattern == "*":
        return True, {}

    # Normalize trailing slashes and empty paths
    pattern = pattern.rstrip("/") or "/"
    path = path.rstrip("/") or "/"

    # Split into segments
    pattern_segments = pattern.split("/")
    path_segments = path.split("/")

    # Must have same number of segments for exact match
    if len(pattern_segments) != len(path_segments):
        return False, {}

    params: dict[str, str] = {}

    for pattern_seg, path_seg in zip(pattern_segments, path_segments, strict=True):
        if pattern_seg.startswith(":"):
            # Parameter segment - extract value
            param_name = pattern_seg[1:]
            if not path_seg:
                # Empty segment doesn't match param
                return False, {}
            params[param_name] = path_seg
        elif pattern_seg != path_seg:
            # Static segment must match exactly
            return False, {}

    return True, params
