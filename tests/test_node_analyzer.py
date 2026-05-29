"""Tests for Node analyzer features."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.node import analyze_node


def test_node_scripts_and_deps() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "package.json").write_text(
            '{"name":"myapp","scripts":{"build":"tsc","test":"jest"},'
            '"dependencies":{"react":"^18.0"},'
            '"devDependencies":{"jest":"^29.0"}}\n'
        )
        (root / "index.js").write_text(
            "const react = require('react');\n"
            "export class App { constructor() {} }\n"
            "export default function main() { return 1; }\n"
        )
        (root / "app.ts").write_text("import express from 'express';\nexport const PORT = 3000;\n")
        result = analyze_node(td)
        assert result.node_packages
        pkg = result.node_packages[0]
        assert pkg.name == "myapp"
        assert "build" in pkg.scripts
        assert "react" in pkg.dependencies
        assert "jest" in pkg.dev_dependencies
        assert len(pkg.import_edges) == 2
        assert any("express" in target for _, target in pkg.import_edges)
        assert any("App" in c for c in pkg.classes)
        assert any("main" in f for f in pkg.functions)
        assert any("PORT" in e for e in pkg.exports)


def test_node_parse_error_collected() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "package.json").write_text("not valid json {\n")
        (root / "index.js").write_text("console.log(1);\n")
        result = analyze_node(td)
        assert any("package.json parse error" in err for err in result.errors)
