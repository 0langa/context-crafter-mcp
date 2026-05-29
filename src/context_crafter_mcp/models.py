"""Typed models for context-crafter-mcp."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
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
            "warnings": [],
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
