"""Tests for VALIDATION_REPORT.md correctness."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all


def test_validation_report_does_not_list_itself_as_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        state = run_generate_all(td, "out")
        assert state.ok
        val_path = Path(td, "out", "VALIDATION_REPORT.md")
        assert val_path.exists()
        content = val_path.read_text()
        assert (
            "VALIDATION_REPORT.md" not in content
            or "Missing" not in content.split("VALIDATION_REPORT.md")[0].split("## Output Files")[-1]
        )
        # More robust: the Missing section should say _None._
        assert "_None._" in content or "Missing" not in content
