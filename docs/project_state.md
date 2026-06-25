# Project State

- Last reviewed: `2026-06-25`
- Package version: `0.7.0b1`
- Latest public git tag: `0.7.0b1`
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
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md` is the tracked repo-side anchor for rebuilding or replacing the retired external `context-crafter-tests` planning and reporting flow.
- The old D-drive external testing platform no longer exists on the current development machine. Treat previous D-drive references as historical only.
- `CHANGELOG.md`, `docs/ROADMAP.md`, `docs/REAL_REPO_SMOKE_MATRIX.md`, `MANUAL_STEPS.md`, and `IMPLEMENTATION_REPORT.md` are release-truth docs that must stay aligned with the current version.
- `src/context_crafter_mcp/cli.py` and `src/context_crafter_mcp/server.py` are the main entrypoints for CLI and MCP use.
- `scripts/validate_project_state.py` validates this file's contract and core references. It does not write repo truth for you.
- `scripts/validate_release_docs.py` validates release-truth docs against current tag/HEAD and workflow action baselines.
- `scripts/local_release_gate.ps1` is the current reset-PC local release gate command bundle.
- `scripts/validate_public_surface.py` checks CLI help/version, every supported MCP client config, and MCP stdio initialize/tools-list.
- `scripts/smoke_repos.py` is the real-repo smoke automation for the fixed Python/Node/Go/Rust set.
- GitHub Actions workflows use Node 24-compatible actions: `actions/checkout@v7`, `actions/setup-python@v6`, and immutable `astral-sh/setup-uv@v8.2.0`.

## Current Truths
- Source code, tests, and packaging config beat prose docs when they disagree.
- The product is local-first and static-analysis-only. It should not claim to execute target repo code or call external models.
- Generated outputs under `docs/generated/` and `examples/outputs/` are artifacts and examples, not the authoritative description of current implementation.
- There is currently no live external battle-testing platform available in this setup. Rebuild it intentionally before using any external run claims as release evidence.
- If MCP tool, CLI, or output-contract behavior changes, update the adjacent docs in the same change set.
- Keep claims explicit about what is observed, inferred, or still unverified.
- Python/Node/Go/Rust have real-repo smoke confidence. Java/.NET remain fixture-backed and lower-confidence.
- `RUN_STATE.json` schema is additive; consumers should parse defensively.
- Historical external battle-testing material referenced 17 scenarios, ~4,499 files, and ~196,129 lines, but those artifacts are unavailable after the PC reset.
- The historical dominant product failure was `L1-GENERIC-001` generic fallback honesty. Local regression coverage now lives in `tests/test_generic_fallback_honesty.py`.
- Stack detection promotes marker/extension evidence only from trusted primary-surface paths; low-trust docs/tests/examples/tooling hints stay non-promoting and keep ambiguous repos generic.
- The local release gate is `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1`; network-dependent smoke testing remains separate.
- The current release is the `0.7.0b1` beta prerelease. It is not the stable `1.0.0` gate.
- CI and CodeQL should stay free of Node 20 deprecation annotations before any stable-release cut.
- Fresh fixed real-repo smoke automation passed on `2026-06-25` for `pallets/click`, `sindresorhus/ky`, `spf13/cobra`, and `serde-rs/json`.
- The historical bounded-scan honesty logic used a three-tier materiality test: hard blocker for `budget_exhausted`, major blocker for material non-budget skips (>=5 files or >=5% ratio), minor finding for benign skips only.
- Repo-side mirror docs (`docs/testing/TESTING_STATUS.md`) describe stable/historical facts only; volatile latest-run state is currently unavailable.
- Durable session-end testing reports should be recreated in a tracked or newly documented location before release-gate claims depend on them.

## Validation Commands
Run the checks that match the surface you changed.

- Project-state validation:
  - `python .\scripts\validate_project_state.py`
- Release-doc validation:
  - `python .\scripts\validate_release_docs.py`
- Python/package validation:
  - `python -m py_compile .\scripts\validate_project_state.py`
  - `uv run ruff check .`
  - `uv run mypy src`
  - `uv run pytest -q`
- CLI/runtime validation when behavior changes:
  - `uv run context-crafter-mcp --help`
  - `uv run context-crafter-mcp doctor`
  - `python .\scripts\validate_public_surface.py`
  - `uv run context-crafter-mcp self-test .`
- Local release gate:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1`
- Release validation:
  - `uv run context-crafter-mcp generate . --output docs/generated --profile standard --json`
  - `uv run context-crafter-mcp validate docs/generated --json`
  - `uv run python scripts/smoke_repos.py`

## Drift Watchlist
- `README.md`, `docs/MCP_CLIENTS.md`, and `docs/OUTPUT_CONTRACT.md` can drift when CLI flags, MCP tools, or generated-file expectations change.
- `CHANGELOG.md`, `docs/ROADMAP.md`, `docs/REAL_REPO_SMOKE_MATRIX.md`, and `IMPLEMENTATION_REPORT.md` can drift when versions or release scope changes.
- `docs/testing/TEST_ENVIRONMENT_HANDOFF.md` can drift if a replacement external testing platform is created or if release-evidence rules change.
- `docs/testing/TESTING_STATUS.md` is a stable-facts summary, not a live latest-run mirror. It describes historical platform context, current availability, and known stable failure patterns. It must NOT claim specific run IDs, timestamps, or pass/fail counts. Update it only when stable facts change or a replacement platform is created.
- `docs/generated/` can look authoritative even though it is generated output; do not treat it as a design source.
- Optional parser support and confidence notes should stay aligned with `pyproject.toml`, tests, and smoke-matrix docs.
- If context is getting long, update this file before continuing. Delaying memory writes until the end of a large run is a repo risk.
