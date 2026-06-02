"""Go analyzer with tree-sitter AST and regex fallback."""

from __future__ import annotations

import re
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.analyzers.snapshot_utils import get_analysis_snapshot, iter_snapshot_files
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, GoModule, ScanConfig
from context_crafter_mcp.parsers import get_parser_backend
from context_crafter_mcp.scanner import SnapshotFile

GO_MOD_MODULE_RE = re.compile(r"^module\s+(\S+)", re.MULTILINE)
GO_MOD_REQUIRE_RE = re.compile(r"^require\s+\(?\s*(\S+)", re.MULTILINE)
GO_IMPORT_RE = re.compile(r'^\s*import\s+(?:\(\s*([^)]*)\s*\)|"([^"]+)")', re.MULTILINE)
GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(", re.MULTILINE)
GO_STRUCT_RE = re.compile(r"^type\s+(\w+)\s+struct\b", re.MULTILINE)
GO_INTERFACE_RE = re.compile(r"^type\s+(\w+)\s+interface\b", re.MULTILINE)
GO_INTERFACE_ASSERT_RE = re.compile(r"var\s+_\s+(\w+)\s*=\s*\(?\*?(\w+)\)?")
GO_METHOD_RECEIVER_RE = re.compile(r"^func\s+\((?:\w+\s+)?\*?(\w+)\)\s+(\w+)", re.MULTILINE)


def analyze_go(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze Go files in the repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    snapshot = get_analysis_snapshot(path, result, cfg)
    ev = result.evidence_set
    parser_used = "regex"

    # Pass 1: discover go.mod files and collect Go source paths
    go_mod_files: list[Path] = []
    go_files: list[tuple[SnapshotFile, Path]] = []
    count = 0

    for sf, file_path in iter_snapshot_files(snapshot):
        if _is_fixture_path(sf.rel_path):
            continue
        name = file_path.name
        if name == "go.mod":
            go_mod_files.append(file_path)
        elif name.endswith(".go"):
            go_files.append((sf, file_path))
            count += 1

    # Parse each go.mod into a module keyed by directory
    modules: dict[Path, GoModule] = {}
    for gm in go_mod_files:
        mod = GoModule()
        text = safe_read_text(gm)
        if text:
            rel = gm.relative_to(path).as_posix()
            mod.rel_path = str(Path(rel).parent) if Path(rel).parent.as_posix() != "." else "."
            m = GO_MOD_MODULE_RE.search(text)
            if m:
                mod.name = m.group(1)
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Go module `{mod.name}` from `{rel}`",
                    source_path=rel,
                    analyzer="go",
                )
            for req in GO_MOD_REQUIRE_RE.finditer(text):
                mod.dependencies.append(req.group(1))
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Go dependency `{req.group(1)}` from `{rel}`",
                    source_path=rel,
                    analyzer="go",
                )
        modules[gm.parent] = mod

    if not modules:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `go.mod` found; Go module metadata unavailable.",
            analyzer="go",
        )

    # Fallback module for orphan .go files
    if path not in modules:
        fallback = GoModule()
        fallback.rel_path = "."
        modules[path] = fallback

    # Pass 2: assign each .go file to nearest module by path prefix
    for sf, file_path in go_files:
        file_dir = file_path.parent
        best_mod = modules[path]
        best_depth = -1
        for root, mod in modules.items():
            if root == path:
                continue
            try:
                file_dir.relative_to(root)
                depth = len(root.parts)
                if depth > best_depth:
                    best_mod = mod
                    best_depth = depth
            except ValueError:
                continue

        pkg_dir = str(Path(sf.rel_path).parent)
        if pkg_dir == ".":
            pkg_dir = ""
        best_mod.packages.append(pkg_dir or "main")

        # Try tree-sitter first
        backend = get_parser_backend("go")
        try:
            source = file_path.read_bytes()
        except OSError:
            parsed = None
        else:
            parsed = backend.parse(source, "go")
        if parsed and getattr(parsed, "parser_used", "none") != "none":
            parser_used = parsed.parser_used
            for imp in parsed.imports:
                best_mod.dependencies.append(imp)
            for func in parsed.functions:
                best_mod.packages.append(f"{pkg_dir or 'main'}.{func}")
            for cls in parsed.classes:
                best_mod.structs.append(f"{pkg_dir or 'main'}.{cls}")
            for iface in parsed.dependencies:
                best_mod.interfaces.append(f"{pkg_dir or 'main'}.{iface}")
            # Convert absolute paths from parser to relative
            for ep in parsed.entry_points:
                # parser returns "" when the file contains main(); map to file path
                if ep == "":
                    entry_rel = sf.rel_path
                elif Path(ep).is_absolute():
                    entry_rel = str(Path(ep).relative_to(path))
                else:
                    entry_rel = str(ep)
                if entry_rel not in best_mod.entry_points:
                    best_mod.entry_points.append(entry_rel)
                    ev.add(
                        EvidenceKind.OBSERVED,
                        f"Go entry point `{entry_rel}` (package main)",
                        source_path=entry_rel,
                        analyzer="go",
                    )
        else:
            # Regex fallback
            src = safe_read_text(file_path, max_bytes=500_000)
            if src:
                if "package main" in src:
                    best_mod.entry_points.append(sf.rel_path)
                    ev.add(
                        EvidenceKind.OBSERVED,
                        f"Go entry point `{sf.rel_path}` (package main)",
                        source_path=sf.rel_path,
                        analyzer="go",
                    )
                for m in GO_IMPORT_RE.finditer(src):
                    block = m.group(1)
                    single = m.group(2)
                    if single:
                        best_mod.dependencies.append(single)
                    elif block:
                        for line in block.splitlines():
                            line = line.strip().strip('"')
                            if line and not line.startswith("."):
                                best_mod.dependencies.append(line)
                for m in GO_FUNC_RE.finditer(src):
                    best_mod.packages.append(f"{pkg_dir or 'main'}.{m.group(1)}")
                for m in GO_STRUCT_RE.finditer(src):
                    best_mod.structs.append(f"{pkg_dir or 'main'}.{m.group(1)}")
                for m in GO_INTERFACE_RE.finditer(src):
                    best_mod.interfaces.append(f"{pkg_dir or 'main'}.{m.group(1)}")

    # Pass 3: detect interface assertions and build package graph
    all_structs: set[str] = set()
    all_interfaces: set[str] = set()
    for mod in modules.values():
        all_structs.update(s.split(".")[-1] for s in mod.structs)
        all_interfaces.update(i.split(".")[-1] for i in mod.interfaces)

    for sf, file_path in go_files:
        src = safe_read_text(file_path, max_bytes=500_000)
        if not src:
            continue
        file_dir_rel = Path(sf.rel_path).parent.as_posix()
        pkg_dir = file_dir_rel if file_dir_rel != "." else "main"
        best_mod = modules[path]
        for root, mod in modules.items():
            if root == path:
                continue
            try:
                file_path.parent.relative_to(root)
                best_mod = mod
            except ValueError:
                continue

        for m in GO_INTERFACE_ASSERT_RE.finditer(src):
            iface = m.group(1)
            struct_name = m.group(2)
            if iface in all_interfaces and struct_name in all_structs:
                best_mod.interface_impls.append((iface, struct_name))
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Go interface assertion: `{struct_name}` implements `{iface}`",
                    source_path=sf.rel_path,
                    analyzer="go",
                )

        # Build package graph from local imports
        for m in GO_IMPORT_RE.finditer(src):
            block = m.group(1)
            single = m.group(2)
            imp = single or (block.splitlines()[0].strip().strip('"') if block else "")
            if imp and not imp.startswith(".") and "/" in imp:
                # Map import to module
                for mod in modules.values():
                    if mod.name and imp.startswith(mod.name):
                        edge = (pkg_dir, mod.name)
                        if edge not in best_mod.package_graph:
                            best_mod.package_graph.append(edge)

    # Deduplicate and sort, drop empty fallback if real modules exist
    for mod in modules.values():
        mod.packages = sorted(set(mod.packages))
        mod.structs = sorted(set(mod.structs))
        mod.interfaces = sorted(set(mod.interfaces))
        mod.dependencies = sorted(set(mod.dependencies))
        mod.entry_points = sorted(set(mod.entry_points))
        mod.interface_impls = sorted(set(mod.interface_impls))
        mod.package_graph = sorted(set(mod.package_graph))

    result.go_modules = [
        m for m in modules.values() if m.rel_path != "." or m.packages or m.dependencies or m.entry_points
    ]
    result.analyzer_files_parsed += count

    total_structs = sum(len(m.structs) for m in result.go_modules)
    total_interfaces = sum(len(m.interfaces) for m in result.go_modules)
    total_impls = sum(len(m.interface_impls) for m in result.go_modules)
    if total_structs or total_interfaces:
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Go symbols via {parser_used}: {total_structs} struct(s), {total_interfaces} interface(s), {total_impls} interface impl(s)",
            analyzer="go",
        )

    return result


register_analyzer("go", analyze_go)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="go",
        display_name="Go",
        support_level="ast",
        parser="tree-sitter-go",
        detects=["go.mod", "*.go"],
        limitations=["Regex fallback when tree-sitter-go is unavailable"],
    )
)
