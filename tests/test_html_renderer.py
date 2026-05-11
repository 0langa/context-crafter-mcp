"""Tests for HTML renderer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from repo_docs_mcp.analyzers.generic import analyze_generic
from repo_docs_mcp.detectors import detect_project
from repo_docs_mcp.renderers.html import render_html_overview


def test_html_overview_generated() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("print(1)\n")
        detect = detect_project(td)
        analysis = analyze_generic(td)
        result = render_html_overview(td, detect, analysis, "docs")
        assert result.ok
        assert any("PROJECT_OVERVIEW.html" in w for w in result.written)
        html_path = Path(result.written[0])
        assert html_path.exists()
        text = html_path.read_text()
        assert "<!DOCTYPE html>" in text
        assert "Project Overview" in text
