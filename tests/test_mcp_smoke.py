"""MCP smoke tests for tools/list and key tool calls."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mcp.types import CallToolRequest, ListToolsRequest, ReadResourceRequest

from context_crafter_mcp.server import app


@pytest.mark.anyio
async def test_list_tools() -> None:
    req = ListToolsRequest(method="tools/list", params=None)
    server_result = await app.request_handlers[ListToolsRequest](req)
    result = server_result.root
    names = [t.name for t in result.tools]
    assert "detect_project" in names
    assert "generate_context" in names
    assert "validate_generated_context" in names
    assert "explain_capabilities" in names


@pytest.mark.anyio
async def test_detect_project_tool() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        req = CallToolRequest(
            method="tools/call",
            params={"name": "detect_project", "arguments": {"repo_path": td}},
        )
        server_result = await app.request_handlers[CallToolRequest](req)
        result = server_result.root
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "python" in result.content[0].text


@pytest.mark.anyio
async def test_generate_context_tool() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        req = CallToolRequest(
            method="tools/call",
            params={
                "name": "generate_context",
                "arguments": {"repo_path": td, "output_dir": "out"},
            },
        )
        server_result = await app.request_handlers[CallToolRequest](req)
        result = server_result.root
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "ok" in result.content[0].text


@pytest.mark.anyio
async def test_explain_capabilities_tool() -> None:
    req = CallToolRequest(
        method="tools/call",
        params={"name": "explain_capabilities", "arguments": {}},
    )
    server_result = await app.request_handlers[CallToolRequest](req)
    result = server_result.root
    assert len(result.content) == 1
    assert "Context Crafter MCP" in result.content[0].text


@pytest.mark.anyio
async def test_read_resource_blocks_arbitrary_paths() -> None:
    req = ReadResourceRequest(
        method="resources/read",
        params={"uri": "file:///etc/passwd"},
    )
    server_result = await app.request_handlers[ReadResourceRequest](req)
    result = server_result.root
    assert len(result.contents) == 1
    assert "Access denied" in result.contents[0].text
