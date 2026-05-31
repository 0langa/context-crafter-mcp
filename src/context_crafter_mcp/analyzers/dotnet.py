""".NET analyzer with tree-sitter C# AST and regex/XML fallback."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import (
    AnalysisResult,
    AnalyzerSpec,
    DotNetProject,
    DotNetSolution,
    EvidenceKind,
    ScanConfig,
)
from context_crafter_mcp.parsers import get_parser_backend

DOTNET_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
DOTNET_NAMESPACE_RE = re.compile(r"\bnamespace\s+([\w.]+)")


def parse_solution(path: Path, rel_path: str) -> DotNetSolution:
    """Parse a .sln file lightly."""
    sol = DotNetSolution(name=path.stem, rel_path=rel_path)
    text = safe_read_text(path)
    if text is None:
        return sol
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Project(") and ".csproj" in line:
            parts = line.split(",")
            if len(parts) >= 2:
                proj_rel = parts[1].strip().strip('"')
                sol.projects.append(proj_rel)
    return sol


def parse_project(path: Path, rel_path: str) -> DotNetProject:
    """Parse a .csproj/.fsproj/.vbproj file."""
    proj = DotNetProject(name=path.stem, rel_path=rel_path)
    text = safe_read_text(path)
    if text is None:
        return proj
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        proj = DotNetProject(name=path.stem, rel_path=rel_path)
        proj.target_frameworks = [f"Parse error: {exc}"]
        return proj

    for tf in root.iter("TargetFramework"):
        if tf.text:
            proj.target_frameworks.append(tf.text)
    for tfs in root.iter("TargetFrameworks"):
        if tfs.text:
            proj.target_frameworks.extend(tfs.text.split(";"))

    for pref in root.iter("PackageReference"):
        name = pref.get("Include") or ""
        if name:
            proj.package_refs.append(name)

    for pref in root.iter("ProjectReference"):
        href = pref.get("Include") or ""
        if href:
            proj.project_refs.append(href)

    for ot in root.iter("OutputType"):
        if ot.text:
            proj.output_type = ot.text

    for an in root.iter("AssemblyName"):
        if an.text:
            proj.assembly_name = an.text

    return proj


def analyze_dotnet(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze .NET solution and project files."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    ev = result.evidence_set
    solutions: list[DotNetSolution] = []
    projects: list[DotNetProject] = []
    count = 0
    parser_used = "regex"

    for fi in safe_scan(path, max_depth=cfg.max_depth + 1, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".sln"):
            count += 1
            sol = parse_solution(fi.path, fi.rel_path)
            solutions.append(sol)
            ev.add(
                EvidenceKind.OBSERVED,
                f".NET solution `{sol.name}` found at `{fi.rel_path}`",
                source_path=fi.rel_path,
                analyzer="dotnet",
            )
        elif name.endswith((".csproj", ".fsproj", ".vbproj")):
            count += 1
            proj = parse_project(fi.path, fi.rel_path)
            projects.append(proj)
            ev.add(
                EvidenceKind.OBSERVED,
                f".NET project `{proj.name}` found at `{fi.rel_path}` (targets: {', '.join(proj.target_frameworks) or 'unknown'})",
                source_path=fi.rel_path,
                analyzer="dotnet",
            )
            for pkg in proj.package_refs:
                ev.add(
                    EvidenceKind.OBSERVED,
                    f".NET package reference `{pkg}` from `{fi.rel_path}`",
                    source_path=fi.rel_path,
                    analyzer="dotnet",
                )

    result.dotnet_solutions = solutions
    result.dotnet_projects = projects
    result.files_scanned += count

    if not projects and not solutions:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `.sln` or `.csproj` files found; .NET metadata unavailable.",
            analyzer="dotnet",
        )

    # Build project graph from solution + project references
    proj_name_map: dict[str, DotNetProject] = {p.name: p for p in projects}
    for p in projects:
        for pref in p.project_refs:
            pref_name = Path(pref).stem
            if pref_name in proj_name_map:
                p.project_graph.append((p.name, pref_name))
    for sol in solutions:
        for proj_rel in sol.projects:
            proj_name = Path(proj_rel).stem
            if proj_name in proj_name_map:
                for other in sol.projects:
                    other_name = Path(other).stem
                    if other_name != proj_name and other_name in proj_name_map:
                        edge = (proj_name, other_name)
                        if edge not in proj_name_map[proj_name].project_graph:
                            proj_name_map[proj_name].project_graph.append(edge)

    # Entry points + class scanning + namespace extraction
    for p in projects:
        proj_dir = Path(p.rel_path).parent
        cs_files = list((path / proj_dir).rglob("*.cs")) if (path / proj_dir).is_dir() else []
        has_source = bool(cs_files)
        if p.output_type == "Exe" and has_source:
            result.likely_entry_points.append(p.rel_path)
            ev.add(
                EvidenceKind.INFERRED,
                f".NET executable project `{p.name}` inferred as entry point (OutputType=Exe)",
                source_path=p.rel_path,
                analyzer="dotnet",
            )
        program_file = path / proj_dir / "Program.cs"
        if program_file.exists():
            result.likely_entry_points.append(str((proj_dir / "Program.cs").as_posix()))
            ev.add(
                EvidenceKind.OBSERVED,
                f".NET entry point `Program.cs` found in `{proj_dir}`",
                source_path=str((proj_dir / "Program.cs").as_posix()),
                analyzer="dotnet",
            )
        # Scan .cs files with tree-sitter or regex
        for cs_file in cs_files[:20]:
            backend = get_parser_backend("csharp")
            try:
                source = cs_file.read_bytes()
            except OSError:
                parsed = None
            else:
                parsed = backend.parse(source, "csharp")
            if parsed and getattr(parsed, "parser_used", "none") != "none":
                parser_used = parsed.parser_used
                for cls in parsed.classes:
                    p.classes.append(cls)
            else:
                src = safe_read_text(cs_file, max_bytes=200_000)
                if src:
                    for m in DOTNET_CLASS_RE.finditer(src):
                        p.classes.append(m.group(1))
                    for m in DOTNET_NAMESPACE_RE.finditer(src):
                        ns = m.group(1)
                        if ns not in p.namespaces:
                            p.namespaces.append(ns)

    for p in projects:
        p.project_graph = sorted(set(p.project_graph))
        p.namespaces = sorted(set(p.namespaces))

    if projects and any(p.classes for p in projects):
        total_classes = sum(len(p.classes) for p in projects)
        total_namespaces = sum(len(p.namespaces) for p in projects)
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f".NET classes via {parser_used}: {total_classes} class(es), {total_namespaces} namespace(s)",
            analyzer="dotnet",
        )

    return result


register_analyzer("dotnet", analyze_dotnet)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="dotnet",
        display_name=".NET",
        support_level="ast",
        parser="tree-sitter-c-sharp + xml",
        detects=["*.sln", "*.csproj", "*.fsproj", "*.vbproj"],
        limitations=["Regex fallback when tree-sitter-c-sharp is unavailable"],
    )
)
