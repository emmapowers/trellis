"""Tests for checked-in widget client dependency alignment."""

from __future__ import annotations

import json
from pathlib import Path

from trellis.platforms.common import CORE_CLIENT_PACKAGES
from trellis.widgets.dependencies import WIDGET_CLIENT_PACKAGES


def test_widget_client_package_json_covers_declared_dependencies() -> None:
    """Tooling package.json should include the Python-declared widget dependencies."""
    package_json_path = (
        Path(__file__).resolve().parents[3] / "frontend" / "trellis-widgets" / "package.json"
    )
    package_json = json.loads(package_json_path.read_text())
    package_dependencies = {
        **package_json.get("dependencies", {}),
        **package_json.get("devDependencies", {}),
        **package_json.get("peerDependencies", {}),
    }

    for package_name, version in WIDGET_CLIENT_PACKAGES.items():
        assert package_dependencies.get(package_name) == version


def test_widget_bundle_dependencies_exclude_shared_react_runtime() -> None:
    """Widget bundle declarations should not own the shared React runtime."""
    assert "react" not in WIDGET_CLIENT_PACKAGES
    assert "react-dom" not in WIDGET_CLIENT_PACKAGES
    assert "@types/react" not in WIDGET_CLIENT_PACKAGES
    assert "@types/react-dom" not in WIDGET_CLIENT_PACKAGES


def test_widget_client_package_json_matches_shared_react_versions() -> None:
    """Tooling package.json should pin React versions to the shared core runtime."""
    package_json_path = (
        Path(__file__).resolve().parents[3] / "frontend" / "trellis-widgets" / "package.json"
    )
    package_json = json.loads(package_json_path.read_text())

    assert package_json["peerDependencies"]["react"] == CORE_CLIENT_PACKAGES["react"]
    assert package_json["peerDependencies"]["react-dom"] == CORE_CLIENT_PACKAGES["react-dom"]
    assert package_json["devDependencies"]["@types/react"] == CORE_CLIENT_PACKAGES["@types/react"]
    assert (
        package_json["devDependencies"]["@types/react-dom"]
        == CORE_CLIENT_PACKAGES["@types/react-dom"]
    )
