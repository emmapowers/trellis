"""PyInstaller hook for the ``rich`` library.

Rich dynamically loads ``rich._unicode_data.unicode17-0-0`` (and similar
version-tagged modules) via ``importlib.import_module()``.  The dots in
the module name confuse PyInstaller's static analysis, so we collect all
data files and submodules explicitly.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("rich")
hiddenimports = collect_submodules("rich")
