#!/usr/bin/env python3
"""Generate example pages for documentation.

Discovers examples in the examples/ folder and generates standalone HTML pages
by calling the trellis CLI. Each example gets its own folder with an index.html
and bundled assets.

Also generates MDX stubs for Docusaurus sidebar navigation.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from trellis.app.config import Config

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
DOCS_STATIC_DIR = PROJECT_ROOT / "docs" / "static"
DOCS_EXAMPLES_DIR = DOCS_STATIC_DIR / "examples"
DOCS_SRC_DIR = PROJECT_ROOT / "docs" / "src"
GENERATED_SIDEBAR_FILE = DOCS_SRC_DIR / "generated-examples-sidebar.json"


@dataclass
class Example:
    """Represents a discovered example."""

    name: str  # URL-friendly name (e.g., "widget-showcase")
    title: str  # Display title (e.g., "Widget Showcase")
    description: str  # Short description
    path: Path  # Path to example directory


def slugify(name: str) -> str:
    """Convert a directory name to a URL-friendly slug."""
    return name.replace("_", "-").lower()


def load_config(config_path: Path) -> Config:
    """Load a Config from a trellis_config.py file."""
    namespace: dict[str, object] = {}
    exec(compile(config_path.read_text(), config_path, "exec"), namespace)
    config = namespace["config"]
    assert isinstance(config, Config)
    return config


def discover_examples() -> list[Example]:
    """Discover all examples in the examples/ folder.

    Each example is a directory containing a trellis_config.py file.
    The display title comes from Config.name, and the description
    from pyproject.toml's project.description field.
    """
    examples: list[Example] = []

    for item in sorted(EXAMPLES_DIR.iterdir()):
        if item.name.startswith(("_", ".")) or not item.is_dir():
            continue

        config_file = item / "trellis_config.py"
        if not config_file.exists():
            continue

        config = load_config(config_file)

        description = ""
        pyproject_file = item / "pyproject.toml"
        if pyproject_file.exists():
            with open(pyproject_file, "rb") as f:
                pyproject = tomllib.load(f)
            description = pyproject.get("project", {}).get("description", "")

        examples.append(
            Example(
                name=slugify(item.name),
                title=config.name,
                description=description,
                path=item,
            )
        )

    return examples


def generate_example_page(example: Example) -> None:
    """Generate an example page by calling the trellis CLI."""
    example_dir = DOCS_EXAMPLES_DIR / example.name

    subprocess.run(
        [
            "trellis",
            "--app-root",
            str(example.path),
            "bundle",
            "--platform",
            "browser",
            "--dest",
            str(example_dir),
            "--force-build",
        ],
        check=True,
    )


def generate_sidebar_items(examples: list[Example]) -> list[dict[str, object]]:
    """Generate sidebar items for examples as external links.

    Uses type: 'html' with target="_blank" to bypass Docusaurus SPA router.
    This opens examples in a new tab.
    """
    return [
        {
            "type": "html",
            "value": (
                f'<a class="menu__link" target="_blank"'
                f' href="/trellis/examples/{example.name}/">'
                f"{example.title}</a>"
            ),
            "defaultStyle": True,
        }
        for example in examples
    ]


def main() -> None:
    """Main entry point."""
    print("Discovering examples...")
    examples = discover_examples()
    print(f"Found {len(examples)} examples: {[e.name for e in examples]}")

    print("Generating example pages...")
    for example in examples:
        print(f"  Building {example.name}...")
        generate_example_page(example)

    print("Generating sidebar configuration...")
    sidebar_items = generate_sidebar_items(examples)
    GENERATED_SIDEBAR_FILE.write_text(json.dumps(sidebar_items, indent=2))
    print(f"  Generated {GENERATED_SIDEBAR_FILE.name}")

    print("Done!")


if __name__ == "__main__":
    main()
