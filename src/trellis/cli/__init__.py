"""Trellis CLI - new modular command structure."""

from dataclasses import dataclass, field
from pathlib import Path

import click


@dataclass
class CliContext:
    """Typed context shared across CLI commands."""

    app_root: Path | None = field(default=None)


# Typed decorator for commands to receive CliContext
pass_cli_context = click.make_pass_decorator(CliContext, ensure=True)


@click.group()
@click.option(
    "--app-root",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    envvar="TRELLIS_APP_ROOT",
    help="Path to Trellis app directory (contains trellis.py)",
)
@pass_cli_context
def trellis(ctx: CliContext, /, app_root: Path | None) -> None:
    """Trellis CLI utilities."""
    ctx.app_root = app_root


# Import commands to register them
from trellis.cli import run  # noqa: F401, E402
