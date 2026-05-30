"""Tests for markdown and mermaid renderers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.generic import analyze_generic
from context_crafter_mcp.detectors import detect_project
from context_crafter_mcp.models import PythonModule
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


def test_render_project_overview_shows_all_source_dirs_with_python() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Python source
        (root / "src" / "app.py").parent.mkdir(parents=True)
        (root / "src" / "app.py").write_text("print(1)\n")
        # Non-Python source directories
        (root / "apps" / "web" / "src" / "index.ts").parent.mkdir(parents=True)
        (root / "apps" / "web" / "src" / "index.ts").write_text("export {}\n")
        (root / "lib" / "helpers.py").parent.mkdir(parents=True)
        (root / "lib" / "helpers.py").write_text("def helper(): pass\n")

        detect = detect_project(td)
        analysis = analyze_generic(td)
        # Inject Python module to trigger the polyglot path
        analysis.python_modules = [
            PythonModule(
                rel_path="src/app.py",
                module_name="app",
                classes=["App"],
                functions=["main"],
            ),
        ]
        result = render_project_overview(td, detect, analysis, "docs")
        assert result.ok
        text = Path(result.written[0]).read_text()
        # Source Layout should show ALL directories, not just Python ones
        assert "apps/web/src" in text, f"missing non-Python source dir in output: {text[:1000]}"
        assert "lib" in text, f"missing lib source dir in output: {text[:1000]}"
        # Python module detail should also appear
        assert "Python modules" in text, f"missing Python modules subsection: {text[:1000]}"
        assert "src/app.py" in text, f"missing Python module in output: {text[:1000]}"


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
