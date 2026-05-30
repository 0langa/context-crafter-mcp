"""Node/JS/TS analyzer with tree-sitter AST and regex fallback."""

from __future__ import annotations

import json
import re
from pathlib import Path

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, NodePackage, ScanConfig
from context_crafter_mcp.parsers import parse_javascript, parse_typescript
from context_crafter_mcp.ranking import is_vendor_path, PathCategory, PRODUCT_SEGMENTS

_IMPORT_PATTERNS = [
    r"(?:^|\s)import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]",
    r"require\(['\"]([^'\"]+)['\"]\)",
    r"export\s+(?:\*|\{[^}]*\})\s+from\s+['\"]([^'\"]+)['\"]",
    r"import\(['\"]([^'\"]+)['\"]\)",
]
IMPORT_RE = re.compile("|".join(_IMPORT_PATTERNS), re.MULTILINE)

NODE_EXPORT_RE = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:const|let|var|function|class|interface|type)?\s*(\w+)", re.MULTILINE
)
NODE_CLASS_RE = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.MULTILINE)
NODE_FUNC_RE = re.compile(r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)", re.MULTILINE)

PRODUCT_SCRIPT_HINTS = {"start", "serve", "dev", "build", "preview", "deploy"}

_NODE_FRAMEWORKS: dict[str, set[str]] = {
    "web-server": {"express", "fastify", "koa", "hapi", "@nestjs/core", "nest"},
    "frontend": {"react", "vue", "angular", "svelte", "next", "nuxt", "remix", "@angular/core"},
    "cli": {"commander", "yargs", "oclif", "meow"},
}


def _detect_frameworks(dependencies: list[str]) -> list[str]:
    """Detect framework categories from dependency names."""
    deps_lower = {d.lower() for d in dependencies}
    found: list[str] = []
    for fw_type, fw_deps in _NODE_FRAMEWORKS.items():
        if deps_lower & fw_deps:
            found.append(fw_type)
    return found


def _infer_node_role(
    pkg: NodePackage,
    dir_path: str,
    frameworks: list[str],
) -> str:
    """Infer package role: app | service | library | tool | unknown."""
    deps = set(pkg.dependencies or [])
    scripts = set(pkg.scripts.keys() or [])

    # CLI framework or bin entry → tool
    if "cli" in frameworks or pkg.scripts.get("bin") or "bin" in (pkg.scripts or {}):
        return "tool"

    # Web server framework → service
    if "web-server" in frameworks:
        return "service"

    # Frontend framework → app
    if "frontend" in frameworks:
        return "app"

    # Has start/serve scripts but no frontend/server framework → service (generic)
    if scripts & {"start", "serve", "dev"}:
        return "service"

    # Has build/preview scripts, no runtime deps → app (static)
    if scripts & {"build", "preview", "deploy"} and not deps:
        return "app"

    # Has main/module/exports but no runtime framework deps → library
    if pkg.likely_entry_points and not frameworks:
        return "library"

    # Only dev deps + lint/test scripts → tool
    if pkg.dev_dependencies and not pkg.dependencies:
        if scripts and all(s in {"lint", "typecheck", "test", "format", "check", "build"} for s in scripts):
            return "tool"

    # Has runtime deps but ambiguous → unknown
    if pkg.dependencies:
        return "unknown"

    return "unknown"


