"""Python-specific analyzer using AST."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from repo_docs_mcp.analyzers import register_analyzer
from repo_docs_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from repo_docs_mcp.models import AnalysisResult, PythonModule, ScanConfig


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


def read_console_scripts(repo_path: Path) -> list[str]:
    """Try to read console_scripts from pyproject.toml."""
    pp = repo_path / "pyproject.toml"
    text = safe_read_text(pp)
    if text is None:
        return []
    try:
        data = tomllib.loads(text)
    except Exception:
        return []
    scripts = data.get("project", {}).get("scripts", {})
    return list(scripts.keys())


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
        if fi.path.name.endswith(".py"):
            count += 1
            mod = analyze_python_file(fi.path, fi.rel_path, path)
            modules.append(mod)

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

    return result


register_analyzer("python", analyze_python)
