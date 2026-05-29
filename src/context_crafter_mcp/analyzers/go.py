"""Go analyzer with tree-sitter AST and regex fallback."""

from __future__ import annotations

import re
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, GoModule, ScanConfig
from context_crafter_mcp.parsers import parse_go

GO_MOD_MODULE_RE = re.compile(r"^module\s+(\S+)", re.MULTILINE)
GO_MOD_REQUIRE_RE = re.compile(r"^require\s+\(?\s*(\S+)", re.MULTILINE)
GO_IMPORT_RE = re.compile(r'^\s*import\s+(?:\(\s*([^)]*)\s*\)|"([^"]+)")', re.MULTILINE)
GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(", re.MULTILINE)
GO_STRUCT_RE = re.compile(r"^type\s+(\w+)\s+struct\b", re.MULTILINE)
GO_INTERFACE_RE = re.compile(r"^type\s+(\w+)\s+interface\b", re.MULTILINE)


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
    ev = result.evidence_set
    mod = GoModule()
    packages: set[str] = set()
    count = 0
    parser_used = "regex"

    go_mod = path / "go.mod"
    text = safe_read_text(go_mod)
    if text:
        m = GO_MOD_MODULE_RE.search(text)
        if m:
            mod.name = m.group(1)
            ev.add(
                EvidenceKind.OBSERVED,
                f"Go module `{mod.name}` from `go.mod`",
                source_path="go.mod",
                analyzer="go",
            )
        for req in GO_MOD_REQUIRE_RE.finditer(text):
            mod.dependencies.append(req.group(1))
            ev.add(
                EvidenceKind.OBSERVED,
                f"Go dependency `{req.group(1)}` from `go.mod`",
                source_path="go.mod",
                analyzer="go",
            )
    else:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `go.mod` found; Go module metadata unavailable.",
            analyzer="go",
        )

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".go"):
            count += 1
            pkg_dir = str(Path(fi.rel_path).parent)
            if pkg_dir == ".":
                pkg_dir = ""
            packages.add(pkg_dir or "main")

            # Try tree-sitter first
            parsed = parse_go(fi.path)
            if parsed and parsed.parser_used != "none":
                parser_used = parsed.parser_used
                for imp in parsed.imports:
                    mod.dependencies.append(imp)
                for func in parsed.functions:
                    mod.packages.append(f"{pkg_dir or 'main'}.{func}")
                for cls in parsed.classes:
                    mod.structs.append(f"{pkg_dir or 'main'}.{cls}")
                for iface in parsed.dependencies:
                    mod.interfaces.append(f"{pkg_dir or 'main'}.{iface}")
                # Convert absolute paths from parser to relative
                for ep in parsed.entry_points:
                    rel = str(Path(ep).relative_to(path)) if Path(ep).is_absolute() else ep
                    if rel not in mod.entry_points:
                        mod.entry_points.append(rel)
                    ev.add(
                        EvidenceKind.OBSERVED,
                        f"Go entry point `{rel}` (package main)",
                        source_path=rel,
                        analyzer="go",
                    )
            else:
                # Regex fallback
                src = safe_read_text(fi.path, max_bytes=500_000)
                if src:
                    if "package main" in src:
                        mod.entry_points.append(fi.rel_path)
                        ev.add(
                            EvidenceKind.OBSERVED,
                            f"Go entry point `{fi.rel_path}` (package main)",
                            source_path=fi.rel_path,
                            analyzer="go",
                        )
                    for m in GO_IMPORT_RE.finditer(src):
                        block = m.group(1)
                        single = m.group(2)
                        if single:
                            mod.dependencies.append(single)
                        elif block:
                            for line in block.splitlines():
                                line = line.strip().strip('"')
                                if line and not line.startswith("."):
                                    mod.dependencies.append(line)
                    for m in GO_FUNC_RE.finditer(src):
                        mod.packages.append(f"{pkg_dir or 'main'}.{m.group(1)}")
                    for m in GO_STRUCT_RE.finditer(src):
                        mod.structs.append(f"{pkg_dir or 'main'}.{m.group(1)}")
                    for m in GO_INTERFACE_RE.finditer(src):
                        mod.interfaces.append(f"{pkg_dir or 'main'}.{m.group(1)}")

    mod.packages = sorted(set(mod.packages) | packages)
    mod.structs = sorted(set(mod.structs))
    mod.interfaces = sorted(set(mod.interfaces))
    result.go_modules = [mod]
    result.files_scanned += count

    if mod.structs or mod.interfaces:
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Go symbols via {parser_used}: {len(mod.structs)} struct(s), {len(mod.interfaces)} interface(s)",
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
