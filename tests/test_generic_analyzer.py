"""Tests for generic analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from repo_docs_mcp.analyzers.generic import analyze_generic


def test_generic_scan() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Hello")
        (root / "src" / "main.py").parent.mkdir(parents=True)
        (root / "src" / "main.py").write_text("print(1)\n")
        (root / "tests" / "test_main.py").parent.mkdir(parents=True)
        (root / "tests" / "test_main.py").write_text("def test(): pass\n")
        result = analyze_generic(td)
        assert result.files_scanned > 0
        assert any("README.md" in f for f in result.root_files)
        assert any("src" in d for d in result.source_directories)
        assert any("tests" in d for d in result.test_directories)
