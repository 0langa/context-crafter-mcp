"""Tests for pluggable analyzer registry."""

from __future__ import annotations

from context_crafter_mcp.analyzers import ANALYZER_REGISTRY, analyze_for_type
from context_crafter_mcp.models import AnalysisResult, ScanConfig


def test_registry_has_expected_types() -> None:
    expected = {"generic", "python", "node", "dotnet", "rust", "go", "java"}
    for ptype in expected:
        assert ptype in ANALYZER_REGISTRY, f"Missing analyzer: {ptype}"


def test_analyze_for_type_missing_returns_base() -> None:
    result = analyze_for_type("nonexistent", "/tmp/fake", None, ScanConfig())
    assert result.repo_path == "/tmp/fake"


def test_register_new_analyzer() -> None:
    def dummy_analyzer(repo_path: str, analysis: AnalysisResult | None, config: ScanConfig) -> AnalysisResult:
        result = analysis or AnalysisResult(repo_path=repo_path)
        result.errors.append("dummy")
        return result

    from context_crafter_mcp.analyzers import register_analyzer

    register_analyzer("dummy", dummy_analyzer)
    assert "dummy" in ANALYZER_REGISTRY
    result = analyze_for_type("dummy", "/tmp/fake", None, ScanConfig())
    assert "dummy" in result.errors
