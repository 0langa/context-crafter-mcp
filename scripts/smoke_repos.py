"""Real-repo smoke automation for context-crafter-mcp.

Clones a fixed set of public repositories with --depth 1, runs detect/generate/validate,
and emits a deterministic JSON summary to stdout and an output file.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _rm_rf(path: Path) -> None:
    """Remove a directory tree, handling read-only files on Windows."""

    def _onexc(_func: Any, p: str, _exc: BaseException) -> None:
        os.chmod(p, stat.S_IWRITE)
        os.remove(p) if os.path.isfile(p) else os.rmdir(p)

    shutil.rmtree(path, onexc=_onexc)


REPOS: list[dict[str, str]] = [
    {"name": "pallets/click", "url": "https://github.com/pallets/click.git", "stack": "Python"},
    {"name": "sindresorhus/ky", "url": "https://github.com/sindresorhus/ky.git", "stack": "Node/TypeScript"},
    {"name": "spf13/cobra", "url": "https://github.com/spf13/cobra.git", "stack": "Go"},
    {"name": "serde-rs/json", "url": "https://github.com/serde-rs/json.git", "stack": "Rust"},
]

DEFAULT_OUTPUT = Path("docs/generated/smoke-results.json")


def _run_cmd(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def _run_cli(
    repo_path: Path,
    command: str,
    extra_args: list[str] | None = None,
    timeout: int = 120,
) -> tuple[int, dict[str, Any]]:
    args = [
        sys.executable,
        "-m",
        "context_crafter_mcp.cli",
        command,
        str(repo_path),
        "--json",
    ]
    if extra_args:
        args.extend(extra_args)
    rc, stdout, stderr = _run_cmd(args, timeout=timeout)
    parsed: dict[str, Any] = {}
    if stdout.strip():
        try:
            parsed = json.loads(stdout.strip())
        except json.JSONDecodeError:
            parsed = {"_raw_stdout": stdout.strip(), "_stderr": stderr.strip()}
    else:
        parsed = {"_stderr": stderr.strip()}
    return rc, parsed


def clone_repo(url: str, dest: Path, timeout: int = 60) -> tuple[bool, str]:
    rc, stdout, stderr = _run_cmd(
        ["git", "clone", "--depth", "1", url, str(dest)],
        timeout=timeout,
    )
    if rc != 0:
        err = (stderr or stdout).strip()
        if "Could not resolve" in err or "unable to access" in err or "Connection" in err:
            return False, "network_unavailable"
        return False, err
    return True, ""


def run_smoke(repo: dict[str, str], keep_temps: bool) -> dict[str, Any]:
    name = repo["name"]
    url = repo["url"]
    stack = repo["stack"]

    tmp_base = Path(tempfile.gettempdir()) / "context-crafter-smoke"
    tmp_base.mkdir(parents=True, exist_ok=True)
    tmp_dir = tmp_base / name.replace("/", "_")

    # Remove previous leftover if any
    if tmp_dir.exists():
        _rm_rf(tmp_dir)

    notes: list[str] = []

    # Clone
    cloned, clone_msg = clone_repo(url, tmp_dir)
    if not cloned:
        if clone_msg == "network_unavailable":
            print(f"Network unavailable while cloning {name}. Aborting.", file=sys.stderr)
            sys.exit(1)
        return {
            "repo": name,
            "stack": stack,
            "detect_ok": False,
            "generate_ok": False,
            "validate_ok": False,
            "files_scanned": 0,
            "warnings": 0,
            "errors": 1,
            "notes": [f"clone failed: {clone_msg}"],
        }

    try:
        # Detect
        detect_rc, detect_out = _run_cli(tmp_dir, "detect", timeout=60)
        detect_ok = detect_rc == 0 and detect_out.get("ok", False)
        detect_warnings = detect_out.get("warnings", []) or []
        detect_errors = detect_out.get("errors", []) or []
        project_types = detect_out.get("project_types", [])

        # Generate
        gen_rc, gen_out = _run_cli(
            tmp_dir,
            "generate",
            extra_args=["--output", "docs/generated", "--profile", "standard"],
            timeout=120,
        )
        generate_ok = gen_rc == 0 and gen_out.get("ok", False)
        files_scanned = gen_out.get("files_scanned", 0)
        gen_warnings = gen_out.get("warnings", []) or []
        gen_errors = gen_out.get("errors", []) or []
        resolved_output_dir = gen_out.get("resolved_output_dir")

        # Validate
        validate_path = Path(resolved_output_dir) if resolved_output_dir else tmp_dir / "docs/generated"
        val_rc, val_out = _run_cli(
            validate_path,
            "validate",
            extra_args=["--repo", str(tmp_dir)],
            timeout=60,
        )
        validate_ok = val_rc == 0 and val_out.get("ok", False)
        val_warnings = val_out.get("warnings", []) or []
        val_errors = val_out.get("errors", []) or []
        missing = val_out.get("missing", []) or []

        warnings_count = len(detect_warnings) + len(gen_warnings) + len(val_warnings)
        errors_count = len(detect_errors) + len(gen_errors) + len(val_errors)

        if project_types:
            notes.append(f"detected {', '.join(project_types)}")
        if resolved_output_dir:
            notes.append(f"resolved_output_dir: {resolved_output_dir}")
        if missing:
            notes.append(f"missing files: {', '.join(missing)}")
        if not detect_ok:
            notes.append("detect failed")
        if not generate_ok:
            notes.append("generate failed")
        if not validate_ok:
            notes.append("validate failed")

        return {
            "repo": name,
            "stack": stack,
            "detect_ok": detect_ok,
            "generate_ok": generate_ok,
            "validate_ok": validate_ok,
            "files_scanned": files_scanned,
            "warnings": warnings_count,
            "errors": errors_count,
            "notes": notes,
        }
    finally:
        if not keep_temps and tmp_dir.exists():
            _rm_rf(tmp_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Real-repo smoke automation.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the JSON summary (default: docs/generated/smoke-results.json).",
    )
    parser.add_argument(
        "--keep-temps",
        action="store_true",
        help="Keep cloned repositories in temp for debugging.",
    )
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    overall_ok = True

    for repo in REPOS:
        print(f"Smoking {repo['name']} ...", file=sys.stderr)
        res = run_smoke(repo, keep_temps=args.keep_temps)
        results.append(res)
        if not (res["detect_ok"] and res["generate_ok"] and res["validate_ok"]):
            overall_ok = False
        print(
            f"  detect={res['detect_ok']} generate={res['generate_ok']} validate={res['validate_ok']} files={res['files_scanned']} warnings={res['warnings']} errors={res['errors']}",
            file=sys.stderr,
        )

    summary_parts: list[str] = []
    for r in results:
        status = "PASS" if r["detect_ok"] and r["generate_ok"] and r["validate_ok"] else "FAIL"
        summary_parts.append(f"{r['repo']} ({status})")
    summary = f"Smoke {'passed' if overall_ok else 'failed'} for {len(results)} repo(s): {', '.join(summary_parts)}."

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": overall_ok,
        "repos": results,
        "summary": summary,
    }

    json_text = json.dumps(report, indent=2)
    print(json_text)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json_text + "\n", encoding="utf-8")
    print(f"Wrote summary to {args.output}", file=sys.stderr)

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
