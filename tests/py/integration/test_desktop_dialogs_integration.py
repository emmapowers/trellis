"""Integration tests for desktop dialogs in callback context."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import requires_pytauri
from trellis.core.callback_context import callback_context
from trellis.core.components.composition import component
from trellis.core.rendering.session import RenderSession
from trellis.desktop import dialogs


class _FakeFileDialogBuilder:
    """Fake async dialog builder that immediately resolves."""

    def __init__(self, file_result: object) -> None:
        self.file_result = file_result

    def pick_file(self, handler, /, **_kwargs):  # type: ignore[no-untyped-def]
        handler(self.file_result)


class _FakeDialogExt:
    """Fake dialog extension namespace."""

    def __init__(self, manager: object, builder: _FakeFileDialogBuilder) -> None:
        self._manager = manager
        self._builder = builder

    def file(self, manager: object) -> _FakeFileDialogBuilder:
        assert manager is self._manager
        return self._builder


@requires_pytauri
@pytest.mark.anyio
async def test_open_file_in_callback_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dialogs API is callable from callback context."""

    @component
    def App() -> None:
        pass

    session = RenderSession(App)
    node_id = "node-1"
    session.states.get_or_create(node_id)

    manager = object()
    builder = _FakeFileDialogBuilder(Path("/tmp/selected.txt"))
    dialogs._set_dialog_runtime(manager)
    monkeypatch.setattr(dialogs, "_load_dialog_ext", lambda: _FakeDialogExt(manager, builder))

    with callback_context(session, node_id):
        selected = await dialogs.open_file()

    assert selected == Path("/tmp/selected.txt")
