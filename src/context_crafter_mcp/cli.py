"""CLI for context-crafter-mcp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_crafter_mcp import __version__

from context_crafter_mcp.graph import run_detect, run_generate_all
from context_crafter_mcp.models import ScanConfig


MCP_CONFIG_TEMPLATES: dict[str, dict] = {
    "claude-desktop": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "claude-code": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "kimi": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "cline": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "roo": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "vscode": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "codex": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
    "generic-stdio": {
        "mcpServers": {
            "context-crafter": {
                "command": "uvx",
                "args": ["context-crafter-mcp", "serve"],
            }
        }
    },
}


def _scan_config_from_args(args: argparse.Namespace) -> ScanConfig:
    max_depth = getattr(args, "scan_depth", None)
    max_files = getattr(args, "max_files_per_dir", None)
    profile = getattr(args, "profile", None)
    return ScanConfig(
        max_depth=max_depth if max_depth is not None else 4,
        max_files_per_dir=max_files if max_files is not None else 80,
        profile=profile if profile is not None else "standard",
    )


def cmd_version(args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    issues: list[str] = []
    ok = True

    print(f"context-crafter-mcp {__version__}")
    print(f"Python: {sys.version}")

    try:
        import mcp

        print(f"mcp SDK: {getattr(mcp, '__version__', 'unknown')}")
    except Exception as exc:
        print(f"mcp SDK: MISSING ({exc})")
        ok = False

    try:
        import pydantic

        print(f"pydantic: {getattr(pydantic, '__version__', 'unknown')}")
    except Exception as exc:
        print(f"pydantic: MISSING ({exc})")
        ok = False

    try:
        import langgraph

        print(f"langgraph: {getattr(langgraph, '__version__', 'unknown')}")
    except Exception as exc:
        print(f"langgraph: MISSING ({exc})")
        ok = False

    if ok:
        print("Status: healthy")
    else:
        print("Status: issues found")
        for issue in issues:
            print(f"  - {issue}")

    return 0 if ok else 1


def cmd_detect(args: argparse.Namespace) -> int:
    repo_path = args.repo_path
    detect = run_detect(repo_path)
    if args.json:
        print(json.dumps(detect.to_dict(), indent=2))
    else:
        print(f"Repo: {detect.repo_path}")
        print(f"Exists: {detect.exists}")
        if detect.exists:
            print(f"Types: {', '.join(detect.project_types)}")
            for ptype, hits in detect.markers.items():
                if hits:
                    print(f"  {ptype}: {len(hits)} marker(s)")
        if detect.error:
            print(f"Error: {detect.error}")
    return 0 if detect.exists else 1


def cmd_generate(args: argparse.Namespace) -> int:
    repo_path = args.repo_path
    output_dir = args.output
    config = _scan_config_from_args(args)
    state = run_generate_all(repo_path, output_dir, config)
    result = state.to_tool_result()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["ok"]:
            print("Generated:")
            for w in result["written"]:
                print(f"  -> {w}")
        else:
            print("Errors:", result["errors"])
    return 0 if result["ok"] else 1


def cmd_validate(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
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
    found: list[str] = []
    missing: list[str] = []
    for name in required:
        if (output_dir / name).exists():
            found.append(name)
        else:
            missing.append(name)
    ok = len(missing) == 0
    result = {
        "ok": ok,
        "output_dir": str(output_dir),
        "found": found,
        "missing": missing,
        "count": len(found),
        "expected": len(required),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Validate: {output_dir}")
        print(f"Found: {len(found)}/{len(required)}")
        if missing:
            print("Missing:")
            for m in missing:
                print(f"  - {m}")
    return 0 if ok else 1


def cmd_self_test(args: argparse.Namespace) -> int:
    repo_path = args.repo_path or "."
    if not Path(repo_path).exists():
        print(f"Path not found, skipping: {repo_path}")
        return 0
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


def cmd_mcp_config(args: argparse.Namespace) -> int:
    client = args.client
    if client not in MCP_CONFIG_TEMPLATES:
        print(f"Unknown client: {client}")
        print(f"Supported: {', '.join(sorted(MCP_CONFIG_TEMPLATES))}")
        return 1
    config = MCP_CONFIG_TEMPLATES[client]
    print(json.dumps(config, indent=2))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import asyncio
    from context_crafter_mcp.server import main as server_main

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context-crafter-mcp",
        description="Context Crafter MCP: local-first repo context generator and MCP server.",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit.")
    sub = parser.add_subparsers(dest="command")

    # version handled via --version flag, but also as command for convenience
    sub.add_parser("version", help="Show version.")

    p_doctor = sub.add_parser("doctor", help="Check environment and package health.")
    p_doctor.set_defaults(func=cmd_doctor)

    p_detect = sub.add_parser("detect", help="Detect project types for a repository.")
    p_detect.add_argument("repo_path", nargs="?", default=".")
    p_detect.add_argument("--json", action="store_true")
    p_detect.add_argument("--scan-depth", type=int, default=None)
    p_detect.add_argument("--max-files-per-dir", type=int, default=None)
    p_detect.set_defaults(func=cmd_detect)

    p_generate = sub.add_parser("generate", help="Generate context docs for a repository.")
    p_generate.add_argument("repo_path", nargs="?", default=".")
    p_generate.add_argument("--output", required=True)
    p_generate.add_argument("--profile", choices=["compact", "standard", "deep"], default="standard")
    p_generate.add_argument("--json", action="store_true")
    p_generate.add_argument("--scan-depth", type=int, default=None)
    p_generate.add_argument("--max-files-per-dir", type=int, default=None)
    p_generate.set_defaults(func=cmd_generate)

    p_validate = sub.add_parser("validate", help="Validate generated output directory.")
    p_validate.add_argument("output_dir")
    p_validate.add_argument("--json", action="store_true")
    p_validate.set_defaults(func=cmd_validate)

    p_self = sub.add_parser("self-test", help="Run end-to-end self test.")
    p_self.add_argument("repo_path", nargs="?", default=".")
    p_self.set_defaults(func=cmd_self_test)

    p_config = sub.add_parser("mcp-config", help="Emit MCP client config snippet.")
    p_config.add_argument("--client", required=True)
    p_config.set_defaults(func=cmd_mcp_config)

    p_serve = sub.add_parser("serve", help="Start MCP stdio server.")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0

    return func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    sys.exit(main())
