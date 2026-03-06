"""Smoke example for the new shadcn-backed widget stack."""

from trellis import component
from trellis import html as h
from trellis import widgets as w
from trellis.app import App


@component
def SmokeApp() -> None:
    """Render a single button inside a simple page shell."""
    with h.Div(
        style={
            "minHeight": "100vh",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
        }
    ):
        w.Button(text="Smoke test")


app = App(SmokeApp)
