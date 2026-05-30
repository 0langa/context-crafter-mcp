---
mode: ask
description: "Create or extend a Context Crafter MCP tool with shared-core-safe implementation, regression tests, and docs sync."
---

Use `context-crafter-mcp-development`.

Goal:
- add or extend one MCP capability in `context-crafter-mcp`
- keep `server.py` thin
- reuse shared logic instead of embedding product logic in handlers
- preserve deterministic static-only behavior

Workflow:
1. inspect `src/context_crafter_mcp/server.py`, `src/context_crafter_mcp/cli.py`, relevant core modules, and matching tests
2. define exact tool contract:
   - tool name
   - input schema
   - output shape
   - warnings/errors
   - whether CLI alignment is needed
3. patch smallest responsible shared layer first
4. wire MCP tool handler in `server.py`
5. if capability overlaps CLI, update `cli.py`
6. add focused regression tests
7. update docs only if behavior changed
8. report commands run and exact results

Quality bar:
- no noisy stdout in stdio path
- no internal helper exposed as public MCP tool
- tests cover happy path + invalid input + contract shape
- docs do not overclaim
