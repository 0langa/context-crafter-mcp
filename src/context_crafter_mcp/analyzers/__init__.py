"""Repository analyzers for different project types."""

from __future__ import annotations

from typing import Callable

from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, ScanConfig

# Registry of analyzer functions keyed by project type.
AnalyzerFn = Callable[[str, AnalysisResult | None, ScanConfig], AnalysisResult]

ANALYZER_REGISTRY: dict[str, AnalyzerFn] = {}

# Registry of analyzer metadata specs keyed by project type.
ANALYZER_SPECS: dict[str, AnalyzerSpec] = {}


def register_analyzer(project_type: str, fn: AnalyzerFn) -> AnalyzerFn:
    """Register an analyzer for a project type."""
    ANALYZER_REGISTRY[project_type] = fn
    return fn


def register_analyzer_spec(spec: AnalyzerSpec) -> None:
    """Register an AnalyzerSpec for a project type."""
    ANALYZER_SPECS[spec.project_type] = spec


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
    generic,
    go,
    java,
    node,
    python,
    rust,
)
