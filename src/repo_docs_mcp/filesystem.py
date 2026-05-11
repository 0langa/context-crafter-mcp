"""Centralized safe filesystem scanning."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

from repo_docs_mcp.models import FileInfo

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
    """Yield FileInfo entries under repo_path, skipping ignored dirs and symlinks."""
    seen: set[Path] = set()
    for root, dirs, files in os.walk(repo_path, topdown=True):
        root_path = Path(root)
        try:
            root_path.resolve()
        except (OSError, ValueError):
            dirs[:] = []
            continue

        # Skip symlinks to avoid loops
        if root_path.resolve() in seen:
            dirs[:] = []
            continue
        seen.add(root_path.resolve())

        # Skip ignored dirs
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not (root_path / d).is_symlink()]

        depth = len(root_path.relative_to(repo_path).parts)
        if depth > max_depth:
            dirs[:] = []
            continue

        if include_dirs:
            rel = root_path.relative_to(repo_path).as_posix()
            if rel == ".":
                rel = ""
            yield FileInfo(path=root_path, rel_path=rel, is_dir=True)

        for i, name in enumerate(files):
            if i >= max_files_per_dir:
                break
            file_path = root_path / name
            if file_path.is_symlink():
                continue
            try:
                rel = file_path.relative_to(repo_path).as_posix()
            except (OSError, ValueError):
                continue
            size = 0
            try:
                size = file_path.stat().st_size
            except (OSError, ValueError):
                pass
            yield FileInfo(path=file_path, rel_path=rel, is_dir=False, size=size)


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
