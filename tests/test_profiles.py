"""Tests that compact/standard/deep profiles produce measurably different output."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all


def test_profiles_differ_on_substantial_repo() -> None:
    with tempfile.TemporaryDirectory() as td:
        # Create enough files that slicing limits matter
        src = Path(td, "src")
        src.mkdir()
        for i in range(30):
            Path(src, f"mod{i}.py").write_text(f"def fn{i}(): pass\n")
        Path(td, "pyproject.toml").write_text("[project]\nname = 'big'\n")

        compact = run_generate_all(
            td,
            "out-compact",
            scan_config=type(
                "C", (), {"max_depth": 4, "max_files_per_dir": 80, "profile": "compact", "max_file_bytes": 5_000_000}
            )(),
        )
        standard = run_generate_all(
            td,
            "out-standard",
            scan_config=type(
                "C", (), {"max_depth": 4, "max_files_per_dir": 80, "profile": "standard", "max_file_bytes": 5_000_000}
            )(),
        )
        deep = run_generate_all(
            td,
            "out-deep",
            scan_config=type(
                "C", (), {"max_depth": 4, "max_files_per_dir": 80, "profile": "deep", "max_file_bytes": 5_000_000}
            )(),
        )

        assert compact.ok and standard.ok and deep.ok

        # REPO_MAP line counts should differ because tree_max_lines differs
        compact_map = Path(td, "out-compact", "REPO_MAP.md").read_text()
        standard_map = Path(td, "out-standard", "REPO_MAP.md").read_text()
        deep_map = Path(td, "out-deep", "REPO_MAP.md").read_text()

        assert len(compact_map.splitlines()) <= len(standard_map.splitlines())
        assert len(standard_map.splitlines()) <= len(deep_map.splitlines())


def test_compact_omits_sections_on_tiny_repo() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "src" / "app.py").parent.mkdir(parents=True)
        (root / "src" / "app.py").write_text("print(1)\n")
        (root / "pyproject.toml").write_text("[project]\nname = 'tiny'\n")

        compact = run_generate_all(
            td,
            "out-compact",
            scan_config=type(
                "C", (), {"max_depth": 4, "max_files_per_dir": 80, "profile": "compact", "max_file_bytes": 5_000_000}
            )(),
        )
        standard = run_generate_all(
            td,
            "out-standard",
            scan_config=type(
                "C", (), {"max_depth": 4, "max_files_per_dir": 80, "profile": "standard", "max_file_bytes": 5_000_000}
            )(),
        )

        assert compact.ok and standard.ok

        compact_arch = Path(td, "out-compact", "ARCHITECTURE_SUMMARY.md").read_text()
        standard_arch = Path(td, "out-standard", "ARCHITECTURE_SUMMARY.md").read_text()

        # Compact on tiny repo should omit empty Architecture Patterns, Key Abstractions, Module Relationships
        assert "## Architecture Patterns" not in compact_arch
        assert "## Key Abstractions" not in compact_arch
        assert "## Module Relationships" not in compact_arch
        # Standard should still have them
        assert "## Architecture Patterns" in standard_arch
        assert "## Key Abstractions" in standard_arch
        assert "## Module Relationships" in standard_arch

        compact_overview = Path(td, "out-compact", "PROJECT_OVERVIEW.md").read_text()
        standard_overview = Path(td, "out-standard", "PROJECT_OVERVIEW.md").read_text()
        # Compact on tiny repo should omit Generic Notes
        assert "## Generic Notes" not in compact_overview
        assert "## Generic Notes" in standard_overview
