"""Go analyzer."""

from __future__ import annotations

import re
from pathlib import Path

from repo_docs_mcp.analyzers import register_analyzer
from repo_docs_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from repo_docs_mcp.models import AnalysisResult, GoModule, ScanConfig

GO_MOD_MODULE_RE = re.compile(r"^module\s+(\S+)", re.MULTILINE)
GO_MOD_REQUIRE_RE = re.compile(r"^require\s+\(?\s*(\S+)", re.MULTILINE)


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
    mod = GoModule()
    packages: set[str] = set()
    count = 0

    go_mod = path / "go.mod"
    text = safe_read_text(go_mod)
    if text:
        m = GO_MOD_MODULE_RE.search(text)
        if m:
            mod.name = m.group(1)
        for req in GO_MOD_REQUIRE_RE.finditer(text):
            mod.dependencies.append(req.group(1))

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        name = fi.path.name
        if name.endswith(".go"):
            count += 1
            pkg_dir = str(Path(fi.rel_path).parent)
            if pkg_dir == ".":
                pkg_dir = ""
            packages.add(pkg_dir or "main")
            src = safe_read_text(fi.path, max_bytes=500_000)
            if src and "package main" in src:
                mod.entry_points.append(fi.rel_path)

    mod.packages = sorted(packages)
    result.go_modules = [mod]
    result.files_scanned += count
    return result


register_analyzer("go", analyze_go)
