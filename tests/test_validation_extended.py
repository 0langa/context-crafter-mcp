"""Tests for extended validation checks."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.validation import validate_output_dir


def test_broken_markdown_link_detected() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td, "out")
        out.mkdir()
        # Create required files
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        # Add a broken link in one file
        Path(out, "AI_CONTEXT_INDEX.md").write_text("[Broken](MISSING.md)\n")
        result = validate_output_dir(out)
        codes = [c.code for c in result.checks]
        assert "broken_markdown_link" in codes


def test_missing_mermaid_block() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        result = validate_output_dir(out)
        codes = [c.code for c in result.checks]
        assert "missing_mermaid_block" in codes


def test_fixture_pollution_warning() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("- tests/fixtures/foo.py\n")
        result = validate_output_dir(out)
        codes = [c.code for c in result.checks]
        assert "fixture_path_primary_claim" in codes


def test_validation_json_structure() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        # Provide a basic mermaid block
        Path(out, "DEPENDENCY_GRAPH.md").write_text("```mermaid\ngraph TD\nA-->B\n```\n")
        result = validate_output_dir(out)
        d = result.to_dict()
        assert "ok" in d
        assert "checks" in d
        assert "found" in d
        assert "missing" in d
        assert "count" in d
        assert "expected" in d
        for c in d["checks"]:
            assert "code" in c
            assert "level" in c
            assert "message" in c


def test_referenced_source_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("See `src/missing.py` for details.\n")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" in codes


def test_referenced_source_with_line_number() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("pass\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        # Reference with line number suffix — should resolve to src/app.py after stripping :42
        Path(out, "PROJECT_OVERVIEW.md").write_text("See `src/app.py:42` for details.\n")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" not in codes


def test_referenced_source_deep_manifest_found() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        # Manifest lives deep in product path, not at root
        (repo / "services" / "api" / "python").mkdir(parents=True)
        (repo / "services" / "api" / "python" / "pyproject.toml").write_text("[project]\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        # Bare manifest name referenced in generated doc
        Path(out, "PROJECT_OVERVIEW.md").write_text("Look for `pyproject.toml`.")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" not in codes, (
            f"deep pyproject.toml should be found, got: {[c.message for c in result.checks if c.code == 'referenced_source_missing']}"
        )


def test_fixture_deep_manifest_does_not_silence_warning() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        # Manifest only exists in fixtures — should NOT suppress warning
        (repo / "tests" / "fixtures").mkdir(parents=True)
        (repo / "tests" / "fixtures" / "pyproject.toml").write_text("[project]\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("Look for `pyproject.toml`.")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" in codes, (
            f"fixture pyproject.toml should NOT suppress warning, got: {[c.message for c in result.checks]}"
        )


def test_vendor_deep_manifest_does_not_silence_warning() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        # Manifest only exists in vendor — should NOT suppress warning
        (repo / "vendor" / "some-lib").mkdir(parents=True)
        (repo / "vendor" / "some-lib" / "pyproject.toml").write_text("[project]\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("Look for `pyproject.toml`.")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" in codes, (
            f"vendor pyproject.toml should NOT suppress warning, got: {[c.message for c in result.checks]}"
        )


def test_demo_repo_deep_manifest_does_not_silence_warning() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        # Manifest only exists in examples/demo-repo — should NOT suppress warning
        (repo / "examples" / "demo-repo").mkdir(parents=True)
        (repo / "examples" / "demo-repo" / "pyproject.toml").write_text("[project]\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("Look for `pyproject.toml`.")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" in codes, (
            f"demo-repo pyproject.toml should NOT suppress warning, got: {[c.message for c in result.checks]}"
        )


def test_product_fixture_manifest_silences_warning() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td, "repo")
        repo.mkdir()
        # Manifest in src/fixtures (legitimate product dir) — SHOULD suppress warning
        (repo / "src" / "fixtures").mkdir(parents=True)
        (repo / "src" / "fixtures" / "pyproject.toml").write_text("[project]\n")
        out = Path(td, "out")
        out.mkdir()
        for name in [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "COMMANDS.md",
            "SCAN_REPORT.md",
            "VALIDATION_REPORT.md",
        ]:
            Path(out, name).write_text("ok\n")
        Path(out, "PROJECT_OVERVIEW.md").write_text("Look for `pyproject.toml`.")
        result = validate_output_dir(out, repo_path=repo)
        codes = [c.code for c in result.checks]
        assert "referenced_source_missing" not in codes, (
            f"product fixtures pyproject.toml SHOULD suppress warning, got: {[c.message for c in result.checks if c.code == 'referenced_source_missing']}"
        )
