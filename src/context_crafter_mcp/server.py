"""MCP server for context-crafter-mcp."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from context_crafter_mcp.graph import (
    run_detect,
    run_generate_all,
    run_generate_architecture_summary,
    run_generate_dependency_graph,
    run_generate_project_overview,
    run_generate_repo_map,
)
from context_crafter_mcp.models import ScanConfig
from context_crafter_mcp.renderers.html import render_html_overview

app = Server("context-crafter")

CAPABILITIES_TEXT = (
    "Context Crafter MCP turns source repositories into compact AI-agent context.\n\n"
    "Languages: Python, Node/TypeScript, .NET, Rust, Go, Java, Generic.\n"
    "Outputs: AI_CONTEXT_INDEX.md, PROJECT_OVERVIEW.md, REPO_MAP.md, "
    "DEPENDENCY_GRAPH.md, ARCHITECTURE_SUMMARY.md, AGENT_BRIEF.md, "
    "VALIDATION_REPORT.md, SCAN_REPORT.md.\n"
    "Safety: static-only, no execution, no network, bounded scans, "
    "no symlinks, output confined to repo root.\n"
    "Profiles: compact, standard, deep.\n"
    "Limitations: static analysis only; no runtime behavior; "
    "non-Python parsing is regex/XML/TOML-based."
)


def _build_scan_config(arguments: dict) -> ScanConfig:
    """Build ScanConfig from tool arguments with safe defaults."""
    depth = arguments.get("scan_depth")
    max_files = arguments.get("max_files_per_dir")
    profile = arguments.get("profile", "standard")
    return ScanConfig(
        max_depth=int(depth) if depth is not None else 4,
        max_files_per_dir=int(max_files) if max_files is not None else 80,
        profile=profile,
    )


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """Dispatch MCP tool calls."""
    scan_config = _build_scan_config(arguments)
    repo_path = arguments.get("repo_path", "")
    output_dir = arguments.get("output_dir", "docs/generated")
    html = arguments.get("html", False)

    if name == "detect_project":
        detect = run_detect(repo_path)
        return [
            TextContent(
                type="text",
                text=json.dumps(detect.to_dict(), indent=2),
            )
        ]

    if name == "generate_project_overview":
        overview_result = run_generate_project_overview(repo_path, output_dir, scan_config)
        written = list(overview_result.written)
        if html and overview_result.ok:
            from context_crafter_mcp.analyzers.generic import analyze_generic
            from context_crafter_mcp.analyzers import analyze_for_type

            detect = run_detect(repo_path)
            if detect.exists:
                analysis = analyze_generic(repo_path, config=scan_config)
                for ptype in detect.project_types:
                    if ptype != "generic":
                        analysis = analyze_for_type(ptype, repo_path, analysis, scan_config)
                html_result = render_html_overview(repo_path, detect, analysis, output_dir)
                if html_result.ok:
                    written.extend(html_result.written)
        return [
            TextContent(
                type="text",
                text=json.dumps({**overview_result.to_dict(), "written": written}, indent=2),
            )
        ]

    if name == "generate_repo_map":
        map_result = run_generate_repo_map(repo_path, output_dir, scan_config)
        return [
            TextContent(
                type="text",
                text=json.dumps(map_result.to_dict(), indent=2),
            )
        ]

    if name == "generate_dependency_graph":
        graph_result = run_generate_dependency_graph(repo_path, output_dir, scan_config)
        return [
            TextContent(
                type="text",
                text=json.dumps(graph_result.to_dict(), indent=2),
            )
        ]

    if name == "generate_architecture_summary":
        arch_result = run_generate_architecture_summary(repo_path, output_dir, scan_config)
        return [
            TextContent(
                type="text",
                text=json.dumps(arch_result.to_dict(), indent=2),
            )
        ]

    if name in ("generate_all", "generate_context"):
        state = run_generate_all(repo_path, output_dir, scan_config)
        result = state.to_tool_result()
        if html and state.ok and state.detect_result and state.analysis:
            html_result = render_html_overview(repo_path, state.detect_result, state.analysis, output_dir)
            if html_result.ok:
                result["written"] = list(result.get("written", [])) + list(html_result.written)
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2),
            )
        ]

    if name == "validate_generated_context":
        out = Path(output_dir)
        required = [
            "AI_CONTEXT_INDEX.md",
            "PROJECT_OVERVIEW.md",
            "REPO_MAP.md",
            "DEPENDENCY_GRAPH.md",
            "ARCHITECTURE_SUMMARY.md",
            "AGENT_BRIEF.md",
            "VALIDATION_REPORT.md",
            "SCAN_REPORT.md",
        ]
        found = [r for r in required if (out / r).exists()]
        missing = [r for r in required if not (out / r).exists()]
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "ok": len(missing) == 0,
                        "output_dir": str(out),
                        "found": found,
                        "missing": missing,
                    },
                    indent=2,
                ),
            )
        ]

    if name == "explain_capabilities":
        return [
            TextContent(
                type="text",
                text=CAPABILITIES_TEXT,
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


@app.list_tools()
async def list_tools() -> list:
    """List available MCP tools."""
    common_props = {
        "repo_path": {
            "type": "string",
            "description": "Absolute path to the repository.",
        },
        "output_dir": {
            "type": "string",
            "description": "Relative output directory inside the repo.",
            "default": "docs/generated",
        },
        "scan_depth": {
            "type": "integer",
            "description": "Maximum directory scan depth (1-20).",
            "default": 4,
        },
        "max_files_per_dir": {
            "type": "integer",
            "description": "Maximum files to scan per directory (1-5000).",
            "default": 80,
        },
        "profile": {
            "type": "string",
            "description": "Output profile: compact, standard, or deep.",
            "enum": ["compact", "standard", "deep"],
            "default": "standard",
        },
        "html": {
            "type": "boolean",
            "description": "Also generate an HTML version of the overview.",
            "default": False,
        },
    }
    return [
        Tool(
            name="detect_project",
            description="Detect project types for a repository path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": common_props["repo_path"],
                },
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="generate_context",
            description="Generate the full context documentation suite for a repository.",
            inputSchema={
                "type": "object",
                "properties": common_props,
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="generate_project_overview",
            description="Generate a Markdown project overview.",
            inputSchema={
                "type": "object",
                "properties": {k: v for k, v in common_props.items() if k != "repo_path" or True},
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="generate_repo_map",
            description="Generate a compact repository map.",
            inputSchema={
                "type": "object",
                "properties": {k: v for k, v in common_props.items() if k != "html" or True},
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="generate_dependency_graph",
            description="Generate Mermaid dependency graph files.",
            inputSchema={
                "type": "object",
                "properties": {k: v for k, v in common_props.items() if k != "html" or True},
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="generate_architecture_summary",
            description="Generate an architecture summary.",
            inputSchema={
                "type": "object",
                "properties": {k: v for k, v in common_props.items() if k != "html" or True},
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="validate_generated_context",
            description="Validate that generated context files exist in the output directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_dir": {
                        "type": "string",
                        "description": "Path to the output directory to validate.",
                    },
                },
                "required": ["output_dir"],
            },
        ),
        Tool(
            name="explain_capabilities",
            description="Explain what Context Crafter MCP can do, including languages, outputs, limits, and safety model.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.list_resources()
async def list_resources() -> list:
    """List available generated-doc resource templates."""
    return []


@app.list_resource_templates()
async def list_resource_templates() -> list:
    """List resource templates for reading generated docs."""
    from mcp.types import ResourceTemplate

    return [
        ResourceTemplate(
            uriTemplate="file:///{repo_path}/{output_dir}/{filename}",
            name="Generated doc",
            mimeType="text/markdown",
            description="Read a generated context document by absolute file path.",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> list[ReadResourceContents]:
    """Read a generated resource by file URI."""
    if uri.startswith("file://"):
        path = Path(uri[7:])
    else:
        path = Path(uri)
    if not path.exists():
        return [ReadResourceContents(content=f"Resource not found: {uri}", mime_type="text/plain")]
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError) as exc:
        return [ReadResourceContents(content=f"Error reading resource: {exc}", mime_type="text/plain")]
    return [ReadResourceContents(content=text, mime_type="text/markdown")]


@app.list_prompts()
async def list_prompts() -> list:
    """List available prompts."""
    from mcp.types import Prompt

    return [
        Prompt(
            name="generate_context",
            description="Prompt to generate full repository context.",
        ),
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> str:
    """Return a prompt template."""
    if name == "generate_context":
        return (
            "Analyze the repository at the given path and generate the full context suite. "
            "Use the generate_context tool with repo_path set to the absolute path."
        )
    return "Unknown prompt"


async def main() -> None:
    """Start the stdio MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def _self_test(repo_path: str) -> int:
    """Run generate_all on a path and print results."""
    print(f"Self-test: {repo_path}")
    state = run_generate_all(repo_path)
    result = state.to_tool_result()
    print(json.dumps(result, indent=2))
    if result["ok"]:
        for w in result["written"]:
            print(f"  -> {w}")
        return 0
    else:
        print("Errors:", result["errors"])
        return 1


def cli_self_test() -> None:
    """Console script entry point for smoke testing."""
    parser = argparse.ArgumentParser(description="context-crafter-mcp self-test")
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Repository path to analyze (default: current directory).",
    )
    args = parser.parse_args()
    path = args.repo_path
    if not Path(path).exists():
        print(f"Path not found, skipping: {path}")
        sys.exit(0)
    sys.exit(_self_test(path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="context-crafter-mcp server")
    parser.add_argument(
        "--self-test",
        metavar="REPO_PATH",
        help="Run a smoke test against REPO_PATH without starting MCP.",
    )
    args = parser.parse_args()

    if args.self_test:
        path = args.self_test
        if not Path(path).exists():
            print(f"Path not found, skipping: {path}")
            sys.exit(0)
        sys.exit(_self_test(path))
    else:
        asyncio.run(main())
