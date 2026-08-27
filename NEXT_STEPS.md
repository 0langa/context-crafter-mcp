# Context Crafter MCP — Status & Roadmap
_Last updated: 2026-08-27 (1.0.0 shipped)_

## What this is
A local-first MCP server and CLI that turns any source repository into a compact, truthful AI-agent
context bundle: 9 Markdown docs plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`,
`CONTEXT_MANIFEST.json`, and `RUN_STATE.json`. Stack: Python 3.11+, `uv` + hatchling packaging,
MCP SDK (`mcp[cli]`), langgraph, pydantic, optional tree-sitter parsers; pytest/ruff/mypy;
GitHub Actions (`ci.yml`, `codeql.yml`, `smoke-repos.yml`, `release.yml`).

## Current state

**1.0.0 is released.** The "one executed checklist away" note from the July audit is closed out.

- Published to PyPI as `context-crafter-mcp` via trusted publishing. `uvx context-crafter-mcp serve`
  resolves the real package, so the MCP client config the README has always documented is now true.
- GitHub release `1.0.0` carries the wheel and sdist.
- `docs/PRE_1_0_GATE.md` was executed end-to-end on 2026-08-27 and holds a dated evidence table.
  Every box is checked.
- Public contract frozen under semver per `docs/PUBLIC_SURFACE_FREEZE.md`. Removals now need a
  deprecation cycle.
- Also ships as a plugin-forge plugin for Claude Code, Codex, and Kimi Code: `forge.yaml`, the
  `crafter:using-context-crafter` and `crafter:onboard-repo` skills, and the `/context-map` command.
  The plugin runs the server from the checkout, so it does not depend on the published package.

## Known gaps (accepted, documented)

- Java and .NET remain fixture-only confidence. Documented in `docs/LIMITATIONS.md`. Not a blocker
  for 1.0; promoting them is the main outstanding quality item.
- The external test platform is retired; `..\context-crafter-tests` is empty. Rebuild instructions
  live in `docs/testing/TEST_ENVIRONMENT_HANDOFF.md`.
- Root still carries planning clutter (`DEVELOPMENT_ROADMAP for context-crafter-mcp.txt`,
  `IMPLEMENTATION_REPORT.md`) that belongs under `docs/internal/`.

## Traps for future maintainers

- **`uuid-utils` is capped on purpose.** Nothing imports it directly, so it looks like dead weight.
  It is a transitive dep via `mcp`, capped because newer releases have shipped without a cp313 wheel
  and break the Python 3.13 CI leg. `pyproject.toml` now carries a comment saying so.
- **`scripts/validate_release_docs.py` pins the GitHub Actions baseline.** Bumping an action in a
  workflow without updating `EXPECTED_ACTION_BASELINES`, `docs/project_state.md`, and `CHANGELOG.md`
  in the same change fails the gate. That is intentional — it is what keeps the docs honest.
- **Stale dependabot branches can revert things.** PR #4 sat open long enough that merging it would
  have downgraded `checkout`, `setup-uv`, and `setup-python`, and deleted the setup-uv cache-suffix.
  Check the diff direction before merging an old dependabot PR, not just its green tick.
- **`mcp-config` output format is per-client and frozen.** `codex` emits TOML; everything else emits
  JSON. `scripts/validate_public_surface.py` parses each client in its own format.

## Roadmap

### Next (post-1.0, additive only)
- Promote Java and .NET from fixture-only to real-repo smoke confidence
  (`test_java_analyzer.py` / `test_dotnet_analyzer.py` already anchor the fixtures).
- Fold `IMPLEMENTATION_REPORT.md` and the root roadmap `.txt` into `docs/internal/`.
- Decide whether to publish the plugin to a marketplace, or leave it install-from-source.

### Later (stretch)
- Incremental regeneration (changed-scope re-render) so large repos do not pay full-scan cost —
  AICtx in this portfolio already solved changed-scope logic worth borrowing.
- Richer `CONTEXT_MANIFEST.json` consumers, HTML renderer polish (`test_html_renderer.py` exists),
  MCP resource pagination for big bundles.

## Release process
`MANUAL_STEPS.md` is the checklist of record. In short: bump version, cut the changelog section, run
`scripts/local_release_gate.ps1` + `validate_public_surface.py` + `installed_artifact_smoke.ps1`,
refresh the smoke matrix, commit, tag, push. `release.yml` handles PyPI and the GitHub release from
the tag. Trusted publishing is already configured for `release.yml` / environment `pypi`.
