"""Unit tests for BrowserMessageHandler."""

from trellis.platforms.browser.handler import _dict_to_message
from trellis.platforms.common.messages import EventMessage, HelloMessage


class TestDictToMessage:
    """Tests for _dict_to_message conversion."""

    def test_hello_message_includes_system_theme(self) -> None:
        """_dict_to_message should parse system_theme from hello dict."""
        msg_dict = {
            "type": "hello",
            "client_id": "test-client",
            "system_theme": "dark",
        }
        msg = _dict_to_message(msg_dict)

        assert isinstance(msg, HelloMessage)
        assert msg.client_id == "test-client"
        assert msg.system_theme == "dark"

    def test_hello_message_includes_theme_mode(self) -> None:
        """_dict_to_message should parse theme_mode from hello dict."""
        msg_dict = {
            "type": "hello",
            "client_id": "test-client",
            "system_theme": "light",
            "theme_mode": "dark",
        }
        msg = _dict_to_message(msg_dict)

        assert isinstance(msg, HelloMessage)
        assert msg.theme_mode == "dark"

    def test_hello_message_defaults(self) -> None:
        """_dict_to_message should use defaults for missing optional fields."""
        msg_dict = {
            "type": "hello",
            "client_id": "test-client",
        }
        msg = _dict_to_message(msg_dict)

        assert isinstance(msg, HelloMessage)
        assert msg.system_theme == "light"  # default
        assert msg.theme_mode is None  # default

    def test_event_message(self) -> None:
        """_dict_to_message should parse event messages correctly."""
        msg_dict = {
            "type": "event",
            "callback_id": "cb_123",
            "args": ["arg1", 42],
        }
        msg = _dict_to_message(msg_dict)

        assert isinstance(msg, EventMessage)
        assert msg.callback_id == "cb_123"
        assert msg.args == ["arg1", 42]
