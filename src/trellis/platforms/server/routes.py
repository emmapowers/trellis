"""HTTP routes for server platform.

WebSocket handling is in handler.py.
"""

from __future__ import annotations

import logging
import typing as tp
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse

from trellis.app.apploader import get_dist_dir

if tp.TYPE_CHECKING:
    from starlette.exceptions import HTTPException as StarletteHTTPException

    from trellis.platforms.server.ssr import SSROrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


def _is_document_request(request: Request) -> bool:
    """Check if the request is a browser document navigation.

    Returns True for requests that accept HTML (standard browser navigation),
    False for asset/API requests that should get a real 404.
    """
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def register_spa_fallback(app: FastAPI) -> None:
    """Register 404 handler that serves SPA HTML for client-side routing.

    This allows users to refresh on any client-side route (e.g., /about,
    /users/123) and get the SPA, which then handles routing on the client.
    Only handles document navigations — asset/API 404s pass through.

    Args:
        app: The FastAPI application to register the handler on.
    """

    @app.exception_handler(404)
    async def spa_fallback_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
        """Return SPA HTML for document 404s to support client-side routing."""
        if not _is_document_request(request):
            return HTMLResponse(content="Not Found", status_code=404)
        return await _ssr_or_static_response(request)


def _get_ssr_orchestrator(request: Request) -> SSROrchestrator | None:
    """Get the SSR orchestrator from app state, if configured."""
    return getattr(request.app.state, "trellis_ssr", None)


async def _ssr_or_static_response(request: Request) -> HTMLResponse:
    """Return SSR-rendered HTML if available, otherwise static HTML."""
    ssr = _get_ssr_orchestrator(request)
    if ssr is not None:
        try:
            html = await ssr.render_to_response(
                path=request.url.path,
                html_template=get_index_html(),
            )
            return HTMLResponse(content=html, status_code=200)
        except Exception:
            logger.exception("SSR render failed, falling back to static HTML")

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
async def index(request: Request) -> HTMLResponse:
    """Serve the main HTML page."""
    return await _ssr_or_static_response(request)


def create_static_dir() -> Path:
    """Get the static files directory for server platform."""
    static_dir = get_dist_dir()
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir
