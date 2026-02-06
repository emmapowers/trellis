"""Bundle command for Trellis CLI (temporarily disabled)."""

import click

from trellis.cli import trellis


@trellis.group()
def bundle() -> None:
    """Bundle management commands."""


@bundle.command()
def build() -> None:
    """Build platform bundles."""
    raise click.UsageError(
        "The bundle command is temporarily disabled during workspace refactoring."
    )
