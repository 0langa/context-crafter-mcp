"""Tests for Go analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.go import analyze_go


def test_go_basic() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "go.mod").write_text(
            "module example.com/foo\n\ngo 1.21\n\nrequire github.com/stretchr/testify v1.8.0\n"
        )
        (root / "main.go").write_text('package main\n\nfunc main() {\n\tprintln("hello")\n}\n')
        (root / "pkg" / "utils.go").parent.mkdir(parents=True)
        (root / "pkg" / "utils.go").write_text(
            'package utils\n\ntype Helper struct{}\n\ntype Stringer interface {\n\tString() string\n}\n\nfunc HelperFunc() string { return "help" }\n'
        )
        result = analyze_go(td)
        assert result.go_modules
        mod = result.go_modules[0]
        assert mod.name == "example.com/foo"
        assert any("github.com/stretchr/testify" in d for d in mod.dependencies)
        assert "main.go" in mod.entry_points
        assert "pkg" in mod.packages or "" in mod.packages
        assert any("Helper" in s for s in mod.structs)
        assert any("Stringer" in i for i in mod.interfaces)
