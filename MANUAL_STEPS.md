# Manual Steps

Steps that remain intentionally manual for release and repository stewardship.

Roadmap note: the current working milestone is the `0.7.0b1` beta prerelease. This file describes what remains manual for beta releases and the eventual first stable release at `1.0.0`.

## Repository settings

- Repository description:
  `Local-first MCP server that turns source repositories into compact AI-agent context: project overviews, repo maps, dependency graphs, architecture notes, and validation reports.`
- Topics:
  `mcp`, `documentation`, `static-analysis`, `ai-agents`, `repository-tools`
- Do not enable automatic publishing workflows before the first public release at `1.0.0`.

## Release checklist

Run this checklist before cutting any release tag.

1. Update version in `pyproject.toml` and `src/context_crafter_mcp/__init__.py`.
2. Move release notes from `CHANGELOG.md` `[Unreleased]` into a dated version section.
3. Run:
   - `uv run python -m compileall src tests`
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy src`
   - `uv run pytest -q`
   - `uv build`
   - `uv run context-crafter-mcp doctor`
   - `uv run context-crafter-mcp self-test .`
   - `uv run context-crafter-mcp generate . --output docs/generated --profile standard --json`
   - `uv run context-crafter-mcp validate docs/generated --json`
   - `uv run context-crafter-mcp validate examples/outputs --repo examples/demo-repo --json`
4. Smoke installed artifacts:
   - remove stale ignored artifacts from `dist/` or explicitly select artifacts matching the version being released
   - install the exact release wheel in a fresh venv
   - install the exact release sdist in a fresh venv
   - run `context-crafter-mcp --help`
   - run `context-crafter-mcp version` and verify it matches the release version
   - run `context-crafter-mcp doctor`
   - run `context-crafter-mcp detect . --json`
   - run `context-crafter-mcp generate . --output docs/generated --profile standard --json`
   - run `context-crafter-mcp validate docs/generated --json`
5. Run real-repo smoke automation and update the public matrix (maintainer/optional if network unavailable):
   - `uv run python scripts/smoke_repos.py`
   - Run that command from the repository root; it is the canonical maintainer invocation.
   - Update `docs/REAL_REPO_SMOKE_MATRIX.md` with results.
6. Regenerate any intentionally committed example output and verify it still matches policy.
7. Review `git status --short` and ensure only intentional tracked changes remain.
8. Build final artifacts, tag release, then publish manually.

## Output confinement note

`generate` and `generate_context` accept an `output_dir`, but paths that would escape the repository root are confined to `docs/generated`. Use the reported `resolved_output_dir` field from JSON results to see the actual write location.

## Screenshots

If adding screenshots to `README.md`, generate them manually from current verified output. Do not add screenshots for behavior that is not already covered by the release checklist.
