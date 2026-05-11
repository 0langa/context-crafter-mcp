"""Tests for self-test CLI mode."""

from __future__ import annotations

import tempfile
from pathlib import Path

from repo_docs_mcp.graph import run_generate_all


def test_self_test_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        state = run_generate_all(td, "docs/generated")
        assert state.ok
        assert len(state.written) == 5
        names = [Path(w).name for w in state.written]
        assert "PROJECT_OVERVIEW.md" in names
        assert "REPO_MAP.md" in names
        assert "DEPENDENCY_GRAPH.mmd" in names
        assert "DEPENDENCY_GRAPH.md" in names
        assert "ARCHITECTURE_SUMMARY.md" in names
