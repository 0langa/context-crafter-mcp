"""Validate the public CLI and MCP stdio surface for release gates."""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from context_crafter_mcp import __version__
from context_crafter_mcp.cli import MCP_CONFIG_TEMPLATES
from context_crafter_mcp.validation import _REQUIRED_FILES


ROOT = Path(__file__).resolve().parents[1]
CLI = [sys.executable, "-m", "context_crafter_mcp.cli"]
EXPECTED_TOOLS = {
    "detect_project",
    "generate_context",
    "generate_project_overview",
    "generate_repo_map",
    "generate_dependency_graph",
    "generate_architecture_summary",
    "validate_generated_context",
    "explain_capabilities",
}
GENERATED_FILES = set(_REQUIRED_FILES) | {"DEPENDENCY_GRAPH.mmd", "CONTEXT_MANIFEST.json", "RUN_STATE.json"}


def _run(args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _fail(message: str) -> None:
    raise AssertionError(message)


def _check_version() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = pyproject["project"]["version"]
    if project_version != __version__:
        _fail(f"version mismatch: pyproject={project_version!r}, package={__version__!r}")

    result = _run(CLI + ["version"])
    if result.returncode != 0:
        _fail(f"version command failed: {result.stderr}")
    if result.stdout.strip() != project_version:
        _fail(f"version command returned {result.stdout.strip()!r}, expected {project_version!r}")

    result = _run(CLI + ["--version"])
    if result.returncode != 0:
        _fail(f"--version failed: {result.stderr}")
    if result.stdout.strip() != project_version:
        _fail(f"--version returned {result.stdout.strip()!r}, expected {project_version!r}")


def _check_help() -> None:
    result = _run(CLI + ["--help"])
    if result.returncode != 0:
        _fail(f"--help failed: {result.stderr}")
    required = ["detect", "generate", "validate", "self-test", "mcp-config", "serve"]
    missing = [item for item in required if item not in result.stdout]
    if missing:
        _fail(f"--help missing expected commands: {', '.join(missing)}")


def _assert_context_crafter_server(
    config: dict[str, Any],
    *,
    expected_command: str,
    expected_args: list[str] | None = None,
) -> dict[str, Any]:
    servers = config.get("mcpServers")
    if not isinstance(servers, dict) or "context-crafter" not in servers:
        _fail(f"missing context-crafter MCP server in config: {config!r}")
    server = servers["context-crafter"]
    if server.get("command") != expected_command:
        _fail(f"unexpected MCP command: {server.get('command')!r}")
    args = server.get("args")
    if not isinstance(args, list):
        _fail(f"MCP args must be a list: {args!r}")
    if expected_args is not None and args != expected_args:
        _fail(f"unexpected MCP args: {args!r}")
    return server


def _check_mcp_config() -> None:
    expected_clients = {
        "claude-desktop",
        "claude-code",
        "kimi",
        "cline",
        "roo",
        "vscode",
        "codex",
        "generic-stdio",
    }
    if set(MCP_CONFIG_TEMPLATES) != expected_clients:
        _fail(
            f"supported client set drifted: actual={sorted(MCP_CONFIG_TEMPLATES)}, expected={sorted(expected_clients)}"
        )

    for client in sorted(expected_clients):
        result = _run(CLI + ["mcp-config", "--client", client])
        if result.returncode != 0:
            _fail(f"mcp-config failed for {client}: {result.stderr or result.stdout}")
        config = json.loads(result.stdout)
        _assert_context_crafter_server(
            config,
            expected_command="uvx",
            expected_args=["context-crafter-mcp", "serve"],
        )

        local_result = _run(CLI + ["mcp-config", "--client", client, "--repo", str(ROOT)])
        if local_result.returncode != 0:
            _fail(f"local mcp-config failed for {client}: {local_result.stderr or local_result.stdout}")
        local_config = json.loads(local_result.stdout)
        server = _assert_context_crafter_server(local_config, expected_command="uv")
        args = server["args"]
        if args[:2] != ["--directory", str(ROOT)] or args[2:] != ["run", "context-crafter-mcp", "serve"]:
            _fail(f"local mcp-config args drifted for {client}: {args!r}")


def _send(stdin, obj: dict[str, Any]) -> None:
    stdin.write(json.dumps(obj) + "\n")
    stdin.flush()


def _readline(stdout_queue: queue.Queue[str], timeout: float = 10.0) -> str:
    try:
        return stdout_queue.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError("no stdout line within timeout") from exc


def _check_stdio_server() -> None:
    proc = subprocess.Popen(
        CLI + ["serve"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_queue: queue.Queue[str] = queue.Queue()

    def _reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            stdout_queue.put(line)

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    try:
        if proc.stdin is None:
            _fail("stdio server did not expose stdin")
        _send(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "public-surface-gate", "version": "1.0"},
                },
            },
        )
        init_response = json.loads(_readline(stdout_queue))
        if init_response.get("id") != 1 or "result" not in init_response:
            _fail(f"unexpected initialize response: {init_response!r}")

        _send(proc.stdin, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _send(proc.stdin, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools_response = json.loads(_readline(stdout_queue))
        tools = tools_response.get("result", {}).get("tools", [])
        tool_names = {tool.get("name") for tool in tools}
        missing = sorted(EXPECTED_TOOLS - tool_names)
        if missing:
            _fail(f"stdio tools/list missing tools: {', '.join(missing)}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    stderr = proc.stderr.read() if proc.stderr is not None else ""
    if stderr:
        _fail(f"stdio server wrote to stderr: {stderr}")


def _read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _check_docs_truth() -> None:
    docs = {
        "README.md": _read_doc("README.md"),
        "docs/MCP_CLIENTS.md": _read_doc("docs/MCP_CLIENTS.md"),
        "docs/OUTPUT_CONTRACT.md": _read_doc("docs/OUTPUT_CONTRACT.md"),
    }

    stale_phrases = ["full 8-file suite"]
    for path, content in docs.items():
        for phrase in stale_phrases:
            if phrase in content:
                _fail(f"{path} contains stale phrase {phrase!r}")

    for client in sorted(MCP_CONFIG_TEMPLATES):
        for path in ("README.md", "docs/MCP_CLIENTS.md"):
            if f"`{client}`" not in docs[path] and f"| {client} " not in docs[path]:
                _fail(f"{path} does not document supported MCP client {client!r}")

    for tool in sorted(EXPECTED_TOOLS):
        for path in ("README.md", "docs/MCP_CLIENTS.md"):
            if f"`{tool}`" not in docs[path]:
                _fail(f"{path} does not document MCP tool {tool!r}")

    for generated_file in sorted(GENERATED_FILES):
        for path in ("README.md", "docs/OUTPUT_CONTRACT.md"):
            if f"`{generated_file}`" not in docs[path]:
                _fail(f"{path} does not document generated file {generated_file!r}")


def main() -> int:
    checks = [
        ("version", _check_version),
        ("help", _check_help),
        ("mcp-config", _check_mcp_config),
        ("stdio server", _check_stdio_server),
        ("docs truth", _check_docs_truth),
    ]
    for name, check in checks:
        print(f"==> public surface: {name}")
        check()
    print("Public surface validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
