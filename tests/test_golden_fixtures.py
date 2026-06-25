"""Golden/snapshot tests for fixture repos."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from context_crafter_mcp.graph import run_generate_all

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUIRED_FILES = [
    "AI_CONTEXT_INDEX.md",
    "PROJECT_OVERVIEW.md",
    "REPO_MAP.md",
    "DEPENDENCY_GRAPH.md",
    "ARCHITECTURE_SUMMARY.md",
    "AGENT_BRIEF.md",
    "VALIDATION_REPORT.md",
    "SCAN_REPORT.md",
]

FIXTURE_KEYWORDS: dict[str, list[str]] = {
    "python_basic": ["pyproject.toml", "requirements.txt"],
    "node_ts_basic": ["package.json", "tsconfig.json"],
    "dotnet_basic": ["csproj", "sln"],
    "rust_basic": ["Cargo.toml"],
    "go_basic": ["go.mod"],
    "java_basic": ["pom.xml", "build.gradle"],
    "generic_unknown": ["generic"],
    "mixed_monorepo": ["node", "python"],
}


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
def test_fixture_golden_generation(name: str) -> None:
    fixture_path = FIXTURES_DIR / name
    state = run_generate_all(str(fixture_path), "docs/generated")
    assert state.ok, f"Generation failed for {name}: {getattr(state, 'errors', [])}"

    written_names = [Path(w).name for w in state.written]
    for required in REQUIRED_FILES:
        assert required in written_names, f"Missing {required} in {name}"

    assert "CONTEXT_MANIFEST.json" in written_names, f"Missing CONTEXT_MANIFEST.json in {name}"
    assert "RUN_STATE.json" in written_names, f"Missing RUN_STATE.json in {name}"

    run_state_path = Path(state.resolved_output_dir) / "RUN_STATE.json"
    run_state_data = json.loads(run_state_path.read_text(encoding="utf-8"))
    assert isinstance(run_state_data, dict)

    # Stack-specific keyword checks
    keywords = FIXTURE_KEYWORDS.get(name, [])
    combined_text = " ".join(written_names)
    for file_path in state.written:
        if Path(file_path).suffix in (".md", ".mmd", ".json"):
            combined_text += Path(file_path).read_text(encoding="utf-8")

    if name == "mixed_monorepo":
        assert all(kw.lower() in combined_text.lower() for kw in keywords), (
            f"Expected all of {keywords} in generated output for {name}"
        )
    else:
        found_any = False
        for kw in keywords:
            if kw.lower() in combined_text.lower():
                found_any = True
                break
        assert found_any, f"Expected one of {keywords} in generated output for {name}"
