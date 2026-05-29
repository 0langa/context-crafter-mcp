"""Tests for pluggable analyzer registry."""

from __future__ import annotations

from context_crafter_mcp.analyzers import (
    ANALYZER_REGISTRY,
    ANALYZER_SPECS,
    analyze_for_type,
    register_analyzer,
    register_analyzer_spec,
)
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, ScanConfig


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
