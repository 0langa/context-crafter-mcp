---
description: "Repo-specific rules for source files in context-crafter-mcp. Use when editing core product code: CLI, MCP server, scanner, analyzers, ranking, validation, renderers, and models."
applyTo: "src/context_crafter_mcp/**/*.py"
---

# Context Crafter Source Rules

## Architecture

- Keep CLI and MCP surface thin; shared logic belongs in core modules.
- `server.py` defines tool/resource/prompt registration and marshaling only.
- `cli.py` defines CLI argument handling and output only.
- Scanner returns bounded snapshot/evidence; analyzers consume snapshot, not ad-hoc traversal.
- Validation and renderers must not invent facts absent from evidence.

## Contracts

- Preserve public CLI command names unless task explicitly changes them.
- Preserve public MCP tool names unless task explicitly changes them.
- Keep MCP result shapes structured and predictable.
- Do not expose internal helpers as MCP tools.
- Keep stdio path quiet: no stray stdout logging from server logic.

## Truthfulness

- Prefer observed over inferred claims.
- If certainty weak, emit warning/unknown/unsupported state rather than overclaim.
- Do not hide budget pressure, skipped files, parse failures, or mixed-monorepo ambiguity.

## Safety

- Static-only. No target repo execution.
- No network dependency for analysis.
- No arbitrary local resource reads through MCP resources.
- Preserve output confinement inside repo-safe paths.

## Editing pattern

- Patch smallest responsible layer first.
- Add or update regression tests for behavior changes.
- Update docs only for verified changes.
