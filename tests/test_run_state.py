"""Regression tests for RUN_STATE.json structure and scan metrics contract."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all
from context_crafter_mcp.models import ScanConfig


def _build_mixed_repo(root: Path) -> None:
    """Create a mixed Python + Node repo with analyzable files."""
    (root / "pyproject.toml").write_text("[project]\nname = 'mixed'\n")
    (root / "package.json").write_text('{"name":"mixed-web","scripts":{"start":"node src/index.js"}}\n')
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("def hello(): pass\n")
    (root / "src" / "index.ts").write_text("export const hi = 1;\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_main.py").write_text("def test_hello(): pass\n")


def test_run_state_structure() -> None:
    """RUN_STATE.json must contain the new canonical fields."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        run_state_path = Path(td, "out", "RUN_STATE.json")
        assert run_state_path.exists()
        data = json.loads(run_state_path.read_text(encoding="utf-8"))

        # Schema contract
        assert data.get("schema_mode") == "additive"

        # Backward compat
        assert "files_scanned" in data
        assert "analyzers_run" in data
        assert "output_files" in data

        # New fields
        assert "scan_summary" in data
        assert "analyzer_summary" in data
        assert "validation_summary" in data
        assert "warnings" in data
        assert "evidence_counts" in data

        ss = data["scan_summary"]
        assert "files_scanned" in ss
        assert "dirs_scanned" in ss
        assert "files_skipped" in ss
        assert "dirs_skipped" in ss
        assert "budget_exhausted" in ss
        assert "skipped_reasons" in ss
        assert "category_counts" in ss

        asum = data["analyzer_summary"]
        assert "analyzers_run" in asum
        assert "files_parsed" in asum

        vs = data["validation_summary"]
        assert "output_files_count" in vs
        assert "errors_count" in vs
        assert "warnings_count" in vs
        assert "bounded_scan" in vs

        ec = data["evidence_counts"]
        assert "observed" in ec
        assert "inferred" in ec
        assert "unknown" in ec
        assert "unsupported" in ec
        assert "error" in ec


def test_run_state_bounded_scan_flag() -> None:
    """bounded_scan is true when budget is exhausted or skips exist."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        # Add extra files in src/ so per-directory cap is hit
        for i in range(5):
            (root / "src" / f"mod_{i}.py").write_text(f"def fn_{i}(): pass\n")
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4, max_files_per_dir=2))
        assert state.ok
        assert state.analysis is not None

        run_state_path = Path(td, "out", "RUN_STATE.json")
        data = json.loads(run_state_path.read_text(encoding="utf-8"))
        vs = data["validation_summary"]
        assert vs["bounded_scan"] is True


def test_run_state_evidence_counts() -> None:
    """evidence_counts must be present and sum to total evidence items."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        run_state_path = Path(td, "out", "RUN_STATE.json")
        data = json.loads(run_state_path.read_text(encoding="utf-8"))
        ec = data["evidence_counts"]
        total = sum(ec.values())
        assert total == len(state.analysis.evidence_set.items)


def test_tool_result_has_scan_summary() -> None:
    """to_tool_result() must include scan_summary and analyzer_files_parsed."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        result = state.to_tool_result()
        assert "scan_summary" in result
        assert "analyzer_files_parsed" in result
        ss = result["scan_summary"]
        assert ss["files_scanned"] == state.analysis.scan_summary.files_scanned
        assert result["analyzer_files_parsed"] == state.analysis.analyzer_files_parsed


def test_run_state_backward_compat_values_match() -> None:
    """Legacy top-level fields must equal their structured counterparts where applicable."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        run_state_path = Path(td, "out", "RUN_STATE.json")
        data = json.loads(run_state_path.read_text(encoding="utf-8"))

        # Legacy files_scanned must equal canonical scan_summary.files_scanned
        assert data["files_scanned"] == data["scan_summary"]["files_scanned"]
        # Legacy analyzers_run must equal analyzer_summary.analyzers_run
        assert data["analyzers_run"] == data["analyzer_summary"]["analyzers_run"]


def test_run_state_output_files_count_matches_list() -> None:
    """validation_summary.output_files_count must equal len(output_files), including JSON companions."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        run_state_path = Path(td, "out", "RUN_STATE.json")
        data = json.loads(run_state_path.read_text(encoding="utf-8"))

        assert data["validation_summary"]["output_files_count"] == len(data["output_files"])
        assert "CONTEXT_MANIFEST.json" in data["output_files"]
        assert "RUN_STATE.json" in data["output_files"]


def test_context_manifest_structure() -> None:
    """CONTEXT_MANIFEST.json describes the generated bundle for downstream consumers."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_mixed_repo(root)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=4))
        assert state.ok
        assert state.analysis is not None

        manifest_path = Path(td, "out", "CONTEXT_MANIFEST.json")
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert data["schema_version"] == "1.0"
        assert data["schema_mode"] == "additive"
        assert state.detect_result is not None
        assert data["project_types"] == state.detect_result.project_types
        assert data["recommended_start"] == {
            "agent": "AGENT_BRIEF.md",
            "human": "PROJECT_OVERVIEW.md",
            "navigation": "AI_CONTEXT_INDEX.md",
            "automation": "RUN_STATE.json",
        }
        assert data["scan_summary"]["files_scanned"] == state.analysis.scan_summary.files_scanned
        assert data["evidence_counts"]["unknown"] >= 0

        files = {entry["path"]: entry for entry in data["files"]}
        assert files["AGENT_BRIEF.md"]["audience"] == ["agent"]
        assert files["CONTEXT_MANIFEST.json"]["role"] == "manifest"
        assert files["RUN_STATE.json"]["role"] == "run-state"
