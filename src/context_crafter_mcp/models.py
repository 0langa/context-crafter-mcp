"""Typed models for context-crafter-mcp."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class EvidenceKind(str, Enum):
    """Kind of evidence supporting a claim."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class Confidence(str, Enum):
    """Confidence level for an evidence claim."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Map evidence kind to default confidence
_KIND_CONFIDENCE: dict[EvidenceKind, Confidence] = {
    EvidenceKind.OBSERVED: Confidence.HIGH,
    EvidenceKind.INFERRED: Confidence.MEDIUM,
    EvidenceKind.UNKNOWN: Confidence.LOW,
    EvidenceKind.UNSUPPORTED: Confidence.LOW,
    EvidenceKind.ERROR: Confidence.HIGH,
}


@dataclass
class Evidence:
    """A single evidence item supporting or qualifying a claim."""

    kind: EvidenceKind
    message: str
    source_path: str | None = None
    analyzer: str | None = None
    confidence: Confidence = Confidence.MEDIUM

    def __post_init__(self) -> None:
        if isinstance(self.confidence, str):
            self.confidence = Confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "message": self.message,
            "source_path": self.source_path,
            "analyzer": self.analyzer,
            "confidence": self.confidence.value,
        }


@dataclass
class EvidenceSet:
    """Collection of evidence items with query helpers."""

    items: list[Evidence] = field(default_factory=list)

    def add(
        self,
        kind: EvidenceKind | str,
        message: str,
        source_path: str | None = None,
        analyzer: str | None = None,
        confidence: Confidence | str | None = None,
    ) -> None:
        if isinstance(kind, str):
            kind = EvidenceKind(kind)
        if confidence is None:
            confidence = _KIND_CONFIDENCE.get(kind, Confidence.MEDIUM)
        if isinstance(confidence, str):
            confidence = Confidence(confidence)
        self.items.append(
            Evidence(kind=kind, message=message, source_path=source_path, analyzer=analyzer, confidence=confidence)
        )

    def by_kind(self, kind: EvidenceKind | str) -> list[Evidence]:
        if isinstance(kind, str):
            kind = EvidenceKind(kind)
        return [e for e in self.items if e.kind == kind]

    def by_analyzer(self, analyzer: str) -> list[Evidence]:
        return [e for e in self.items if e.analyzer == analyzer]

    def by_confidence(self, confidence: Confidence | str) -> list[Evidence]:
        if isinstance(confidence, str):
            confidence = Confidence(confidence)
        return [e for e in self.items if e.confidence == confidence]

    def warnings(self) -> list[Evidence]:
        return [e for e in self.items if e.kind in (EvidenceKind.UNKNOWN, EvidenceKind.UNSUPPORTED, EvidenceKind.ERROR)]

    def verify(self, repo_path: str | Path) -> list[Evidence]:
        """Return evidence items whose source_path does not exist in the repository."""
        root = Path(repo_path)
        missing: list[Evidence] = []
        for e in self.items:
            if e.source_path and not (root / e.source_path).exists():
                missing.append(e)
        return missing

    def to_dicts(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.items]

    def __bool__(self) -> bool:
        return bool(self.items)


@dataclass
class AnalyzerSpec:
    """Metadata describing an analyzer's capabilities and limitations."""

    project_type: str
    display_name: str
    support_level: str  # metadata | syntax | ast | mixed | generic
    parser: str  # stdlib_ast | regex | toml | xml | metadata | none
    detects: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    analyzer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_type": self.project_type,
            "display_name": self.display_name,
            "support_level": self.support_level,
            "parser": self.parser,
            "detects": self.detects,
            "limitations": self.limitations,
        }


@dataclass
class ScanConfig:
    """Configurable scanning limits."""

    max_depth: int = 4
    max_files_per_dir: int = 80
    profile: str = "standard"
    max_file_bytes: int = 5_000_000

    def __post_init__(self) -> None:
        if self.max_depth < 1 or self.max_depth > 20:
            raise ValueError("max_depth must be between 1 and 20")
        if self.max_files_per_dir < 1 or self.max_files_per_dir > 5000:
            raise ValueError("max_files_per_dir must be between 1 and 5000")
        if self.profile not in ("compact", "standard", "deep"):
            raise ValueError("profile must be compact, standard, or deep")


@dataclass
class DetectResult:
    repo_path: str
    exists: bool
    project_types: list[str] = field(default_factory=list)
    markers: dict[str, list[str]] = field(default_factory=dict)
    error: str | None = None
    evidence: dict[str, str] = field(default_factory=dict)
    evidence_set: EvidenceSet = field(default_factory=EvidenceSet)

    def to_dict(self) -> dict[str, Any]:
        warnings = self.evidence_set.warnings()
        return {
            "ok": self.exists,
            "summary": f"Detected types: {', '.join(self.project_types)}"
            if self.exists
            else f"Detection failed: {self.error}",
            "repo_path": self.repo_path,
            "exists": self.exists,
            "project_types": self.project_types,
            "markers": self.markers,
            "error": self.error,
            "evidence": self.evidence,
            "evidence_details": self.evidence_set.to_dicts(),
            "warnings": [e.message for e in warnings],
            "errors": [self.error] if self.error else [],
        }


