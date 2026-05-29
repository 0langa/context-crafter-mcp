"""Go analyzer."""

from __future__ import annotations

import re
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, GoModule, ScanConfig

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
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".go"):
            count += 1
            pkg_dir = str(Path(fi.rel_path).parent)
            if pkg_dir == ".":
                pkg_dir = ""
            packages.add(pkg_dir or "main")
            src = safe_read_text(fi.path, max_bytes=500_000)
            if src:
                if "package main" in src:
                    mod.entry_points.append(fi.rel_path)
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
    return result


register_analyzer("go", analyze_go)
