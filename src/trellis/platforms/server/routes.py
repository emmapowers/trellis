"""HTTP routes for server platform.

WebSocket handling is in handler.py.
"""

from __future__ import annotations

import typing as tp
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse

from trellis.app.apploader import get_dist_dir

if tp.TYPE_CHECKING:
    from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()


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


def get_index_html() -> str:
    """Get the index.html content for serving.

    Reads from dist/index.html which is rendered at build time by IndexHtmlRenderStep.

    Returns:
        HTML string
    """
    index_path = create_static_dir() / "index.html"
    return index_path.read_text()


@router.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Serve the main HTML page."""
    return get_index_html()


def create_static_dir() -> Path:
    """Get the static files directory for server platform."""
    static_dir = get_dist_dir()
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
