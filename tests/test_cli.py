"""Tests for the CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from context_crafter_mcp import __version__


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "context_crafter_mcp.cli"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_version() -> None:
    result = _run(["--version"])
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_cli_help() -> None:
    result = _run(["--help"])
    assert result.returncode == 0
    assert "detect" in result.stdout
    assert "generate" in result.stdout
    assert "validate" in result.stdout


def test_cli_detect_json() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        result = _run(["detect", td, "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert "python" in data["project_types"]


def test_cli_detect_missing_path() -> None:
    result = _run(["detect", "/nonexistent/path/12345", "--json"])
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["ok"] is False
    assert data["exists"] is False


def test_cli_generate_and_validate() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        Path(td, "pyproject.toml").write_text("[project]\nname = 'test'\n")
        out = Path(td, "out")
        result = _run(["generate", td, "--output", str(out), "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert len(data["written"]) >= 8
        assert data["resolved_output_dir"] == str(out.resolve())
        assert "warnings" in data
        assert "errors" in data

        val = _run(["validate", str(out), "--json"])
        assert val.returncode == 0
        vdata = json.loads(val.stdout)
        assert vdata["ok"] is True
        assert vdata["count"] == 8


def test_cli_generate_json_reports_confined_output_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        result = _run(["generate", td, "--output", "../escape", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["resolved_output_dir"] == str((Path(td) / "docs" / "generated").resolve())


def test_cli_doctor() -> None:
    result = _run(["doctor"])
    assert result.returncode == 0
    assert "healthy" in result.stdout


def test_cli_mcp_config_unknown_client() -> None:
    result = _run(["mcp-config", "--client", "nonexistent"])
    assert result.returncode == 1
    assert "Unknown client" in result.stdout


def test_cli_mcp_config_with_repo() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = _run(["mcp-config", "--client", "kimi", "--repo", td])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "context-crafter" in data["mcpServers"]
