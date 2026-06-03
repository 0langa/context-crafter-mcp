# Project State

- Last reviewed: `2026-06-03`
- Package version: `0.6.0`
- Latest public git tag: `0.6.0`
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
- `.kimi-code/AGENTS.md` is the Kimi operating guide for this repo.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/OUTPUT_CONTRACT.md`, `docs/MCP_CLIENTS.md`, and `docs/LIMITATIONS.md` are the main durable docs that can drift.
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md` is the tracked repo-side anchor for the external `context-crafter-tests` planning and future reporting flow.
- `CHANGELOG.md`, `docs/ROADMAP.md`, `docs/REAL_REPO_SMOKE_MATRIX.md`, `MANUAL_STEPS.md`, and `IMPLEMENTATION_REPORT.md` are release-truth docs that must stay aligned with the current version.
- `src/context_crafter_mcp/cli.py` and `src/context_crafter_mcp/server.py` are the main entrypoints for CLI and MCP use.
- `scripts/validate_project_state.py` validates this file's contract and core references. It does not write repo truth for you.
- `scripts/smoke_repos.py` is the real-repo smoke automation for the fixed Python/Node/Go/Rust set.

## Current Truths
- Source code, tests, and packaging config beat prose docs when they disagree.
- The product is local-first and static-analysis-only. It should not claim to execute target repo code or call external models.
- Generated outputs under `docs/generated/` and `examples/outputs/` are artifacts and examples, not the authoritative description of current implementation.
- The external test-platform planning source of truth currently lives under `D:\DEVTESTING\context-crafter-mcp\DOCUMENTS\planning-and-setup\`; the tracked repo-side handoff anchor is `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`.
- If MCP tool, CLI, or output-contract behavior changes, update the adjacent docs in the same change set.
- Keep claims explicit about what is observed, inferred, or still unverified.
- Python/Node/Go/Rust have real-repo smoke confidence. Java/.NET remain fixture-backed and lower-confidence.
- `RUN_STATE.json` schema is additive; consumers should parse defensively.
- The external battle-testing platform (`context-crafter-tests` on `D:\DEVTESTING`) is operational with 17 scenarios, ~4,389 files, ~190,384 lines.
- The dominant current product failure from the external platform is `L1-GENERIC-001` generic fallback honesty (score 40.0 vs floor 90.0).
- The platform bounded-scan honesty logic now uses a three-tier materiality test: hard blocker for `budget_exhausted`, major blocker for material non-budget skips (>=5 files or >=5% ratio), minor finding for benign skips only.
- Repo-side mirror docs (`docs/testing/TESTING_STATUS.md`) describe stable facts only; volatile "latest run" state lives on the D-drive platform.

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
- Release validation:
  - `uv run context-crafter-mcp generate . --output docs/generated --profile standard --json`
  - `uv run context-crafter-mcp validate docs/generated --json`
  - `uv run python scripts/smoke_repos.py`

## Drift Watchlist
- `README.md`, `docs/MCP_CLIENTS.md`, and `docs/OUTPUT_CONTRACT.md` can drift when CLI flags, MCP tools, or generated-file expectations change.
- `CHANGELOG.md`, `docs/ROADMAP.md`, `docs/REAL_REPO_SMOKE_MATRIX.md`, and `IMPLEMENTATION_REPORT.md` can drift when versions or release scope changes.
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md` can drift if the D-drive planning contracts or mirror-back reporting paths change.
- `docs/testing/TESTING_STATUS.md` is a stable-facts summary, not a live latest-run mirror. It describes platform overview, canonical D-drive paths, and known stable failure patterns. It must NOT claim specific run IDs, timestamps, or pass/fail counts. Update it only when stable facts change (e.g., scenario count, scale, known failure patterns). Volatile latest-run state lives on the D-drive platform.
- `docs/generated/` can look authoritative even though it is generated output; do not treat it as a design source.
- Optional parser support and confidence notes should stay aligned with `pyproject.toml`, tests, and smoke-matrix docs.
- If context is getting long, update this file before continuing. Delaying memory writes until the end of a large run is a repo risk.
