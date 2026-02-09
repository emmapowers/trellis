"""Trellis configuration for the browser library build."""

from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

config = Config(
    name="trellis",
    module="trellis_lib",
    platform=PlatformType.BROWSER,
    library=True,
)
