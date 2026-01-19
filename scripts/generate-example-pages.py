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
from dataclasses import dataclass
from pathlib import Path

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
    entry_path: Path  # Path to Python entry point
    module_name: str | None = None  # Module name for packages (None for single files)


def slugify(name: str) -> str:
    """Convert a Python module/file name to a URL-friendly slug."""
    return name.replace("_", "-").lower()


def titleize(name: str) -> str:
    """Convert a slug or module name to a display title."""
    return name.replace("_", " ").replace("-", " ").title()


def extract_docstring(code: str) -> str:
    """Extract the module docstring from Python code."""
    import ast

    try:
        tree = ast.parse(code)
        docstring = ast.get_docstring(tree)
        return docstring.split("\n")[0] if docstring else ""
    except SyntaxError:
        return ""


def discover_examples() -> list[Example]:
    """Discover all examples in the examples/ folder.

    Returns:
        List of Example objects
    """
    examples: list[Example] = []

    for item in sorted(EXAMPLES_DIR.iterdir()):
        # Skip hidden files and __pycache__
        if item.name.startswith(("_", ".")):
            continue

        if item.is_file() and item.suffix == ".py":
            # Single-file example
            code = item.read_text()
            name = slugify(item.stem)
            title = titleize(item.stem)
            description = extract_docstring(code)

            examples.append(
                Example(
                    name=name,
                    title=title,
                    description=description,
                    entry_path=item,
                )
            )

        elif item.is_dir() and (item / "__main__.py").exists():
            # Package example
            module_name = item.name  # e.g., "breakfast_todo"
            name = slugify(item.name)
            title = titleize(item.name)
            entry_path = item / "__main__.py"

            # Try to extract description from __init__.py or __main__.py
            init_file = item / "__init__.py"
            init_code = init_file.read_text() if init_file.exists() else ""
            main_code = entry_path.read_text()
            description = extract_docstring(init_code) or extract_docstring(main_code)

            examples.append(
                Example(
                    name=name,
                    title=title,
                    description=description,
                    entry_path=entry_path,
                    module_name=module_name,
                )
            )

    return examples


def generate_example_page(example: Example) -> None:
    """Generate an example page by calling the trellis CLI.

    Args:
        example: Example to generate page for
    """
    example_dir = DOCS_EXAMPLES_DIR / example.name

    subprocess.run(
        [
            "trellis",
            "bundle",
            "build",
            "--platform",
            "browser",
            "--app",
            str(example.entry_path),
            "--dest",
            str(example_dir),
        ],
        check=True,
    )


def generate_sidebar_items(examples: list[Example]) -> list[dict]:
    """Generate sidebar items for examples as external links.

    Args:
        examples: List of examples

    Returns:
        List of sidebar item dicts for Docusaurus
    """
    # Use type: 'html' with target="_blank" to bypass Docusaurus SPA router
    # This opens examples in a new tab, similar to navbar external links
    # See: https://docusaurus.canny.io/feature-requests/p/support-target-for-sidebar-links
    return [
        {
            "type": "html",
            "value": f'<a class="menu__link" target="_blank" href="/trellis/examples/{example.name}/">{example.title}</a>',
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
