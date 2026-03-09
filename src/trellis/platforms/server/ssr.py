"""SSR orchestration for the HTTP route."""

from __future__ import annotations

import logging
import typing as tp
from uuid import uuid4

from trellis.core.rendering.session import RenderSession
from trellis.core.rendering.ssr import render_for_ssr
from trellis.platforms.common.handler import _serialize_patches
from trellis.platforms.common.serialization import serialize_element
from trellis.platforms.common.ssr_utils import build_dehydration_data
from trellis.platforms.server.session_store import SessionEntry, SessionStore
from trellis.platforms.server.ssr_cache import SSRCache

if tp.TYPE_CHECKING:
    from trellis.platforms.common.handler import AppWrapper
    from trellis.platforms.server.ssr_renderer import SSRRenderer

logger = logging.getLogger(__name__)


class SSROrchestrator:
    """Orchestrates SSR: creates session, renders, stores for resumption.

    Caches the rendered HTML fragment (renderToString output) per
    route+theme.  Dehydration data (patches, session ID) is always
    computed fresh because element IDs are non-deterministic across
    sessions.
    """

    def __init__(
        self,
        root_component: tp.Any,
        app_wrapper: AppWrapper,
        session_store: SessionStore,
        ssr_renderer: SSRRenderer | None,
    ) -> None:
        self._root_component = root_component
        self._app_wrapper = app_wrapper
        self._session_store = session_store
        self._ssr_renderer = ssr_renderer
        self._cache = SSRCache()

    def render_to_response(
        self,
        path: str,
        system_theme: str,
        theme_mode: str | None,
        html_template: str,
    ) -> str:
        """Render the app to a complete HTML response.

        Every request creates a fresh session and computes dehydration
        data.  The expensive renderToString() call is cached per
        route+theme so only the first request for each combination hits
        the Bun sidecar.
        """
        # Create session and render (always — patches are per-session)
        wrapped = self._app_wrapper(
            self._root_component,
            system_theme,
            theme_mode,
        )
        session = RenderSession(wrapped)
        session.initial_path = path
        session_id = str(uuid4())

        ssr_result = render_for_ssr(session)
        wire_patches = _serialize_patches(ssr_result.patches, session)

        # Store session for WebSocket resumption
        entry = SessionEntry(
            session=session,
            deferred_mounts=ssr_result.deferred_mounts,
            deferred_unmounts=ssr_result.deferred_unmounts,
            patches=wire_patches,
        )
        self._session_store.store(session_id, entry)

        # Get rendered HTML — from cache or Bun sidecar
        ssr_html = self._get_ssr_html(path, system_theme, theme_mode, session)

        # Build dehydration data (always fresh — element IDs are per-session)
        dehydration_data = build_dehydration_data(session_id, wire_patches)

        # Inject into template
        result = html_template.replace("<!--ssr-outlet-->", ssr_html)
        dehydration_script = f"<script>window.__TRELLIS_SSR__ = {dehydration_data};</script>"
        return result.replace("</body>", f"{dehydration_script}\n</body>")

    def invalidate_cache(self) -> None:
        """Clear the HTML cache. Called on hot reload / rebuild."""
        self._cache.invalidate()

    def _get_ssr_html(
        self, path: str, system_theme: str, theme_mode: str | None, session: RenderSession
    ) -> str:
        """Get rendered HTML, using the cache when possible."""
        cache_key = f"{system_theme}:{theme_mode or 'system'}"
        cached = self._cache.get(path, cache_key)
        if cached is not None:
            return cached

        # Render via Bun sidecar
        ssr_html = ""
        if self._ssr_renderer is not None and self._ssr_renderer.is_available:
            assert session.root_element is not None
            tree = serialize_element(session.root_element, session)
            rendered = self._ssr_renderer.render(tree)
            if rendered is not None:
                ssr_html = rendered
                self._cache.put(path, cache_key, ssr_html)

        return ssr_html
