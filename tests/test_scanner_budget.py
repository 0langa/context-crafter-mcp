"""Tests for scanner budget allocation and directory prioritization."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.scanner import Scanner, ScannerOptions


def test_per_directory_cap_limits_single_directory() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Create one directory with 150 files
        big = root / "big"
        big.mkdir()
        for i in range(150):
            (big / f"f{i}.txt").write_text("x")
        # Create another directory with 10 files
        small = root / "small"
        small.mkdir()
        for i in range(10):
            (small / f"s{i}.txt").write_text("x")

        scanner = Scanner()
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=500, max_files_per_dir=50))

        # big dir should be capped at 50
        big_files = [f for f in snapshot.files if f.rel_path.startswith("big/")]
        assert len(big_files) == 50, f"expected 50, got {len(big_files)}"

        # small dir should get all 10
        small_files = [f for f in snapshot.files if f.rel_path.startswith("small/")]
        assert len(small_files) == 10, f"expected 10, got {len(small_files)}"


def test_directory_prioritization_walks_product_dirs_first() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # vendor dir alphabetically first, 100 files
        vendor = root / "aa_vendor"
        vendor.mkdir()
        for i in range(100):
            (vendor / f"v{i}.txt").write_text("x")
        # services dir alphabetically later, 10 files
        services = root / "services"
        services.mkdir()
        for i in range(10):
            (services / f"s{i}.txt").write_text("x")

        scanner = Scanner()
        # Tight global budget: only 50 files total
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=50, max_files_per_dir=30))
        rels = [f.rel_path for f in snapshot.files]

        # services should be walked before aa_vendor due to priority sorting
        services_files = [f for f in rels if f.startswith("services/")]
        vendor_files = [f for f in rels if f.startswith("aa_vendor/")]

        assert len(services_files) == 10, f"services should get all files, got {len(services_files)}"
        # vendor gets remaining budget after services
        assert len(vendor_files) == 30, f"vendor should be capped at 30, got {len(vendor_files)}"


def test_skipped_entries_include_max_files_per_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "dir"
        d.mkdir()
        for i in range(5):
            (d / f"f{i}.txt").write_text("x")

        scanner = Scanner()
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=100, max_files_per_dir=2))

        per_dir_skips = [s for s in snapshot.skipped if s.reason == "max_files_per_dir"]
        assert len(per_dir_skips) == 3, f"expected 3 skips, got {len(per_dir_skips)}"


def test_important_files_retained_deterministically_under_per_dir_cap() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "src"
        d.mkdir()
        # Create many generic files
        for i in range(50):
            (d / f"noise{i}.txt").write_text("x")
        # Add important manifests and entrypoints
        (d / "pyproject.toml").write_text("[project]\n")
        (d / "__init__.py").write_text("")
        (d / "main.py").write_text("pass\n")
        (d / "config.yaml").write_text("key: value\n")
        (d / "package.json").write_text("{}\n")

        scanner = Scanner()
        results: list[list[str]] = []
        for _ in range(5):
            snapshot = scanner.scan(root, ScannerOptions(max_depth=3, max_files=100, max_files_per_dir=10))
            results.append(sorted([f.rel_path for f in snapshot.files]))

        # All 5 scans should be identical
        for r in results[1:]:
            assert r == results[0], "scan results should be deterministic"

        # Important files should be retained ahead of noise
        kept = set(results[0])
        assert "src/pyproject.toml" in kept
        assert "src/package.json" in kept
        assert "src/__init__.py" in kept
        assert "src/main.py" in kept
        assert "src/config.yaml" in kept


def test_priority_reserve_protects_product_dirs() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Low-priority dir with many files (use zz_noise instead of vendor because vendor is now ignored)
        noise = root / "zz_noise"
        noise.mkdir()
        for i in range(60):
            (noise / f"v{i}.txt").write_text("x")
        # High-priority dir with many files
        src = root / "src"
        src.mkdir()
        for i in range(60):
            (src / f"s{i}.txt").write_text("x")

        scanner = Scanner()
        # Global budget = 80. Without reserve, noise (walked after src due to priority,
        # but alphabetically before src in raw os.walk) could consume all budget.
        # With reserve, at least 20% (16 files) are preserved for src.
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=80, max_files_per_dir=0))

        src_files = [f for f in snapshot.files if f.rel_path.startswith("src/")]

        # src should get at least the reserve amount
        assert len(src_files) >= 16, f"src should get at least reserve budget, got {len(src_files)}"
        # Total should not exceed global cap
        assert len(snapshot.files) <= 80, f"total files should not exceed cap, got {len(snapshot.files)}"
        # budget_exhausted should be True since we have 120 files and cap is 80
        assert snapshot.stats.budget_exhausted, "budget_exhausted should be True"


def test_tiered_entrypoint_priority() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "src"
        d.mkdir()
        # Tier 2 entrypoint
        (d / "worker.py").write_text("pass\n")
        # Tier 1 entrypoint
        (d / "main.py").write_text("pass\n")
        # Noise
        (d / "noise.txt").write_text("x")

        scanner = Scanner()
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=100, max_files_per_dir=2))

        rels = [f.rel_path for f in snapshot.files]
        # With cap=2, tier 1 (main.py) should be kept, tier 2 (worker.py) should also
        # be kept since it's priority 2 and config is priority 3
        assert "src/main.py" in rels, "tier 1 entrypoint should be retained"
        assert "src/worker.py" in rels, "tier 2 entrypoint should be retained"
        assert "src/noise.txt" not in rels, "noise should be skipped under cap"


def test_vendor_dirs_are_skipped_entirely() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vendor = root / "vendor"
        vendor.mkdir()
        for i in range(50):
            (vendor / f"v{i}.txt").write_text("x")
        src = root / "src"
        src.mkdir()
        for i in range(10):
            (src / f"s{i}.txt").write_text("x")

        scanner = Scanner()
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=100))

        vendor_files = [f for f in snapshot.files if f.rel_path.startswith("vendor/")]
        assert len(vendor_files) == 0, f"vendor dir should be skipped entirely, got {len(vendor_files)}"
        src_files = [f for f in snapshot.files if f.rel_path.startswith("src/")]
        assert len(src_files) == 10, f"src should get all files, got {len(src_files)}"


def test_category_counts_tracked() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        src = root / "src"
        src.mkdir()
        (src / "main.py").write_text("pass\n")
        tests = root / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("pass\n")

        scanner = Scanner()
        snapshot = scanner.scan(root, ScannerOptions(max_depth=2, max_files=100))

        assert "product" in snapshot.stats.category_counts, "product category should be counted"
        assert "test" in snapshot.stats.category_counts, "test category should be counted"
        assert snapshot.stats.category_counts["product"] >= 1
        assert snapshot.stats.category_counts["test"] >= 1
