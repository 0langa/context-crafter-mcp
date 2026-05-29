"""Centralized safe filesystem scanning."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from context_crafter_mcp.models import FileInfo

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".tox",
    ".next",
    "coverage",
    ".coverage",
    "bin",
    "obj",
    "target",
}

INTERESTING_ROOT_FILES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "README.md",
    "README",
    "LICENSE",
    "Dockerfile",
    "docker-compose.yml",
    ".gitignore",
    "Makefile",
    "makefile",
    "justfile",
}

MAX_TREE_DEPTH = 4
MAX_FILES_PER_DIR = 80


def validate_repo_path(repo_path: str) -> Path | None:
    """Resolve and validate repo_path. Returns None if invalid."""
    if not repo_path:
        return None
    try:
        path = Path(repo_path).resolve()
        if not path.exists():
            return None
        if not path.is_dir():
            return None
        return path
    except (OSError, ValueError):
        return None


def safe_output_path(repo_path: Path, output_dir: str) -> Path:
    """Return a safe output directory inside repo_path."""
    output = (repo_path / output_dir).resolve()
    # Prevent escaping repo root
    try:
        output.relative_to(repo_path.resolve())
    except ValueError:
        output = repo_path.resolve() / "docs" / "generated"
    return output


def safe_scan(
    repo_path: Path,
    *,
    max_depth: int = MAX_TREE_DEPTH,
    max_files_per_dir: int = MAX_FILES_PER_DIR,
    include_dirs: bool = False,
) -> Iterator[FileInfo]:
    """Yield FileInfo entries under repo_path, skipping ignored dirs and symlinks.

    Thin compatibility wrapper around Scanner.scan().
    """
    from context_crafter_mcp.scanner import Scanner, ScannerOptions

    scanner = Scanner()
    snapshot = scanner.scan(
        repo_path,
        ScannerOptions(
            max_depth=max_depth,
            max_files=max(5_000, max_files_per_dir * 10),
        ),
    )

    if include_dirs:
        for sd in snapshot.directories:
            rel = sd.rel_path if sd.rel_path != "." else ""
            yield FileInfo(path=repo_path / rel, rel_path=rel, is_dir=True)

    for sf in snapshot.files:
        yield FileInfo(
            path=repo_path / sf.rel_path,
            rel_path=sf.rel_path,
            is_dir=False,
            size=sf.size,
        )


def safe_read_text(path: Path, max_bytes: int = 5_000_000) -> str | None:
    """Read text with UTF-8 fallback and size limits."""
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def list_root_files(repo_path: Path) -> list[str]:
    """List interesting root files."""
    try:
        return sorted([f.name for f in repo_path.iterdir() if f.is_file() and not f.is_symlink()])
    except (OSError, ValueError):
        return []


def list_directory_tree(
    repo_path: Path,
    max_depth: int = MAX_TREE_DEPTH,
    max_files_per_dir: int = MAX_FILES_PER_DIR,
) -> list[str]:
    """Return a simple ASCII tree representation."""
    lines: list[str] = []
    for fi in safe_scan(repo_path, max_depth=max_depth, max_files_per_dir=max_files_per_dir, include_dirs=True):
        if fi.is_dir:
            depth = len(Path(fi.rel_path).parts) if fi.rel_path else 0
            indent = "  " * depth
            name = fi.path.name or repo_path.name or "."
            lines.append(f"{indent}{name}/")
        else:
            depth = len(Path(fi.rel_path).parts)
            indent = "  " * (depth - 1)
            lines.append(f"{indent}{fi.path.name}")
    return lines
