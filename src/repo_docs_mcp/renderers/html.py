"""Optional HTML renderer wrapping Markdown output."""

from __future__ import annotations

from pathlib import Path

from repo_docs_mcp.filesystem import safe_output_path
from repo_docs_mcp.models import AnalysisResult, DetectResult, RenderResult


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _markdown_to_html(markdown_text: str) -> str:
    """Very lightweight markdown-to-html conversion using stdlib only."""
    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    in_code = False
    code_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("<pre><code>" + _escape_html("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        # HTML comments pass through
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            html_lines.append(stripped)
            continue

        # Headings
        if stripped.startswith("# "):
            text = stripped[2:]
            html_lines.append(f"<h1>{_escape_html(text)}</h1>")
        elif stripped.startswith("## "):
            text = stripped[3:]
            html_lines.append(f"<h2>{_escape_html(text)}</h2>")
        elif stripped.startswith("### "):
            text = stripped[4:]
            html_lines.append(f"<h3>{_escape_html(text)}</h3>")
        elif stripped.startswith("#### "):
            text = stripped[5:]
            html_lines.append(f"<h4>{_escape_html(text)}</h4>")
        # Bullet lists
        elif stripped.startswith("- "):
            text = stripped[2:]
            html_lines.append(f"<li>{_escape_html(text)}</li>")
        # Empty line
        elif not stripped:
            html_lines.append("<br/>")
        # Plain text
        else:
            html_lines.append(f"<p>{_escape_html(line)}</p>")

    return "\n".join(html_lines)


def render_html_overview(
    repo_path: str,
    detect: DetectResult,
    analysis: AnalysisResult,
    output_dir: str,
) -> RenderResult:
    """Generate a simple HTML report from the Markdown content."""
    from repo_docs_mcp.renderers.markdown import render_project_overview

    md_result = render_project_overview(repo_path, detect, analysis, output_dir)
    if not md_result.ok or not md_result.written:
        return RenderResult(ok=False, error="Markdown generation failed")

    md_path = Path(md_result.written[0])
    md_text = md_path.read_text(encoding="utf-8")
    html_body = _markdown_to_html(md_text)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Project Overview: {Path(repo_path).resolve().name}</title>
<style>
body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
h1, h2, h3, h4 {{ color: #111; }}
pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 4px; }}
li {{ margin: 0.25rem 0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

    out = safe_output_path(Path(repo_path), output_dir)
    html_path = out / "PROJECT_OVERVIEW.html"
    html_path.write_text(html, encoding="utf-8")
    return RenderResult(
        ok=True,
        written=[str(html_path)],
        files_scanned=analysis.files_scanned,
        project_types=detect.project_types,
    )
