"""Router protocol messages."""

import msgspec

from trellis.core.protocol import register_message_types


class HistoryPush(msgspec.Struct, tag="history_push", tag_field="type"):
    """Push a new path to browser history."""

    path: str


class HistoryBack(msgspec.Struct, tag="history_back", tag_field="type"):
    """Navigate back in browser history."""

    pass


class HistoryForward(msgspec.Struct, tag="history_forward", tag_field="type"):
    """Navigate forward in browser history."""

    pass


class UrlChanged(msgspec.Struct, tag="url_changed", tag_field="type"):
    """Browser URL changed outside a direct server-driven navigation."""

    path: str


register_message_types(HistoryPush, HistoryBack, HistoryForward, UrlChanged)


__all__ = ["HistoryBack", "HistoryForward", "HistoryPush", "UrlChanged"]
