"""HTTP routes for server platform.

WebSocket handling is in handler.py.
"""

from __future__ import annotations

import typing as tp
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from trellis.bundler.workspace import get_project_workspace

if tp.TYPE_CHECKING:
    from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()

# Jinja2 environment for HTML templates
_TEMPLATE_DIR = Path(__file__).parent / "client" / "src"
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)


def register_spa_fallback(app: FastAPI) -> None:
    """Register 404 handler that serves SPA HTML for client-side routing.

    This allows users to refresh on any client-side route (e.g., /about,
    /users/123) and get the SPA, which then handles routing on the client.

    Args:
        app: The FastAPI application to register the handler on.
    """

    @app.exception_handler(404)
    async def spa_fallback_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
        """Return SPA HTML for 404s to support client-side routing."""
        return HTMLResponse(content=get_index_html(), status_code=200)


def get_index_html(static_path: str = "/static", title: str = "Trellis App") -> str:
    """Generate the HTML page that loads the React app.

    Uses the index.html.j2 Jinja2 template from server/client/src/.

    Args:
        static_path: URL path prefix for static assets (bundle.js, bundle.css)
        title: Page title

    Returns:
        Rendered HTML string
    """
    template = _jinja_env.get_template("index.html.j2")
    return template.render(static_path=static_path, title=title)


@router.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the main HTML page."""
    return get_index_html()


def create_static_dir() -> Path:
    """Get or create the static files directory for server platform.

    Returns the dist directory in the workspace cache, which contains
    the bundled JS and CSS files.
    """
    entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
    workspace = get_project_workspace(entry_point)
    static_dir = workspace / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
