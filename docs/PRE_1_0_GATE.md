# Pre-1.0 Gate Checklist

Explicit checklist for the first stable release (`1.0.0`).

Current release note: `0.8.0` is the consumer-value release line. Passing the local gate is required for `0.8.0`, but the full stable `1.0.0` checklist below remains open until wheel/sdist, smoke, docs-truth, and surface-freeze evidence are complete.

## Required command pass set

- [ ] Local reset-PC release gate passes:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\local_release_gate.ps1`
- [ ] Public surface validation passes:
  - `python .\scripts\validate_public_surface.py`
- [ ] `context-crafter-mcp --help` prints without error
- [ ] `context-crafter-mcp version` matches `pyproject.toml`
- [ ] `context-crafter-mcp doctor` reports healthy on a clean checkout
- [ ] `context-crafter-mcp detect <repo> --json` returns valid JSON for all fixed smoke repos
- [ ] `context-crafter-mcp generate <repo> --output <dir> --profile standard --json` produces 9 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`
- [ ] `context-crafter-mcp validate <output_dir> --json` passes with zero errors
- [ ] `context-crafter-mcp self-test .` passes without dirtying the repository
- [ ] `context-crafter-mcp mcp-config --client <client>` emits valid JSON for every supported client
- [ ] `context-crafter-mcp serve` starts the MCP stdio server and responds to initialize/tools-list

## Smoke expectations

- [ ] Local generic fallback honesty guard passes:
  - `python -m pytest -q tests/test_generic_fallback_honesty.py`
- [ ] Fixed smoke set passes automation:
  - `pallets/click`
  - `sindresorhus/ky`
  - `spf13/cobra`
  - `serde-rs/json`
- [ ] Smoke results are captured in `docs/REAL_REPO_SMOKE_MATRIX.md`
- [ ] No command crashes on any smoke repo
- [ ] Output files are generated and validate cleanly or with documented non-blocking warnings

## Docs-truth expectations

- [ ] `README.md` claims match actual CLI/MCP surface
- [ ] `docs/LIMITATIONS.md` does not understate or overstate gaps
- [ ] `docs/OUTPUT_CONTRACT.md` describes every generated file and JSON field accurately
- [ ] `docs/ARCHITECTURE.md` matches the current scanner/analyzer/renderer split
- [ ] `SECURITY.md` threat model is current and complete
- [ ] `MANUAL_STEPS.md` release checklist has been executed successfully at least once
- [ ] `CHANGELOG.md` has a dated section for the release
- [ ] No documentation claims real-repo confidence for stacks that are still fixture-only

## Stack confidence expectations

- [ ] Python: real-repo smoke verified, AST-backed, no known blockers
- [ ] Node/TypeScript: real-repo smoke verified, tree-sitter + regex fallback
- [ ] Go: real-repo smoke verified, tree-sitter + regex fallback
- [ ] Rust: real-repo smoke verified, tree-sitter + regex fallback
- [ ] Java: fixture-backed + manual validation; real-repo smoke not required for 1.0 but gap documented
- [ ] .NET: fixture-backed + manual validation; real-repo smoke not required for 1.0 but gap documented
- [ ] Generic: always available, no blockers

## Current local-gate notes

- The retired D-drive battle-testing platform is not required for the current local gate.
- `scripts/local_release_gate.ps1` includes public-surface validation for CLI help/version, every supported MCP client config, and MCP stdio initialize/tools-list.
- `scripts/local_release_gate.ps1` includes release-doc validation so pre-`1.0.0` checklist wording, roadmap state, and workflow action baselines stay aligned with repo reality.
- `tests/test_session_completion_verifier.py` is optional and skips unless `CONTEXT_CRAFTER_TESTS_TOOL` points to a rebuilt verifier tool.
- Network-dependent real-repo smoke automation remains a separate release confidence step after the local gate is repeatable.

## MCP surface freeze expectations

- [ ] Tool names and signatures are stable:
  - `detect_project`
  - `generate_context`
  - `generate_project_overview`
  - `generate_repo_map`
  - `generate_dependency_graph`
  - `generate_architecture_summary`
  - `validate_generated_context`
  - `explain_capabilities`
- [ ] Resource URI scheme `context-crafter://latest/<filename>` is stable
- [ ] JSON result fields are additive-only (no removals without deprecation cycle)
- [ ] `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json` fields evolve additively (no removals without deprecation cycle); automation consumers should parse defensively

## Release artifacts

- [ ] `pyproject.toml` version is `1.0.0`
- [ ] `src/context_crafter_mcp/__init__.py` version is `1.0.0`
- [ ] Wheel and sdist build cleanly
- [ ] Installed wheel passes `doctor`, `self-test`, and `generate`/`validate`
- [ ] Installed sdist passes the same checks
- [ ] Git tag `1.0.0` exists and points to the release commit
