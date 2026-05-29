"""Scanner boundary: Scanner.scan(root, options) -> RepoSnapshot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pathspec


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


_TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".cs",
    ".fs",
    ".vb",
    ".rs",
    ".go",
    ".java",
    ".md",
    ".txt",
    ".rst",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".xml",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".rb",
    ".php",
    ".pl",
    ".lua",
    ".r",
    ".m",
    ".mm",
    ".dart",
    ".elm",
    ".erl",
    ".ex",
    ".exs",
    ".hs",
    ".lhs",
    ".ml",
    ".mli",
    ".nim",
    ".nims",
    ".pas",
    ".pp",
    ".lpr",
    ".dpr",
    ".cr",
    ".gd",
    ".gdscript",
    ".lua",
    ".moon",
    ".pwn",
    ".inc",
    ".sma",
    ".pawn",
    ".glsl",
    ".vert",
    ".frag",
    ".geom",
    ".comp",
    ".tesc",
    ".tese",
    ".wgsl",
    ".hlsl",
    ".cg",
    ".shader",
    ". Compute",
}

_BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".ico",
    ".icns",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".a",
    ".lib",
    ".o",
    ".obj",
    ".class",
    ".jar",
    ".war",
    ".ear",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".mkv",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".webm",
    ".wasm",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".deb",
    ".rpm",
    ".msi",
    ".dmg",
    ".pkg",
    ".iso",
    ".img",
    ".vmdk",
    ".qcow2",
    ".vhd",
    ".vhdx",
    ".ova",
    ".ovf",
}

_LANGUAGE_HINTS: dict[str, str] = {
    ".py": "python",
    ".js": "node",
    ".jsx": "node",
    ".ts": "node",
    ".tsx": "node",
    ".cs": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
    ".fsproj": "dotnet",
    ".vbproj": "dotnet",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".md": "docs",
    ".txt": "docs",
    ".rst": "docs",
    ".json": "config",
    ".toml": "config",
    ".yaml": "config",
    ".yml": "config",
    ".ini": "config",
    ".cfg": "config",
    ".conf": "config",
    ".config": "config",
}

_FILENAME_HINTS: dict[str, str] = {
    "package.json": "node",
    "tsconfig.json": "node",
    "jsconfig.json": "node",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "pyproject.toml": "python",
    "setup.py": "python",
    "requirements.txt": "python",
}


# Common binary file magic bytes
_BINARY_MAGIC = {
    b"\x89PNG",
    b"\xff\xd8\xff",
    b"\x7fELF",
    b"MZ",
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"Rar!",
    b"7z\xbc\xaf",
    b"\x1f\x8b",
    b"BZh",
    b"\xfd7z",
    b"%PDF",
    b"\x00\x00\x01\x00",
    b"\x00\x00\x02\x00",
    b"\xca\xfe\xba\xbe",
    b"\xfe\xed\xfa",
    b"\xcf\xfa\xed\xfe",
    b"\x28\xb5\x2f\xfd",
}


def _has_binary_magic(chunk: bytes) -> bool:
    """Check if chunk starts with known binary file magic bytes."""
    for magic in _BINARY_MAGIC:
        if chunk.startswith(magic):
            return True
    return False


def _guess_is_text(path: Path) -> bool:
    """Guess whether a file is text using extension heuristics, magic bytes, and null-byte check."""
    ext = path.suffix.lower()
    if ext in _TEXT_EXTENSIONS:
        return True
    if ext in _BINARY_EXTENSIONS:
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
        if not chunk:
            return True
        if _has_binary_magic(chunk):
            return False
        return b"\x00" not in chunk
    except (OSError, ValueError):
        return False


def _language_hint(path: Path) -> str | None:
    """Guess language hint from filename or extension."""
    name = path.name
    if name in _FILENAME_HINTS:
        return _FILENAME_HINTS[name]
    ext = path.suffix.lower()
    return _LANGUAGE_HINTS.get(ext)


@dataclass
class SnapshotFile:
    """A file entry in the snapshot."""

    rel_path: str
    size: int
    extension: str = ""
    language_hint: str | None = None
    is_text: bool = True


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

        active_gitignores: list[tuple[str, pathspec.PathSpec, int]] = []

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

            # Prune gitignores from deeper directories and load current dir's gitignore
            if opts.respect_gitignore:
                active_gitignores = [(r, s, d) for r, s, d in active_gitignores if d <= depth]
                gitignore_path = walk_root_path / ".gitignore"
                if gitignore_path.exists():
                    try:
                        lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
                        spec = pathspec.PathSpec.from_lines("gitignore", lines)
                        active_gitignores.append((rel_root, spec, depth))
                    except (OSError, ValueError):
                        pass

            def _match_gitignore(rel_path: str, is_dir: bool = False) -> bool:
                if not active_gitignores:
                    return False
                best_result = None
                best_depth = -1
                for gitignore_dir, spec, spec_depth in active_gitignores:
                    if gitignore_dir:
                        prefix = gitignore_dir + "/"
                        if rel_path.startswith(prefix):
                            sub = rel_path[len(prefix) :]
                        elif rel_path == gitignore_dir:
                            sub = "."
                        else:
                            continue
                    else:
                        sub = rel_path
                    check = spec.check_file(sub + "/" if is_dir else sub)
                    if check.include is not None and spec_depth > best_depth:
                        best_depth = spec_depth
                        best_result = check
                if best_result is None:
                    return False
                return best_result.include is True

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
                if opts.respect_gitignore and _match_gitignore((rel_root + "/" + d) if rel_root else d, is_dir=True):
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
                if opts.respect_gitignore and _match_gitignore(rel, is_dir=False):
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

                ext = Path(name).suffix.lower()
                if ext in _TEXT_EXTENSIONS:
                    is_text = True
                elif ext in _BINARY_EXTENSIONS:
                    is_text = False
                else:
                    is_text = _guess_is_text(fpath)

                files.append(
                    SnapshotFile(
                        rel_path=rel,
                        size=size,
                        extension=ext,
                        language_hint=_language_hint(fpath),
                        is_text=is_text,
                    )
                )
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
