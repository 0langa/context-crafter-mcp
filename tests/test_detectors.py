"""Tests for project type detection."""

from __future__ import annotations

import tempfile
from pathlib import Path

from repo_docs_mcp.detectors import detect_project


def test_detect_missing_path() -> None:
    result = detect_project("/nonexistent/path/12345")
    assert not result.exists
    assert result.error is not None


def test_detect_python_project() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text('[project]\nname = "x"\n')
        (root / "src" / "app.py").parent.mkdir(parents=True)
        (root / "src" / "app.py").write_text("print(1)\n")
        result = detect_project(td)
        assert result.exists
        assert "python" in result.project_types
        assert "generic" in result.project_types
        assert any("pyproject.toml" in m for m in result.markers.get("python", []))


def test_detect_node_project() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "package.json").write_text('{"name":"x"}\n')
        (root / "index.js").write_text("module.exports = 1;\n")
        result = detect_project(td)
        assert result.exists
        assert "node" in result.project_types


def test_detect_dotnet_project() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "App.csproj").write_text("<Project></Project>\n")
        result = detect_project(td)
        assert result.exists
        assert "dotnet" in result.project_types
