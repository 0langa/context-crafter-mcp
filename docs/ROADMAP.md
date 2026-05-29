# Roadmap

## Current state

Package is at **v0.4.0**. Core scanner, CLI, MCP server, analyzers, validation, and example outputs are working.

Pre-`1.0.0` version labels in this repository are internal planning markers only. No public package releases are planned before `1.0.0`.

## Broad path to 1.0.0

### Foundation hardening

- Freeze CLI command names and MCP tool names.
- Keep result payloads additive-only; no intentional key removals or renames.
- Make generation responses report `resolved_output_dir`.
- Align MCP tool schemas with actual accepted arguments.
- Ensure MCP server metadata reports package version, not SDK/library internals.
- Keep package metadata clean enough for future publishing: homepage, repository, issue tracker, changelog links.
- Keep installed-artifact smoke coverage for wheel and sdist so release mechanics are never a last-minute surprise.

### Operational maturity

- Add Dependabot for Python deps and GitHub Actions.
- Add CodeQL workflow for Python.
- Pin GitHub Actions more deliberately than floating legacy refs.
- Validate committed example outputs in CI.
- Assert CLI smoke commands do not dirty tracked repo state unexpectedly.
- Rewrite maintainer docs and user docs to match actual behavior:
  - release checklist
  - output confinement behavior
  - install paths
  - contract expectations

### Real-repo confidence

- Run fixed public smoke set and capture results:
  - Python: `pallets/click`
  - Node/TypeScript: `sindresorhus/ky`
  - Go: `spf13/cobra`
  - Rust: `serde-rs/json`
- For each repo: run `detect`, `generate`, `validate`, record warnings, scan stats, and notable limitations.
- Keep Java and .NET on fixture coverage until a blocker appears or the release sprint expands scope.

### Feature completion toward 1.0.0

- Continue feature and quality work without publishing.
- Keep public-surface discipline so `1.0.0` does not require a late contract cleanup.
- Only introduce breaking changes intentionally and document them as pre-`1.0.0` repo changes, not public release promises.

### 0.9.5 release sprint

Use `0.9.5` as the dedicated release-preparation sprint. At that point:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest -q`
- `uv build`
- `uv run context-crafter-mcp doctor`
- `uv run context-crafter-mcp self-test .`
- `uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json`
- `uv run context-crafter-mcp validate docs/generated --repo . --json`
- installed wheel smoke passes
- installed sdist smoke passes
- roadmap, limitations, output contract, README, security docs, and manual steps contain no stale claims
- public smoke matrix is executed and captured
- release notes, packaging metadata, and examples are in final public form

### 1.0.0 first public release

- First published release happens here, not earlier.
- Release should follow the full manual checklist and public-repo confidence matrix.
- Public compatibility expectations begin here.

## Deferred until after 1.0.0

- Broader real-world matrix for Java and .NET
- Any major public contract redesign
- Automated publish workflow