@dataclass
class FileInfo:
    path: Path
    rel_path: str
    is_dir: bool
    size: int = 0


@dataclass
class PythonModule:
    rel_path: str
    module_name: str
    imports: list[str] = field(default_factory=list)
    internal_imports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    async_functions: list[str] = field(default_factory=list)
    top_level_constants: list[str] = field(default_factory=list)
    is_entry_point: bool = False
    parse_error: str | None = None


@dataclass
class NodePackage:
    name: str | None = None
    scripts: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    import_edges: list[tuple[str, str]] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)


@dataclass
class DotNetProject:
    name: str
    rel_path: str
    target_frameworks: list[str] = field(default_factory=list)
    package_refs: list[str] = field(default_factory=list)
    project_refs: list[str] = field(default_factory=list)
    output_type: str | None = None
    assembly_name: str | None = None
    classes: list[str] = field(default_factory=list)


@dataclass
class DotNetSolution:
    name: str
    rel_path: str
    projects: list[str] = field(default_factory=list)


@dataclass
class RustCrate:
    name: str | None = None
    dependencies: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    impls: list[str] = field(default_factory=list)


@dataclass
class GoModule:
    name: str | None = None
    dependencies: list[str] = field(default_factory=list)
    packages: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    structs: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)


@dataclass
class JavaProject:
    name: str | None = None
    build_tool: str | None = None
    dependencies: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    annotations: list[str] = field(default_factory=list)


@dataclass
class ProjectMetadata:
    """Basic project metadata extracted from config files."""

    name: str | None = None
    description: str | None = None
    version: str | None = None
    authors: list[str] = field(default_factory=list)
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    repo_path: str
    project_types: list[str] = field(default_factory=list)
    root_files: list[str] = field(default_factory=list)
    directory_tree: list[str] = field(default_factory=list)
    docs_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    likely_entry_points: list[str] = field(default_factory=list)
    test_directories: list[str] = field(default_factory=list)
    source_directories: list[str] = field(default_factory=list)
    python_modules: list[PythonModule] = field(default_factory=list)
    node_packages: list[NodePackage] = field(default_factory=list)
    dotnet_projects: list[DotNetProject] = field(default_factory=list)
    dotnet_solutions: list[DotNetSolution] = field(default_factory=list)
    rust_crates: list[RustCrate] = field(default_factory=list)
    go_modules: list[GoModule] = field(default_factory=list)
    java_projects: list[JavaProject] = field(default_factory=list)
    files_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    python_dependencies: list[str] = field(default_factory=list)
    python_dev_dependencies: list[str] = field(default_factory=list)
    profile: str = "standard"
    evidence_set: EvidenceSet = field(default_factory=EvidenceSet)


@dataclass
class RenderResult:
    ok: bool
    written: list[str] = field(default_factory=list)
    files_scanned: int = 0
    project_types: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": f"Generated {len(self.written)} file(s)" if self.ok else f"Generation failed: {self.error}",
            "generated_files": self.written,
            "written": self.written,
            "files_scanned": self.files_scanned,
            "project_types": self.project_types,
            "warnings": [],
            "errors": [self.error] if self.error else [],
        }


_PROFILE_LIMITS: dict[str, dict[str, int]] = {
    "compact": {
        "tree_max_lines": 80,
        "root_files": 15,
        "source_dirs": 10,
        "entry_points": 10,
        "test_dirs": 10,
        "docs_files": 20,
        "config_files": 20,
        "deps": 15,
        "dev_deps": 15,
        "python_modules_display": 5,
        "classes_display": 5,
        "functions_display": 5,
        "mermaid_external": 20,
        "internal_edges": 8,
        "large_modules": 3,
        "cycles": 3,
        "abstractions": 5,
    },
    "standard": {
        "tree_max_lines": 200,
        "root_files": 30,
        "source_dirs": 20,
        "entry_points": 20,
        "test_dirs": 20,
        "docs_files": 50,
        "config_files": 50,
        "deps": 30,
        "dev_deps": 30,
        "python_modules_display": 10,
        "classes_display": 10,
        "functions_display": 10,
        "mermaid_external": 40,
        "internal_edges": 15,
        "large_modules": 5,
        "cycles": 5,
        "abstractions": 10,
    },
    "deep": {
        "tree_max_lines": 400,
        "root_files": 60,
        "source_dirs": 40,
        "entry_points": 40,
        "test_dirs": 40,
        "docs_files": 100,
        "config_files": 100,
        "deps": 60,
        "dev_deps": 60,
        "python_modules_display": 20,
        "classes_display": 20,
        "functions_display": 20,
        "mermaid_external": 80,
        "internal_edges": 30,
        "large_modules": 10,
        "cycles": 10,
        "abstractions": 20,
    },
}


def get_profile_limit(profile: str, key: str) -> int:
    """Return a numeric limit for the given profile and key."""
    return _PROFILE_LIMITS.get(profile, _PROFILE_LIMITS["standard"]).get(key, _PROFILE_LIMITS["standard"][key])
