# Manual Steps

Steps that remain intentionally manual for release and repository stewardship.

Roadmap note: the current public release is `1.0.0`, the first stable release. Later releases stay additive against the frozen public contract in `docs/PUBLIC_SURFACE_FREEZE.md`.

## Repository settings

- Repository description:
  `Local-first MCP server that turns source repositories into compact AI-agent context: project overviews, repo maps, dependency graphs, architecture notes, and validation reports.`
- Topics:
  `mcp`, `documentation`, `static-analysis`, `ai-agents`, `repository-tools`
- Publishing is automated from `1.0.0` onward: pushing a version tag runs `.github/workflows/release.yml`, which verifies the tag matches `__version__`, builds the wheel and sdist, publishes to PyPI via trusted publishing, and attaches the artifacts to the GitHub release.
- Trusted publishing requires a one-time PyPI setup: a pending publisher for project `context-crafter-mcp` pointing at repository `0langa/context-crafter-mcp`, workflow `release.yml`, environment `pypi`.

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
8. Commit the release preparation, then tag and push:
   - `git tag <version>`
   - `git push origin main --tags`
   - `.github/workflows/release.yml` takes it from there: build, PyPI publish, GitHub release upload.
9. After the workflow finishes, confirm the published package installs cleanly:
   - `uvx context-crafter-mcp@<version> version`

## Output confinement note

`generate` and `generate_context` accept an `output_dir`, but paths that would escape the repository root are confined to `docs/generated`. Use the reported `resolved_output_dir` field from JSON results to see the actual write location.

## Screenshots

If adding screenshots to `README.md`, generate them manually from current verified output. Do not add screenshots for behavior that is not already covered by the release checklist.
