---
mode: ask
description: "Change a shared capability across Context Crafter CLI and MCP surfaces without contract drift."
---

Use `context-crafter-mcp-development`.

Goal:
- modify a capability exposed through both CLI and MCP
- keep naming, args, output semantics, tests, and docs aligned

Workflow:
1. inspect `cli.py`, `server.py`, shared core module, and related tests/docs
2. define old contract and new contract
3. patch shared logic first
4. update CLI command behavior
5. update MCP tool schema/handler behavior
6. update tests for both surfaces
7. update docs that mention either path
8. report compatibility impact clearly

Quality bar:
- no silent drift between CLI and MCP semantics
- docs/examples align with code
- validation results reported exactly
