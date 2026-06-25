#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_MARKERS = [
    "pyproject.toml",
    "docs/project_state.md",
    "src/context_crafter_mcp/cli.py",
]

REQUIRED_SECTIONS = [
    "Repo Snapshot",
    "Active Surfaces",
    "Current Truths",
    "Validation Commands",
    "Drift Watchlist",
]

REQUIRED_PATHS = [
    "docs/project_state.md",
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/OUTPUT_CONTRACT.md",
    "docs/PUBLIC_SURFACE_FREEZE.md",
    "docs/MCP_CLIENTS.md",
    "docs/LIMITATIONS.md",
    "SECURITY.md",
    "src/context_crafter_mcp/cli.py",
    "src/context_crafter_mcp/server.py",
    "tests",
    ".github/workflows/ci.yml",
    "scripts/installed_artifact_smoke.ps1",
]

REQUIRED_PHRASES = [
    "agent-authored, validator-checked",
    "Update this file directly whenever repo reality changes.",
    "before context compaction risk grows",
]


def detect_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    raise FileNotFoundError("Could not detect repo root for context-crafter-mcp.")


def validate(repo_root: Path) -> list[str]:
    issues: list[str] = []
    project_state_path = repo_root / "docs/project_state.md"
    text = project_state_path.read_text(encoding="utf-8")

    if not text.startswith("# Project State\n"):
        issues.append("docs/project_state.md must start with '# Project State'.")

    sections = re.findall(r"^## (.+)$", text, re.MULTILINE)
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            issues.append(f"Missing required section: {section}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            issues.append(f"Missing required phrase in docs/project_state.md: {phrase}")

    for relative_path in REQUIRED_PATHS:
        if not (repo_root / relative_path).exists():
            issues.append(f"Required path missing: {relative_path}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the agent-authored project_state.md contract.")
    parser.add_argument("--repo-root", default=None, help="Optional explicit repo root.")
    args = parser.parse_args()

    start = Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()
    repo_root = detect_repo_root(start)
    issues = validate(repo_root)

    if issues:
        print("project_state validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"project_state validation passed for {repo_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
