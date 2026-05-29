"""HTML renderer using markdown library with stdlib fallback."""

from __future__ import annotations

from pathlib import Path

from context_crafter_mcp.filesystem import safe_output_path
from context_crafter_mcp.models import AnalysisResult, DetectResult, RenderResult


def _markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to HTML using the `markdown` library, with stdlib fallback."""
    try:
        import markdown  # type: ignore[import-untyped]

        return str(
            markdown.markdown(
                markdown_text,
                extensions=["tables", "fenced_code", "toc"],
            )
        )
    except Exception:
        return _stdlib_markdown_to_html(markdown_text)


def _stdlib_markdown_to_html(markdown_text: str) -> str:
    """Lightweight markdown-to-html conversion using stdlib only."""
    import re

    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    in_code = False
    code_lines: list[str] = []
    in_ul = False
    in_ol = False
    in_paragraph = False

    _MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
    _MD_ITALIC_RE = re.compile(r"\*(.+?)\*|_(.+?)_")
    _MD_CODE_RE = re.compile(r"`(.+?)`")
    _MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def _escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _inline_md_to_html(text: str) -> str:
        text = _MD_CODE_RE.sub(lambda m: f"<code>{_escape_html(m.group(1))}</code>", text)
        text = _MD_BOLD_RE.sub(lambda m: f"<strong>{_escape_html(m.group(1) or m.group(2))}</strong>", text)
        text = _MD_ITALIC_RE.sub(lambda m: f"<em>{_escape_html(m.group(1) or m.group(2))}</em>", text)
        text = _MD_LINK_RE.sub(lambda m: f'<a href="{_escape_html(m.group(2))}">{_escape_html(m.group(1))}</a>', text)
        return text

    def _close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False
        if in_ol:
            html_lines.append("</ol>")
            in_ol = False

    def _close_paragraph() -> None:
        nonlocal in_paragraph
        if in_paragraph:
            html_lines.append("</p>")
            in_paragraph = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            _close_lists()
            _close_paragraph()
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

        if stripped.startswith("<!--") and stripped.endswith("-->"):
            html_lines.append(stripped)
            continue

        if stripped in ("---", "***", "___"):
            _close_lists()
            _close_paragraph()
            html_lines.append("<hr/>")
            continue

        if stripped.startswith("# "):
            _close_lists()
            _close_paragraph()
            html_lines.append(f"<h1>{_inline_md_to_html(_escape_html(stripped[2:]))}</h1>")
            continue
        if stripped.startswith("## "):
            _close_lists()
            _close_paragraph()
            html_lines.append(f"<h2>{_inline_md_to_html(_escape_html(stripped[3:]))}</h2>")
            continue
        if stripped.startswith("### "):
            _close_lists()
            _close_paragraph()
            html_lines.append(f"<h3>{_inline_md_to_html(_escape_html(stripped[4:]))}</h3>")
            continue
        if stripped.startswith("#### "):
            _close_lists()
            _close_paragraph()
            html_lines.append(f"<h4>{_inline_md_to_html(_escape_html(stripped[5:]))}</h4>")
            continue

        if stripped.startswith("> "):
            _close_lists()
            _close_paragraph()
            html_lines.append(f"<blockquote>{_inline_md_to_html(_escape_html(stripped[2:]))}</blockquote>")
            continue

        if stripped.startswith("- "):
            _close_paragraph()
            if not in_ul:
                if in_ol:
                    html_lines.append("</ol>")
                    in_ol = False
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{_inline_md_to_html(_escape_html(stripped[2:]))}</li>")
            continue

        num_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if num_match:
            _close_paragraph()
            if not in_ol:
                if in_ul:
                    html_lines.append("</ul>")
                    in_ul = False
                html_lines.append("<ol>")
                in_ol = True
            html_lines.append(f"<li>{_inline_md_to_html(_escape_html(num_match.group(2)))}</li>")
            continue

        if not stripped:
            _close_lists()
            _close_paragraph()
            continue

        _close_lists()
        if not in_paragraph:
            html_lines.append("<p>")
            in_paragraph = True
        else:
            html_lines.append("<br/>")
        html_lines.append(_inline_md_to_html(_escape_html(line)))

    _close_lists()
    _close_paragraph()

    return "\n".join(html_lines)


def render_html_overview(
    repo_path: str,
    detect: DetectResult,
    analysis: AnalysisResult,
    output_dir: str,
) -> RenderResult:
    """Generate a simple HTML report from the Markdown content."""
    from context_crafter_mcp.renderers.markdown import render_project_overview

    md_result = render_project_overview(repo_path, detect, analysis, output_dir)
    if not md_result.ok or not md_result.written:
        return RenderResult(
            ok=False,
            error="Markdown generation failed",
            resolved_output_dir=md_result.resolved_output_dir,
        )

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
ul, ol {{ margin: 0.5rem 0; padding-left: 1.5rem; }}
li {{ margin: 0.25rem 0; }}
blockquote {{ border-left: 3px solid #ccc; margin: 0; padding-left: 1rem; color: #555; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 1rem 0; }}
code {{ background: #f4f4f4; padding: 0.15rem 0.3rem; border-radius: 3px; font-size: 0.9em; }}
a {{ color: #0366d6; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
th {{ background: #f4f4f4; }}
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
        resolved_output_dir=str(out),
    )
