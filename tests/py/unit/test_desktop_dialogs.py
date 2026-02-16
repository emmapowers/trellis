"""Unit tests for desktop file dialog APIs."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import requires_pytauri


class _FakeFileDialogBuilder:
    """Simple fake of pytauri dialog builder."""

    def __init__(
        self,
        *,
        file_result: object = None,
        files_result: object = None,
        save_result: object = None,
        folder_result: object = None,
    ) -> None:
        self.file_result = file_result
        self.files_result = files_result
        self.save_result = save_result
        self.folder_result = folder_result
        self.calls: list[tuple[str, dict[str, object]]] = []

    def pick_file(self, handler, /, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(("pick_file", kwargs))
        handler(self.file_result)

    def pick_files(self, handler, /, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(("pick_files", kwargs))
        handler(self.files_result)

    def save_file(self, handler, /, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(("save_file", kwargs))
        handler(self.save_result)

    def pick_folder(self, handler, /, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(("pick_folder", kwargs))
        handler(self.folder_result)


class _FakeDialogExt:
    """Fake dialog extension namespace."""

    def __init__(self, manager: object, builder: _FakeFileDialogBuilder) -> None:
        self._manager = manager
        self._builder = builder

    def file(self, manager: object) -> _FakeFileDialogBuilder:
        assert manager is self._manager
        return self._builder


@pytest.fixture
def dialogs_module():
    # Runtime import keeps desktop-only module loading aligned with requires_pytauri.
    from trellis.desktop import dialogs  # noqa: PLC0415

    dialogs._clear_dialog_runtime()
    yield dialogs
    dialogs._clear_dialog_runtime()


@requires_pytauri
@pytest.mark.anyio
async def test_open_file_raises_outside_desktop_runtime(dialogs_module) -> None:
    with pytest.raises(RuntimeError, match="desktop runtime"):
        await dialogs_module.open_file()


@requires_pytauri
@pytest.mark.anyio
async def test_open_file_returns_selected_path(
    monkeypatch: pytest.MonkeyPatch,
    dialogs_module,
) -> None:
    manager = object()
    builder = _FakeFileDialogBuilder(file_result=Path("/tmp/example.txt"))
    dialogs_module._set_dialog_runtime(manager)
    monkeypatch.setattr(
        dialogs_module,
        "_load_dialog_ext",
        lambda: _FakeDialogExt(manager, builder),
    )

    options = dialogs_module.FileDialogOptions(
        title="Choose file",
        directory=Path("/tmp"),
    )
    result = await dialogs_module.open_file(options=options)

    assert result == Path("/tmp/example.txt")
    assert builder.calls == [
        (
            "pick_file",
            {
                "set_title": "Choose file",
                "set_directory": Path("/tmp"),
            },
        )
    ]


@requires_pytauri
@pytest.mark.anyio
async def test_open_files_returns_empty_list_on_cancel(
    monkeypatch: pytest.MonkeyPatch,
    dialogs_module,
) -> None:
    manager = object()
    builder = _FakeFileDialogBuilder(files_result=None)
    dialogs_module._set_dialog_runtime(manager)
    monkeypatch.setattr(
        dialogs_module,
        "_load_dialog_ext",
        lambda: _FakeDialogExt(manager, builder),
    )

    result = await dialogs_module.open_files()

    assert result == []
    assert builder.calls[0][0] == "pick_files"


@requires_pytauri
@pytest.mark.anyio
async def test_save_file_applies_filter_and_filename(
    monkeypatch: pytest.MonkeyPatch,
    dialogs_module,
) -> None:
    manager = object()
    builder = _FakeFileDialogBuilder(save_result=Path("/tmp/result.txt"))
    dialogs_module._set_dialog_runtime(manager)
    monkeypatch.setattr(
        dialogs_module,
        "_load_dialog_ext",
        lambda: _FakeDialogExt(manager, builder),
    )

    options = dialogs_module.FileDialogOptions(
        file_name="result.txt",
        filter=dialogs_module.FileDialogFilter(name="Text files", extensions=("txt", "md")),
    )
    result = await dialogs_module.save_file(options=options)

    assert result == Path("/tmp/result.txt")
    assert builder.calls == [
        (
            "save_file",
            {
                "set_file_name": "result.txt",
                "add_filter": ("Text files", ("txt", "md")),
            },
        )
    ]


@requires_pytauri
@pytest.mark.anyio
async def test_select_directory_returns_selected_path(
    monkeypatch: pytest.MonkeyPatch,
    dialogs_module,
) -> None:
    manager = object()
    builder = _FakeFileDialogBuilder(folder_result=Path("/tmp/project"))
    dialogs_module._set_dialog_runtime(manager)
    monkeypatch.setattr(
        dialogs_module,
        "_load_dialog_ext",
        lambda: _FakeDialogExt(manager, builder),
    )

    result = await dialogs_module.select_directory()

    assert result == Path("/tmp/project")
    assert builder.calls[0][0] == "pick_folder"
