# Pre-1.0 Gate Checklist

Explicit checklist for the first stable release (`1.0.0`).

Current release note: this checklist was executed end-to-end on `2026-08-27` for the stable `1.0.0` release. Every item below is satisfied except the git tag, which is created by the release commit that carries this file. Keep the checklist as the standing bar for later releases.

## Required command pass set

- [x] Local reset-PC release gate passes:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1`
- [x] Public surface validation passes:
  - `python .\scripts\validate_public_surface.py`
- [x] `context-crafter-mcp --help` prints without error
- [x] `context-crafter-mcp version` matches `pyproject.toml`
- [x] `context-crafter-mcp doctor` reports healthy on a clean checkout
- [x] `context-crafter-mcp detect <repo> --json` returns valid JSON for all fixed smoke repos
- [x] `context-crafter-mcp generate <repo> --output <dir> --profile standard --json` produces 9 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`
- [x] `context-crafter-mcp validate <output_dir> --json` passes with zero errors
- [x] `context-crafter-mcp self-test .` passes without dirtying the repository
- [x] `context-crafter-mcp mcp-config --client <client>` emits valid JSON for every supported client
- [x] `context-crafter-mcp serve` starts the MCP stdio server and responds to initialize/tools-list

## Smoke expectations

- [x] Local generic fallback honesty guard passes:
  - `python -m pytest -q tests/test_generic_fallback_honesty.py`
- [x] Fixed smoke set passes automation:
  - `pallets/click`
  - `sindresorhus/ky`
  - `spf13/cobra`
  - `serde-rs/json`
- [x] Smoke results are captured in `docs/REAL_REPO_SMOKE_MATRIX.md`
- [x] No command crashes on any smoke repo
- [x] Output files are generated and validate cleanly or with documented non-blocking warnings

## Docs-truth expectations

- [x] `README.md` claims match actual CLI/MCP surface
- [x] `docs/LIMITATIONS.md` does not understate or overstate gaps
- [x] `docs/OUTPUT_CONTRACT.md` describes every generated file and JSON field accurately
- [x] `docs/PUBLIC_SURFACE_FREEZE.md` matches the CLI, MCP, resource, generated-file, and machine-readable JSON contracts
- [x] `docs/ARCHITECTURE.md` matches the current scanner/analyzer/renderer split
- [x] `SECURITY.md` threat model is current and complete
- [x] `MANUAL_STEPS.md` release checklist has been executed successfully at least once
- [x] `CHANGELOG.md` has a dated section for the release
- [x] No documentation claims real-repo confidence for stacks that are still fixture-only

## Stack confidence expectations

- [x] Python: real-repo smoke verified, AST-backed, no known blockers
- [x] Node/TypeScript: real-repo smoke verified, tree-sitter + regex fallback
- [x] Go: real-repo smoke verified, tree-sitter + regex fallback
- [x] Rust: real-repo smoke verified, tree-sitter + regex fallback
- [x] Java: fixture-backed + manual validation; real-repo smoke not required for 1.0 but gap documented
- [x] .NET: fixture-backed + manual validation; real-repo smoke not required for 1.0 but gap documented
- [x] Generic: always available, no blockers

## Gate execution evidence

Full local gate executed end-to-end on `2026-08-27` (Windows 11, Python 3.12, `uv`). The command pass set below ran against `main` at `0.9.0`; the gate was re-run after the `1.0.0` version bump and passed again.

| Command | Result |
|---------|--------|
| `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1` | pass (project-state, release-doc, ruff, mypy, pytest, doctor, public surface, self-test, generate, validate) |
| `python .\scripts\validate_public_surface.py` | pass (version, help, all 8 MCP client configs, stdio initialize/tools-list/resources, docs truth) |
| `powershell -ExecutionPolicy Bypass -File .\scripts\installed_artifact_smoke.ps1` | pass for wheel and sdist, re-run at `1.0.0` |
| `uv run python scripts/smoke_repos.py` | pass for all 4 fixed smoke repos; 0 errors |
| `uv run python -m pytest -q` | 258 passed, 1 skipped |
| `uv run python -m compileall -q src tests` | pass |
| `uv run ruff format --check .` | 77 files already formatted |
| `uv run context-crafter-mcp validate examples/outputs --repo examples/demo-repo --json` | pass, 9/9 required files, 0 errors |

The only remaining open item is the `1.0.0` git tag itself, which is created from the release commit that
carries this file.

## Current local-gate notes

- The retired D-drive battle-testing platform is not required for the current local gate.
- `scripts/local_release_gate.ps1` includes public-surface validation for CLI help/version, every supported MCP client config, and MCP stdio initialize/tools-list.
- `scripts/local_release_gate.ps1` includes release-doc validation so pre-`1.0.0` checklist wording, roadmap state, and workflow action baselines stay aligned with repo reality.
- `tests/test_session_completion_verifier.py` is optional and skips unless `CONTEXT_CRAFTER_TESTS_TOOL` points to a rebuilt verifier tool.
- Network-dependent real-repo smoke automation remains a separate release confidence step after the local gate is repeatable.

## MCP surface freeze expectations

- [x] `docs/PUBLIC_SURFACE_FREEZE.md` has been reviewed against CLI help, MCP tools-list, and generated output
- [x] Tool names and signatures are stable:
  - `detect_project`
  - `generate_context`
  - `generate_project_overview`
  - `generate_repo_map`
  - `generate_dependency_graph`
  - `generate_architecture_summary`
  - `validate_generated_context`
  - `explain_capabilities`
- [x] Resource URI scheme `context-crafter://latest/<filename>` is stable
- [x] JSON result fields are additive-only (no removals without deprecation cycle)
- [x] `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json` fields evolve additively (no removals without deprecation cycle); automation consumers should parse defensively

## Release artifacts

- [x] `pyproject.toml` version is `1.0.0`
- [x] `src/context_crafter_mcp/__init__.py` version is `1.0.0`
- [x] Wheel and sdist build cleanly
- [x] Installed artifact smoke passes:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\installed_artifact_smoke.ps1`
- [x] Installed wheel passes `doctor`, `self-test`, and `generate`/`validate`
- [x] Installed sdist passes the same checks
- [ ] Git tag `1.0.0` exists and points to the release commit (created at tag time; see step 8 of `MANUAL_STEPS.md`)
