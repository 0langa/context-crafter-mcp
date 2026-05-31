"""Tests for pluggable analyzer registry."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers import (
    ANALYZER_REGISTRY,
    ANALYZER_SPECS,
    AnalyzerRegistry,
    DetectedProject,
    analyze_for_type,
    register_analyzer,
    register_analyzer_spec,
)
from context_crafter_mcp.detectors import detect_project_from_snapshot
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, ScanConfig
from context_crafter_mcp.scanner import Scanner, ScannerOptions


def test_registry_has_expected_types() -> None:
    expected = {"generic", "python", "node", "dotnet", "rust", "go", "java"}
    for ptype in expected:
        assert ptype in ANALYZER_REGISTRY, f"Missing analyzer: {ptype}"


def test_specs_has_expected_types() -> None:
    expected = {"generic", "python", "node", "dotnet", "rust", "go", "java"}
    for ptype in expected:
        assert ptype in ANALYZER_SPECS, f"Missing analyzer spec: {ptype}"
        spec = ANALYZER_SPECS[ptype]
        assert spec.project_type == ptype
        assert spec.display_name
        assert spec.support_level in ("metadata", "syntax", "ast", "mixed", "generic")
        assert spec.parser


def test_analyze_for_type_missing_returns_base() -> None:
    result = analyze_for_type("nonexistent", "/tmp/fake", None, ScanConfig())
    assert result.repo_path == "/tmp/fake"


def test_register_new_analyzer() -> None:
    def dummy_analyzer(repo_path: str, analysis: AnalysisResult | None, config: ScanConfig) -> AnalysisResult:
        result = analysis or AnalysisResult(repo_path=repo_path)
        result.errors.append("dummy")
        return result

    register_analyzer("dummy", dummy_analyzer)
    assert "dummy" in ANALYZER_REGISTRY
    result = analyze_for_type("dummy", "/tmp/fake", None, ScanConfig())
    assert "dummy" in result.errors


def test_register_new_spec() -> None:
    spec = AnalyzerSpec(
        project_type="dummy2",
        display_name="Dummy",
        support_level="metadata",
        parser="none",
        detects=["dummy.txt"],
        limitations=["None"],
    )
    register_analyzer_spec(spec)
    assert "dummy2" in ANALYZER_SPECS
    assert ANALYZER_SPECS["dummy2"].display_name == "Dummy"


# AnalyzerRegistry class tests


def test_analyzer_registry_from_globals() -> None:
    registry = AnalyzerRegistry.from_globals()
    expected = {"generic", "python", "node", "dotnet", "rust", "go", "java"}
    for ptype in expected:
        assert ptype in registry._analyzers, f"Missing analyzer in registry: {ptype}"
        assert ptype in registry._specs, f"Missing spec in registry: {ptype}"


def test_analyzer_registry_register() -> None:
    registry = AnalyzerRegistry()

    def dummy_analyzer(repo_path: str, analysis: AnalysisResult | None, config: ScanConfig) -> AnalysisResult:
        result = analysis or AnalysisResult(repo_path=repo_path)
        result.errors.append("registry_dummy")
        return result

    spec = AnalyzerSpec(
        project_type="registry_dummy",
        display_name="Registry Dummy",
        support_level="metadata",
        parser="none",
    )
    registry.register(spec, dummy_analyzer)
    assert "registry_dummy" in registry._analyzers
    assert "registry_dummy" in registry._specs
    result = registry.analyze_for_type("registry_dummy", "/tmp/fake", None, ScanConfig())
    assert "registry_dummy" in result.errors


def test_analyzer_registry_analyze_for_type_missing_returns_base() -> None:
    registry = AnalyzerRegistry()
    result = registry.analyze_for_type("nonexistent", "/tmp/fake", None, ScanConfig())
    assert result.repo_path == "/tmp/fake"


def test_analyzer_registry_analyze_for_type_preserves_base() -> None:
    registry = AnalyzerRegistry.from_globals()
    base = AnalysisResult(repo_path="/tmp/fake")
    base.errors.append("existing")
    result = registry.analyze_for_type("nonexistent", "/tmp/fake", base, ScanConfig())
    assert result.errors == ["existing"]


def test_analyzer_registry_merge() -> None:
    a = AnalysisResult(repo_path="/tmp/a", project_types=["python"], files_scanned=10)
    a.python_modules = []
    a.errors = ["e1"]
    b = AnalysisResult(repo_path="/tmp/b", project_types=["node"], files_scanned=20)
    b.python_modules = []
    b.errors = ["e2"]

    registry = AnalyzerRegistry()
    merged = registry.merge([a, b])
    assert merged.repo_path == "/tmp/a"
    assert set(merged.project_types) == {"python", "node"}
    assert merged.files_scanned == 20
    assert merged.errors == ["e1", "e2"]


def test_analyzer_registry_merge_empty_list() -> None:
    registry = AnalyzerRegistry()
    merged = registry.merge([])
    assert merged.repo_path == ""


def test_detect_project_from_snapshot() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        Path(td, "main.py").write_text("print('hi')\n", encoding="utf-8")
        snapshot = Scanner().scan(td, ScannerOptions(max_depth=3, max_files=500, max_files_per_dir=100))
        result = detect_project_from_snapshot(snapshot)
        assert result.exists
        assert "python" in result.project_types
        assert "generic" in result.project_types


def test_analyzer_registry_analyze_uses_snapshot() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        Path(td, "main.py").write_text("print('hi')\n", encoding="utf-8")
        snapshot = Scanner().scan(td, ScannerOptions(max_depth=6, max_files=500, max_files_per_dir=100))
        registry = AnalyzerRegistry.from_globals()
        result = registry.analyze(snapshot, DetectedProject(project_type="python"), ScanConfig())
        assert result.snapshot is snapshot
        assert any(mod.rel_path == "main.py" for mod in result.python_modules)
