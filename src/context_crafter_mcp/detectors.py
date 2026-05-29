"""Project type detection logic."""

from __future__ import annotations

from pathlib import Path

from context_crafter_mcp.filesystem import validate_repo_path
from context_crafter_mcp.models import DetectResult
from context_crafter_mcp.scanner import Scanner, ScannerOptions


# Paths that indicate test fixtures or examples, not primary project stacks
FIXTURE_PATH_INDICATORS = ("tests/fixtures/", "examples/", "docs/generated/")


def _is_fixture_path(rel_path: str) -> bool:
    """Return True if rel_path is inside a fixture/example/generated directory."""
    lower = rel_path.lower()
    return any(ind in lower for ind in FIXTURE_PATH_INDICATORS)


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

    scanner = Scanner()
    snapshot = scanner.scan(path, ScannerOptions(max_depth=3, max_files=2_000))

    project_types: list[str] = []
    markers: dict[str, list[str]] = {}

    # Check marker files and extensions
    for ptype, exts in EXTENSIONS.items():
        markers[ptype] = []
        marker_hits: list[str] = []
        ext_hits: list[str] = []

        for sf in snapshot.files:
            if _is_fixture_path(sf.rel_path):
                continue
            name = Path(sf.rel_path).name
            if ptype in MARKERS and name in MARKERS[ptype]:
                marker_hits.append(sf.rel_path)
            for ext in exts:
                if name.endswith(ext):
                    ext_hits.append(sf.rel_path)
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
        for sf in snapshot.files:
            if _is_fixture_path(sf.rel_path):
                continue
            name = Path(sf.rel_path).name
            if name in names:
                marker_hits2.append(sf.rel_path)
        if marker_hits2:
            project_types.append(ptype)
            markers[ptype] = sorted(set(marker_hits2))[:20]

    # Always include generic for existing repos
    project_types.append("generic")
    markers["generic"] = []

    # Build evidence map
    evidence: dict[str, str] = {}
    for ptype in project_types:
        if ptype == "generic":
            evidence[ptype] = "observed"
        elif markers.get(ptype) and any(Path(m).name in MARKERS.get(ptype, []) for m in markers[ptype]):
            evidence[ptype] = "observed"
        elif markers.get(ptype):
            evidence[ptype] = "inferred"
        else:
            evidence[ptype] = "unknown"

    return DetectResult(
        repo_path=str(path),
        exists=True,
        project_types=sorted(set(project_types)),
        markers=markers,
        evidence=evidence,
    )
