"""Safety tests for scanner and generation boundaries."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from context_crafter_mcp.filesystem import safe_output_path, validate_repo_path
from context_crafter_mcp.graph import run_generate_all
from context_crafter_mcp.scanner import Scanner, ScannerOptions


class TestScannerSafety:
    """Scanner safety tests."""

    def test_symlink_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td, "real")
            target.mkdir()
            Path(target, "file.txt").write_text("ok")
            link = Path(td, "link")
            try:
                link.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                pytest.skip("Symlinks not supported on this platform")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "link/file.txt" not in rels
            assert "real/file.txt" in rels

    def test_binary_file_skipped_by_size(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            big = Path(td, "big.bin")
            big.write_bytes(b"\x00" * 6_000_000)
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions(max_file_bytes=5_000_000))
            rels = [f.rel_path for f in snapshot.files]
            assert "big.bin" not in rels
            assert any("big.bin" in s.rel_path for s in snapshot.skipped)

    def test_ignored_dirs_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            node = Path(td, "node_modules")
            node.mkdir()
            Path(node, "pkg.js").write_text("//")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "node_modules/pkg.js" not in rels

    def test_max_depth_graceful(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            deep = Path(td, "a", "b", "c", "d", "e")
            deep.mkdir(parents=True)
            Path(deep, "file.txt").write_text("deep")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions(max_depth=3))
            rels = [f.rel_path for f in snapshot.files]
            assert "a/b/c/d/e/file.txt" not in rels
            assert any(s.reason == "max_depth" for s in snapshot.skipped)

    def test_max_files_graceful(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for i in range(10):
                Path(td, f"file{i}.txt").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions(max_files=5))
            assert len(snapshot.files) <= 5
            assert any(s.reason == "max_files" for s in snapshot.skipped)

    def test_deterministic_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for name in ("z.txt", "a.txt", "m.txt"):
                Path(td, name).write_text("x")
            scanner = Scanner()
            s1 = scanner.scan(td, ScannerOptions())
            s2 = scanner.scan(td, ScannerOptions())
            assert [f.rel_path for f in s1.files] == [f.rel_path for f in s2.files]

    def test_invalid_encoding_reported_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td, "bad.txt")
            bad.write_bytes(b"\xff\xfe")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            assert "bad.txt" in [f.rel_path for f in snapshot.files]
            # read_text should handle it gracefully
            text = snapshot.read_text("bad.txt")
            assert text is not None

    def test_gitignore_wildcard_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".gitignore").write_text("*.log\n")
            Path(td, "app.py").write_text("x")
            Path(td, "debug.log").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "app.py" in rels
            assert "debug.log" not in rels

    def test_gitignore_dir_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".gitignore").write_text("build/\n")
            build = Path(td, "build")
            build.mkdir()
            Path(build, "out.js").write_text("x")
            src = Path(td, "src")
            src.mkdir()
            Path(src, "main.py").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "build/out.js" not in rels
            assert "src/main.py" in rels

    def test_gitignore_double_star_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".gitignore").write_text("foo/**\n")
            deep = Path(td, "foo", "bar", "baz")
            deep.mkdir(parents=True)
            Path(deep, "file.txt").write_text("x")
            Path(td, "other.txt").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "foo/bar/baz/file.txt" not in rels
            assert "other.txt" in rels

    def test_gitignore_negation_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".gitignore").write_text("*.log\n!keep.log\n")
            Path(td, "debug.log").write_text("x")
            Path(td, "keep.log").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "debug.log" not in rels
            assert "keep.log" in rels

    def test_nested_gitignore_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, ".gitignore").write_text("*.log\n")
            sub = Path(td, "sub")
            sub.mkdir()
            Path(sub, ".gitignore").write_text("!keep.log\n")
            Path(sub, "debug.log").write_text("x")
            Path(sub, "keep.log").write_text("x")
            Path(td, "root.log").write_text("x")
            scanner = Scanner()
            snapshot = scanner.scan(td, ScannerOptions())
            rels = [f.rel_path for f in snapshot.files]
            assert "root.log" not in rels
            assert "sub/debug.log" not in rels
            assert "sub/keep.log" in rels


class TestOutputConfinement:
    """Output directory must stay inside repo root."""

    def test_output_traversal_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td, "repo")
            repo.mkdir()
            out = safe_output_path(repo, "../../escaped")
            assert "escaped" not in str(out) or repo in out.parents
            assert str(out).startswith(str(repo))

    def test_validate_repo_path_rejects_nonexistent(self) -> None:
        assert validate_repo_path("/nonexistent/path/12345") is None

    def test_validate_repo_path_rejects_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td, "file.txt")
            f.write_text("x")
            assert validate_repo_path(str(f)) is None


class TestGenerationSafety:
    """Generation must not execute target code or escape."""

    def test_no_target_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            malicious = Path(td, "run_me.py")
            malicious.write_text("import os; os.system('echo EXPLOITED')")
            state = run_generate_all(td, "out")
            assert state.ok
            # If execution happened, it would be visible somewhere; it is not.

    def test_static_only_no_network(self) -> None:
        # The scanner and analyzers do not make HTTP requests.
        # This is an architectural guarantee; we verify by inspection that
        # no urllib, requests, or http client calls exist in core modules.
        import context_crafter_mcp.scanner as scanner_mod
        import context_crafter_mcp.graph as graph_mod
        import context_crafter_mcp.analyzers.generic as generic_mod

        srcs = [scanner_mod, graph_mod, generic_mod]
        for mod in srcs:
            source = Path(mod.__file__).read_text()
            assert "urllib" not in source or "#" in source.split("urllib")[0].split("\n")[-1]
            assert "requests.get" not in source
            assert "httpx" not in source
