"""Validate release-truth documentation against the current repository state."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_BETA_TAG = "0.7.0b1"
EXPECTED_GENERATION_PHRASE = "8 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`"
EXPECTED_ACTION_BASELINES = [
    "actions/checkout@v7",
    "actions/setup-python@v6",
    "astral-sh/setup-uv@v8.2.0",
]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def _is_head_ahead_of_tag(tag: str) -> bool:
    try:
        count = int(_git("rev-list", "--count", f"{tag}..HEAD"))
    except (RuntimeError, ValueError):
        return False
    return count > 0


def validate() -> list[str]:
    issues: list[str] = []
    pre_gate = _read("docs/PRE_1_0_GATE.md")
    roadmap = _read("docs/ROADMAP.md")
    project_state = _read("docs/project_state.md")
    changelog = _read("CHANGELOG.md")
    ci = _read(".github/workflows/ci.yml")
    smoke = _read(".github/workflows/smoke-repos.yml")
    codeql = _read(".github/workflows/codeql.yml")

    if EXPECTED_GENERATION_PHRASE not in pre_gate:
        issues.append(f"docs/PRE_1_0_GATE.md must describe generation as {EXPECTED_GENERATION_PHRASE}.")
    if "all 8 Markdown files + `RUN_STATE.json`" in pre_gate:
        issues.append("docs/PRE_1_0_GATE.md contains stale generated-output wording.")

    if _is_head_ahead_of_tag(CURRENT_BETA_TAG):
        required_post_beta_phrase = f"post-`{CURRENT_BETA_TAG}` hardening commits"
        if required_post_beta_phrase not in roadmap:
            issues.append(
                "docs/ROADMAP.md must say main has post-beta hardening commits "
                f"when HEAD is ahead of {CURRENT_BETA_TAG}."
            )

    for action in EXPECTED_ACTION_BASELINES:
        if action not in project_state:
            issues.append(f"docs/project_state.md must record action baseline {action}.")
        if action not in changelog:
            issues.append(f"CHANGELOG.md must mention action baseline {action}.")

    workflow_text = "\n".join([ci, smoke, codeql])
    stale_actions = [
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "astral-sh/setup-uv@v5",
    ]
    for action in stale_actions:
        if action in workflow_text:
            issues.append(f"Workflow still references stale action {action}.")

    if "cache-suffix: ${{ matrix.os }}-${{ matrix.python-version }}" not in ci:
        issues.append("CI workflow must include matrix-specific setup-uv cache-suffix.")

    beta_tag_pattern = re.compile(r"Latest public git tag(?: on the remote)?: `?0\.7\.0b1`?")
    if not beta_tag_pattern.search(roadmap) and "Latest public git tag: `0.7.0b1`" not in project_state:
        issues.append("Release docs must record latest public git tag 0.7.0b1.")

    return issues


def main() -> int:
    issues = validate()
    if issues:
        print("release-doc validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"release-doc validation passed for {ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
