"""Generated-output redaction tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from context_crafter_mcp.graph import run_generate_all
from context_crafter_mcp.redaction import REDACTION_MARKER, redact_sensitive_text


def test_redact_sensitive_text_key_value_patterns() -> None:
    text = (
        'api_key = "abc123SECRET"\n'
        "token: ghp_abcdefghijklmnopqrstuvwxyz\n"
        '{"client_secret": "super-secret-value"}\n'
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ\n"
        "openai=sk-proj-abcdefghijklmnopqrstuvwxyz\n"
    )
    redacted = redact_sensitive_text(text)

    assert "abc123SECRET" not in redacted
    assert "ghp_abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "super-secret-value" not in redacted
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ" not in redacted
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in redacted
    assert redacted.count(REDACTION_MARKER) >= 5


def test_generated_outputs_redact_secret_like_metadata() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "pyproject.toml").write_text(
            "[project]\n"
            "name = 'redaction-demo'\n"
            "version = '0.1.0'\n"
            "description = 'connects with password=supersecret and api_key=abc123SECRET'\n",
            encoding="utf-8",
        )
        (root / "secrets.json").write_text('{"api_key": "abc123SECRET"}\n', encoding="utf-8")

        state = run_generate_all(td, "out")
        assert state.ok

        out = root / "out"
        overview = (out / "PROJECT_OVERVIEW.md").read_text(encoding="utf-8")
        scan_report = (out / "SCAN_REPORT.md").read_text(encoding="utf-8")
        ledger = json.loads((out / "EVIDENCE_LEDGER.json").read_text(encoding="utf-8"))

        combined = overview + scan_report + json.dumps(ledger)
        assert "supersecret" not in combined
        assert "abc123SECRET" not in combined
        assert REDACTION_MARKER in combined
        assert "Potential secret files detected" in scan_report
        assert "secrets.json" in scan_report
