"""Browser platform - Pyodide function calls.

This platform is not yet implemented.
"""

from trellis.core.platform import Platform


class BrowserPlatform(Platform):
    """Browser platform using Pyodide function calls.

    Not yet implemented - raises NotImplementedError when used.
    """

    @property
    def name(self) -> str:
        return "browser"

    async def run(self, root_component, **kwargs) -> None:  # type: ignore[no-untyped-def]
        raise NotImplementedError(
            "Browser platform is not yet implemented. Use platform='server' for now."
        )


__all__ = ["BrowserPlatform"]
