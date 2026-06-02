"""Analyzer registry with detection, analysis, and merge support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from context_crafter_mcp.detectors import detect_project_from_snapshot
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, ScanConfig
from context_crafter_mcp.scanner import RepoSnapshot

AnalyzerFn = Callable[[str, AnalysisResult | None, ScanConfig], AnalysisResult]


@dataclass
class DetectedProject:
    """Lightweight wrapper for a detected project type."""

    project_type: str
    markers: list[str] = field(default_factory=list)
    evidence: str = "unknown"


class AnalyzerRegistry:
    """Registry for analyzer specs and functions with detect/analyze/merge helpers."""

    def __init__(
        self,
        analyzers: dict[str, AnalyzerFn] | None = None,
        specs: dict[str, AnalyzerSpec] | None = None,
    ) -> None:
        self._analyzers: dict[str, AnalyzerFn] = dict(analyzers) if analyzers else {}
        self._specs: dict[str, AnalyzerSpec] = dict(specs) if specs else {}

    @classmethod
    def from_globals(cls) -> AnalyzerRegistry:
        """Create a registry populated from the global analyzer modules."""
        from context_crafter_mcp.analyzers import ANALYZER_REGISTRY, ANALYZER_SPECS

        return cls(ANALYZER_REGISTRY, ANALYZER_SPECS)

    def register(self, spec: AnalyzerSpec, fn: AnalyzerFn) -> None:
        """Register an analyzer spec and function."""
        self._analyzers[spec.project_type] = fn
        self._specs[spec.project_type] = spec

    def detect(self, snapshot: RepoSnapshot) -> list[DetectedProject]:
        """Detect project types from a repository snapshot."""
        result = detect_project_from_snapshot(snapshot)
        detected: list[DetectedProject] = []
        for ptype in result.project_types:
            markers = result.markers.get(ptype, [])
            ev = result.evidence.get(ptype, "unknown")
            detected.append(DetectedProject(project_type=ptype, markers=markers, evidence=ev))
        return detected

    def analyze(self, snapshot: RepoSnapshot, detected: DetectedProject, config: ScanConfig) -> AnalysisResult:
        """Run the registered analyzer for a detected project type."""
        fn = self._analyzers.get(detected.project_type)
        if fn is None:
            return AnalysisResult(repo_path=str(snapshot.root), snapshot=snapshot)
        base = AnalysisResult(repo_path=str(snapshot.root), snapshot=snapshot)
        return fn(str(snapshot.root), base, config)

    def analyze_for_type(
        self,
        project_type: str,
        repo_path: str,
        analysis: AnalysisResult | None,
        config: ScanConfig,
    ) -> AnalysisResult:
        """Run the registered analyzer for a project type, passing an existing result for in-place mutation."""
        fn = self._analyzers.get(project_type)
        if fn is None:
            result = analysis or AnalysisResult(repo_path=repo_path)
            return result
        return fn(repo_path, analysis, config)

    def merge(self, results: list[AnalysisResult]) -> AnalysisResult:
        """Merge multiple analysis results into one."""
        if not results:
            return AnalysisResult(repo_path="")
        base = results[0]
        for other in results[1:]:
            base.project_types = sorted(set(base.project_types + other.project_types))
            base.root_files = sorted(set(base.root_files + other.root_files))
            base.directory_tree = sorted(set(base.directory_tree + other.directory_tree))
            base.docs_files = sorted(set(base.docs_files + other.docs_files))
            base.config_files = sorted(set(base.config_files + other.config_files))
            base.likely_entry_points = sorted(set(base.likely_entry_points + other.likely_entry_points))
            base.test_directories = sorted(set(base.test_directories + other.test_directories))
            base.source_directories = sorted(set(base.source_directories + other.source_directories))
            base.python_modules = base.python_modules + other.python_modules
            base.node_packages = base.node_packages + other.node_packages
            base.dotnet_projects = base.dotnet_projects + other.dotnet_projects
            base.dotnet_solutions = base.dotnet_solutions + other.dotnet_solutions
            base.rust_crates = base.rust_crates + other.rust_crates
            base.go_modules = base.go_modules + other.go_modules
            base.java_projects = base.java_projects + other.java_projects
            base.files_scanned = max(base.files_scanned, other.files_scanned)
            base.analyzer_files_parsed = base.analyzer_files_parsed + other.analyzer_files_parsed
            base.errors = base.errors + other.errors
            base.python_dependencies = sorted(set(base.python_dependencies + other.python_dependencies))
            base.python_dev_dependencies = sorted(set(base.python_dev_dependencies + other.python_dev_dependencies))
            base.workspace_packages = sorted(set(base.workspace_packages + other.workspace_packages))
            base.profile = other.profile or base.profile
            base.evidence_set.items.extend(other.evidence_set.items)
            base.scan_summary.files_scanned = max(base.scan_summary.files_scanned, other.scan_summary.files_scanned)
            base.scan_summary.dirs_scanned = max(base.scan_summary.dirs_scanned, other.scan_summary.dirs_scanned)
            base.scan_summary.files_skipped = max(base.scan_summary.files_skipped, other.scan_summary.files_skipped)
            base.scan_summary.dirs_skipped = max(base.scan_summary.dirs_skipped, other.scan_summary.dirs_skipped)
            base.scan_summary.budget_exhausted = (
                base.scan_summary.budget_exhausted or other.scan_summary.budget_exhausted
            )
            for k, v in other.scan_summary.skipped_reasons.items():
                base.scan_summary.skipped_reasons[k] = base.scan_summary.skipped_reasons.get(k, 0) + v
            for k, v in other.scan_summary.category_counts.items():
                base.scan_summary.category_counts[k] = base.scan_summary.category_counts.get(k, 0) + v
            if not base.metadata.name and other.metadata.name:
                base.metadata = other.metadata
        return base
