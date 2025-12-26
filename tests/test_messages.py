"""Tests for message types."""

import msgspec

from trellis.core.messages import (
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    PatchMessage,
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
        decoder = msgspec.msgpack.Decoder(Message)

        original = EventMessage(callback_id="cb_42", args=["hello", 123, True])
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

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


class TestMessageUnion:
    """Tests for Message union type dispatch."""

    def test_decode_hello_message(self) -> None:
        """HelloMessage decodes correctly from union."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HelloMessage(client_id="test-client")
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HelloMessage)
        assert decoded.client_id == "test-client"

    def test_decode_hello_response_message(self) -> None:
        """HelloResponseMessage decodes correctly from union."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = HelloResponseMessage(session_id="sess-1", server_version="1.0.0")
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, HelloResponseMessage)
        assert decoded.session_id == "sess-1"
        assert decoded.server_version == "1.0.0"

    def test_decode_patch_message(self) -> None:
        """PatchMessage decodes correctly from union."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = PatchMessage(patches=[])
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, PatchMessage)
        assert decoded.patches == []

    def test_decode_event_message(self) -> None:
        """EventMessage decodes correctly from union."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = EventMessage(callback_id="cb_99", args=[{"key": "value"}])
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, EventMessage)
        assert decoded.callback_id == "cb_99"
        assert decoded.args == [{"key": "value"}]

    def test_all_message_types_distinguishable(self) -> None:
        """All message types can be distinguished after decoding."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        messages = [
            HelloMessage(client_id="c1"),
            HelloResponseMessage(session_id="s1", server_version="1.0"),
            PatchMessage(patches=[]),
            EventMessage(callback_id="cb_1"),
        ]

        for original in messages:
            decoded = decoder.decode(encoder.encode(original))
            assert type(decoded) is type(original)
