"""MCP smoke tests for tools/list and key tool calls."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mcp.types import CallToolRequest, ListResourcesRequest, ListToolsRequest, ReadResourceRequest

from context_crafter_mcp.server import _REGISTERED_RESOURCES, app


@pytest.fixture(autouse=True)
def _clear_registered_resources():
    _REGISTERED_RESOURCES.clear()
    yield
    _REGISTERED_RESOURCES.clear()


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


@pytest.mark.anyio
async def test_read_resource_allows_registered_generated_files() -> None:
    with tempfile.TemporaryDirectory() as td:
        Path(td, "main.py").write_text("print(1)\n")
        gen_req = CallToolRequest(
            method="tools/call",
            params={
                "name": "generate_context",
                "arguments": {"repo_path": td, "output_dir": "out"},
            },
        )
        await app.request_handlers[CallToolRequest](gen_req)

        # Should be listed
        list_req = ListResourcesRequest(method="resources/list", params=None)
        list_result = await app.request_handlers[ListResourcesRequest](list_req)
        uris = [str(r.uri) for r in list_result.root.resources]
        assert any("AI_CONTEXT_INDEX.md" in u for u in uris)

        # Should be readable
        uri = "context-crafter://latest/AI_CONTEXT_INDEX.md"
        read_req = ReadResourceRequest(
            method="resources/read",
            params={"uri": uri},
        )
        read_result = await app.request_handlers[ReadResourceRequest](read_req)
        assert len(read_result.root.contents) == 1
        assert "AI Context Index" in read_result.root.contents[0].text

        # Unknown file should be denied
        bad_req = ReadResourceRequest(
            method="resources/read",
            params={"uri": "context-crafter://latest/SECRET.md"},
        )
        bad_result = await app.request_handlers[ReadResourceRequest](bad_req)
        assert "Access denied" in bad_result.root.contents[0].text
