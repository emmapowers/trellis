"""Router protocol messages."""

from trellis.core.protocol import Message, register_message_types


class HistoryPush(Message, tag="history_push"):
    """Push a new path to browser history."""

    path: str


class HistoryBack(Message, tag="history_back"):
    """Navigate back in browser history."""

    pass


class HistoryForward(Message, tag="history_forward"):
    """Navigate forward in browser history."""

    pass


class UrlChanged(Message, tag="url_changed"):
    """Browser URL changed outside a direct server-driven navigation."""

    path: str


register_message_types(HistoryPush, HistoryBack, HistoryForward, UrlChanged)


__all__ = ["HistoryBack", "HistoryForward", "HistoryPush", "UrlChanged"]
