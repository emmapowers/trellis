"""Trellis CLI - new modular command structure."""

import click


@click.group()
def trellis() -> None:
    """Trellis CLI utilities."""


# Import commands to register them
from trellis.cli import run  # noqa: F401, E402
