"""Tests for the LangGraph pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import build_graph, run_generate_all
from context_crafter_mcp.models import ScanConfig
from context_crafter_mcp.state import RepoState


def _state_from_result(result):
    if isinstance(result, RepoState):
        return result
    final = RepoState()
    for key, value in result.items():
        if hasattr(final, key):
            setattr(final, key, value)
    return final


def test_graph_pipeline_success() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        Path(td, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        graph = build_graph()
        state = RepoState(repo_path=td, output_dir="out")
        result = _state_from_result(graph.invoke(state))
        assert result.ok is True
        assert len(result.written) >= 8
        assert result.detect_result is not None
        assert "python" in result.detect_result.project_types
        assert result.analysis is not None
        assert result.analysis.files_scanned > 0


def test_graph_pipeline_invalid_repo() -> None:
    graph = build_graph()
    state = RepoState(repo_path="/nonexistent/path/12345", output_dir="out")
    result = _state_from_result(graph.invoke(state))
    assert result.ok is False
    assert len(result.errors) > 0
    assert len(result.written) == 0


def test_repo_state_to_tool_result() -> None:
    state = RepoState(repo_path=".", output_dir="out")
    state.written = ["a.md", "b.md"]
    result = state.to_tool_result()
    assert result["ok"] is True
    assert result["written"] == ["a.md", "b.md"]
    assert "summary" in result
    assert "errors" in result


def test_run_generate_all_with_config() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        Path(td, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        config = ScanConfig(profile="deep", max_depth=6)
        result = run_generate_all(td, "out", config)
        assert result.ok is True
        assert len(result.written) >= 8
