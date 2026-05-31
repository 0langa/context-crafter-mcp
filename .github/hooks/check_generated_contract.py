from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_DOCS = {
    "AI_CONTEXT_INDEX.md",
    "PROJECT_OVERVIEW.md",
    "REPO_MAP.md",
    "DEPENDENCY_GRAPH.md",
    "ARCHITECTURE_SUMMARY.md",
    "AGENT_BRIEF.md",
    "SCAN_REPORT.md",
    "VALIDATION_REPORT.md",
}


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    server_text = (repo / "src" / "context_crafter_mcp" / "server.py").read_text(encoding="utf-8")
    missing = [name for name in REQUIRED_DOCS if name not in server_text]
    if missing:
        sys.stderr.write(
            "Hook fail: required generated docs missing from server-facing contract -> "
            + ", ".join(sorted(missing))
            + "\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
