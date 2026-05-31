"""Source-text injection safety tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from context_crafter_mcp.graph import run_generate_all


def _has_unmatched_backticks(text: str) -> bool:
    """Return True if there are unmatched backticks outside code fences."""
    parts = text.split("```")
    for i, part in enumerate(parts):
        if i % 2 == 1:
            continue  # inside code fence
        if part.count("`") % 2 != 0:
            return True
    return False


def _has_broken_mermaid(text: str) -> bool:
    """Basic structural checks for Mermaid graph blocks."""
    lines = text.splitlines()
    in_mermaid = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            continue
        if stripped == "```" and in_mermaid:
            in_mermaid = False
            continue
        if in_mermaid:
            # Mermaid lines should not contain raw HTML tags
            if "<script>" in stripped or "</script>" in stripped:
                return True
    return False


class TestSourceTextSafety:
    """Inject malicious strings and verify outputs remain safe."""

    def test_malicious_strings_do_not_break_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "README.md").write_text("# Project\n\n`nested backtick` and [link](evil)\n")
            Path(td, "package.json").write_text('{"name": "foo[bar]\\"baz", "version": "1.0.0"}\n')
            Path(td, "bad.py").write_text("# evil\nx = '<script>alert(1)</script>'\n")
            state = run_generate_all(td, "out")
            assert state.ok

            out = Path(td) / "out"
            agent_brief = (out / "AGENT_BRIEF.md").read_text(encoding="utf-8")
            overview = (out / "PROJECT_OVERVIEW.md").read_text(encoding="utf-8")
            dep_graph_md = (out / "DEPENDENCY_GRAPH.md").read_text(encoding="utf-8")

            assert not _has_unmatched_backticks(agent_brief)
            assert not _has_unmatched_backticks(overview)
            assert not _has_broken_mermaid(dep_graph_md)

    @pytest.mark.anyio
    async def test_html_renderer_escapes_angle_brackets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "main.py").write_text("x = '<script>alert(1)</script>'\n")
            from context_crafter_mcp.server import call_tool

            result = await call_tool(
                "generate_project_overview",
                {"repo_path": td, "output_dir": "out", "html": True},
            )
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["ok"] is True
            written = data.get("written", [])
            html_paths = [w for w in written if w.endswith(".html")]
            if html_paths:
                html_text = Path(html_paths[0]).read_text(encoding="utf-8")
                assert "<script>" not in html_text
                assert "&lt;script&gt;" in html_text or "&lt;" in html_text
