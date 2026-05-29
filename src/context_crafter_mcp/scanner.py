"""Scanner boundary: Scanner.scan(root, options) -> RepoSnapshot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "bin",
    "obj",
    ".next",
    ".turbo",
    ".cache",
}


@dataclass
class ScannerOptions:
    """Options controlling filesystem scanning behavior."""

    follow_symlinks: bool = False
    respect_gitignore: bool = True
    include_hidden: bool = False
    include_tests: bool = True
    max_files: int = 5_000
    max_depth: int = 6
    max_file_bytes: int = 5_000_000

    def __post_init__(self) -> None:
        if self.max_depth < 1 or self.max_depth > 20:
            raise ValueError("max_depth must be between 1 and 20")
        if self.max_files < 1 or self.max_files > 100_000:
            raise ValueError("max_files must be between 1 and 100000")
        if self.max_file_bytes < 1:
            raise ValueError("max_file_bytes must be positive")


@dataclass
class SnapshotFile:
    """A file entry in the snapshot."""

    rel_path: str
    size: int


@dataclass
class SnapshotDirectory:
    """A directory entry in the snapshot."""

    rel_path: str


@dataclass
class SkippedEntry:
    """An entry that was skipped and why."""

    rel_path: str
    reason: str


@dataclass
class ScanError:
    """A non-fatal scan error."""

    rel_path: str
    message: str


@dataclass
class ScanStats:
    """Summary statistics for a scan."""

    files_scanned: int = 0
    dirs_scanned: int = 0
    files_skipped: int = 0
    dirs_skipped: int = 0
    errors: list[ScanError] = field(default_factory=list)


@dataclass
class GitMetadata:
    """Optional git metadata if available."""

    commit: str | None = None
    branch: str | None = None
    dirty: bool = False


@dataclass
class RepoSnapshot:
    """Immutable-ish snapshot of a repository filesystem scan."""

    root: Path
    files: list[SnapshotFile] = field(default_factory=list)
    directories: list[SnapshotDirectory] = field(default_factory=list)
    skipped: list[SkippedEntry] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    git: GitMetadata = field(default_factory=GitMetadata)

    def file_rel_paths(self) -> list[str]:
        return [f.rel_path for f in self.files]

    def dir_rel_paths(self) -> list[str]:
        return [d.rel_path for d in self.directories]

    def read_text(self, rel_path: str) -> str | None:
        """Read UTF-8 text with fallback, respecting max_file_bytes."""
        for f in self.files:
            if f.rel_path == rel_path:
                path = self.root / rel_path
                try:
                    return path.read_text(encoding="utf-8", errors="replace")
                except (OSError, ValueError):
                    return None
        return None


class Scanner:
    """Safe, bounded, deterministic filesystem scanner."""

    def scan(self, root: str | Path, options: ScannerOptions | None = None) -> RepoSnapshot:
        """Scan a directory and return a RepoSnapshot."""
        opts = options or ScannerOptions()
        root_path = Path(root).resolve()
        if not root_path.exists() or not root_path.is_dir():
            return RepoSnapshot(root=root_path)

        files: list[SnapshotFile] = []
        directories: list[SnapshotDirectory] = []
        skipped: list[SkippedEntry] = []
        errors: list[ScanError] = []
        seen: set[Path] = set()
        file_count = 0
        dir_count = 0

        gitignore_patterns: set[str] = set()
        if opts.respect_gitignore:
            gitignore_path = root_path / ".gitignore"
            if gitignore_path.exists():
                try:
                    for line in gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines():
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            gitignore_patterns.add(stripped)
                except (OSError, ValueError):
                    pass

        for walk_root, dirs, walk_files in os.walk(root_path, topdown=True):
            walk_root_path = Path(walk_root)
            try:
                resolved = walk_root_path.resolve()
            except (OSError, ValueError):
                dirs[:] = []
                continue

            if not opts.follow_symlinks and resolved in seen:
                dirs[:] = []
                continue
            seen.add(resolved)

            rel_root = walk_root_path.relative_to(root_path).as_posix()
            if rel_root == ".":
                rel_root = ""

            depth = len(Path(rel_root).parts) if rel_root else 0
            if depth > opts.max_depth:
                dirs[:] = []
                skipped.append(SkippedEntry(rel_path=rel_root or ".", reason="max_depth"))
                continue

            # Filter dirs
            filtered_dirs: list[str] = []
            for d in dirs:
                dpath = walk_root_path / d
                if not opts.follow_symlinks and dpath.is_symlink():
                    skipped.append(SkippedEntry(rel_path=(rel_root + "/" + d) if rel_root else d, reason="symlink"))
                    continue
                if d in DEFAULT_IGNORED_DIRS:
                    skipped.append(SkippedEntry(rel_path=(rel_root + "/" + d) if rel_root else d, reason="ignored_dir"))
                    continue
                if not opts.include_hidden and d.startswith("."):
                    skipped.append(SkippedEntry(rel_path=(rel_root + "/" + d) if rel_root else d, reason="hidden"))
                    continue
                if opts.respect_gitignore and d in gitignore_patterns:
                    skipped.append(SkippedEntry(rel_path=(rel_root + "/" + d) if rel_root else d, reason="gitignore"))
                    continue
                filtered_dirs.append(d)
            dirs[:] = filtered_dirs

            directories.append(SnapshotDirectory(rel_path=rel_root or "."))
            dir_count += 1

            for name in walk_files:
                if file_count >= opts.max_files:
                    skipped.append(
                        SkippedEntry(rel_path=(rel_root + "/" + name) if rel_root else name, reason="max_files")
                    )
                    continue

                fpath = walk_root_path / name
                rel = (rel_root + "/" + name) if rel_root else name

                if not opts.follow_symlinks and fpath.is_symlink():
                    skipped.append(SkippedEntry(rel_path=rel, reason="symlink"))
                    continue
                if not opts.include_hidden and name.startswith("."):
                    skipped.append(SkippedEntry(rel_path=rel, reason="hidden"))
                    continue
                if opts.respect_gitignore and name in gitignore_patterns:
                    skipped.append(SkippedEntry(rel_path=rel, reason="gitignore"))
                    continue

                size = 0
                try:
                    size = fpath.stat().st_size
                except (OSError, ValueError):
                    errors.append(ScanError(rel_path=rel, message="stat_failed"))
                if size > opts.max_file_bytes:
                    skipped.append(SkippedEntry(rel_path=rel, reason="max_file_bytes"))
                    continue

                files.append(SnapshotFile(rel_path=rel, size=size))
                file_count += 1

        git = GitMetadata()
        git_dir = root_path / ".git"
        if git_dir.is_dir():
            try:
                import subprocess

                commit = subprocess.run(
                    ["git", "-C", str(root_path), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if commit.returncode == 0:
                    git.commit = commit.stdout.strip()
                branch = subprocess.run(
                    ["git", "-C", str(root_path), "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if branch.returncode == 0:
                    git.branch = branch.stdout.strip()
                dirty = subprocess.run(
                    ["git", "-C", str(root_path), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if dirty.returncode == 0 and dirty.stdout.strip():
                    git.dirty = True
            except Exception:
                pass

        return RepoSnapshot(
            root=root_path,
            files=sorted(files, key=lambda f: f.rel_path),
            directories=sorted(directories, key=lambda d: d.rel_path),
            skipped=skipped,
            stats=ScanStats(
                files_scanned=file_count,
                dirs_scanned=dir_count,
                files_skipped=len([s for s in skipped if "max_file_bytes" in s.reason or "max_files" in s.reason]),
                dirs_skipped=len([s for s in skipped if "max_depth" in s.reason or "ignored_dir" in s.reason]),
                errors=errors,
            ),
            git=git,
        )
