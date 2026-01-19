"""Unit tests for message conversion functions - dict to/from Message types."""

import msgspec
import pytest

from trellis.platforms.browser.handler import _dict_to_message, _message_to_dict
from trellis.platforms.common.messages import (
    AddPatch,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    PatchMessage,
    RemovePatch,
    UpdatePatch,
)


class TestMessageToDict:
    """Tests for _message_to_dict conversion."""

    def test_converts_patch_message(self) -> None:
        """_message_to_dict converts PatchMessage to dict with type field."""
        msg = PatchMessage(patches=[])
        result = _message_to_dict(msg)

        assert result == {"type": "patch", "patches": []}

    def test_converts_nested_patch_structs(self) -> None:
        """_message_to_dict recursively converts nested msgspec structs to dicts.

        This is required for postMessage which can only clone plain objects,
        not msgspec Struct instances.
        """
        msg = PatchMessage(
            patches=[
                AddPatch(
                    parent_id="root", children=["child1"], element={"id": "child1", "name": "Label"}
                ),
                UpdatePatch(id="node1", props={"text": "hello"}, children=None),
                RemovePatch(id="node2"),
            ]
        )
        result = _message_to_dict(msg)

        # All patches should be plain dicts, not msgspec Struct instances
        assert isinstance(result["patches"], list)
        for patch in result["patches"]:
            assert isinstance(patch, dict), f"Expected dict, got {type(patch)}"

        # Verify the structure is correct
        assert result["patches"][0] == {
            "op": "add",
            "parent_id": "root",
            "children": ["child1"],
            "element": {"id": "child1", "name": "Label"},
        }
        assert result["patches"][1] == {
            "op": "update",
            "id": "node1",
            "props": {"text": "hello"},
            "children": None,
        }
        assert result["patches"][2] == {
            "op": "remove",
            "id": "node2",
        }

    def test_converts_error_message(self) -> None:
        """_message_to_dict converts ErrorMessage to dict with type field."""
        msg = ErrorMessage(error="test error", context="callback")
        result = _message_to_dict(msg)

        assert result == {"type": "error", "error": "test error", "context": "callback"}


class TestDictToMessage:
    """Tests for _dict_to_message conversion."""

    def test_unknown_type_raises(self) -> None:
        """_dict_to_message raises ValidationError for unknown message type."""
        with pytest.raises(msgspec.ValidationError):
            _dict_to_message({"type": "unknown_type"})

    def test_missing_callback_id_raises(self) -> None:
        """_dict_to_message raises ValidationError when event is missing callback_id."""
        with pytest.raises(msgspec.ValidationError):
            _dict_to_message({"type": "event", "args": []})

    def test_converts_hello(self) -> None:
        """_dict_to_message converts hello message dict to HelloMessage."""
        result = _dict_to_message({"type": "hello", "client_id": "test-123"})

        assert isinstance(result, HelloMessage)
        assert result.client_id == "test-123"

    def test_converts_event(self) -> None:
        """_dict_to_message converts event message dict to EventMessage."""
        result = _dict_to_message({"type": "event", "callback_id": "cb-1", "args": [1, 2]})

        assert isinstance(result, EventMessage)
        assert result.callback_id == "cb-1"
        assert result.args == [1, 2]
