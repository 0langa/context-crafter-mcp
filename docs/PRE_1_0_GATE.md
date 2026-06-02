# Pre-1.0 Gate Checklist

Explicit checklist for the first stable release (`1.0.0`).

## Required command pass set

- [ ] `context-crafter-mcp --help` prints without error
- [ ] `context-crafter-mcp version` matches `pyproject.toml`
- [ ] `context-crafter-mcp doctor` reports healthy on a clean checkout
- [ ] `context-crafter-mcp detect <repo> --json` returns valid JSON for all fixed smoke repos
- [ ] `context-crafter-mcp generate <repo> --output <dir> --profile standard --json` produces all 8 Markdown files + `RUN_STATE.json`
- [ ] `context-crafter-mcp validate <output_dir> --json` passes with zero errors
- [ ] `context-crafter-mcp self-test .` passes without dirtying the repository
- [ ] `context-crafter-mcp mcp-config --client <client>` emits valid JSON for every supported client
- [ ] `context-crafter-mcp serve` starts the MCP stdio server

## Smoke expectations

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
- [ ] `RUN_STATE.json` structure is stable enough for automation consumers

## Release artifacts

- [ ] `pyproject.toml` version is `1.0.0`
- [ ] `src/context_crafter_mcp/__init__.py` version is `1.0.0`
- [ ] Wheel and sdist build cleanly
- [ ] Installed wheel passes `doctor`, `self-test`, and `generate`/`validate`
- [ ] Installed sdist passes the same checks
- [ ] Git tag `1.0.0` exists and points to the release commit
