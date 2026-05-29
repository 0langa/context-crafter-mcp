"""Generic repository analyzer."""

from __future__ import annotations

from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.filesystem import (
    INTERESTING_ROOT_FILES,
    list_directory_tree,
    list_root_files,
    validate_repo_path,
)
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, ScanConfig, get_profile_limit
from context_crafter_mcp.scanner import Scanner, ScannerOptions


ENTRY_POINT_HINTS = {
    "main.py",
    "app.py",
    "cli.py",
    "server.py",
    "index.js",
    "index.ts",
    "main.js",
    "main.ts",
    "app.js",
    "app.ts",
    "server.js",
    "server.ts",
    "cli.js",
    "cli.ts",
    "Program.cs",
    "Startup.cs",
    "main.rs",
    "lib.rs",
    "main.go",
    "Main.java",
}

TEST_DIR_HINTS = {"test", "tests", "spec", "specs", "__tests__", "testing"}

SOURCE_DIR_HINTS = {"src", "lib", "source", "pkg", "app", "core"}

DOCS_HINTS = {"docs", "doc", "documentation", "wiki", "guides"}

CONFIG_HINTS = {
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
}


def analyze_generic(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Perform generic analysis on a repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        return AnalysisResult(
            repo_path=repo_path,
            errors=[f"Invalid repo_path: {repo_path}"],
        )

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))

    # Adjust tree depth by profile
    tree_depth = cfg.max_depth
    if cfg.profile == "compact":
        tree_depth = max(2, cfg.max_depth - 1)
    elif cfg.profile == "deep":
        tree_depth = cfg.max_depth + 2

    # Root files
    all_root = list_root_files(path)
    result.root_files = [f for f in all_root if f in INTERESTING_ROOT_FILES or f.endswith(tuple(CONFIG_HINTS))]

    # Directory tree
    result.directory_tree = list_directory_tree(path, max_depth=tree_depth, max_files_per_dir=cfg.max_files_per_dir)

    scanner = Scanner()
    snapshot = scanner.scan(
        path,
        ScannerOptions(
            max_depth=tree_depth + 1,
            max_files=cfg.max_files_per_dir * 10,
            max_file_bytes=cfg.max_file_bytes,
        ),
    )

    docs_files: list[str] = []
    config_files: list[str] = []
    likely_entry_points: list[str] = []
    test_dirs: set[str] = set()
    source_dirs: set[str] = set()
    docs_dirs: set[str] = set()

    for sd in snapshot.directories:
        if _is_fixture_path(sd.rel_path):
            continue
        name = Path(sd.rel_path).name.lower()
        if name in TEST_DIR_HINTS:
            test_dirs.add(sd.rel_path)
        if name in SOURCE_DIR_HINTS:
            source_dirs.add(sd.rel_path)
        if name in DOCS_HINTS:
            docs_dirs.add(sd.rel_path)

    for sf in snapshot.files:
        if _is_fixture_path(sf.rel_path):
            continue
        name = Path(sf.rel_path).name
        rel = sf.rel_path

        if name.lower().endswith((".md", ".rst", ".txt")) and "readme" not in name.lower():
            docs_files.append(rel)
        if name in INTERESTING_ROOT_FILES or name.endswith(tuple(CONFIG_HINTS)):
            config_files.append(rel)
        if name in ENTRY_POINT_HINTS:
            likely_entry_points.append(rel)

    result.profile = cfg.profile
    result.files_scanned = len(snapshot.files)
    result.docs_files = sorted(set(docs_files))[: get_profile_limit(cfg.profile, "docs_files")]
    result.config_files = sorted(set(config_files))[: get_profile_limit(cfg.profile, "config_files")]
    result.likely_entry_points = sorted(set(likely_entry_points))[: get_profile_limit(cfg.profile, "entry_points")]
    result.test_directories = sorted(test_dirs)[: get_profile_limit(cfg.profile, "test_dirs")]
    result.source_directories = sorted(source_dirs)[: get_profile_limit(cfg.profile, "source_dirs")]

    ev = result.evidence_set
    ev.add(
        EvidenceKind.OBSERVED,
        f"Scanned {result.files_scanned} files, {len(snapshot.directories)} directories",
        analyzer="generic",
    )
    for ep in result.likely_entry_points:
        ev.add(
            EvidenceKind.INFERRED,
            f"Likely entry point `{ep}` inferred from filename",
            source_path=ep,
            analyzer="generic",
        )
    for cfg_file in result.config_files[:5]:
        ev.add(
            EvidenceKind.OBSERVED,
            f"Config file `{cfg_file}` found",
            source_path=cfg_file,
            analyzer="generic",
        )

    return result


register_analyzer("generic", analyze_generic)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="generic",
        display_name="Generic",
        support_level="generic",
        parser="none",
        detects=[],
        limitations=["No language-specific parsing", "Directory and filename heuristics only"],
    )
)
