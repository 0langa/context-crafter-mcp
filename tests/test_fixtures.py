"""Golden tests against fixture repos."""

from __future__ import annotations

from pathlib import Path

import pytest

from context_crafter_mcp.graph import run_detect, run_generate_all

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "name,expected_types",
    [
        ("python_basic", ["python"]),
        ("node_ts_basic", ["node"]),
        ("dotnet_basic", ["dotnet"]),
        ("rust_basic", ["rust"]),
        ("go_basic", ["go"]),
        ("java_basic", ["java"]),
        ("generic_unknown", []),
        ("mixed_monorepo", ["node", "python"]),
    ],
)
def test_fixture_detection(name: str, expected_types: list[str]) -> None:
    path = FIXTURES_DIR / name
    detect = run_detect(str(path))
    assert detect.exists
    for t in expected_types:
        assert t in detect.project_types, f"Expected {t} in {detect.project_types}"
    assert "generic" in detect.project_types


@pytest.mark.parametrize(
    "name",
    [
        "python_basic",
        "node_ts_basic",
        "dotnet_basic",
        "rust_basic",
        "go_basic",
        "java_basic",
        "generic_unknown",
        "mixed_monorepo",
    ],
)
def test_fixture_generation(name: str) -> None:
    path = FIXTURES_DIR / name
    state = run_generate_all(str(path), "docs/generated")
    assert state.ok
    names = [Path(w).name for w in state.written]
    assert "AI_CONTEXT_INDEX.md" in names
    assert "PROJECT_OVERVIEW.md" in names
    assert "REPO_MAP.md" in names
    assert "DEPENDENCY_GRAPH.md" in names
    assert "ARCHITECTURE_SUMMARY.md" in names
    assert "AGENT_BRIEF.md" in names
    assert "VALIDATION_REPORT.md" in names
    assert "SCAN_REPORT.md" in names
