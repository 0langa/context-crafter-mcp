"""Tests for MCP tool backing functions."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import (
    run_detect,
    run_generate_all,
    run_generate_architecture_summary,
    run_generate_dependency_graph,
    run_generate_project_overview,
    run_generate_repo_map,
)


def test_run_detect() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "package.json").write_text('{"name":"x"}')
        result = run_detect(td)
        assert result.exists
        assert "node" in result.project_types


def test_run_generate_project_overview() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        result = run_generate_project_overview(td, "out")
        assert result.ok
        assert any("PROJECT_OVERVIEW.md" in w for w in result.written)


def test_run_generate_repo_map() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        result = run_generate_repo_map(td, "out")
        assert result.ok
        assert any("REPO_MAP.md" in w for w in result.written)


def test_run_generate_dependency_graph() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("import os\n")
        result = run_generate_dependency_graph(td, "out")
        assert result.ok
        assert any("DEPENDENCY_GRAPH.mmd" in w for w in result.written)
        assert any("DEPENDENCY_GRAPH.md" in w for w in result.written)


def test_run_generate_architecture_summary() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        result = run_generate_architecture_summary(td, "out")
        assert result.ok
        assert any("ARCHITECTURE_SUMMARY.md" in w for w in result.written)


def test_run_generate_all() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("import os\nclass A: pass\n")
        state = run_generate_all(td, "out")
        assert state.ok
        assert len(state.written) == 11
        assert state.resolved_output_dir == str((Path(td) / "out").resolve())
        names = [Path(w).name for w in state.written]
        assert "AI_CONTEXT_INDEX.md" in names
        assert "PROJECT_OVERVIEW.md" in names
        assert "REPO_MAP.md" in names
        assert "DEPENDENCY_GRAPH.mmd" in names
        assert "DEPENDENCY_GRAPH.md" in names
        assert "ARCHITECTURE_SUMMARY.md" in names
        assert "AGENT_BRIEF.md" in names
        assert "VALIDATION_REPORT.md" in names
        assert "SCAN_REPORT.md" in names
        assert "CONTEXT_MANIFEST.json" in names
        assert "RUN_STATE.json" in names


def test_run_generate_all_confines_output_outside_repo() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("import os\n")
        state = run_generate_all(td, "../escape")
        assert state.ok
        assert state.resolved_output_dir == str((Path(td) / "docs" / "generated").resolve())
