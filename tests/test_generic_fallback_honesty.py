"""Regression tests for honest generic fallback behavior."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_detect, run_generate_all
from context_crafter_mcp.models import ScanConfig


def _write(path: Path, text: str = "placeholder\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_plain_generic_repo_detects_only_generic() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "README.md", "# Notes\n")
        _write(root / "docs" / "overview.md", "Architecture notes.\n")
        _write(root / "data" / "sample.txt", "non-code data\n")

        result = run_detect(str(root))

        assert result.exists
        assert result.project_types == ["generic"]
        assert result.evidence == {"generic": "observed"}


def test_low_trust_language_files_do_not_promote_stacks() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "README.md", "# Ambiguous\n")
        _write(root / "docs" / "guide.py", "print('doc sample')\n")
        _write(root / "tests" / "test_example.py", "def test_example(): pass\n")
        _write(root / "examples" / "snippet" / "index.js", "console.log('example')\n")
        _write(root / "tools" / "package.json", '{"name":"repo-tools"}\n')
        _write(root / "tools" / "build.ts", "export const build = true;\n")

        result = run_detect(str(root))

        assert result.project_types == ["generic"]
        assert result.markers["python"] == []
        assert result.markers["node"] == []
        warnings = result.to_dict()["warnings"]
        assert any("python: only low-trust" in warning for warning in warnings)
        assert any("node: only low-trust" in warning for warning in warnings)


def test_product_surface_markers_still_promote_real_mixed_repo() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "README.md", "# Mixed\n")
        _write(root / "services" / "api" / "pyproject.toml", "[project]\nname = 'api'\n")
        _write(root / "services" / "api" / "src" / "api" / "main.py", "def main(): pass\n")
        _write(root / "web" / "package.json", '{"name":"web","dependencies":{"react":"^18"}}\n')
        _write(root / "web" / "src" / "index.ts", "export const app = true;\n")
        _write(root / "docs" / "old_app.py", "print('historical sample')\n")

        result = run_detect(str(root))

        assert result.project_types == ["generic", "node", "python"]
        assert any(path.startswith("services/api/") for path in result.markers["python"])
        assert any(path.startswith("web/") for path in result.markers["node"])
        assert all("docs/" not in path for paths in result.markers.values() for path in paths)


def test_generated_docs_stay_generic_for_low_trust_language_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "README.md", "# Ambiguous\n")
        _write(root / "docs" / "guide.py", "print('doc sample')\n")
        _write(root / "tests" / "test_example.py", "def test_example(): pass\n")
        _write(root / "tools" / "build.ts", "export const build = true;\n")

        state = run_generate_all(str(root), "out")
        out = Path(state.resolved_output_dir or root / "out")

        assert state.ok
        overview = (out / "PROJECT_OVERVIEW.md").read_text(encoding="utf-8")
        agent_brief = (out / "AGENT_BRIEF.md").read_text(encoding="utf-8")
        run_state = json.loads((out / "RUN_STATE.json").read_text(encoding="utf-8"))

        assert "- **Detected types**: generic" in overview
        assert "- **Types**: generic" in agent_brief
        assert "docs/guide.py" not in agent_brief
        assert "tests/test_example.py" not in agent_brief
        assert "tools/build.ts" not in agent_brief
        assert run_state["project_types"] == ["generic"]
        assert run_state["analyzers_run"] == ["generic"]


def test_bounded_noisy_generic_repo_discloses_scan_bounds_without_stack_promotion() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root / "README.md", "# Bounded ambiguous\n")
        for idx in range(12):
            _write(root / "docs" / f"sample_{idx:02d}.py", f"print({idx})\n")
            _write(root / "docs" / f"sample_{idx:02d}.js", f"console.log({idx})\n")

        state = run_generate_all(str(root), "out", ScanConfig(max_depth=4, max_files_per_dir=2))
        out = Path(state.resolved_output_dir or root / "out")
        scan_report = (out / "SCAN_REPORT.md").read_text(encoding="utf-8")
        run_state = json.loads((out / "RUN_STATE.json").read_text(encoding="utf-8"))

        assert state.ok
        assert state.detect_result is not None
        assert state.detect_result.project_types == ["generic"]
        assert "- generic" in scan_report
        assert "- Skipped (`max_files_per_dir`):" in scan_report
        assert run_state["project_types"] == ["generic"]
        assert run_state["validation_summary"]["bounded_scan"] is True
