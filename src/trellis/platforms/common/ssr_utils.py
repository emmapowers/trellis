"""Shared SSR utilities for building dehydration data.

Used by both the server platform (runtime SSR per-request) and the desktop
platform (build-time SSR).
"""

from __future__ import annotations

import json
import typing as tp

_SERVER_VERSION_KEY = "serverVersion"
_SESSION_ID_KEY = "sessionId"
_PATCHES_KEY = "patches"


def _get_version() -> str:
    """Get package version from metadata."""
    try:
        from importlib.metadata import version as get_package_version  # noqa: PLC0415

        return get_package_version("trellis")
    except Exception:
        return "0.0.0"


def build_dehydration_data(
    session_id: str | None,
    wire_patches: list[tp.Any],
) -> str:
    """Build the JSON string for the dehydration script.

    Args:
        session_id: Session ID for server SSR (None for desktop/build-time SSR)
        wire_patches: Serialized patches to embed

    Returns:
        JSON string containing server version, optional session ID, and patches
    """
    import msgspec  # noqa: PLC0415

    # Encode patches using msgspec for correct serialization of Struct types
    encoder = msgspec.json.Encoder()
    patches_json = encoder.encode(wire_patches).decode("utf-8")

    data: dict[str, tp.Any] = {
        _SERVER_VERSION_KEY: _get_version(),
    }
    if session_id is not None:
        data[_SESSION_ID_KEY] = session_id

    # Build JSON manually to embed pre-encoded patches
    data_json = json.dumps(data)
    result = data_json[:-1] + f', "{_PATCHES_KEY}": {patches_json}' + "}"

    # Escape characters that could break inline <script> embedding:
    # - </script> injection via < becoming \u003c
    # - JS line terminators that break string literals
    return result.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
