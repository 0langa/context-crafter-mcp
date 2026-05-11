""".NET analyzer using stdlib XML parsing."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from repo_docs_mcp.analyzers import register_analyzer
from repo_docs_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from repo_docs_mcp.models import AnalysisResult, DotNetProject, DotNetSolution, ScanConfig


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

    # Target frameworks
    for tf in root.iter("TargetFramework"):
        if tf.text:
            proj.target_frameworks.append(tf.text)
    for tfs in root.iter("TargetFrameworks"):
        if tfs.text:
            proj.target_frameworks.extend(tfs.text.split(";"))

    # Package references
    for pref in root.iter("PackageReference"):
        name = pref.get("Include") or ""
        if name:
            proj.package_refs.append(name)

    # Project references
    for pref in root.iter("ProjectReference"):
        href = pref.get("Include") or ""
        if href:
            proj.project_refs.append(href)

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
    solutions: list[DotNetSolution] = []
    projects: list[DotNetProject] = []
    count = 0

    for fi in safe_scan(path, max_depth=cfg.max_depth + 1, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        name = fi.path.name
        if name.endswith(".sln"):
            count += 1
            solutions.append(parse_solution(fi.path, fi.rel_path))
        elif name.endswith((".csproj", ".fsproj", ".vbproj")):
            count += 1
            projects.append(parse_project(fi.path, fi.rel_path))

    result.dotnet_solutions = solutions
    result.dotnet_projects = projects
    result.files_scanned += count

    # Entry points
    for p in projects:
        if "Exe" in p.target_frameworks or any("Exe" in str(t) for t in p.target_frameworks):
            result.likely_entry_points.append(p.rel_path)
        proj_dir = Path(p.rel_path).parent
        program_file = path / proj_dir / "Program.cs"
        if program_file.exists():
            result.likely_entry_points.append(str((proj_dir / "Program.cs").as_posix()))

    return result


register_analyzer("dotnet", analyze_dotnet)
