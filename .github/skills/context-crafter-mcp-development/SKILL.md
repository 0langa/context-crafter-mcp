---
name: context-crafter-mcp-development
description: "Develop context-crafter-mcp with a repo-specific workflow for MCP tool changes, scanner-safe architecture, regression tests, validation runs, and docs truth sync. Use when: add MCP tool, extend context-crafter tool, modify server.py, change CLI + MCP contract, update generated output contract, improve validation, improve ranking, improve scanner behavior, or ship a feature in context-crafter-mcp."
---

# Context Crafter MCP Development

Use this skill for feature work in `context-crafter-mcp`.

## Outcome

Ship grounded changes to CLI or MCP server without breaking:

- deterministic static-only analysis
- bounded scanning
- small predictable MCP surface
- clean stdio behavior
- source-grounded generated docs

## Repo map first

Read before edits:

- `AGENTS.md`
- `src/context_crafter_mcp/server.py`
- `src/context_crafter_mcp/cli.py`
- relevant shared module under `src/context_crafter_mcp/`
- relevant tests under `tests/`
- docs matching changed contract

## Working model

Treat repo as 3 layers:

1. surface layer
   - CLI commands in `cli.py`
   - MCP tools/resources/prompts in `server.py`
2. core layer
   - scanner, detectors, analyzers, ranking, graph, validation, renderers
3. contract layer
   - JSON result shapes
   - generated file set
   - docs and tests proving behavior

Keep business logic out of surface layer.

## Standard workflow

### 1. Intake

- identify exact public contract touched
- find shared logic path
- list likely tests to update
- note docs that could become stale

### 2. Define change

Write down:

- input args
- output keys
- warnings/errors shape
- determinism or safety constraints
- whether CLI and MCP must stay aligned

### 3. Patch smallest layer

- prefer shared helper/module changes first
- wire CLI and server after shared logic stable
- avoid duplicate branching in `cli.py` and `server.py`

### 4. Add regression coverage

At minimum cover:

- happy path
- invalid or edge input
- contract shape
- safety boundary if touched

If MCP surface changed, add or update `tests/test_mcp_smoke.py` or `tests/test_mcp_tools.py`.

### 5. Validate

Preferred order:

1. focused pytest file
2. `uv run python -m compileall src tests`
3. `uv run ruff check .`
4. `uv run mypy src`
5. `uv run pytest -q`

Run strongest feasible subset. Report exact blockers if any step cannot pass.

### 6. Sync docs

Update only verified behavior:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_CONTRACT.md`
- `docs/MCP_CLIENTS.md`
- `CHANGELOG.md`
- `IMPLEMENTATION_REPORT.md`

## Decision rules

### Change belongs in `server.py` when

- defining MCP tool schema
- registering resource/prompt handlers
- marshaling request args into shared logic

### Change does **not** belong in `server.py` when

- scanning filesystem
- ranking files
- language analysis
- rendering docs
- validating output

### Change needs both CLI and MCP updates when

- same user capability exists in both surfaces
- result shape or argument semantics changed
- docs describe both paths together

## Repo-specific quality bar

Done means:

- no noisy stdout regression in stdio mode
- MCP tool names stay small/predictable
- output confinement and resource safety preserved
- tests prove changed behavior
- docs do not overclaim

## Anti-patterns

- embedding scanner/ranking logic inside tool handler
- changing JSON keys casually
- widening MCP tool surface for internal helpers
- hiding uncertainty instead of warning
- fixing challenge-repo behavior with repo-specific hacks

## Prompt examples

- "Use context-crafter-mcp-development to add a new MCP capability with tests."
- "Use context-crafter-mcp-development to refactor shared logic out of `server.py`."
- "Use context-crafter-mcp-development to keep CLI and MCP contracts aligned for this feature."
