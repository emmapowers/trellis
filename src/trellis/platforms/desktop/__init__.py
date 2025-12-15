"""Desktop platform - PyTorii IPC.

This platform is not yet implemented.
"""

from trellis.core.platform import Platform


class DesktopPlatform(Platform):
    """Desktop platform using PyTorii IPC.

    Not yet implemented - raises NotImplementedError when used.
    """

    @property
    def name(self) -> str:
        return "desktop"

    async def run(self, root_component, **kwargs) -> None:  # type: ignore[no-untyped-def]
        raise NotImplementedError(
            "Desktop platform is not yet implemented. Use platform='server' for now."
        )


__all__ = ["DesktopPlatform"]
