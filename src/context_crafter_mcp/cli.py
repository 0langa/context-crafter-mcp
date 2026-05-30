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

        ver = getattr(mcp, "__version__", None)
        print(f"mcp SDK: installed{' (' + ver + ')' if ver else ''}")
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"mcp SDK: MISSING ({exc})")
        issues.append(f"mcp SDK missing: {exc}")
        ok = False

    try:
        import pydantic

        ver = getattr(pydantic, "__version__", None)
        print(f"pydantic: installed{' (' + ver + ')' if ver else ''}")
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"pydantic: MISSING ({exc})")
        issues.append(f"pydantic missing: {exc}")
        ok = False

    try:
        import langgraph

        ver = getattr(langgraph, "__version__", None)
        print(f"langgraph: installed{' (' + ver + ')' if ver else ''}")
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"langgraph: MISSING ({exc})")
        issues.append(f"langgraph missing: {exc}")
        ok = False

    # CLI entrypoint check
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "context_crafter_mcp.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and __version__ in result.stdout:
            print("CLI entrypoint: ok")
        else:
            print("CLI entrypoint: unexpected output")
            issues.append("CLI entrypoint check failed")
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"CLI entrypoint: error ({exc})")
        issues.append(f"CLI entrypoint error: {exc}")

    # Temp output write check
    try:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            test_path = Path(td) / "write_test.txt"
            test_path.write_text("ok", encoding="utf-8")
            assert test_path.read_text(encoding="utf-8") == "ok"
        print("Temp output write: ok")
    except (OSError, AssertionError) as exc:
        print(f"Temp output write: error ({exc})")
        issues.append(f"Temp output write error: {exc}")
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
        print(f"Resolved output dir: {result.get('resolved_output_dir')}")
        if result["ok"]:
            print("Generated:")
            for w in result["written"]:
                print(f"  -> {w}")
        else:
            print("Errors:", result["errors"])
    return 0 if result["ok"] else 1


def cmd_validate(args: argparse.Namespace) -> int:
    from context_crafter_mcp.validation import validate_output_dir

    result = validate_output_dir(args.output_dir, repo_path=getattr(args, "repo", None))
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Validate: {result.output_dir}")
        print(f"Found: {len(result.found)}/{result.to_dict()['expected']}")
        if result.missing:
            print("Missing:")
            for m in result.missing:
                print(f"  - {m}")
        warnings = [c for c in result.checks if c.level == "warning"]
        errors = [c for c in result.checks if c.level == "error"]
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f"  [{w.code}] {w.file}: {w.message}")
        if errors:
            print("Errors:")
            for e in errors:
                print(f"  [{e.code}] {e.file}: {e.message}")
    return 0 if result.ok else 1


def cmd_self_test(args: argparse.Namespace) -> int:
    repo_path = args.repo_path or "."
    if not Path(repo_path).exists():
        print(f"Path not found, skipping: {repo_path}")
        return 0
    print(f"Self-test: {repo_path}")
    output_dir = getattr(args, "output", None)
    if output_dir:
        state = run_generate_all(repo_path, output_dir)
        result = state.to_tool_result()
        print(json.dumps(result, indent=2))
        if result["ok"]:
            for w in result["written"]:
                print(f"  -> {w}")
            return 0
        else:
            print("Errors:", result["errors"])
            return 1
    import tempfile

    repo = Path(repo_path).resolve()
    with tempfile.TemporaryDirectory(dir=repo) as td:
        rel = Path(td).name
        state = run_generate_all(repo_path, rel)
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
    repo_path = getattr(args, "repo", None)
    if repo_path:
        # Local development config using uv run
        abs_path = str(Path(repo_path).resolve())
        config = {
            "mcpServers": {
                "context-crafter": {
                    "command": "uv",
                    "args": [
                        "--directory",
                        abs_path,
                        "run",
                        "context-crafter-mcp",
                        "serve",
                    ],
                }
            }
        }
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
    p_validate.add_argument(
        "--repo",
        default=None,
        help="Repository root path for source-reference validation.",
    )
    p_validate.set_defaults(func=cmd_validate)

    p_self = sub.add_parser("self-test", help="Run end-to-end self test.")
    p_self.add_argument("repo_path", nargs="?", default=".")
    p_self.add_argument(
        "--output",
        default=None,
        help="Output directory for self-test generated docs (default: temporary directory).",
    )
    p_self.set_defaults(func=cmd_self_test)

    p_config = sub.add_parser("mcp-config", help="Emit MCP client config snippet.")
    p_config.add_argument("--client", required=True)
    p_config.add_argument(
        "--repo", default=None, help="Local repo path for development config (uses uv run instead of uvx)."
    )
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
