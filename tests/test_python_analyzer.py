"""Tests for Python analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from repo_docs_mcp.analyzers.python import analyze_python


def test_python_basic() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text(
            "import os\n"
            "from collections import abc\n"
            "class Foo:\n    pass\n"
            "def bar():\n    pass\n"
            "async def baz():\n    pass\n"
            'if __name__ == "__main__":\n    bar()\n'
        )
        result = analyze_python(td)
        assert result.python_modules
        mod = result.python_modules[0]
        assert "os" in mod.imports
        assert "collections" in mod.imports
        assert "Foo" in mod.classes
        assert "bar" in mod.functions
        assert "baz" in mod.async_functions
        assert mod.is_entry_point


def test_python_console_scripts() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "x"\nscripts = { cli = "app:main" }\n')
        result = analyze_python(td)
        assert any("cli" in ep for ep in result.likely_entry_points)
