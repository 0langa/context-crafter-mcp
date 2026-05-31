"""MCP stdio quietness runtime test."""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading

PYTHON = sys.executable
SERVER_MODULE = "context_crafter_mcp.server"


def _send(stdin, obj: dict) -> None:
    stdin.write(json.dumps(obj) + "\n")
    stdin.flush()


def _readline(stdout_queue: queue.Queue, timeout: float = 10.0) -> str:
    try:
        return stdout_queue.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError("No stdout line within timeout")


def test_stdio_every_line_is_valid_json() -> None:
    """Spawn server, send JSON-RPC, assert no log noise on stdout."""
    proc = subprocess.Popen(
        [PYTHON, "-m", SERVER_MODULE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_queue: queue.Queue = queue.Queue()

    def _reader() -> None:
        for line in proc.stdout:
            stdout_queue.put(line)

    reader_thread = threading.Thread(target=_reader, daemon=True)
    reader_thread.start()

    try:
        _send(
            proc.stdin,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"},
                },
            },
        )
        line1 = _readline(stdout_queue)
        assert line1.strip(), "Expected initialize response"
        data1 = json.loads(line1)
        assert data1.get("id") == 1

        _send(
            proc.stdin,
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )

        _send(
            proc.stdin,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        line2 = _readline(stdout_queue)
        assert line2.strip(), "Expected tools/list response"
        data2 = json.loads(line2)
        assert data2.get("id") == 2
        assert "result" in data2

        _send(
            proc.stdin,
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/list", "params": {}},
        )
        line3 = _readline(stdout_queue)
        assert line3.strip(), "Expected prompts/list response"
        data3 = json.loads(line3)
        assert data3.get("id") == 3
        assert "result" in data3
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    # stderr must be empty (no log noise)
    assert proc.stderr.read() == ""
