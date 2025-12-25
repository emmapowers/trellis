"""HTTP routes for server platform.

WebSocket handling is in handler.py.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


def get_index_html(static_path: str = "/static") -> str:
    """Generate the HTML page that loads the React app."""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Trellis App</title>
    <link rel="stylesheet" href="{static_path}/bundle.css">
    <script>
        // Early theme detection to prevent flash of wrong theme
        (function() {{
            var theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            document.documentElement.dataset.theme = theme;
        }})();
    </script>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; }}
        html, body, #root {{ margin: 0; padding: 0; height: 100%; min-height: 100vh; }}
    </style>
</head>
<body>
    <div id="root" class="trellis-root"></div>
    <script type="module" src="{static_path}/bundle.js"></script>
</body>
</html>
"""


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
