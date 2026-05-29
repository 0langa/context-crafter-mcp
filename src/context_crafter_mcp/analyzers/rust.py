"""Rust analyzer."""

from __future__ import annotations

import tomllib

from context_crafter_mcp.analyzers import register_analyzer
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, RustCrate, ScanConfig


def analyze_rust(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze Rust files in the repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    crate = RustCrate()
    modules: list[str] = []
    count = 0

    cargo_toml = path / "Cargo.toml"
    text = safe_read_text(cargo_toml)
    if text:
        try:
            data = tomllib.loads(text)
        except Exception as exc:
            result.errors.append(f"Cargo.toml parse error: {exc}")
            data = {}
        crate.name = data.get("package", {}).get("name")
        deps = data.get("dependencies", {})
        crate.dependencies = list(deps.keys()) if isinstance(deps, dict) else []

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".rs"):
            count += 1
            modules.append(fi.rel_path)
            if name == "main.rs":
                crate.entry_points.append(fi.rel_path)
            if name == "lib.rs":
                crate.entry_points.append(fi.rel_path)

    crate.modules = modules
    result.rust_crates = [crate]
    result.files_scanned += count
    return result


register_analyzer("rust", analyze_rust)
