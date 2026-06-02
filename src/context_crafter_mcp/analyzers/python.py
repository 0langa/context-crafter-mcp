"""Python-specific analyzer using AST."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path
from typing import Any

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.analyzers.snapshot_utils import get_analysis_snapshot, iter_snapshot_files
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, PythonModule, ScanConfig
from context_crafter_mcp.scanner import RepoSnapshot


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
            except (ValueError, TypeError):
                continue
            if "__name__" in test_src and '"__main__"' in test_src:
                mod.is_entry_point = True
                break

    if not mod.is_entry_point:
        base = Path(rel_path).name
        if base in {"main.py", "app.py", "cli.py", "server.py", "manage.py"}:
            mod.is_entry_point = True

    return mod


def _discover_package_roots(
    modules: list[PythonModule], repo_path: Path, snapshot: RepoSnapshot | None = None
) -> set[str]:
    """Discover internal package roots from scanned modules and repo layout."""
    roots: set[str] = set()

    if snapshot is not None:
        top_level_with_py: set[str] = set()
        source_layout_with_py: set[str] = set()
        for sf in snapshot.files:
            if _is_fixture_path(sf.rel_path) or not sf.rel_path.endswith(".py"):
                continue
            parts = Path(sf.rel_path).parts
            if len(parts) > 1:
                top_level_with_py.add(parts[0])
            if len(parts) > 2 and parts[0] in ("src", "lib", "source", "sources"):
                source_layout_with_py.add(parts[1])
        roots.update(top_level_with_py)
        roots.update(source_layout_with_py)
    else:
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


def _read_pyproject_at(pp: Path) -> dict[str, Any]:
    """Read and parse a specific pyproject.toml path."""
    text = safe_read_text(pp)
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def _read_pyproject(repo_path: Path) -> dict[str, Any]:
    """Read and parse pyproject.toml if it exists at repo root."""
    return _read_pyproject_at(repo_path / "pyproject.toml")


def read_console_scripts(pyproject_path: Path) -> list[str]:
    """Try to read console_scripts from a pyproject.toml path."""
    data = _read_pyproject_at(pyproject_path)
    scripts = data.get("project", {}).get("scripts", {})
    return list(scripts.keys())


def _read_requirements_txt(repo_path: Path) -> list[str]:
    """Read requirements.txt and return package names."""
    path = repo_path / "requirements.txt"
    text = safe_read_text(path)
    if text is None:
        return []
    deps: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Skip pip options and references
        if line.startswith("-"):
            continue
        # Strip inline comments
        if " #" in line:
            line = line.split(" #")[0].strip()
        # Extract package name (first token before version specs, extras, markers)
        name = line.split(";")[0].strip()
        name = name.split("[")[0].strip()
        # Split on common version operators
        for op in ("==", ">=", "<=", ">", "<", "!=", "~=", "===", "@"):
            if op in name:
                name = name.split(op)[0].strip()
                break
        if name and not name.startswith("-"):
            deps.append(name)
    return deps


def _read_setup_py(repo_path: Path) -> tuple[list[str], list[str], str | None]:
    """Read setup.py and extract install_requires and extras_require.

    Returns (runtime_deps, dev_deps, error_message).
    File read is capped at 500 KB to avoid regex hangs on huge files.
    """
    path = repo_path / "setup.py"
    text = safe_read_text(path, max_bytes=500_000)
    if text is None:
        return [], [], None
    deps: list[str] = []
    dev_deps: list[str] = []

    # install_requires=["pkg>=1.0", "pkg2", ...]
    import re as _re

    try:
        install_match = _re.search(
            r"install_requires\s*=\s*(?:\(|\[)(.*?)(?:\)|\])",
            text,
            _re.DOTALL,
        )
        if install_match:
            block = install_match.group(1)
            for m in _re.finditer(r'["\']([^"\']+)["\']', block):
                dep = m.group(1).split(";")[0].split("[")[0].strip()
                for op in ("==", ">=", "<=", ">", "<", "!=", "~=", "===", "@"):
                    if op in dep:
                        dep = dep.split(op)[0].strip()
                        break
                if dep:
                    deps.append(dep)

        # extras_require={"dev": ["pkg>=1.0", ...], ...}
        extras_match = _re.search(
            r"extras_require\s*=\s*\{(.*?)\}",
            text,
            _re.DOTALL,
        )
        if extras_match:
            block = extras_match.group(1)
            # Extract each list inside the dict
            for list_match in _re.finditer(r'["\'](\w+)["\']\s*:\s*(?:\(|\[)(.*?)(?:\)|\])', block, _re.DOTALL):
                group_name = list_match.group(1).lower()
                list_block = list_match.group(2)
                is_dev = group_name in ("dev", "test", "lint", "docs", "typing")
                for m in _re.finditer(r'["\']([^"\']+)["\']', list_block):
                    dep = m.group(1).split(";")[0].split("[")[0].strip()
                    for op in ("==", ">=", "<=", ">", "<", "!=", "~=", "===", "@"):
                        if op in dep:
                            dep = dep.split(op)[0].strip()
                            break
                    if dep:
                        if is_dev:
                            dev_deps.append(dep)
                        else:
                            deps.append(dep)
    except (OSError, ValueError, _re.error) as exc:
        return [], [], f"setup.py regex extraction failed: {exc}"

    return deps, dev_deps, None


def _read_pipfile(repo_path: Path) -> tuple[list[str], list[str], str | None]:
    """Read Pipfile and return runtime and dev package names.

    Returns (runtime_deps, dev_deps, error_message).
    """
    path = repo_path / "Pipfile"
    text = safe_read_text(path)
    if text is None:
        return [], [], None
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return [], [], f"Pipfile parse error: {exc}"
    deps: list[str] = []
    dev_deps: list[str] = []
    packages = data.get("packages", {})
    dev_packages = data.get("dev-packages", {})
    for pkg in packages:
        if isinstance(pkg, str):
            deps.append(pkg)
    for pkg in dev_packages:
        if isinstance(pkg, str):
            dev_deps.append(pkg)
    return deps, dev_deps, None


def extract_python_dependencies(base_path: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    """Extract runtime and dev dependencies from pyproject.toml, requirements.txt, setup.py, and Pipfile.

    Looks in *base_path* (e.g. repo root or a subproject directory).
    Returns (runtime_deps, dev_deps, sources, errors).
    """
    data = _read_pyproject_at(base_path / "pyproject.toml")
    deps: list[str] = []
    dev_deps: list[str] = []
    sources: list[str] = []
    errors: list[str] = []

    def _strip_version(name: str) -> str:
        for op in ("==", ">=", "<=", ">", "<", "!=", "~=", "===", "@"):
            if op in name:
                name = name.split(op)[0].strip()
                break
        return name

    # PEP 621 standard dependencies
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        # Strip version specifiers for cleaner output
        name = dep.split("[")[0].split(";")[0].strip()
        name = _strip_version(name)
        if name:
            deps.append(name)

    # Optional dependency groups
    optional = project.get("optional-dependencies", {})
    for group_name, group_deps in optional.items():
        is_dev = group_name.lower() in ("dev", "test", "lint", "docs", "typing")
        for dep in group_deps:
            name = dep.split("[")[0].split(";")[0].strip()
            name = _strip_version(name)
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

    if deps or dev_deps:
        sources.append("pyproject.toml")

    # requirements.txt
    req_deps = _read_requirements_txt(base_path)
    if req_deps:
        deps.extend(req_deps)
        sources.append("requirements.txt")

    # setup.py
    setup_deps, setup_dev_deps, setup_err = _read_setup_py(base_path)
    if setup_err:
        errors.append(setup_err)
    if setup_deps or setup_dev_deps:
        deps.extend(setup_deps)
        dev_deps.extend(setup_dev_deps)
        sources.append("setup.py")

    # Pipfile
    pip_deps, pip_dev_deps, pip_err = _read_pipfile(base_path)
    if pip_err:
        errors.append(pip_err)
    if pip_deps or pip_dev_deps:
        deps.extend(pip_deps)
        dev_deps.extend(pip_dev_deps)
        sources.append("Pipfile")

    return sorted(set(deps)), sorted(set(dev_deps)), sources, errors


def extract_project_metadata(base_path: Path) -> dict[str, Any]:
    """Extract project metadata from pyproject.toml in base_path."""
    data = _read_pyproject_at(base_path / "pyproject.toml")
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
    snapshot = get_analysis_snapshot(path, result, cfg)
    ev = result.evidence_set
    modules: list[PythonModule] = []
    count = 0

    for sf, file_path in iter_snapshot_files(snapshot):
        if _is_fixture_path(sf.rel_path):
            continue
        if file_path.name.endswith(".py"):
            count += 1
            mod = analyze_python_file(file_path, sf.rel_path, path)
            modules.append(mod)
            if mod.parse_error:
                ev.add(
                    EvidenceKind.ERROR,
                    f"Python parse error in `{mod.rel_path}`: {mod.parse_error}",
                    source_path=mod.rel_path,
                    analyzer="python",
                )
            else:
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Python module `{mod.rel_path}`: {len(mod.classes)} class(es), {len(mod.functions)} function(s), {len(mod.imports)} import(s)",
                    source_path=mod.rel_path,
                    analyzer="python",
                )

    # Discover package roots and re-classify imports
    package_roots = _discover_package_roots(modules, path, snapshot)
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
    result.analyzer_files_parsed += count

    # Discover the best pyproject.toml for metadata / deps / console scripts
    from context_crafter_mcp.ranking import score_path

    best_pyproject: Path | None = None
    best_score = -999.0
    for sf, file_path in iter_snapshot_files(snapshot):
        if _is_fixture_path(sf.rel_path):
            continue
        if file_path.name == "pyproject.toml":
            sc = score_path(sf.rel_path, has_marker=True)
            if sc > best_score:
                best_score = sc
                best_pyproject = file_path

    pyproject_dir = best_pyproject.parent if best_pyproject else path
    pyproject_rel = str(best_pyproject.relative_to(path)) if best_pyproject else "pyproject.toml"

    # Add console scripts as likely entry points
    if best_pyproject:
        scripts = read_console_scripts(best_pyproject)
    else:
        scripts = []
    for s in scripts:
        result.likely_entry_points.append(f"[console_script] {s}")
        ev.add(
            EvidenceKind.OBSERVED,
            f"Console script `{s}` declared in `{pyproject_rel}`",
            source_path=pyproject_rel,
            analyzer="python",
        )

    # Update source dirs from modules
    src_dirs: set[str] = set()
    for m in modules:
        p = Path(m.rel_path)
        if len(p.parts) > 1:
            src_dirs.add(p.parts[0])
    if src_dirs:
        result.source_directories = sorted(set(result.source_directories) | src_dirs)

    # Extract project metadata and dependencies from the best pyproject.toml
    meta_dict = extract_project_metadata(pyproject_dir)
    for key, value in meta_dict.items():
        if value is not None and hasattr(result.metadata, key):
            setattr(result.metadata, key, value)
            if key in ("name", "version", "description"):
                ev.add(
                    EvidenceKind.OBSERVED,
                    f"Project {key} `{value}` from `{pyproject_rel}`",
                    source_path=pyproject_rel,
                    analyzer="python",
                )

    deps, dev_deps, dep_sources, dep_errors = extract_python_dependencies(pyproject_dir)
    result.python_dependencies = deps
    result.python_dev_dependencies = dev_deps
    for dep in deps:
        ev.add(
            EvidenceKind.OBSERVED,
            f"Python runtime dependency `{dep}`",
            analyzer="python",
        )
    for dep in dev_deps:
        ev.add(
            EvidenceKind.OBSERVED,
            f"Python dev dependency `{dep}`",
            analyzer="python",
        )
    for src in dep_sources:
        ev.add(
            EvidenceKind.OBSERVED,
            f"Python dependency source `{src}` detected",
            source_path=src,
            analyzer="python",
        )
    for err in dep_errors:
        ev.add(
            EvidenceKind.ERROR,
            err,
            analyzer="python",
        )

    # Entry points inferred from filenames
    for mod in modules:
        if mod.is_entry_point and not any(mod.rel_path == ep for ep in result.likely_entry_points):
            result.likely_entry_points.append(mod.rel_path)
            ev.add(
                EvidenceKind.INFERRED,
                f"Likely entry point `{mod.rel_path}` inferred from filename or `__main__` guard",
                source_path=mod.rel_path,
                analyzer="python",
            )

    ev.add(
        EvidenceKind.UNSUPPORTED,
        "Deep semantic call graph and dynamic import analysis are not implemented.",
        analyzer="python",
    )

    return result


register_analyzer("python", analyze_python)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="python",
        display_name="Python",
        support_level="ast",
        parser="stdlib_ast + toml",
        detects=["pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "*.py"],
        limitations=["Deep semantic call graph not implemented", "Dynamic imports not resolved"],
    )
)
