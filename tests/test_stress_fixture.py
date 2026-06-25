"""Stress regression tests approximating ugly real-repo behavior under bounds."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all
from context_crafter_mcp.models import ScanConfig


def _build_stress_repo(root: Path, files: int = 500, depth: int = 5) -> None:
    """Create a large, deep, mixed-stack repo with vendor-like noise."""
    # Multi-stack markers
    (root / "pyproject.toml").write_text("[project]\nname = 'stress'\n")
    (root / "package.json").write_text('{"name":"stress-web"}\n')
    (root / "go.mod").write_text("module stress\n")
    (root / "Cargo.toml").write_text("[package]\nname = 'stress'\n")

    # Generate many tiny files across deep tree
    for i in range(files):
        # Vary depth
        parts = [f"depth{d}" for d in range(1, (i % depth) + 1)]
        if i % 7 == 0:
            parts.insert(0, "src")
        if i % 11 == 0:
            parts.insert(0, "tests")
        if i % 13 == 0:
            parts.insert(0, "node_modules")  # scanner should skip
        if i % 17 == 0:
            parts.insert(0, "vendor")  # scanner should skip
        if i % 19 == 0:
            parts.insert(0, "output")  # scanned, should classify GENERATED
        if i % 23 == 0:
            parts.insert(0, "generated")  # scanner should skip
        subdir = root.joinpath(*parts)
        subdir.mkdir(parents=True, exist_ok=True)

        # Vary extensions
        if i % 5 == 0:
            (subdir / f"file{i}.py").write_text(f"def fn{i}(): pass\n")
        elif i % 5 == 1:
            (subdir / f"file{i}.ts").write_text(f"export const x{i} = 1;\n")
        elif i % 5 == 2:
            (subdir / f"file{i}.go").write_text(f"package main\nfunc Fn{i}() {{}}\n")
        elif i % 5 == 3:
            (subdir / f"file{i}.rs").write_text(f"fn fn{i}() {{}}\n")
        else:
            (subdir / f"file{i}.md").write_text(f"# doc {i}\n")

    # Add a large source file near max_file_bytes boundary
    large = root / "src" / "large.py"
    large.parent.mkdir(parents=True, exist_ok=True)
    large.write_text("x = 1\n" * 50_000)  # ~350 KB, well under 5 MB


def test_stress_repo_generates_without_crash() -> None:
    """Large mixed repo must complete generation and produce all expected outputs."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_stress_repo(root, files=500, depth=5)
        state = run_generate_all(td, "out", ScanConfig(profile="standard", max_depth=6, max_files_per_dir=200))
        assert state.ok, f"Generation failed: {state.errors}"
        assert state.analysis is not None
        assert state.analysis.scan_summary.files_scanned > 0
        # All required Markdown outputs plus machine-readable companions.
        assert len(state.written) >= 8
        names = [Path(w).name for w in state.written]
        assert "CONTEXT_MANIFEST.json" in names
        assert "RUN_STATE.json" in names


def test_stress_repo_scan_count_bounded_and_stable() -> None:
    """Scanner count must reflect actual walked files, not analyzer inflation."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _build_stress_repo(root, files=300, depth=4)
        state = run_generate_all(td, "out")
        assert state.ok
        assert state.analysis is not None

        a = state.analysis
        # Scanner truth equals result.files_scanned (no drift)
        assert a.files_scanned == a.scan_summary.files_scanned
        # Parsed files are tracked separately
        assert a.analyzer_files_parsed > 0
        assert a.analyzer_files_parsed <= a.files_scanned
        # Budget not exhausted at this scale with default limits
        assert not a.scan_summary.budget_exhausted


def test_stress_repo_classifies_generated_paths() -> None:
    """Generated-like directories that survive scanning must be classified GENERATED."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "output" / "build.js").parent.mkdir(parents=True, exist_ok=True)
        (root / "output" / "build.js").write_text("console.log(1);\n")
        (root / "src" / "main.py").parent.mkdir(parents=True, exist_ok=True)
        (root / "src" / "main.py").write_text("print(1)\n")
        state = run_generate_all(td, "out")
        assert state.ok
        assert state.analysis is not None
        # output/ is not in DEFAULT_IGNORED_DIRS, so it gets scanned
        cats = state.analysis.scan_summary.category_counts
        assert cats.get("generated", 0) >= 1, f"Expected generated count >= 1, got {cats}"
