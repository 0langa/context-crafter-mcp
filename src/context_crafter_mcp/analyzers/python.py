"""Python-specific analyzer using AST."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path
from typing import Any

from context_crafter_mcp.analyzers import register_analyzer
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, PythonModule, ScanConfig


def guess_module_name(rel_path: str) -> str:
    """Guess dotted module name from relative path."""
    parts = list(Path(rel_path).parts)
    if parts[-1].endswith(".py"):
        parts = parts[:-1] + [parts[-1][:-3]]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def analyze_python_file(path: Path, rel_path: str, repo_path: Path) -> PythonModule:
    """Parse a single Python file."""
    mod = PythonModule(
        rel_path=rel_path,
        module_name=guess_module_name(rel_path),
    )
    text = safe_read_text(path)
    if text is None:
        mod.parse_error = "Could not read file"
        return mod

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        mod.parse_error = str(exc)
        return mod

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module or ""
            mod.imports.append(mod_name)
        elif isinstance(node, ast.ClassDef):
            mod.classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            mod.functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            mod.async_functions.append(node.name)

    # Guess internal imports
    for imp in mod.imports:
        first = imp.split(".")[0]
        candidate = repo_path / first
        if candidate.exists() and candidate.is_dir():
            mod.internal_imports.append(imp)

    # Entry point detection
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            try:
                test_src = ast.unparse(node.test)
            except Exception:
                continue
            if "__name__" in test_src and '"__main__"' in test_src:
                mod.is_entry_point = True
                break

    if not mod.is_entry_point:
        base = Path(rel_path).name
        if base in {"main.py", "app.py", "cli.py", "server.py", "manage.py"}:
            mod.is_entry_point = True

    return mod


def _discover_package_roots(modules: list[PythonModule], repo_path: Path) -> set[str]:
    """Discover internal package roots from scanned modules and repo layout."""
    roots: set[str] = set()

    # Direct top-level directories that contain Python files
    for item in repo_path.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            if _is_fixture_path(item.relative_to(repo_path).as_posix()):
                continue
            has_py = any(
                f.suffix == ".py"
                for f in item.rglob("*")
                if f.is_file() and not _is_fixture_path(f.relative_to(repo_path).as_posix())
            )
            if has_py:
                roots.add(item.name)

    # Common source layout: src/<pkg>, lib/<pkg>, etc.
    for src_name in ("src", "lib", "source", "sources"):
        src_dir = repo_path / src_name
        if src_dir.is_dir():
            for item in src_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    if _is_fixture_path(item.relative_to(repo_path).as_posix()):
                        continue
                    has_py = any(
                        f.suffix == ".py"
                        for f in item.rglob("*")
                        if f.is_file() and not _is_fixture_path(f.relative_to(repo_path).as_posix())
                    )
                    if has_py:
                        roots.add(item.name)

    # Also collect first segments from module paths (for packages at repo root)
    for mod in modules:
        parts = Path(mod.rel_path).parts
        if len(parts) > 1:
            roots.add(parts[0])

    return roots


def _read_pyproject(repo_path: Path) -> dict[str, Any]:
    """Read and parse pyproject.toml if it exists."""
    pp = repo_path / "pyproject.toml"
    text = safe_read_text(pp)
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except Exception:
        return {}


def read_console_scripts(repo_path: Path) -> list[str]:
    """Try to read console_scripts from pyproject.toml."""
    data = _read_pyproject(repo_path)
    scripts = data.get("project", {}).get("scripts", {})
    return list(scripts.keys())


def extract_python_dependencies(repo_path: Path) -> tuple[list[str], list[str]]:
    """Extract runtime and dev dependencies from pyproject.toml."""
    data = _read_pyproject(repo_path)
    deps: list[str] = []
    dev_deps: list[str] = []

    # PEP 621 standard dependencies
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        # Strip version specifiers for cleaner output
        name = dep.split("[")[0].split(";")[0].strip()
        if name:
            deps.append(name)

    # Optional dependency groups
    optional = project.get("optional-dependencies", {})
    for group_name, group_deps in optional.items():
        is_dev = group_name.lower() in ("dev", "test", "lint", "docs", "typing")
        for dep in group_deps:
            name = dep.split("[")[0].split(";")[0].strip()
            if name:
                if is_dev:
                    dev_deps.append(name)
                else:
                    deps.append(name)

    # Poetry dependencies
    poetry = data.get("tool", {}).get("poetry", {})
    for dep in poetry.get("dependencies", {}):
        if dep != "python":
            deps.append(dep)
    for dep in poetry.get("dev-dependencies", {}):
        dev_deps.append(dep)
    for group in poetry.get("group", {}).values():
        for dep in group.get("dependencies", {}):
            dev_deps.append(dep)

    # UV / Hatch / PDM dependency groups
    dep_groups = data.get("dependency-groups", {})
    for group_name, group_deps in dep_groups.items():
        for dep in group_deps:
            if isinstance(dep, str):
                name = dep.split("[")[0].split(";")[0].strip()
                if name:
                    if group_name in ("dev", "test", "lint", "docs"):
                        dev_deps.append(name)
                    else:
                        deps.append(name)
            elif isinstance(dep, dict) and "include-group" in dep:
                pass  # skip include-group references for now

    return sorted(set(deps)), sorted(set(dev_deps))


def extract_project_metadata(repo_path: Path) -> dict[str, Any]:
    """Extract project metadata from pyproject.toml."""
    data = _read_pyproject(repo_path)
    project = data.get("project", {})
    poetry = data.get("tool", {}).get("poetry", {})

    metadata: dict[str, Any] = {}

    # PEP 621 fields
    metadata["name"] = project.get("name")
    metadata["description"] = project.get("description")
    metadata["version"] = project.get("version")
    metadata["license"] = (
        project.get("license", {}).get("text") if isinstance(project.get("license"), dict) else project.get("license")
    )
    metadata["keywords"] = project.get("keywords", [])

    authors = project.get("authors", [])
    metadata["authors"] = [a.get("name", a) if isinstance(a, dict) else a for a in authors]

    urls = project.get("urls", {})
    metadata["homepage"] = urls.get("homepage")
    metadata["repository"] = urls.get("repository") or urls.get("source")

    # Poetry fallback
    if not metadata["name"]:
        metadata["name"] = poetry.get("name")
    if not metadata["description"]:
        metadata["description"] = poetry.get("description")
    if not metadata["version"]:
        metadata["version"] = poetry.get("version")

    return metadata


def analyze_python(
    repo_path: str,
    base_result: AnalysisResult | None = None,
    config: ScanConfig | None = None,
) -> AnalysisResult:
    """Analyze Python files in the repository."""
    path = validate_repo_path(repo_path)
    if path is None:
        result = base_result or AnalysisResult(repo_path=repo_path)
        result.errors.append(f"Invalid repo_path: {repo_path}")
        return result

    cfg = config or ScanConfig()
    result = base_result or AnalysisResult(repo_path=str(path))
    modules: list[PythonModule] = []
    count = 0

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        if fi.path.name.endswith(".py"):
            count += 1
            mod = analyze_python_file(fi.path, fi.rel_path, path)
            modules.append(mod)

    # Discover package roots and re-classify imports
    package_roots = _discover_package_roots(modules, path)
    for mod in modules:
        internal: list[str] = []
        external: list[str] = []
        for imp in mod.imports:
            first = imp.split(".")[0]
            if first in package_roots:
                internal.append(imp)
            else:
                external.append(imp)
        mod.internal_imports = internal

    result.python_modules = modules
    result.files_scanned += count

    # Add console scripts as likely entry points
    scripts = read_console_scripts(path)
    for s in scripts:
        result.likely_entry_points.append(f"[console_script] {s}")

    # Update source dirs from modules
    src_dirs: set[str] = set()
    for m in modules:
        p = Path(m.rel_path)
        if len(p.parts) > 1:
            src_dirs.add(p.parts[0])
    if src_dirs:
        result.source_directories = sorted(set(result.source_directories) | src_dirs)

    # Extract project metadata and dependencies from pyproject.toml
    meta_dict = extract_project_metadata(path)
    for key, value in meta_dict.items():
        if value is not None and hasattr(result.metadata, key):
            setattr(result.metadata, key, value)

    deps, dev_deps = extract_python_dependencies(path)
    result.python_dependencies = deps
    result.python_dev_dependencies = dev_deps

    return result


register_analyzer("python", analyze_python)