def _extract_likely_entrypoints(data: dict, dir_path: str) -> list[str]:
    """Extract likely entry points from package.json fields."""
    eps: list[str] = []
    # main / module / types
    for key in ("main", "module", "types"):
        val = data.get(key)
        if val and isinstance(val, str):
            eps.append(f"{dir_path}/{val}" if dir_path != "." else val)
    # exports
    exports = data.get("exports", {})
    if isinstance(exports, dict):
        for exp_key, exp_val in exports.items():
            if isinstance(exp_val, str):
                eps.append(f"{dir_path}/{exp_val}" if dir_path != "." else exp_val)
            elif isinstance(exp_val, dict):
                for sub_val in exp_val.values():
                    if isinstance(sub_val, str):
                        eps.append(f"{dir_path}/{sub_val}" if dir_path != "." else sub_val)
    elif isinstance(exports, str):
        eps.append(f"{dir_path}/{exports}" if dir_path != "." else exports)
    # bin
    bin_data = data.get("bin", {})
    if isinstance(bin_data, dict):
        for bin_name, bin_path in bin_data.items():
            if isinstance(bin_path, str):
                eps.append(f"[bin] {bin_name}: {bin_path}")
    elif isinstance(bin_data, str):
        eps.append(f"[bin] {bin_data}")
    return eps


def _classify_node_package(pkg: NodePackage, dir_path: str) -> PathCategory:
    """Classify a Node package as product, tooling, vendor, or unknown."""
    if is_vendor_path(pkg.rel_path or dir_path):
        return PathCategory.VENDOR

    parts = Path((pkg.rel_path or dir_path).lower()).parts
    if any(p in PRODUCT_SEGMENTS for p in parts):
        return PathCategory.PRODUCT

    if dir_path == ".":
        # Root package: private + only dev deps → tooling
        if pkg.dev_dependencies and not pkg.dependencies:
            return PathCategory.TOOLING
        # Root package with only lint/typecheck scripts → tooling
        if pkg.scripts and not pkg.dependencies:
            if all(s in {"lint", "typecheck", "test", "format", "check"} for s in pkg.scripts):
                return PathCategory.TOOLING

    if pkg.dependencies:
        return PathCategory.PRODUCT

    if pkg.scripts and any(s in PRODUCT_SCRIPT_HINTS for s in pkg.scripts):
        return PathCategory.PRODUCT

    return PathCategory.UNKNOWN


