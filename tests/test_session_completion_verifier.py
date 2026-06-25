"""Tests for the context-crafter-tests session completion verifier.

These tests exercise the tightened verifier behavior:
- explicit --report is required (no auto-discovery fallback)
- explicit --run-id is required for profiles that need runs
- no silent fallback to runtime-state last_run_id
- report-to-run binding is enforced
- live validate-contract check for platform-contract-change
- contradiction detection for release-gate claims, blocker claims, completion claims
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH_ENV = "CONTEXT_CRAFTER_TESTS_TOOL"
TOOL_PATH_VALUE = os.environ.get(TOOL_PATH_ENV)
TOOL_PATH = Path(TOOL_PATH_VALUE).expanduser() if TOOL_PATH_VALUE else None

if TOOL_PATH is None or not TOOL_PATH.exists():
    pytest.skip(
        f"external context-crafter-tests verifier unavailable; set {TOOL_PATH_ENV} to run these tests",
        allow_module_level=True,
    )


def _run_tool(*args: str) -> tuple[int, dict]:
    assert TOOL_PATH is not None
    cmd = [sys.executable, str(TOOL_PATH), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    stdout = result.stdout.strip()
    # Find the first top-level JSON object by counting braces.
    depth = 0
    json_end = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(stdout):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                json_end = i
                break
    if json_end == 0:
        json_text = stdout
    else:
        json_text = stdout[: json_end + 1]
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Could not parse JSON from stdout:\n{stdout}") from exc
    return result.returncode, payload


def _make_valid_report(path: Path, run_id: str | None = None) -> None:
    """Write a minimal valid final report."""
    runs_table = (
        "| Run ID | Target | Classification | Reason |\n"
        "|---|---|---|---|\n"
        f"| {run_id} | L3-GENNOISE-001 | targeted-regression | test |\n\n"
        if run_id else ""
    )
    evidence_rows = (
        f"| Targeted issue proof | PASS | {run_id} | path | note |\n"
        if run_id else
        "| Contract docs updated | PASS | N/A | path | note |\n"
    )
    path.write_text(
        "# Session summary\n\n"
        "- Scope: test\n"
        "- Result: complete\n"
        "\n"
        "## Re-verified first\n\n"
        "- validate-contract\n"
        "\n"
        "## Changes made\n\n"
        "- None\n"
        "\n"
        "## Official runs executed\n\n"
        f"{runs_table}"
        "## Evidence table\n\n"
        "| Evidence item | Status | Run ID | Artifact path | Note |\n"
        "|---|---|---|---|---|\n"
        f"{evidence_rows}"
        "| Final report creation | PASS | N/A | path | note |\n"
        "\n"
        "## Failures and blockers\n\n"
        "- None\n"
        "\n"
        "## Truthfulness call\n\n"
        "- Platform quality: improved\n"
        "\n"
        "## Next exact step\n\n"
        "- Done\n",
        encoding="utf-8",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Explicit-input enforcement
# ──────────────────────────────────────────────────────────────────────────────


class TestExplicitInputRequired:
    def test_no_report_fails_immediately(self) -> None:
        """Auto-discovery is disabled; missing --report must fail closed."""
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
        )
        assert code == 1
        assert payload["pass"] is False
        check = next((c for c in payload["checks"] if c["name"] == "explicit report required"), None)
        assert check is not None
        assert check["pass"] is False
        assert "auto-discovering" in check["detail"].lower()

    def test_no_run_id_for_run_requiring_profile_fails(self, tmp_path: Path) -> None:
        """Profiles needing runs require explicit --run-id; no silent fallback."""
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id="RUN-20260603-032309-codex-e847")
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--report", str(report),
        )
        assert code == 1
        assert payload["pass"] is False
        check = next((c for c in payload["checks"] if c["name"] == "explicit run-id required"), None)
        assert check is not None
        assert check["pass"] is False
        assert "--run-id must be provided" in check["detail"]

    def test_platform_contract_change_does_not_require_run_id(self, tmp_path: Path) -> None:
        """platform-contract-change requires 0 runs, so --run-id is optional."""
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id=None)
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "platform-contract-change",
            "--report", str(report),
        )
        # Should pass validate-contract live check and other checks
        assert code == 0, f"Unexpected failure: {json.dumps(payload, indent=2)}"
        assert payload["pass"] is True
        run_check = next((c for c in payload["checks"] if c["name"] == "required run execution"), None)
        assert run_check is not None
        assert run_check["pass"] is True


# ──────────────────────────────────────────────────────────────────────────────
# Stale-evidence rejection
# ──────────────────────────────────────────────────────────────────────────────


class TestStaleEvidenceRejection:
    def test_runtime_state_last_run_id_is_ignored(self, tmp_path: Path) -> None:
        """The verifier must NOT silently fall back to runtime-state last_run_id."""
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id="RUN-20260603-032309-codex-e847")
        # Provide a report that references a valid run, but do NOT provide --run-id
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--report", str(report),
        )
        assert code == 1
        assert payload["pass"] is False
        # Must fail because --run-id is missing, not silently validate the old run
        check = next((c for c in payload["checks"] if c["name"] == "explicit run-id required"), None)
        assert check is not None
        assert check["pass"] is False

    def test_old_report_not_auto_discovered(self, tmp_path: Path) -> None:
        """Even if a valid old report exists on disk, missing --report must fail."""
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "platform-contract-change",
        )
        assert code == 1
        assert payload["pass"] is False
        check = next((c for c in payload["checks"] if c["name"] == "explicit report required"), None)
        assert check is not None
        assert check["pass"] is False


# ──────────────────────────────────────────────────────────────────────────────
# Report structure and evidence table
# ──────────────────────────────────────────────────────────────────────────────


class TestReportStructure:
    def test_valid_report_passes(self, tmp_path: Path) -> None:
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id="RUN-20260603-032309-codex-e847")
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 0, f"Expected pass but got: {json.dumps(payload, indent=2)}"
        assert payload["pass"] is True
        assert all(c["pass"] for c in payload["checks"])

    def test_missing_sections_fails(self, tmp_path: Path) -> None:
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Targeted issue proof | PASS | RUN-20260603-032309-codex-e847 | path | note |\n",
            encoding="utf-8",
        )
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 1
        struct_check = next((c for c in payload["checks"] if c["name"] == "report structure"), None)
        assert struct_check is not None
        assert struct_check["pass"] is False
        assert "missing required sections" in struct_check["detail"]

    def test_invalid_evidence_status_fails(self, tmp_path: Path) -> None:
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "## Re-verified first\n\n"
            "## Changes made\n\n"
            "## Official runs executed\n\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Targeted issue proof | PENDING | RUN-20260603-032309-codex-e847 | path | note |\n"
            "## Failures and blockers\n\n"
            "## Truthfulness call\n\n"
            "## Next exact step\n\n",
            encoding="utf-8",
        )
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 1
        table_check = next((c for c in payload["checks"] if c["name"] == "evidence table completeness"), None)
        assert table_check is not None
        assert table_check["pass"] is False
        assert "invalid status values" in table_check["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# Report-to-run binding and freshness
# ──────────────────────────────────────────────────────────────────────────────


class TestReportToRunBinding:
    def test_report_omitting_run_id_fails(self, tmp_path: Path) -> None:
        """The report evidence table must reference the explicit run IDs."""
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "## Re-verified first\n\n"
            "## Changes made\n\n"
            "## Official runs executed\n\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Targeted issue proof | PASS | N/A | path | note |\n"
            "## Failures and blockers\n\n"
            "## Truthfulness call\n\n"
            "## Next exact step\n\n",
            encoding="utf-8",
        )
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 1
        binding_check = next((c for c in payload["checks"] if c["name"] == "report-to-run binding"), None)
        assert binding_check is not None
        assert binding_check["pass"] is False
        assert "RUN-20260603-032309-codex-e847" in binding_check["detail"]

    def test_report_with_matching_run_id_passes(self, tmp_path: Path) -> None:
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id="RUN-20260603-032309-codex-e847")
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 0
        binding_check = next((c for c in payload["checks"] if c["name"] == "report-to-run binding"), None)
        assert binding_check is not None
        assert binding_check["pass"] is True


# ──────────────────────────────────────────────────────────────────────────────
# Release-gate contradiction
# ──────────────────────────────────────────────────────────────────────────────


class TestReleaseGateContradiction:
    def test_release_gate_claim_without_artifact_fails(self, tmp_path: Path) -> None:
        """A report claiming release-gate success must have release-gate/latest.md."""
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "## Re-verified first\n\n"
            "## Changes made\n\n"
            "## Official runs executed\n\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Release gate | PASS | N/A | path | note |\n"
            "## Failures and blockers\n\n"
            "## Truthfulness call\n\n"
            "- Release-gate passed successfully\n"
            "## Next exact step\n\n",
            encoding="utf-8",
        )
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "release-gate",
            "--run-id", "RUN-20260603-032309-codex-e847",
            "--report", str(report),
        )
        assert code == 1
        assert payload["pass"] is False
        # Should fail on missing release-gate/latest.md AND missing artifact presence
        artifact_check = next((c for c in payload["checks"] if c["name"] == "required artifact presence"), None)
        assert artifact_check is not None
        assert artifact_check["pass"] is False
        assert "release-gate/latest.md" in artifact_check["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# Non-canonical proof rejection
# ──────────────────────────────────────────────────────────────────────────────


class TestNonCanonicalProofRejection:
    def test_debug_script_does_not_satisfy_run_check(self, tmp_path: Path) -> None:
        """A .tmp script or scratch file is not a canonical raw run + ledger."""
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "## Re-verified first\n\n"
            "## Changes made\n\n"
            "## Official runs executed\n\n"
            "| Run ID | Target | Classification | Reason |\n"
            "|---|---|---|---|\n"
            "| RUN-SCRATCH-001 | L3-GENNOISE-001 | targeted-regression | debug |\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Targeted issue proof | PASS | RUN-SCRATCH-001 | path | note |\n"
            "## Failures and blockers\n\n"
            "## Truthfulness call\n\n"
            "## Next exact step\n\n",
            encoding="utf-8",
        )
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-SCRATCH-001",
            "--report", str(report),
        )
        assert code == 1
        run_check = next((c for c in payload["checks"] if c["name"] == "required run execution"), None)
        assert run_check is not None
        assert run_check["pass"] is False
        # The run check fails because the scratch run ID has no raw dir or ledger.
        # The detail may describe the count failure or the per-run missing artifacts.
        assert "valid" in run_check["detail"].lower() or "raw run dir" in run_check["detail"].lower() or "ledger" in run_check["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# Contradiction detection
# ──────────────────────────────────────────────────────────────────────────────


class TestContradictionDetection:
    def test_completion_claim_with_failing_checks(self, tmp_path: Path) -> None:
        report = tmp_path / "FINAL-REPORT-bad.md"
        report.write_text(
            "# Session summary\n\n"
            "- Result: complete\n"
            "\n"
            "## Re-verified first\n\n"
            "## Changes made\n\n"
            "## Official runs executed\n\n"
            "## Evidence table\n\n"
            "| Evidence item | Status | Run ID | Artifact path | Note |\n"
            "|---|---|---|---|---|\n"
            "| Targeted issue proof | PASS | RUN-20260603-032309-codex-e847 | path | note |\n"
            "## Failures and blockers\n\n"
            "## Truthfulness call\n\n"
            "## Next exact step\n\n"
            "Done\n",
            encoding="utf-8",
        )
        # Use a fake run ID so run check fails, triggering contradiction with "complete"
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--run-id", "RUN-FAKE-000000000000-0000",
            "--report", str(report),
        )
        assert code == 1
        assert payload["pass"] is False
        contradiction_check = next(
            (c for c in payload["checks"] if "closure claim consistency" in c["name"]), None
        )
        assert contradiction_check is not None
        assert contradiction_check["pass"] is False
        assert "completion" in contradiction_check["detail"].lower()


# ──────────────────────────────────────────────────────────────────────────────
# Platform-contract-change live validation
# ──────────────────────────────────────────────────────────────────────────────


class TestPlatformContractChange:
    def test_live_validate_contract_check(self, tmp_path: Path) -> None:
        """platform-contract-change must pass a live validate-contract check."""
        report = tmp_path / "FINAL-REPORT-test.md"
        _make_valid_report(report, run_id=None)
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "platform-contract-change",
            "--report", str(report),
        )
        assert code == 0, f"Unexpected failure: {json.dumps(payload, indent=2)}"
        contract_check = next(
            (c for c in payload["checks"] if c["name"] == "platform contract validation"), None
        )
        assert contract_check is not None
        assert contract_check["pass"] is True
        assert "zero issues" in contract_check["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# Quiet flag
# ──────────────────────────────────────────────────────────────────────────────


class TestQuietFlag:
    def test_quiet_flag_suppresses_human_block(self) -> None:
        code, payload = _run_tool(
            "verify-session-completion",
            "--profile", "targeted-regression",
            "--quiet",
        )
        assert isinstance(payload, dict)
        assert "profile" in payload
