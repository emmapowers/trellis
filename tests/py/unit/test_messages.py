"""Tests for message types."""

import msgspec

from trellis.platforms.common.messages import (
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    PatchMessage,
    ProxyRequest,
    ProxyResponse,
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


class TestReloadMessage:
    """Tests for ReloadMessage serialization."""

    def test_reload_message_creation(self) -> None:
        """ReloadMessage can be created with no arguments."""
        msg = ReloadMessage()
        assert msg is not None

    def test_reload_message_msgpack_roundtrip(self) -> None:
        """ReloadMessage survives msgpack encode/decode."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = ReloadMessage()
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

        assert isinstance(decoded, ReloadMessage)

    def test_reload_message_has_type_tag(self) -> None:
        """ReloadMessage includes type tag for dispatch."""
        encoder = msgspec.msgpack.Encoder()
        msg = ReloadMessage()
        encoded = encoder.encode(msg)

        # Decode as raw dict to check structure
        raw = msgspec.msgpack.decode(encoded)
        assert raw["type"] == "reload"


class TestProxyRequestMessage:
    """Tests for ProxyRequest serialization."""

    def test_proxy_request_call_msgpack_roundtrip(self) -> None:
        """Method call requests survive msgpack encode/decode."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = ProxyRequest(
            request_id="req-1",
            proxy_id="demo_api",
            operation="call",
            member="greet",
            args=["Emma"],
        )
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

        assert isinstance(decoded, ProxyRequest)
        assert decoded.request_id == "req-1"
        assert decoded.proxy_id == "demo_api"
        assert decoded.operation == "call"
        assert decoded.member == "greet"
        assert decoded.args == ["Emma"]
        assert decoded.value is None

    def test_proxy_request_property_set_msgpack_roundtrip(self) -> None:
        """Property set requests preserve value and member."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = ProxyRequest(
            request_id="req-2",
            proxy_id="document",
            operation="set",
            member="title",
            value="New title",
        )
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

        assert isinstance(decoded, ProxyRequest)
        assert decoded.request_id == "req-2"
        assert decoded.proxy_id == "document"
        assert decoded.operation == "set"
        assert decoded.member == "title"
        assert decoded.value == "New title"
        assert decoded.args == []


class TestProxyResponseMessage:
    """Tests for ProxyResponse serialization."""

    def test_proxy_response_msgpack_roundtrip(self) -> None:
        """ProxyResponse survives msgpack encode/decode."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = ProxyResponse(
            request_id="req-1",
            result={"message": "hello"},
        )
        encoded = encoder.encode(original)
        decoded = decoder.decode(encoded)

        assert isinstance(decoded, ProxyResponse)
        assert decoded.request_id == "req-1"
        assert decoded.result == {"message": "hello"}
        assert decoded.error is None
        assert decoded.error_type is None


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
            ProxyRequest(
                request_id="req-1",
                proxy_id="demo_api",
                operation="call",
                member="greet",
            ),
            ProxyRequest(
                request_id="req-2",
                proxy_id="document",
                operation="get",
                member="title",
            ),
            ProxyResponse(request_id="req-1", result="ok"),
            ReloadMessage(),
        ]

        for original in messages:
            decoded = decoder.decode(encoder.encode(original))
            assert type(decoded) is type(original)

    def test_decode_reload_message(self) -> None:
        """ReloadMessage decodes correctly from union."""
        encoder = msgspec.msgpack.Encoder()
        decoder = msgspec.msgpack.Decoder(Message)

        original = ReloadMessage()
        decoded = decoder.decode(encoder.encode(original))

        assert isinstance(decoded, ReloadMessage)
