"""Tests for message types."""

import msgspec

from trellis.core.protocol import decode_message
from trellis.platforms.common.messages import (
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    PatchMessage,
    ReloadMessage,
)


class TestEventMessage:
    """Tests for EventMessage serialization."""

    def test_event_message_creation(self) -> None:
        """EventMessage can be created with callback_id and args."""
        msg = EventMessage(callback_id="cb_1", args=[1, 2, 3])
        assert msg.callback_id == "cb_1"
        assert msg.args == [1, 2, 3]

    def test_event_message_default_args(self) -> None:
        """EventMessage args defaults to empty list."""
        msg = EventMessage(callback_id="cb_1")
        assert msg.args == []

    def test_event_message_msgpack_roundtrip(self) -> None:
        """EventMessage survives msgpack encode/decode."""
        encoder = msgspec.msgpack.Encoder()

        original = EventMessage(callback_id="cb_42", args=["hello", 123, True])
        encoded = encoder.encode(original)
        decoded = decode_message(msgspec.msgpack.decode(encoded))

        assert isinstance(decoded, EventMessage)
        assert decoded.callback_id == "cb_42"
        assert decoded.args == ["hello", 123, True]

    def test_event_message_has_type_tag(self) -> None:
        """EventMessage includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = EventMessage(callback_id="cb_1")
        encoded = encoder.encode(msg)

        # Decode as raw dict to check structure
        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "event"
        assert raw["callback_id"] == "cb_1"


class TestReloadMessage:
    """Tests for ReloadMessage serialization."""

    def test_reload_message_creation(self) -> None:
        """ReloadMessage can be created with no arguments."""
        msg = ReloadMessage()
        assert msg is not None

    def test_reload_message_msgpack_roundtrip(self) -> None:
        """ReloadMessage survives msgpack encode/decode."""
        encoder = msgspec.msgpack.Encoder()

        original = ReloadMessage()
        encoded = encoder.encode(original)
        decoded = decode_message(msgspec.msgpack.decode(encoded))

        assert isinstance(decoded, ReloadMessage)

    def test_reload_message_has_type_tag(self) -> None:
        """ReloadMessage includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = ReloadMessage()
        encoded = encoder.encode(msg)

        # Decode as raw dict to check structure
        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "reload"


class TestMessageDecoding:
    """Tests for registry-backed message decoding."""

    def test_message_is_common_base_class(self) -> None:
        """All built-in messages inherit from the common Message base."""
        assert issubclass(HelloMessage, Message)
        assert issubclass(HelloResponseMessage, Message)
        assert issubclass(PatchMessage, Message)
        assert issubclass(EventMessage, Message)
        assert issubclass(ReloadMessage, Message)

    def test_decode_hello_message(self) -> None:
        """HelloMessage decodes correctly from the message registry."""
        encoder = msgspec.msgpack.Encoder()

        original = HelloMessage(client_id="test-client")
        decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))

        assert isinstance(decoded, HelloMessage)
        assert decoded.client_id == "test-client"

    def test_decode_hello_response_message(self) -> None:
        """HelloResponseMessage decodes correctly from the message registry."""
        encoder = msgspec.msgpack.Encoder()

        original = HelloResponseMessage(session_id="sess-1", server_version="1.0.0")
        decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))

        assert isinstance(decoded, HelloResponseMessage)
        assert decoded.session_id == "sess-1"
        assert decoded.server_version == "1.0.0"

    def test_decode_patch_message(self) -> None:
        """PatchMessage decodes correctly from the message registry."""
        encoder = msgspec.msgpack.Encoder()

        original = PatchMessage(patches=[])
        decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))

        assert isinstance(decoded, PatchMessage)
        assert decoded.patches == []

    def test_decode_event_message(self) -> None:
        """EventMessage decodes correctly from the message registry."""
        encoder = msgspec.msgpack.Encoder()

        original = EventMessage(callback_id="cb_99", args=[{"key": "value"}])
        decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))

        assert isinstance(decoded, EventMessage)
        assert decoded.callback_id == "cb_99"
        assert decoded.args == [{"key": "value"}]

    def test_all_message_types_distinguishable(self) -> None:
        """All message types can be distinguished after decoding."""
        encoder = msgspec.msgpack.Encoder()

        messages = [
            HelloMessage(client_id="c1"),
            HelloResponseMessage(session_id="s1", server_version="1.0"),
            PatchMessage(patches=[]),
            EventMessage(callback_id="cb_1"),
            ReloadMessage(),
        ]

        for original in messages:
            decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))
            assert type(decoded) is type(original)

    def test_decode_reload_message(self) -> None:
        """ReloadMessage decodes correctly from the message registry."""
        encoder = msgspec.msgpack.Encoder()

        original = ReloadMessage()
        decoded = decode_message(msgspec.msgpack.decode(encoder.encode(original)))

        assert isinstance(decoded, ReloadMessage)
