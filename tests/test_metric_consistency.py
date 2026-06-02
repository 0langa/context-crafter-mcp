"""Regression tests for scan-count truth and metric consistency."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all
from context_crafter_mcp.models import ScanConfig
from context_crafter_mcp.renderers.markdown import (
    render_agent_brief,
    render_ai_context_index,
    render_architecture_summary,
    render_project_overview,
    render_repo_map,
    render_run_state,
    render_scan_report,
    render_validation_report,
)


def _build_mixed_repo(root: Path) -> None:
    """Create a mixed Python + Node repo with analyzable files."""
    (root / "pyproject.toml").write_text("[project]\nname = 'mixed'\n")
    (root / "package.json").write_text('{"name":"mixed-web","scripts":{"start":"node src/index.js"}}\n')
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("def hello(): pass\n")
    (root / "src" / "index.ts").write_text("export const hi = 1;\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("def test_hello(): pass\n")


def test_scan_count_consistent_across_all_outputs() -> None:
    """Same generation run must yield identical files_scanned in every doc and JSON surface."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        analysis = state.analysis
        detect = state.detect_result
        assert detect is not None

        canonical = analysis.scan_summary.files_scanned
        # No drift: AnalysisResult.files_scanned must equal scanner truth
        assert analysis.files_scanned == canonical

        # Every renderer must emit the same count
        renderers = [
            render_project_overview(td, detect, analysis, "out"),
            render_repo_map(td, detect, analysis, "out"),
            render_architecture_summary(td, detect, analysis, "out"),
            render_ai_context_index(td, detect, analysis, "out"),
            render_agent_brief(td, detect, analysis, "out"),
            render_validation_report(td, detect, analysis, "out"),
            render_scan_report(td, detect, analysis, "out"),
            render_run_state(td, detect, analysis, "out", [], []),
        ]
        for rr in renderers:
            assert rr.files_scanned == canonical, f"Renderer {rr.written} used wrong count"

        # CLI / MCP JSON surface
        tool_result = state.to_tool_result()
        assert tool_result["files_scanned"] == canonical

        # Analyzer parsed count tracked separately and is positive
        assert analysis.analyzer_files_parsed > 0


def test_no_analyzer_can_inflate_scanner_count() -> None:
    """Language analyzers must not mutate the canonical scanner file count."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out")
        assert state.ok
        assert state.analysis is not None

        # scan_summary is scanner truth
        scanner_truth = state.analysis.scan_summary.files_scanned
        # files_scanned on AnalysisResult must not exceed scanner truth
        assert state.analysis.files_scanned == scanner_truth
        # parsed files may be fewer or equal, never greater than truth
        assert state.analysis.analyzer_files_parsed <= scanner_truth


def test_mixed_language_repo_stable_scanner_count() -> None:
    """Mixed-language repo must report stable, non-drifting scanner count."""
    with tempfile.TemporaryDirectory() as td1:
        root1 = Path(td1)
        _build_mixed_repo(root1)
        state1 = run_generate_all(td1, "out1")

        with tempfile.TemporaryDirectory() as td2:
            root2 = Path(td2)
            _build_mixed_repo(root2)
            state2 = run_generate_all(td2, "out2")

        assert state1.ok and state2.ok
        assert state1.analysis is not None
        assert state2.analysis is not None

        assert state1.analysis.scan_summary.files_scanned == state2.analysis.scan_summary.files_scanned
        assert state1.analysis.files_scanned == state2.analysis.files_scanned
        assert state1.analysis.analyzer_files_parsed == state2.analysis.analyzer_files_parsed
