# Context Crafter MCP Customizations

This repository includes repo-scoped customizations to help coding agents work on `context-crafter-mcp` safely and efficiently.

## Purpose

The customization set is tuned for this repository's actual product shape:

- Python CLI + stdio MCP server
- deterministic, local-first, static-only analysis
- thin surface layer in `cli.py` and `server.py`
- shared core logic in scanner, analyzers, ranking, validation, and renderers
- strict truthfulness and no-overclaim documentation

These files are intended to reduce drift, encourage regression-first work, and keep agent changes aligned with the repository contract.

## Layout

### Skills

Located in `.github/skills/`.

- `context-crafter-mcp-development`
  - use for general feature work on CLI, MCP tools, shared logic, tests, and docs sync
- `context-crafter-analyzer-authoring`
  - use for detector/analyzer/ranking work and language-analysis changes
- `context-crafter-evidence-grounding`
  - use for confidence, warning quality, validation hardening, and docs truthfulness
- `python-mcp-server-dev`
  - broader Python MCP workflow skill; still useful, but less repo-specific than the skills above

### Instructions

Located in `.github/instructions/`.

- `context-crafter-src.instructions.md`
  - applies to `src/context_crafter_mcp/**/*.py`
  - keeps source-layer boundaries, safety, and truthfulness rules visible
- `context-crafter-tests.instructions.md`
  - applies to `tests/**/*.py`
  - reinforces regression-first test patterns and challenge-repo discipline
- `context-crafter-customization.instructions.md`
  - applies to `.github/**/*.md`
  - keeps future customization files grounded and narrowly scoped

### Agents

Located in `.github/agents/`.

- `context-crafter-mcp-implementer.agent.md`
  - focused agent for MCP/CLI feature work and shared-core-safe implementation
- `context-crafter-analyzer.agent.md`
  - focused agent for analyzers, detectors, ranking, validation, and challenge-repo work
- `context-crafter-docs-sync.agent.md`
  - focused agent for syncing docs to verified code behavior

### Hooks

Located in `.github/hooks/`.

- `check_stdio_quiet.py`
  - flags obvious stdout/logging noise markers in `server.py`
- `check_mcp_contract_sync.py`
  - flags obvious drift between key MCP tools and CLI commands
- `check_generated_contract.py`
  - checks required generated-doc contract markers remain visible
- `hooks.json`
  - example hook registration file tying checks to edit operations

## How to use

### For general feature work

Use:

- `context-crafter-mcp-development`
- optionally `context-crafter-mcp-implementer.agent.md`

Example prompt:

- "Use `context-crafter-mcp-development` to add a new MCP tool with regression tests and docs sync."

### For analyzer or ranking work

Use:

- `context-crafter-analyzer-authoring`
- `context-crafter-evidence-grounding`
- optionally `context-crafter-analyzer.agent.md`

Example prompt:

- "Use `context-crafter-analyzer-authoring` to improve deep entrypoint detection without overclaiming."

### For docs cleanup

Use:

- `context-crafter-docs-sync.agent.md`
- `context-crafter-evidence-grounding`

Example prompt:

- "Use `context-crafter-docs-sync` to sync `README.md` and `docs/OUTPUT_CONTRACT.md` to actual code."

## Design principles

These customizations assume:

- code and tests are source of truth
- CLI and MCP public contracts should stay stable unless intentionally changed
- MCP stdio mode must not emit stray human text to stdout
- generated docs must be source-grounded and honest about unknowns
- challenge-repo fixes must generalize, not hardcode against one repository

## Notes about hooks

The Python hook scripts are ready to run, but the exact activation mechanism depends on the client/tool host.

`hooks.json` is included as a starting point, not guaranteed final wiring for every environment.
If your active host expects a different hook schema, adapt the config while keeping the same checks.

## Suggested next additions

If this customization system grows, good next files are:

- `.github/prompts/create-mcp-tool.prompt.md`
- `.github/prompts/harden-analyzer.prompt.md`
- `.github/prompts/docs-truth-sync.prompt.md`
- hook or task wiring that runs the checks in your preferred environment

## Maintenance rule

When product architecture or public contracts change, update these customizations too.

At minimum, review:

- skill descriptions and prompt triggers
- instruction `applyTo` scopes
- agent role boundaries
- hook checks tied to file names or contracts
