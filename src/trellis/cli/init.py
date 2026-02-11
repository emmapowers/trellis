"""Init command for Trellis CLI — scaffolds a new project."""

from __future__ import annotations

import keyword
import re
from pathlib import Path

import click
import questionary
from jinja2 import Environment, FileSystemLoader

from trellis.cli import trellis
from trellis.platforms.common.base import PlatformType

_TEMPLATE_DIR = Path(__file__).parent / "project_template"


def _to_package_name(name: str) -> str:
    """Convert a project name to a valid Python package name.

    Lowercases, replaces hyphens/spaces with underscores, collapses
    consecutive underscores, and strips leading/trailing underscores.
    """
    result = name.lower()
    result = re.sub(r"[-\s]+", "_", result)
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


def _is_valid_package_name(name: str) -> bool:
    """Check whether a string is a valid Python package name."""
    return bool(name) and name.isidentifier() and not keyword.iskeyword(name)


def _check_conflicts(dest_dir: Path, template_dir: Path, package_name: str) -> list[Path]:
    """Walk the template tree and return destination paths that already exist."""
    if not dest_dir.exists():
        return []

    conflicts: list[Path] = []
    for template_file in template_dir.rglob("*.j2"):
        rel = template_file.relative_to(template_dir).with_suffix("")
        # Substitute __package_name__ in path parts
        parts = [package_name if p == "__package_name__" else p for p in rel.parts]
        dest_file = dest_dir / Path(*parts)
        if dest_file.exists():
            conflicts.append(Path(*parts))

    return conflicts


def _prompt_missing(
    name: str | None,
    title: str | None,
    platform: str | None,
    directory: str | None,
) -> tuple[str, str, str, str]:
    """Prompt for any values that are None. Returns (name, title, platform, directory).

    When name is provided via CLI, remaining values use defaults silently.
    When name is missing (fully interactive), all missing values are prompted.
    """
    interactive = name is None

    if name is None:
        name = _ask_text("Project name:")
        if not name:
            raise click.Abort()

    package_name = _to_package_name(name)
    default_title = name.replace("-", " ").replace("_", " ").title()

    if title is None:
        if interactive:
            title = _ask_text("Display title:", default=default_title) or default_title
        else:
            title = default_title

    if platform is None:
        if interactive:
            platform = _ask_select(
                "Platform:",
                choices=[p.value for p in PlatformType],
                default="server",
            )
            if not platform:
                raise click.Abort()
        else:
            platform = "server"

    if directory is None:
        if interactive:
            directory = _ask_text("Directory:", default=f"./{package_name}")
            if not directory:
                directory = f"./{package_name}"
        else:
            directory = f"./{package_name}"

    return name, title, platform, directory


def _ask_text(message: str, default: str = "") -> str | None:
    """Prompt for text input. Returns None if the user cancels."""
    result: str | None = questionary.text(message, default=default).ask()
    return result


def _ask_select(message: str, choices: list[str], default: str | None = None) -> str | None:
    """Prompt for a selection from choices. Returns None if the user cancels."""
    result: str | None = questionary.select(message, choices=choices, default=default).ask()
    return result


def _render_template_tree(template_dir: Path, dest_dir: Path, context: dict[str, str]) -> None:
    """Render all .j2 files from template_dir into dest_dir."""
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
    )

    for template_file in template_dir.rglob("*.j2"):
        rel = template_file.relative_to(template_dir)
        # Strip .j2 suffix
        out_rel = rel.with_suffix("")
        # Substitute __package_name__ in path parts
        parts = [context["package_name"] if p == "__package_name__" else p for p in out_rel.parts]
        out_path = dest_dir / Path(*parts)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        template = env.get_template(str(rel))
        content = template.render(context)
        out_path.write_text(content)


@trellis.command()
@click.option("--name", "-n", default=None, help="Project name")
@click.option("--title", "-t", default=None, help="Display title (default: titlecased name)")
@click.option(
    "--platform",
    default=None,
    type=click.Choice([p.value for p in PlatformType], case_sensitive=False),
    help="Target platform",
)
@click.option("--directory", "-d", default=None, help="Destination directory")
def init(
    name: str | None,
    title: str | None,
    platform: str | None,
    directory: str | None,
) -> None:
    """Create a new Trellis project."""
    name, title, platform_str, directory_str = _prompt_missing(name, title, platform, directory)

    package_name = _to_package_name(name)
    if not _is_valid_package_name(package_name):
        raise click.UsageError(
            f"'{name}' does not produce a valid Python package name (got '{package_name}')"
        )

    dest = Path(directory_str)

    conflicts = _check_conflicts(dest, _TEMPLATE_DIR, package_name)
    if conflicts:
        file_list = "\n  ".join(str(c) for c in conflicts)
        raise click.UsageError(f"Files already exist in {dest}:\n  {file_list}")

    context = {
        "name": name,
        "title": title,
        "package_name": package_name,
        "module": f"{package_name}.app",
        "platform": platform_str,
        "platform_upper": platform_str.upper(),
    }

    dest.mkdir(parents=True, exist_ok=True)
    _render_template_tree(_TEMPLATE_DIR, dest, context)

    click.echo(f"Created project '{name}' in {dest}")
