#!/usr/bin/env python3
"""Generate example pages for documentation.

Discovers examples in the examples/ folder and generates standalone HTML pages
that can be served as static files. Each example gets its own folder with an
index.html that embeds the source code and links to shared bundle assets.

Also generates MDX stubs for Docusaurus sidebar navigation.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "examples"
DOCS_STATIC_DIR = PROJECT_ROOT / "docs" / "static"
DOCS_EXAMPLES_DIR = DOCS_STATIC_DIR / "examples"
DOCS_SRC_DIR = PROJECT_ROOT / "docs" / "src"
GENERATED_SIDEBAR_FILE = DOCS_SRC_DIR / "generated-examples-sidebar.json"
BROWSER_CLIENT_DIST = PROJECT_ROOT / "src" / "trellis" / "platforms" / "browser" / "client" / "dist"
BROWSER_CLIENT_SRC = PROJECT_ROOT / "src" / "trellis" / "platforms" / "browser" / "client" / "src"

# Jinja2 environment for HTML template
_jinja_env = Environment(loader=FileSystemLoader(BROWSER_CLIENT_SRC), autoescape=False)


@dataclass
class Example:
    """Represents a discovered example."""

    name: str  # URL-friendly name (e.g., "widget-showcase")
    title: str  # Display title (e.g., "Widget Showcase")
    description: str  # Short description
    source: dict[str, Any]  # Source config for __TRELLIS_CONFIG__


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


def collect_package_files(package_dir: Path) -> dict[str, str]:
    """Collect all Python files in a package directory.

    Args:
        package_dir: Root directory of the package

    Returns:
        Dict mapping relative paths to file contents
    """
    files: dict[str, str] = {}

    for py_file in package_dir.rglob("*.py"):
        # Skip __pycache__
        if "__pycache__" in py_file.parts:
            continue
        # Get path relative to package parent (so package name is included)
        rel_path = py_file.relative_to(package_dir.parent)
        files[str(rel_path)] = py_file.read_text()

    return files


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
                    source={"type": "code", "code": code},
                )
            )

        elif item.is_dir() and (item / "__main__.py").exists():
            # Package example
            files = collect_package_files(item)
            module_name = item.name  # e.g., "breakfast_todo"
            name = slugify(item.name)
            title = titleize(item.name)

            # Try to extract description from __init__.py or __main__.py
            init_code = files.get(f"{module_name}/__init__.py", "")
            main_code = files.get(f"{module_name}/__main__.py", "")
            description = extract_docstring(init_code) or extract_docstring(main_code)

            examples.append(
                Example(
                    name=name,
                    title=title,
                    description=description,
                    source={"type": "module", "files": files, "moduleName": module_name},
                )
            )

    return examples


def generate_html(source: dict[str, Any], title: str) -> str:
    """Generate the HTML page with embedded source config.

    Args:
        source: Source config dict for __TRELLIS_CONFIG__
        title: Page title

    Returns:
        Generated HTML content
    """
    # JSON-encode the source config for embedding in JavaScript
    # Escape </ to prevent script tag injection (e.g., </script> in code)
    source_json = json.dumps(source).replace("</", r"<\/")

    template = _jinja_env.get_template("index.html")
    return template.render(
        source_json=source_json,
        title=f"{title} | Trellis",
        asset_prefix="../",
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


def copy_shared_assets() -> None:
    """Copy bundle.js and bundle.css to the examples directory."""
    DOCS_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    bundle_js = BROWSER_CLIENT_DIST / "bundle.js"
    bundle_css = BROWSER_CLIENT_DIST / "bundle.css"

    if not bundle_js.exists():
        raise RuntimeError(
            f"Browser bundle not found at {bundle_js}. "
            "Run 'trellis bundle build --platform browser' first."
        )

    shutil.copy(bundle_js, DOCS_EXAMPLES_DIR / "bundle.js")
    if bundle_css.exists():
        shutil.copy(bundle_css, DOCS_EXAMPLES_DIR / "bundle.css")
    else:
        # Create empty CSS file if it doesn't exist
        (DOCS_EXAMPLES_DIR / "bundle.css").touch()


def main() -> None:
    """Main entry point."""
    print("Discovering examples...")
    examples = discover_examples()
    print(f"Found {len(examples)} examples: {[e.name for e in examples]}")

    print("Copying shared assets...")
    copy_shared_assets()

    print("Generating example pages...")
    for example in examples:
        example_dir = DOCS_EXAMPLES_DIR / example.name
        example_dir.mkdir(parents=True, exist_ok=True)

        html = generate_html(example.source, example.title)
        (example_dir / "index.html").write_text(html)
        print(f"  Generated {example.name}/index.html")

    print("Generating sidebar configuration...")
    sidebar_items = generate_sidebar_items(examples)
    GENERATED_SIDEBAR_FILE.write_text(json.dumps(sidebar_items, indent=2))
    print(f"  Generated {GENERATED_SIDEBAR_FILE.name}")

    print("Done!")


if __name__ == "__main__":
    main()