def _find_nearest_pkg_dir(file_dir: str, pkg_dirs: set[str]) -> str | None:
    """Find the nearest package directory that contains the file path."""
    if file_dir in pkg_dirs:
        return file_dir
    parts = Path(file_dir).parts
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i])
        if candidate in pkg_dirs:
            return candidate
    if "." in pkg_dirs:
        return "."
    return None


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
    ev = result.evidence_set
    count = 0
    parser_used = "regex"

    # Discover all package.json files
    pkg_json_map: dict[str, NodePackage] = {}  # dir -> package
    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        if fi.path.name == "package.json" and not is_vendor_path(fi.rel_path):
            text = safe_read_text(fi.path)
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                result.errors.append(f"package.json parse error at {fi.rel_path}: {exc}")
                ev.add(
                    EvidenceKind.ERROR,
                    f"package.json parse error at `{fi.rel_path}`: {exc}",
                    source_path=fi.rel_path,
                    analyzer="node",
                )
                continue
            dir_path = Path(fi.rel_path).parent.as_posix()
            if dir_path == ".":
                dir_path = "."
            deps = list(data.get("dependencies", {}).keys())
            dev_deps = list(data.get("devDependencies", {}).keys())
            peer_deps = list(data.get("peerDependencies", {}).keys())
            pkg = NodePackage(
                name=data.get("name"),
                rel_path=fi.rel_path,
                scripts=data.get("scripts", {}),
                dependencies=deps,
                dev_dependencies=dev_deps,
                peer_dependencies=peer_deps,
                package_type=data.get("type") or "unknown",
                likely_entry_points=_extract_likely_entrypoints(data, dir_path),
            )
            pkg.frameworks = _detect_frameworks(deps + peer_deps)
            pkg.role = _infer_node_role(pkg, dir_path, pkg.frameworks)
            pkg.category = _classify_node_package(pkg, dir_path).value
            pkg_json_map[dir_path] = pkg

    # Discover workspace definitions
    workspaces: list[str] = []
    monorepo_tool: str | None = None
    pnpm_ws = path / "pnpm-workspace.yaml"
    pnpm_text = safe_read_text(pnpm_ws)
    if pnpm_text:
        monorepo_tool = "pnpm"
        for line in pnpm_text.splitlines():
            line = line.strip()
            if line.startswith("- "):
                workspaces.append(line[2:].strip().strip('"').strip("'"))
        if workspaces:
            ev.add(
                EvidenceKind.OBSERVED,
                f"pnpm workspace detected with {len(workspaces)} pattern(s)",
                source_path="pnpm-workspace.yaml",
                analyzer="node",
            )

    # Also read root package.json workspaces field
    root_pkg = pkg_json_map.get(".")
    if root_pkg:
        root_text = safe_read_text(path / "package.json")
        if root_text:
            try:
                root_data = json.loads(root_text)
                pkg_workspaces = root_data.get("workspaces", [])
                if isinstance(pkg_workspaces, list):
                    workspaces.extend(pkg_workspaces)
                elif isinstance(pkg_workspaces, dict):
                    workspaces.extend(pkg_workspaces.get("packages", []))
            except json.JSONDecodeError:
                pass

    # Detect other monorepo tools
    if (path / "turbo.json").exists():
        monorepo_tool = monorepo_tool or "turbo"
        ev.add(EvidenceKind.OBSERVED, "Turbo monorepo detected", source_path="turbo.json", analyzer="node")
    if (path / "nx.json").exists():
        monorepo_tool = monorepo_tool or "nx"
        ev.add(EvidenceKind.OBSERVED, "Nx monorepo detected", source_path="nx.json", analyzer="node")
    if (path / "lerna.json").exists():
        monorepo_tool = monorepo_tool or "lerna"
        ev.add(EvidenceKind.OBSERVED, "Lerna monorepo detected", source_path="lerna.json", analyzer="node")

    result.workspace_packages = sorted(set(workspaces))

    # Build set of package directories for file assignment
    pkg_dirs = set(pkg_json_map.keys())

    # Scan JS/TS files and assign to nearest package
    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        if is_vendor_path(fi.rel_path):
            continue
        name = fi.path.name
        if not name.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
            continue

        count += 1
        file_dir = Path(fi.rel_path).parent.as_posix()
        nearest = _find_nearest_pkg_dir(file_dir, pkg_dirs)
        if nearest is None:
            continue
        pkg = pkg_json_map[nearest]
        pkg.files.append(fi.rel_path)

        # Try tree-sitter first
        parsed = None
        if name.endswith((".ts", ".tsx")):
            parsed = parse_typescript(fi.path)
        else:
            parsed = parse_javascript(fi.path)

        if parsed and parsed.parser_used != "none":
            parser_used = parsed.parser_used
            for imp in parsed.imports:
                pkg.import_edges.append((fi.rel_path, imp))
            for exp in parsed.exports:
                pkg.exports.append(f"{fi.rel_path}:{exp}")
            for cls in parsed.classes:
                pkg.classes.append(f"{fi.rel_path}:{cls}")
            for func in parsed.functions:
                pkg.functions.append(f"{fi.rel_path}:{func}")
        else:
            # Regex fallback
            text = safe_read_text(fi.path, max_bytes=1_000_000)
            if text:
                for m in IMPORT_RE.finditer(text):
                    target = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                    if target:
                        pkg.import_edges.append((fi.rel_path, target))
                for m in NODE_EXPORT_RE.finditer(text):
                    pkg.exports.append(f"{fi.rel_path}:{m.group(1)}")
                for m in NODE_CLASS_RE.finditer(text):
                    pkg.classes.append(f"{fi.rel_path}:{m.group(1)}")
                for m in NODE_FUNC_RE.finditer(text):
                    pkg.functions.append(f"{fi.rel_path}:{m.group(1)}")

    # Compute local package dependencies and build package graph
    local_pkg_names = {p.name for p in pkg_json_map.values() if p.name}
    name_to_pkg: dict[str, NodePackage] = {p.name: p for p in pkg_json_map.values() if p.name}
    for pkg in pkg_json_map.values():
        all_deps = set(pkg.dependencies or []) | set(pkg.peer_dependencies or [])
        pkg.local_deps = sorted(all_deps & local_pkg_names)
        pkg.monorepo_tool = monorepo_tool
        # Build package graph from local deps
        for dep in pkg.local_deps:
            pkg.package_graph.append((pkg.name or pkg.rel_path or "?", dep))
        # Build package graph from internal file imports
        for _file, imp in pkg.import_edges:
            if imp.startswith("."):
                # Relative import → local package
                continue
            first = imp.split("/")[0]
            if first in name_to_pkg and first != pkg.name:
                edge = (pkg.name or pkg.rel_path or "?", first)
                if edge not in pkg.package_graph:
                    pkg.package_graph.append(edge)

    # Finalize packages: deduplicate, sort, drop empty vendor packages
    final_packages: list[NodePackage] = []
    for pkg in pkg_json_map.values():
        pkg.files = sorted(set(pkg.files))
        pkg.import_edges = sorted(set(pkg.import_edges))
        pkg.exports = sorted(set(pkg.exports))
        pkg.classes = sorted(set(pkg.classes))
        pkg.functions = sorted(set(pkg.functions))
        if pkg.category == PathCategory.VENDOR.value and not pkg.files:
            continue
        final_packages.append(pkg)

    # Sort: product > unknown > tooling > vendor; deeper first
    def _pkg_sort_key(pkg: NodePackage) -> tuple[int, int, str]:
        cat_order = {
            PathCategory.PRODUCT.value: 0,
            PathCategory.UNKNOWN.value: 1,
            PathCategory.TOOLING.value: 2,
            PathCategory.VENDOR.value: 3,
        }
        depth = len(Path(pkg.rel_path or ".").parts)
        return (cat_order.get(pkg.category or "unknown", 1), -depth, pkg.rel_path or "")

    final_packages.sort(key=_pkg_sort_key)
    result.node_packages = final_packages
    result.files_scanned += count

    if final_packages:
        total_classes = sum(len(p.classes) for p in final_packages)
        total_funcs = sum(len(p.functions) for p in final_packages)
        total_exports = sum(len(p.exports) for p in final_packages)
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Node symbols via {parser_used}: {total_classes} class(es), {total_funcs} function(s), {total_exports} export(s) across {len(final_packages)} package(s)",
            analyzer="node",
        )
        for pkg in final_packages[:5]:
            cat_label = f" ({pkg.category})" if pkg.category else ""
            role_label = f" [{pkg.role}]" if pkg.role else ""
            fw_label = f" frameworks={pkg.frameworks}" if pkg.frameworks else ""
            ev.add(
                EvidenceKind.OBSERVED,
                f"Node package `{pkg.name or pkg.rel_path}`{cat_label}{role_label}{fw_label}: {len(pkg.files)} file(s), {len(pkg.dependencies)} runtime dep(s)",
                source_path=pkg.rel_path or "package.json",
                analyzer="node",
            )

    # Entry points: per-package filename hits + scripts
    for pkg in final_packages:
        for f in pkg.files:
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
                ev.add(
                    EvidenceKind.INFERRED,
                    f"Likely Node entry point `{f}` inferred from filename",
                    source_path=f,
                    analyzer="node",
                )
        for script_name, cmd in pkg.scripts.items():
            result.likely_entry_points.append(f"[npm script] {script_name}: {cmd}")

    return result


register_analyzer("node", analyze_node)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="node",
        display_name="Node / TypeScript",
        support_level="ast",
        parser="tree-sitter-javascript/typescript",
        detects=["package.json", "tsconfig.json", "*.js", "*.ts", "*.jsx", "*.tsx"],
        limitations=["Regex fallback when tree-sitter is unavailable"],
    )
)
