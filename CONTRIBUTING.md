# Contributing

## Setup

```sh
git clone https://github.com/0langa/context-crafter-mcp.git
cd context-crafter-mcp
uv sync --extra dev
```

## Development workflow

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
uv run context-crafter-mcp self-test .
```

For deeper parser support (Tree-sitter backends):

```sh
uv sync --extra parsers
```

## Adding an analyzer

1. Create a module under `src/context_crafter_mcp/analyzers/`.
2. Implement the analyzer function signature.
3. Call `register_analyzer(project_type, fn)` and `register_analyzer_spec(AnalyzerSpec(...))` at module bottom.
4. Add detection markers in `src/context_crafter_mcp/detectors.py`.
5. Add tests with a fixture repo under `tests/fixtures/`.
6. Add golden fixture assertions in `tests/test_golden_fixtures.py`.

The `AnalyzerRegistry` class in `src/context_crafter_mcp/analyzers/registry.py` wraps registration, detection, analysis, and merging. Prefer using it over ad-hoc module-level calls in new code.

## Pull requests

- Keep changes focused.
- Add tests for new behavior.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Do not add placeholder TODOs.
