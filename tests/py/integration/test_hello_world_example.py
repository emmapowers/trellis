"""Behavior tests for the hello world example app."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.conftest import render_to_tree
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import parse_callback_id, serialize_element


def _find_button_by_text(node: dict[str, Any], text: str) -> dict[str, Any] | None:
    if node.get("type") == "Button" and node.get("props", {}).get("text") == text:
        return node
    for child in node.get("children", []):
        result = _find_button_by_text(child, text)
        if result is not None:
            return result
    return None


def _find_count_label(node: dict[str, Any]) -> dict[str, Any] | None:
    if node.get("type") == "Label" and node.get("props", {}).get("font_size") == 36:
        return node
    for child in node.get("children", []):
        result = _find_count_label(child)
        if result is not None:
            return result
    return None


def _invoke_callback(session: RenderSession, callback_id: str) -> None:
    element_id, prop_name = parse_callback_id(callback_id)
    callback = session.get_callback(element_id, prop_name)
    assert callback is not None
    callback()


class TestHelloWorldExample:
    def test_reset_restores_initial_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.syspath_prepend(str(Path("examples/hello_world").resolve()))

        import hello_world.app as hello_world_app  # noqa: PLC0415

        monkeypatch.setattr(hello_world_app, "INITIAL_COUNT", 7)

        session = RenderSession(hello_world_app.HelloWorld)
        tree = render_to_tree(session)

        increment_button = _find_button_by_text(tree, "+")
        reset_button = _find_button_by_text(tree, "Reset")
        assert increment_button is not None
        assert reset_button is not None

        _invoke_callback(session, increment_button["props"]["on_click"]["__callback__"])
        render(session)
        _invoke_callback(session, reset_button["props"]["on_click"]["__callback__"])
        render(session)

        updated_tree = serialize_element(session.root_element, session)
        count_label = _find_count_label(updated_tree)
        assert count_label is not None
        assert count_label["props"]["text"] == "7"
