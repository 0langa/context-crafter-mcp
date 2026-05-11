"""MCP server for repo-docs-mcp."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from repo_docs_mcp.graph import (
    run_detect,
    run_generate_all,
    run_generate_architecture_summary,
    run_generate_dependency_graph,
    run_generate_project_overview,
    run_generate_repo_map,
)
from repo_docs_mcp.models import ScanConfig
from repo_docs_mcp.renderers.html import render_html_overview

app = Server("repo-docs-mcp")


def _build_scan_config(arguments: dict) -> ScanConfig:
    """Build ScanConfig from tool arguments with safe defaults."""
    depth = arguments.get("scan_depth")
    max_files = arguments.get("max_files_per_dir")
    kwargs: dict[str, int] = {}
    if depth is not None:
        kwargs["max_depth"] = int(depth)
    if max_files is not None:
        kwargs["max_files_per_dir"] = int(max_files)
    return ScanConfig(**kwargs)


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
            from repo_docs_mcp.analyzers.generic import analyze_generic
            from repo_docs_mcp.analyzers import analyze_for_type

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

    if name == "generate_all":
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
            name="generate_all",
            description="Run all generators.",
            inputSchema={
                "type": "object",
                "properties": common_props,
                "required": ["repo_path"],
            },
        ),
    ]


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
    parser = argparse.ArgumentParser(description="repo-docs-mcp self-test")
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
    parser = argparse.ArgumentParser(description="repo-docs-mcp server")
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
