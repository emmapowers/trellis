"""Tests for resolve_app_root() function."""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.app import resolve_app_root


class TestResolveAppRoot:
    """Test resolve_app_root() with CLI > ENV > auto-detect resolution."""

    def test_returns_cli_value_when_provided(self, tmp_path: Path) -> None:
        """CLI value is used directly when provided."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "trellis_config.py").write_text("config = None")

        result = resolve_app_root(cli_value=app_dir)
        assert result == app_dir

    def test_cli_takes_precedence_over_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI value wins over TRELLIS_APP_ROOT environment variable."""
        cli_dir = tmp_path / "cli_app"
        cli_dir.mkdir()
        (cli_dir / "trellis_config.py").write_text("config = None")

        env_dir = tmp_path / "env_app"
        env_dir.mkdir()
        (env_dir / "trellis_config.py").write_text("config = None")

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(env_dir))

        result = resolve_app_root(cli_value=cli_dir)
        assert result == cli_dir

    def test_uses_env_when_no_cli(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """TRELLIS_APP_ROOT is used when no CLI value provided."""
        env_dir = tmp_path / "env_app"
        env_dir.mkdir()
        (env_dir / "trellis_config.py").write_text("config = None")

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(env_dir))

        result = resolve_app_root(cli_value=None)
        assert result == env_dir

    def test_auto_detects_when_no_cli_or_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Falls back to find_app_path() when no CLI or ENV provided."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "trellis_config.py").write_text("config = None")

        # Ensure env var is not set
        monkeypatch.delenv("TRELLIS_APP_ROOT", raising=False)
        # Change cwd to app_dir so find_app_path() finds it
        monkeypatch.chdir(app_dir)

        result = resolve_app_root(cli_value=None)
        assert result == app_dir

    def test_file_path_uses_parent_directory(self, tmp_path: Path) -> None:
        """When CLI points to trellis_config.py file, parent directory is used."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        trellis_file = app_dir / "trellis_config.py"
        trellis_file.write_text("config = None")

        result = resolve_app_root(cli_value=trellis_file)
        assert result == app_dir

    def test_raises_when_path_not_found(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when CLI path doesn't exist."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError, match="does not exist"):
            resolve_app_root(cli_value=nonexistent)

    def test_raises_when_no_trellis_config_py(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when directory has no trellis_config.py."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(FileNotFoundError, match=r"trellis_config\.py not found"):
            resolve_app_root(cli_value=empty_dir)

    def test_raises_when_auto_detect_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raises FileNotFoundError when auto-detect finds no trellis_config.py."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        monkeypatch.delenv("TRELLIS_APP_ROOT", raising=False)
        monkeypatch.chdir(empty_dir)

        with pytest.raises(FileNotFoundError, match=r"trellis_config\.py not found"):
            resolve_app_root(cli_value=None)

    def test_empty_env_falls_through_to_auto_detect(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty TRELLIS_APP_ROOT is treated as unset."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "trellis_config.py").write_text("config = None")

        monkeypatch.setenv("TRELLIS_APP_ROOT", "")
        monkeypatch.chdir(app_dir)

        result = resolve_app_root(cli_value=None)
        assert result == app_dir

    def test_env_path_file_uses_parent_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When ENV points to trellis_config.py file, parent directory is used."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        trellis_file = app_dir / "trellis_config.py"
        trellis_file.write_text("config = None")

        monkeypatch.setenv("TRELLIS_APP_ROOT", str(trellis_file))

        result = resolve_app_root(cli_value=None)
        assert result == app_dir

    def test_relative_cli_path_resolved_to_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative CLI paths are resolved to absolute paths."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "trellis_config.py").write_text("config = None")
        monkeypatch.chdir(tmp_path)

        result = resolve_app_root(cli_value=Path("myapp"))

        assert result.is_absolute()
        assert result == app_dir.resolve()

    def test_relative_env_path_resolved_to_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relative ENV paths are resolved to absolute paths."""
        app_dir = tmp_path / "myapp"
        app_dir.mkdir()
        (app_dir / "trellis_config.py").write_text("config = None")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TRELLIS_APP_ROOT", "myapp")

        result = resolve_app_root(cli_value=None)

        assert result.is_absolute()
        assert result == app_dir.resolve()
