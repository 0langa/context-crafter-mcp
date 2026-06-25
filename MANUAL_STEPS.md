# Manual Steps

Steps that remain intentionally manual for release and repository stewardship.

Roadmap note: the current public release is `0.9.0`. The active release train targets the first stable release at `1.0.0`.

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
   - `powershell -ExecutionPolicy Bypass -File .\scripts\installed_artifact_smoke.ps1`
   - The script builds exact-version artifacts, installs wheel and sdist in fresh venvs, then runs `--help`, `version`, `doctor`, `detect`, `self-test`, `generate`, and `validate` from the installed CLI.
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
