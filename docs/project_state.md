# Project State

- Last reviewed: `2026-06-02`
- Memory model: `agent-authored, validator-checked`
- Critical rule: Update this file directly whenever repo reality changes. For long runs, update it at each meaningful milestone before context compaction risk grows.

## Repo Snapshot
`context-crafter-mcp` is a local-first Python MCP server and CLI that turns repositories into deterministic AI-agent context documents.

The checked-in product surface is centered on:

- `src/context_crafter_mcp/` for the CLI, MCP server, scanner, analyzers, and renderers
- `tests/` for the main confidence set
- `docs/` for contracts, architecture, smoke matrices, and limits
- `examples/outputs/` and `docs/generated/` as generated output examples, not as architecture source of truth

## Active Surfaces
- `.kimi/AGENTS.md` is the Kimi operating guide for this repo.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/OUTPUT_CONTRACT.md`, `docs/MCP_CLIENTS.md`, and `docs/LIMITATIONS.md` are the main durable docs that can drift.
- `src/context_crafter_mcp/cli.py` and `src/context_crafter_mcp/server.py` are the main entrypoints for CLI and MCP use.
- `scripts/validate_project_state.py` validates this file's contract and core references. It does not write repo truth for you.

## Current Truths
- Source code, tests, and packaging config beat prose docs when they disagree.
- The product is local-first and static-analysis-only. It should not claim to execute target repo code or call external models.
- Generated outputs under `docs/generated/` and `examples/outputs/` are artifacts and examples, not the authoritative description of current implementation.
- If MCP tool, CLI, or output-contract behavior changes, update the adjacent docs in the same change set.
- Keep claims explicit about what is observed, inferred, or still unverified.

## Validation Commands
Run the checks that match the surface you changed.

- Project-state validation:
  - `python .\scripts\validate_project_state.py`
- Python/package validation:
  - `python -m py_compile .\scripts\validate_project_state.py`
  - `uv run ruff check .`
  - `uv run mypy src`
  - `uv run pytest -q`
- CLI/runtime validation when behavior changes:
  - `uv run context-crafter-mcp --help`
  - `uv run context-crafter-mcp doctor`
  - `uv run context-crafter-mcp self-test .`

## Drift Watchlist
- `README.md`, `docs/MCP_CLIENTS.md`, and `docs/OUTPUT_CONTRACT.md` can drift when CLI flags, MCP tools, or generated-file expectations change.
- `docs/generated/` can look authoritative even though it is generated output; do not treat it as a design source.
- Optional parser support and confidence notes should stay aligned with `pyproject.toml`, tests, and smoke-matrix docs.
- If context is getting long, update this file before continuing. Delaying memory writes until the end of a large run is a repo risk.
