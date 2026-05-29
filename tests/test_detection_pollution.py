"""Tests proving fixture stacks do not pollute primary project detection."""

from __future__ import annotations

from pathlib import Path

from context_crafter_mcp.graph import run_detect


def test_this_repo_primary_stack_is_python() -> None:
    """This repo contains fixtures for dotnet/go/java/node/rust, but detection must report only Python."""
    detect = run_detect(".")
    assert detect.exists
    assert "python" in detect.project_types
    assert "generic" in detect.project_types
    # Fixture stacks must NOT appear
    for fake in ("dotnet", "go", "java", "node", "rust"):
        assert fake not in detect.project_types, f"Fixture stack {fake} leaked into primary detection"


def test_fixture_repo_still_detects_own_stack() -> None:
    """When pointed directly at a fixture, detection must still work."""
    fixtures = Path(__file__).parent / "fixtures"
    for name, expected in (
        ("python_basic", "python"),
        ("node_ts_basic", "node"),
        ("dotnet_basic", "dotnet"),
        ("rust_basic", "rust"),
        ("go_basic", "go"),
        ("java_basic", "java"),
    ):
        detect = run_detect(str(fixtures / name))
        assert detect.exists, f"{name} should exist"
        assert expected in detect.project_types, f"{name} should detect {expected}"
