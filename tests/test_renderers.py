"""Tests for markdown and mermaid renderers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.generic import analyze_generic
from context_crafter_mcp.detectors import detect_project
from context_crafter_mcp.renderers.markdown import (
    render_architecture_summary,
    render_project_overview,
    render_repo_map,
)
from context_crafter_mcp.renderers.mermaid import render_dependency_graph


def test_render_project_overview() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "x"\n')
        detect = detect_project(td)
        analysis = analyze_generic(td)
        result = render_project_overview(td, detect, analysis, "docs")
        assert result.ok
        assert len(result.written) == 1
        assert Path(result.written[0]).exists()
        text = Path(result.written[0]).read_text()
        assert "GENERATED" in text


def test_render_repo_map() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src" / "app.py").parent.mkdir(parents=True)
        (root / "src" / "app.py").write_text("print(1)\n")
        detect = detect_project(td)
        analysis = analyze_generic(td)
        result = render_repo_map(td, detect, analysis, "docs")
        assert result.ok
        assert Path(result.written[0]).exists()


def test_render_dependency_graph() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "main.py").write_text("import os\n")
        detect = detect_project(td)
        analysis = analyze_generic(td)
        result = render_dependency_graph(td, detect, analysis, "docs")
        assert result.ok
        assert len(result.written) == 2
        mmd = Path(result.written[0])
        assert mmd.exists()
        text = mmd.read_text()
        assert "graph TD" in text


def test_render_architecture_summary() -> None:
    with tempfile.TemporaryDirectory() as td:
        detect = detect_project(td)
        analysis = analyze_generic(td)
        result = render_architecture_summary(td, detect, analysis, "docs")
        assert result.ok
        assert Path(result.written[0]).exists()
