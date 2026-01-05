"""Tests for router message types."""

import msgspec

from trellis.platforms.common.messages import (
    HelloMessage,
    HistoryBack,
    HistoryForward,
    HistoryPush,
    Message,
    UrlChanged,
)


class TestHelloMessagePath:
    """Tests for HelloMessage path field."""

    def test_hello_with_path(self) -> None:
        """HelloMessage can include initial path."""
        msg = HelloMessage(client_id="test-client", path="/users")
        assert msg.client_id == "test-client"
        assert msg.path == "/users"

    def test_hello_path_defaults_to_root(self) -> None:
        """HelloMessage path defaults to root."""
        msg = HelloMessage(client_id="test-client")
        assert msg.path == "/"

    def test_hello_with_path_roundtrip(self) -> None:
        """HelloMessage with path survives msgpack roundtrip."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HelloMessage(client_id="test-client", path="/users/123")
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HelloMessage)
        assert decoded.client_id == "test-client"
        assert decoded.path == "/users/123"


class TestHistoryPush:
    """Tests for HistoryPush message."""

    def test_history_push_creation(self) -> None:
        """HistoryPush can be created with path."""
        msg = HistoryPush(path="/users")
        assert msg.path == "/users"

    def test_history_push_roundtrip(self) -> None:
        """HistoryPush survives msgpack roundtrip."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HistoryPush(path="/users/42")
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HistoryPush)
        assert decoded.path == "/users/42"

    def test_history_push_has_type_tag(self) -> None:
        """HistoryPush includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = HistoryPush(path="/test")
        encoded = encoder.encode(msg)

        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "history_push"
        assert raw["path"] == "/test"


class TestHistoryBack:
    """Tests for HistoryBack message."""

    def test_history_back_creation(self) -> None:
        """HistoryBack can be created with no fields."""
        msg = HistoryBack()
        assert msg is not None

    def test_history_back_roundtrip(self) -> None:
        """HistoryBack survives msgpack roundtrip."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HistoryBack()
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HistoryBack)

    def test_history_back_has_type_tag(self) -> None:
        """HistoryBack includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = HistoryBack()
        encoded = encoder.encode(msg)

        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "history_back"


class TestHistoryForward:
    """Tests for HistoryForward message."""

    def test_history_forward_creation(self) -> None:
        """HistoryForward can be created with no fields."""
        msg = HistoryForward()
        assert msg is not None

    def test_history_forward_roundtrip(self) -> None:
        """HistoryForward survives msgpack roundtrip."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HistoryForward()
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HistoryForward)

    def test_history_forward_has_type_tag(self) -> None:
        """HistoryForward includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = HistoryForward()
        encoded = encoder.encode(msg)

        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "history_forward"


class TestUrlChanged:
    """Tests for UrlChanged message."""

    def test_url_changed_creation(self) -> None:
        """UrlChanged can be created with path."""
        msg = UrlChanged(path="/new-path")
        assert msg.path == "/new-path"

    def test_url_changed_roundtrip(self) -> None:
        """UrlChanged survives msgpack roundtrip."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = UrlChanged(path="/about")
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, UrlChanged)
        assert decoded.path == "/about"

    def test_url_changed_has_type_tag(self) -> None:
        """UrlChanged includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = UrlChanged(path="/contact")
        encoded = encoder.encode(msg)

        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "url_changed"
        assert raw["path"] == "/contact"


class TestRouterMessagesInUnion:
    """Tests for router messages in the Message union."""

    def test_all_router_messages_distinguishable(self) -> None:
        """All router message types can be distinguished after decoding."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        messages = [
            HelloMessage(client_id="c1", path="/test"),
            HistoryPush(path="/users"),
            HistoryBack(),
            HistoryForward(),
            UrlChanged(path="/new"),
        ]

        for original in messages:
            decoded = decoder.decode(encoder.encode(original))
            assert type(decoded) is type(original)
