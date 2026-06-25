"""Project type detection logic."""

from __future__ import annotations

from pathlib import Path

from context_crafter_mcp.filesystem import validate_repo_path
from context_crafter_mcp.models import Confidence, DetectResult, EvidenceKind, EvidenceSet
from context_crafter_mcp.ranking import is_primary_surface_path
from context_crafter_mcp.scanner import RepoSnapshot, Scanner, ScannerOptions


# Paths that indicate test fixtures or examples, not primary project stacks
FIXTURE_PATH_INDICATORS = ("tests/fixtures/", "examples/", "docs/generated/")


def _is_fixture_path(rel_path: str) -> bool:
    """Return True if rel_path is inside a fixture/example/generated directory."""
    lower = rel_path.lower()
    return any(ind in lower for ind in FIXTURE_PATH_INDICATORS)


def _is_trusted_detection_path(rel_path: str) -> bool:
    """Return True when rel_path belongs to primary repo surface for stack detection."""
    return not _is_fixture_path(rel_path) and is_primary_surface_path(rel_path)


MARKERS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"],
    "node": ["package.json", "tsconfig.json", "jsconfig.json"],
    "dotnet": [],
    "rust": ["Cargo.toml"],
    "go": ["go.mod", "go.work"],
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


def _detect_project_from_snapshot(snapshot: RepoSnapshot) -> DetectResult:
    """Detect project types from an existing repository snapshot."""
    path = snapshot.root
    project_types: list[str] = []
    markers: dict[str, list[str]] = {}
    ev = EvidenceSet()

    # Check marker files and extensions
    for ptype, exts in EXTENSIONS.items():
        markers[ptype] = []
        marker_hits: list[str] = []
        ext_hits: list[str] = []
        weak_hits: list[str] = []

        for sf in snapshot.files:
            name = Path(sf.rel_path).name
            trusted = _is_trusted_detection_path(sf.rel_path)
            if ptype in MARKERS and name in MARKERS[ptype]:
                if trusted:
                    marker_hits.append(sf.rel_path)
                else:
                    weak_hits.append(sf.rel_path)
            for ext in exts:
                if name.endswith(ext):
                    if trusted:
                        ext_hits.append(sf.rel_path)
                    else:
                        weak_hits.append(sf.rel_path)
                    break

        hits = marker_hits + ext_hits
        if hits:
            project_types.append(ptype)
            markers[ptype] = sorted(set(hits))[:20]
            for mh in marker_hits:
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"{ptype}: marker file `{Path(mh).name}` found at `{mh}`",
                    source_path=mh,
                    analyzer="detectors",
                )
            # Cap inferred extension evidence to avoid flooding from large directories
            for eh in ext_hits[:10]:
                ev.add(
                    EvidenceKind.INFERRED,
                    f"{ptype}: extension `{Path(eh).suffix}` inferred from `{eh}`",
                    source_path=eh,
                    analyzer="detectors",
                )
            if len(ext_hits) > 10:
                ev.add(
                    EvidenceKind.INFERRED,
                    f"{ptype}: {len(ext_hits)} additional extension hits omitted to avoid noise",
                    analyzer="detectors",
                    confidence=Confidence.LOW,
                )
        elif weak_hits:
            ev.add(
                EvidenceKind.UNKNOWN,
                f"{ptype}: only low-trust marker/extension hits found; not promoted to detected stack",
                source_path=sorted(set(weak_hits))[0],
                analyzer="detectors",
                confidence=Confidence.LOW,
            )

    # Also check explicit marker files for types without extensions
    for ptype, names in MARKERS.items():
        if ptype == "dotnet":
            continue
        if ptype in project_types:
            continue
        marker_hits2: list[str] = []
        for sf in snapshot.files:
            name = Path(sf.rel_path).name
            if name in names and _is_trusted_detection_path(sf.rel_path):
                marker_hits2.append(sf.rel_path)
        if marker_hits2:
            project_types.append(ptype)
            markers[ptype] = sorted(set(marker_hits2))[:20]
            for mh in marker_hits2:
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"{ptype}: marker file `{Path(mh).name}` found at `{mh}`",
                    source_path=mh,
                    analyzer="detectors",
                )

    # Always include generic for existing repos
    project_types.append("generic")
    markers["generic"] = []
    ev.add(
        EvidenceKind.OBSERVED,
        "generic: directory exists and was readable",
        analyzer="detectors",
    )

    # Build legacy evidence map
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

    # Add unknown evidence for any supported type not detected
    for ptype in MARKERS:
        if ptype not in project_types:
            ev.add(
                EvidenceKind.UNKNOWN,
                f"{ptype}: no trusted primary-surface marker files or extensions found",
                analyzer="detectors",
            )

    return DetectResult(
        repo_path=str(path),
        exists=True,
        project_types=sorted(set(project_types)),
        markers=markers,
        evidence=evidence,
        evidence_set=ev,
    )


def detect_project_from_snapshot(snapshot: RepoSnapshot) -> DetectResult:
    """Public snapshot-based detector used by the analyzer registry and graph."""
    return _detect_project_from_snapshot(snapshot)


def detect_project(repo_path: str) -> DetectResult:
    """Detect project types for a repository path."""
    path = validate_repo_path(repo_path)
    if path is None:
        ev = EvidenceSet()
        ev.add(EvidenceKind.ERROR, f"Path does not exist or is not a directory: {repo_path}")
        return DetectResult(
            repo_path=repo_path,
            exists=False,
            error=f"Path does not exist or is not a directory: {repo_path}",
            evidence_set=ev,
        )

    scanner = Scanner()
    snapshot = scanner.scan(path, ScannerOptions(max_depth=3, max_files=5_000, max_files_per_dir=200))
    return _detect_project_from_snapshot(snapshot)
