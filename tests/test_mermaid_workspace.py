"""Tests for workspace wiring in Mermaid dependency graph."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.models import AnalysisResult, DetectResult, NodePackage
from context_crafter_mcp.renderers.mermaid import render_dependency_graph


def test_workspace_packages_appear_in_graph() -> None:
    with tempfile.TemporaryDirectory() as td:
        analysis = AnalysisResult(repo_path=td)
        analysis.node_packages = [
            NodePackage(name="root-tooling", rel_path="package.json", category="tooling"),
            NodePackage(name="dashboard", rel_path="apps/dashboard/package.json", category="product"),
        ]
        detect = DetectResult(repo_path=td, exists=True, project_types=["node"])
        result = render_dependency_graph(td, detect, analysis, "out")
        assert result.ok
        mmd_path = Path(result.written[0])
        content = mmd_path.read_text()
        assert "subgraph NodeWorkspace" in content
        assert "root-tooling" in content
        assert "dashboard" in content


def test_local_dependency_edges_wired() -> None:
    with tempfile.TemporaryDirectory() as td:
        analysis = AnalysisResult(repo_path=td)
        analysis.node_packages = [
            NodePackage(
                name="root-tooling",
                rel_path="package.json",
                category="tooling",
                dependencies=["dashboard"],
            ),
            NodePackage(
                name="dashboard",
                rel_path="apps/dashboard/package.json",
                category="product",
                dependencies=["react"],
            ),
        ]
        detect = DetectResult(repo_path=td, exists=True, project_types=["node"])
        result = render_dependency_graph(td, detect, analysis, "out")
        assert result.ok
        mmd_path = Path(result.written[0])
        content = mmd_path.read_text()
        # Edge from root-tooling to dashboard because dashboard is a local dep
        assert "root-tooling --> dashboard" in content or "root_tooling --> dashboard" in content
