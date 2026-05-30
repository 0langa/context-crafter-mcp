from __future__ import annotations

import re
import sys
from pathlib import Path


def _extract_server_tools(server_text: str) -> set[str]:
    return set(re.findall(r'name="([a-z_]+)"', server_text))


def _extract_cli_commands(cli_text: str) -> set[str]:
    return set(re.findall(r'cmd_([a-z_]+)\(', cli_text))


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    server_text = (repo / "src" / "context_crafter_mcp" / "server.py").read_text(encoding="utf-8")
    cli_text = (repo / "src" / "context_crafter_mcp" / "cli.py").read_text(encoding="utf-8")

    tools = _extract_server_tools(server_text)
    commands = _extract_cli_commands(cli_text)

    expected_overlap = {"detect_project": "detect", "generate_context": "generate", "validate_generated_context": "validate"}
    missing = []
    for tool_name, cli_name in expected_overlap.items():
        if tool_name not in tools:
            missing.append(f"missing tool:{tool_name}")
        if cli_name not in commands:
            missing.append(f"missing cli:{cli_name}")

    if missing:
        sys.stderr.write("Hook fail: MCP/CLI contract drift -> " + "; ".join(missing) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
