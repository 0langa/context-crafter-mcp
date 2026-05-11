"""Project type detection logic."""

from __future__ import annotations

from repo_docs_mcp.filesystem import safe_scan, validate_repo_path
from repo_docs_mcp.models import DetectResult


MARKERS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "node": ["package.json", "tsconfig.json", "jsconfig.json"],
    "dotnet": [],
    "rust": ["Cargo.toml"],
    "go": ["go.mod"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
}

EXTENSIONS: dict[str, list[str]] = {
    "python": [".py"],
    "node": [".js", ".jsx", ".ts", ".tsx"],
    "dotnet": [".sln", ".csproj", ".fsproj", ".vbproj"],
    "rust": [".rs"],
    "go": [".go"],
    "java": [".java"],
}


def detect_project(repo_path: str) -> DetectResult:
    """Detect project types for a repository path."""
    path = validate_repo_path(repo_path)
    if path is None:
        return DetectResult(
            repo_path=repo_path,
            exists=False,
            error=f"Path does not exist or is not a directory: {repo_path}",
        )

    project_types: list[str] = []
    markers: dict[str, list[str]] = {}

    # Check marker files and extensions
    for ptype, exts in EXTENSIONS.items():
        markers[ptype] = []
        marker_hits: list[str] = []
        ext_hits: list[str] = []

        for fi in safe_scan(path, max_depth=3, max_files_per_dir=200):
            if fi.is_dir:
                continue
            name = fi.path.name
            if ptype in MARKERS and name in MARKERS[ptype]:
                marker_hits.append(fi.rel_path)
            for ext in exts:
                if name.endswith(ext):
                    ext_hits.append(fi.rel_path)
                    break

        hits = marker_hits + ext_hits
        if hits:
            project_types.append(ptype)
            markers[ptype] = sorted(set(hits))[:20]

    # Also check explicit marker files for types without extensions
    for ptype, names in MARKERS.items():
        if ptype == "dotnet":
            continue
        if ptype in project_types:
            continue
        marker_hits2: list[str] = []
        for fi in safe_scan(path, max_depth=2, max_files_per_dir=200):
            if fi.is_dir:
                continue
            if fi.path.name in names:
                marker_hits2.append(fi.rel_path)
        if marker_hits2:
            project_types.append(ptype)
            markers[ptype] = sorted(set(marker_hits2))[:20]

    # Always include generic for existing repos
    project_types.append("generic")
    markers["generic"] = []

    return DetectResult(
        repo_path=str(path),
        exists=True,
        project_types=sorted(set(project_types)),
        markers=markers,
    )
