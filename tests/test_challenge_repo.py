"""Regression tests against adversarial repo patterns (challenge-repo traps)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.detectors import detect_project
from context_crafter_mcp.analyzers.node import analyze_node
from context_crafter_mcp.analyzers.python import analyze_python


def _make_challenge_like_repo(root: Path) -> None:
    """Create a repo that reproduces key challenge-repo traps."""
    # Trap 1: Root Node manifests are tooling-only
    (root / "package.json").write_text(
        '{"name": "root-tooling", "private": true, "devDependencies": {"eslint": "^9"}}\n'
    )
    (root / "tsconfig.json").write_text('{"compilerOptions": {}}\n')
    (root / "pnpm-workspace.yaml").write_text('packages:\n  - "apps/*/*"\n  - "packages/*"\n')

    # Trap 1b: Real Node product surface deep
    web_pkg = root / "apps" / "dashboard" / "web"
    web_pkg.mkdir(parents=True)
    (web_pkg / "package.json").write_text(
        '{"name": "dashboard-web", "dependencies": {"react": "^18", "express": "^4"}}\n'
    )

    # Trap 2: Large vendor mirror at top of alphabet
    # ~2200 files to exceed detect_project's 2_000 max_files budget
    for sdk in range(1, 6):
        vendor = root / "aa_vendor_mirror" / f"sdk{sdk:03d}"
        vendor.mkdir(parents=True)
        for i in range(1, 221):
            (vendor / f"shim{i}.js").write_text("// vendor\n")
            (vendor / f"shim{i}.ts").write_text("// vendor\n")

    # Trap 3: Real Python entrypoint deep
    py_pkg = root / "services" / "api" / "python" / "src" / "context_api"
    py_pkg.mkdir(parents=True)
    (root / "services" / "api" / "python" / "pyproject.toml").write_text(
        '[project]\nname = "context-api"\ndependencies = ["fastapi>=0.115", "uvicorn>=0.30"]\n\n'
        '[project.scripts]\ncontext-api = "context_api.bootstrap.server:main"\n'
    )
    (py_pkg / "__init__.py").write_text("")
    (py_pkg / "bootstrap").mkdir(parents=True, exist_ok=True)
    (py_pkg / "bootstrap" / "__main__.py").write_text("def main(): pass\n")
    (py_pkg / "bootstrap" / "server.py").write_text("class Server: pass\n")

    # Trap 4: Go workspace
    (root / "go.work").write_text("go 1.23\nuse (./services/worker/go)\n")
    go_pkg = root / "services" / "worker" / "go" / "cmd" / "reconcile"
    go_pkg.mkdir(parents=True)
    (root / "services" / "worker" / "go" / "go.mod").write_text("module worker\ngo 1.23\n")
    (go_pkg / "main.go").write_text("package main\nfunc main() {}\n")

    # Trap 5: Java deep
    java_pkg = root / "java" / "ingest" / "src" / "main" / "java" / "com" / "example" / "ingest"
    java_pkg.mkdir(parents=True)
    (root / "java" / "ingest" / "pom.xml").write_text("<project><artifactId>ingest</artifactId></project>\n")
    (java_pkg / "Main.java").write_text("package com.example.ingest; public class Main {}\n")

    # Trap 6: Rust workspace at root (tooling per challenge)
    (root / "Cargo.toml").write_text('[workspace]\nmembers = ["crates/indexer"]\n')
    rust_pkg = root / "crates" / "indexer" / "src"
    rust_pkg.mkdir(parents=True)
    (rust_pkg / "main.rs").write_text("fn main() {}\n")

    # Trap 7: Pollution dirs that look analyzable
    (root / "examples" / "demo-repo" / "src" / "example_app").mkdir(parents=True)
    (root / "examples" / "demo-repo" / "src" / "example_app" / "main.py").write_text("print(1)\n")
    (root / "tests" / "fixtures" / "mini-python" / "src" / "mini_app").mkdir(parents=True)
    (root / "tests" / "fixtures" / "mini-python" / "src" / "mini_app" / "main.py").write_text("print(1)\n")


def test_detects_python_despite_deep_layout_and_vendor_noise() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        assert result.exists
        assert "python" in result.project_types, f"python missing from {result.project_types}"


def test_detects_java_despite_deep_layout_and_vendor_noise() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        assert "java" in result.project_types


def test_detects_go_via_go_work() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        assert "go" in result.project_types


def test_vendor_mirror_does_not_hide_rust() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        assert "rust" in result.project_types


def test_node_still_detected_from_root_manifests() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        assert "node" in result.project_types


def test_python_api_surface_in_generated_docs() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = analyze_python(str(root))
        # Real Python code should be found
        mod_names = [m.module_name for m in result.python_modules]
        assert "context_api.bootstrap.server" in mod_names or any("server" in m for m in mod_names)
        assert "context_api" in result.source_directories or any("services" in d for d in result.source_directories)


def test_vendor_extensions_do_not_flood_markers() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = detect_project(str(root))
        node_markers = result.markers.get("node", [])
        vendor_in_markers = any("vendor_mirror" in m for m in node_markers)
        assert not vendor_in_markers, f"vendor shims leaked into node markers: {node_markers[:10]}"


def test_node_packages_classified_correctly() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = analyze_node(str(root))
        categories = {p.category for p in result.node_packages}
        assert "tooling" in categories, f"expected tooling package, got {categories}"
        assert "product" in categories, f"expected product package, got {categories}"
        product_pkgs = [p for p in result.node_packages if p.category == "product"]
        assert any("dashboard" in (p.rel_path or "") for p in product_pkgs)


def test_python_deps_extracted_from_deep_pyproject() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = analyze_python(str(root))
        assert "fastapi" in result.python_dependencies, f"expected fastapi in deps, got {result.python_dependencies}"
        assert "uvicorn" in result.python_dependencies, f"expected uvicorn in deps, got {result.python_dependencies}"


def test_workspace_packages_detected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td, "challenge")
        root.mkdir()
        _make_challenge_like_repo(root)
        result = analyze_node(str(root))
        assert any("apps/*/*" in w for w in result.workspace_packages), (
            f"workspace patterns missing: {result.workspace_packages}"
        )
