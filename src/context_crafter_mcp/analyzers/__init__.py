"""Repository analyzers for different project types."""

from __future__ import annotations

from typing import Callable

from context_crafter_mcp.models import AnalysisResult, ScanConfig

# Registry of analyzers keyed by project type name.
# Each analyzer must accept (repo_path: str, analysis: AnalysisResult | None, config: ScanConfig) -> AnalysisResult
AnalyzerFn = Callable[[str, AnalysisResult | None, ScanConfig], AnalysisResult]

ANALYZER_REGISTRY: dict[str, AnalyzerFn] = {}


def register_analyzer(project_type: str, fn: AnalyzerFn) -> AnalyzerFn:
    """Register an analyzer for a project type."""
    ANALYZER_REGISTRY[project_type] = fn
    return fn


def analyze_for_type(
    project_type: str,
    repo_path: str,
    analysis: AnalysisResult | None,
    config: ScanConfig,
) -> AnalysisResult:
    """Run the registered analyzer for a project type, if one exists."""
    fn = ANALYZER_REGISTRY.get(project_type)
    if fn is None:
        result = analysis or AnalysisResult(repo_path=repo_path)
        return result
    return fn(repo_path, analysis, config)


# Import all analyzers so they self-register in ANALYZER_REGISTRY.
# These imports must stay at the bottom to avoid circular import issues.
from context_crafter_mcp.analyzers import (  # noqa: E402,F401
    dotnet,
    go,
    java,
    node,
    python,
    rust,
)
