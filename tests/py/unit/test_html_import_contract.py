from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path


def test_trellis_html_does_not_import_generated_style_types(tmp_path: Path) -> None:
    snippet = textwrap.dedent(
        """
        import json
        import sys

        import trellis.html

        print(json.dumps(sorted(name for name in sys.modules if name.startswith("trellis.html"))))
        """
    )
    snippet_path = tmp_path / "inspect_html_imports.py"
    snippet_path.write_text(snippet)

    result = subprocess.run(
        [sys.executable, str(snippet_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[4],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    loaded_modules = set(json.loads(result.stdout))
    assert "trellis.html._generated_style_types" not in loaded_modules


def test_trellis_html_does_not_import_generated_attribute_types(tmp_path: Path) -> None:
    snippet = textwrap.dedent(
        """
        import json
        import sys

        import trellis.html

        print(json.dumps(sorted(name for name in sys.modules if name.startswith("trellis.html"))))
        """
    )
    snippet_path = tmp_path / "inspect_html_imports.py"
    snippet_path.write_text(snippet)

    result = subprocess.run(
        [sys.executable, str(snippet_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[4],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    loaded_modules = set(json.loads(result.stdout))
    assert "trellis.html._generated_attribute_types" not in loaded_modules
