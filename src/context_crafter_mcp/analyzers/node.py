"""Node/JS/TS analyzer."""

from __future__ import annotations

import json
import re
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, NodePackage, ScanConfig

IMPORT_RE = re.compile(
    r"(?:^|\s)import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\)",
    re.MULTILINE,
)


def analyze_node(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze Node/JS/TS files in the repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    pkg = NodePackage()
    files: list[str] = []
    edges: list[tuple[str, str]] = []
    count = 0

    # Read package.json if present
    pkg_json = path / "package.json"
    pkg_text = safe_read_text(pkg_json)
    if pkg_text:
        try:
            data = json.loads(pkg_text)
        except json.JSONDecodeError as exc:
            result.errors.append(f"package.json parse error: {exc}")
            data = {}
        pkg.name = data.get("name")
        pkg.scripts = data.get("scripts", {})
        pkg.dependencies = list(data.get("dependencies", {}).keys())
        pkg.dev_dependencies = list(data.get("devDependencies", {}).keys())

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            count += 1
            files.append(fi.rel_path)
            text = safe_read_text(fi.path, max_bytes=1_000_000)
            if text:
                for m in IMPORT_RE.finditer(text):
                    target = m.group(1) or m.group(2)
                    if target:
                        edges.append((fi.rel_path, target))

    pkg.files = files
    pkg.import_edges = edges
    result.node_packages = [pkg]
    result.files_scanned += count

    # Entry points
    for f in files:
        base = Path(f).name
        if base in {
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
        }:
            result.likely_entry_points.append(f)

    scripts = pkg.scripts
    for script_name, cmd in scripts.items():
        result.likely_entry_points.append(f"[npm script] {script_name}: {cmd}")

    return result


register_analyzer("node", analyze_node)
