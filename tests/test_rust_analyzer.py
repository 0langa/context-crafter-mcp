"""Tests for Rust analyzer."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.analyzers.rust import analyze_rust


def test_rust_basic() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "Cargo.toml").write_text(
            '[package]\nname = "mycrate"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1.0"\n'
        )
        (root / "src" / "main.rs").parent.mkdir(parents=True)
        (root / "src" / "main.rs").write_text('fn main() { println!("hi"); }\n')
        (root / "src" / "lib.rs").write_text("pub fn add(a: i32, b: i32) -> i32 { a + b }\n")
        result = analyze_rust(td)
        assert result.rust_crates
        crate = result.rust_crates[0]
        assert crate.name == "mycrate"
        assert "serde" in crate.dependencies
        assert "src/main.rs" in crate.entry_points
        assert "src/lib.rs" in crate.entry_points
        assert len(crate.modules) == 2
