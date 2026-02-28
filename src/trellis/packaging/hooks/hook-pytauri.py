"""PyInstaller hook for the ``pytauri`` ecosystem.

The ``pytauri`` distribution installs several sibling packages
(``pytauri_plugins``, ``pytauri_utils``) that have no distribution
metadata of their own.  Trellis loads ``pytauri_plugins.dialog`` via
``importlib.import_module()`` at runtime, so PyInstaller can't trace it.
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("pytauri_plugins")
    + collect_submodules("pytauri_utils")
)
