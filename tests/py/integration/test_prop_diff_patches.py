"""Integration tests for prop diff patches.

Verifies that RenderUpdatePatch contains only changed/added/removed keys
rather than the full props dict.
"""

from __future__ import annotations

from dataclasses import dataclass

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.core.rendering.element import _REMOVED
from trellis.core.rendering.patches import RenderUpdatePatch
from trellis.core.state.stateful import Stateful
from trellis.widgets.basic import Label
from trellis.widgets.hot_key import HotKey


class TestPropDiffPatches:
    def test_removed_prop_emits_removed_sentinel(self, capture_patches: type[PatchCapture]) -> None:
        """A prop present in the old render but absent in the new render
        should appear as _REMOVED in the update patch."""

        @dataclass(kw_only=True)
        class State(Stateful):
            show_extra: bool = True

        state = State()

        @component
        def MyLabel() -> None:
            if state.show_extra:
                Label(text="hello", color="red")
            else:
                Label(text="hello")

        capture = capture_patches(MyLabel)
        capture.render()

        state.show_extra = False
        patches = capture.render()

        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        assert len(update_patches) == 1
        assert update_patches[0].props is not None
        assert update_patches[0].props["color"] is _REMOVED

    def test_only_changed_key_in_patch(self, capture_patches: type[PatchCapture]) -> None:
        """When only one of several props changes, only that key appears in the patch."""

        @dataclass(kw_only=True)
        class State(Stateful):
            text: str = "hello"

        state = State()

        @component
        def MyLabel() -> None:
            Label(text=state.text, color="red", size=14)

        capture = capture_patches(MyLabel)
        capture.render()

        state.text = "world"
        patches = capture.render()

        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        assert len(update_patches) == 1
        props = update_patches[0].props
        assert props is not None
        assert props == {"text": "world"}
        assert "color" not in props
        assert "size" not in props

    def test_unchanged_props_no_update_patch(self, capture_patches: type[PatchCapture]) -> None:
        """When props are unchanged, no RenderUpdatePatch is emitted."""

        @dataclass(kw_only=True)
        class State(Stateful):
            count: int = 0

        state = State()

        @component
        def Counter() -> None:
            _ = state.count
            Label(text="static")

        capture = capture_patches(Counter)
        capture.render()

        state.count = 1
        patches = capture.render()

        # The Counter re-renders but Label props are unchanged
        label_updates = [
            p
            for p in patches
            if isinstance(p, RenderUpdatePatch) and p.props is not None and "text" in p.props
        ]
        assert len(label_updates) == 0

    def test_hotkey_enabled_toggle_removes_key_filters(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """When HotKey enabled flips to False, __global_key_filters__ is removed."""

        @dataclass(kw_only=True)
        class State(Stateful):
            enabled: bool = True

        state = State()

        @component
        def App() -> None:
            HotKey(filter="Mod+D", handler=lambda: None, enabled=state.enabled)

        capture = capture_patches(App)
        capture.render()

        state.enabled = False
        patches = capture.render()

        update_patches = [p for p in patches if isinstance(p, RenderUpdatePatch)]
        # Find the patch that removes __global_key_filters__
        removal_patches = [
            p for p in update_patches if p.props is not None and "__global_key_filters__" in p.props
        ]
        assert len(removal_patches) == 1
        assert removal_patches[0].props["__global_key_filters__"] is _REMOVED
