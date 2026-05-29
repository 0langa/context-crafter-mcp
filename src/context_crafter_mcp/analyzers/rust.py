"""Rust analyzer with tree-sitter AST and regex fallback."""

from __future__ import annotations

import re
import tomllib

from context_crafter_mcp.analyzers import register_analyzer, register_analyzer_spec
from context_crafter_mcp.detectors import _is_fixture_path
from context_crafter_mcp.filesystem import safe_read_text, safe_scan, validate_repo_path
from context_crafter_mcp.models import AnalysisResult, AnalyzerSpec, EvidenceKind, RustCrate, ScanConfig
from context_crafter_mcp.parsers import parse_rust

RUST_MOD_RE = re.compile(r"^\s*mod\s+(\w+);", re.MULTILINE)
RUST_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
RUST_FN_MAIN_RE = re.compile(r"^\s*fn\s+main\s*\(", re.MULTILINE)
RUST_TRAIT_RE = re.compile(r"^\s*(?:pub\s+)?trait\s+(\w+)", re.MULTILINE)
RUST_IMPL_RE = re.compile(r"^\s*impl\s+(?:<[^>]+>\s+)?(?:\w+\s+for\s+)?(\w+)", re.MULTILINE)


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
    ev = result.evidence_set
    crate = RustCrate()
    modules: list[str] = []
    mod_refs: list[str] = []
    count = 0
    parser_used = "regex"

    cargo_toml = path / "Cargo.toml"
    text = safe_read_text(cargo_toml)
    if text:
        try:
            data = tomllib.loads(text)
        except Exception as exc:
            result.errors.append(f"Cargo.toml parse error: {exc}")
            ev.add(
                EvidenceKind.ERROR,
                f"Cargo.toml parse error: {exc}",
                source_path="Cargo.toml",
                analyzer="rust",
            )
            data = {}
        crate.name = data.get("package", {}).get("name")
        if crate.name:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Rust crate `{crate.name}` from `Cargo.toml`",
                source_path="Cargo.toml",
                analyzer="rust",
            )
        deps = data.get("dependencies", {})
        crate.dependencies = list(deps.keys()) if isinstance(deps, dict) else []
        for dep in crate.dependencies:
            ev.add(
                EvidenceKind.OBSERVED,
                f"Rust dependency `{dep}` from `Cargo.toml`",
                source_path="Cargo.toml",
                analyzer="rust",
            )
    else:
        ev.add(
            EvidenceKind.UNKNOWN,
            "No `Cargo.toml` found; Rust crate metadata unavailable.",
            analyzer="rust",
        )

    for fi in safe_scan(path, max_depth=cfg.max_depth + 2, max_files_per_dir=cfg.max_files_per_dir):
        if fi.is_dir:
            continue
        if _is_fixture_path(fi.rel_path):
            continue
        name = fi.path.name
        if name.endswith(".rs"):
            count += 1
            modules.append(fi.rel_path)

            # Try tree-sitter first
            parsed = parse_rust(fi.path)
            if parsed and parsed.parser_used != "none":
                parser_used = parsed.parser_used
                for imp in parsed.imports:
                    crate.dependencies.append(imp)
                for mod_name in parsed.exports:
                    mod_refs.append(f"{fi.rel_path}::mod::{mod_name}")
                for func in parsed.functions:
                    if func == "main":
                        crate.entry_points.append(fi.rel_path)
                if name == "lib.rs":
                    crate.entry_points.append(fi.rel_path)
                for cls in parsed.classes:
                    crate.traits.append(cls)
                for trait in parsed.traits:
                    crate.traits.append(trait)
                for impl in parsed.impls:
                    crate.impls.append(impl)
            else:
                # Regex fallback
                src = safe_read_text(fi.path, max_bytes=500_000)
                if src:
                    if name == "main.rs" or RUST_FN_MAIN_RE.search(src):
                        crate.entry_points.append(fi.rel_path)
                        ev.add(
                            EvidenceKind.OBSERVED,
                            f"Rust entry point `{fi.rel_path}` (`fn main`)",
                            source_path=fi.rel_path,
                            analyzer="rust",
                        )
                    if name == "lib.rs":
                        crate.entry_points.append(fi.rel_path)
                        ev.add(
                            EvidenceKind.OBSERVED,
                            f"Rust library root `{fi.rel_path}`",
                            source_path=fi.rel_path,
                            analyzer="rust",
                        )
                    for m in RUST_MOD_RE.finditer(src):
                        mod_refs.append(f"{fi.rel_path}::mod::{m.group(1)}")
                    for m in RUST_USE_RE.finditer(src):
                        use_path = m.group(1).split("::")[0].strip()
                        if use_path not in ("std", "core", "alloc", "crate", "self", "super"):
                            crate.dependencies.append(use_path)
                    for m in RUST_TRAIT_RE.finditer(src):
                        crate.traits.append(m.group(1))
                    for m in RUST_IMPL_RE.finditer(src):
                        crate.impls.append(m.group(1))

    crate.modules = sorted(set(modules + mod_refs))
    crate.dependencies = sorted(set(crate.dependencies))
    crate.traits = sorted(set(crate.traits))
    crate.impls = sorted(set(crate.impls))
    result.rust_crates = [crate]
    result.files_scanned += count

    if crate.traits or crate.impls:
        ev.add(
            EvidenceKind.OBSERVED if parser_used != "regex" else EvidenceKind.INFERRED,
            f"Rust symbols via {parser_used}: {len(crate.traits)} trait(s), {len(crate.impls)} impl(s)",
            analyzer="rust",
        )

    return result


register_analyzer("rust", analyze_rust)
register_analyzer_spec(
    AnalyzerSpec(
        project_type="rust",
        display_name="Rust",
        support_level="ast",
        parser="tree-sitter-rust",
        detects=["Cargo.toml", "*.rs"],
        limitations=["Regex fallback when tree-sitter-rust is unavailable"],
    )
)
