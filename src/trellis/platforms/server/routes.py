"""HTTP routes for server platform.

WebSocket handling is in handler.py.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

router = APIRouter()

# Jinja2 environment for HTML templates
_TEMPLATE_DIR = Path(__file__).parent / "client" / "src"
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=False)


def get_index_html(static_path: str = "/static", title: str = "Trellis App") -> str:
    """Generate the HTML page that loads the React app.

    Uses the index.html Jinja2 template from server/client/src/.

    Args:
        static_path: URL path prefix for static assets (bundle.js, bundle.css)
        title: Page title

    Returns:
        Rendered HTML string
    """
    template = _jinja_env.get_template("index.html")
    return template.render(static_path=static_path, title=title)


@router.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the main HTML page."""
    return get_index_html()


def create_static_dir() -> Path:
    """Get or create the static files directory for server platform."""
    # Static files are in platforms/server/client/dist/
    static_dir = Path(__file__).parent / "client" / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
