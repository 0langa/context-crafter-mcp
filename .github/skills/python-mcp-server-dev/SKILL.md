---
name: python-mcp-server-dev
description: "Develop and extend Python MCP servers with a grounded workflow for repo intake, tool design, implementation, validation, and docs sync. Use when: Python MCP server, Model Context Protocol server in Python, add MCP tool, extend MCP server, stdio MCP, MCP handler, MCP resource, MCP prompt, MCP server tests, verify MCP server behavior."
---

# Python MCP Server Development

Use this skill when building or extending MCP servers written in Python.

## Outcomes

- Map current server structure before edits.
- Add or update MCP tools/resources/prompts with shared-core patterns.
- Keep transport behavior quiet, deterministic, and testable.
- Verify CLI/server behavior and sync docs with truth.

## Workflow

### 1. Intake repo first

- Find product entrypoints: CLI, server bootstrap, package config, tests.
- Identify MCP surface already present: tools, resources, prompts, schemas, result shapes.
- Inspect how request handling reaches shared services.
- Note validation path, logging rules, stdout/stderr constraints, and test style.

### 2. Define exact change

- Clarify target: new capability vs extension of existing capability.
- Write down:
	- inputs
	- outputs
	- error cases
	- deterministic constraints
	- files likely affected
- Prefer smallest public-surface change that solves request.

### 3. Choose placement

- Put transport-facing code in server/CLI layer only.
- Put reusable logic in shared modules/services.
- Reuse existing models/schema helpers before inventing new ones.
- Avoid ad-hoc filesystem/network/process behavior unless already part of project contract.

### 4. Implement safely

- Preserve existing response envelope/style.
- Return structured results with explicit `ok`, `summary`, `warnings`, `errors`, and stats when project uses them.
- Keep stdout clean for stdio mode; avoid human chatter from server path.
- Add narrow types/models instead of loose dict sprawl when possible.
- Keep naming aligned with existing MCP tool naming conventions.

### 5. Add regression coverage

- Update or add focused tests for:
	- happy path
	- invalid input
	- edge/empty cases
	- transport contract or output schema
- Prefer unit tests around shared logic plus one integration/smoke test for server surface when useful.
- Do not add brittle tests coupled to incidental wording unless wording is contract.

### 6. Validate strongest feasible set

- Run relevant targeted tests first.
- Then run broader checks appropriate for repo, such as:
	- compile/import checks
	- lint/format
	- type checks
	- MCP smoke tests
- If command fails, capture exact blocker and fix or report precisely.

### 7. Sync docs if behavior changed

- Update README/help/docs/changelog only for verified behavior changes.
- Remove stale claims instead of documenting fantasy support.
- Keep examples consistent with actual command names and result shapes.

## Decision points

### New tool or extend existing one?

- Extend existing tool when behavior is same domain and schema can evolve compatibly.
- Add new tool when capability is distinct, naming would become muddy, or compatibility risk is high.

### Shared helper or inline logic?

- Use shared helper when logic is reusable, testable in isolation, or needed by CLI + server.
- Keep inline only when logic is trivial and transport-specific.

### Ask user before proceeding?

- Ask when contract unclear, irreversible behavior shift, multiple valid public APIs, or deployment/runtime assumptions missing.
- Skip asking when request is precise and repo patterns already dictate one clear path.

## Quality bar

Done means:

- behavior grounded in existing repo architecture
- public MCP surface minimal and predictable
- tests cover new behavior meaningfully
- validation commands run or blockers reported exactly
- docs updated if and only if behavior changed
- no noisy stdout/logging regressions in stdio mode

## Common pitfalls

- Putting business logic directly in MCP handlers.
- Returning inconsistent shapes across tools.
- Printing diagnostics to stdout in server mode.
- Adding broad filesystem access without safety contract.
- Claiming support not covered by tests or code path.
- Editing docs without verifying commands/results.

## Prompt patterns

Use this skill for prompts like:

- "Add a new tool to this Python MCP server."
- "Extend existing Python MCP server capability with validation and tests."
- "Review this Python MCP server design before implementation."
- "Make this stdio MCP server deterministic and properly tested."

