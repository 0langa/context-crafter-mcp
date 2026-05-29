# Implementation Report

Date: 2026-05-29

## Verification Commands

### git status --short

Working tree has intentional modifications:
- Modified: version bump files, MCP server, CLI, tests, example outputs
- Untracked: new validation module, benchmark script, demo-repo source
- Clean: no cache/build artifacts tracked

### uv sync --extra dev

Dependencies synced successfully.

### uv run python -m compileall src tests

All modules compile without syntax errors.

### uv run ruff check .

All checks passed.

### uv run ruff format --check .

All files already formatted.

### uv run mypy src

Success: no issues found in 22 source files.

### uv run pytest -q

70 passed in ~4s.

### uv build

Successfully built dist/context_crafter_mcp-0.3.1.tar.gz and dist/context_crafter_mcp-0.3.1-py3-none-any.whl.

### uv run context-crafter-mcp --help

Help text displayed correctly with all subcommands.

### uv run context-crafter-mcp doctor

```
context-crafter-mcp 0.3.1
Python: 3.12.7
mcp SDK: installed
pydantic: installed (2.13.4)
langgraph: installed
CLI entrypoint: ok
Temp output write: ok
Status: healthy
```

### uv run context-crafter-mcp detect . --json

Returns only `python` and `generic` project types. Evidence: `python: observed`, `generic: observed`. No fixture pollution.

### uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json

Generates all 8 output files successfully (9 including .mmd).

### uv run context-crafter-mcp validate .tmp/generated --json

```json
{
  "ok": true,
  "found": [...],
  "missing": [],
  "count": 8,
  "expected": 8,
  "checks": [
    {
      "code": "MERMAID_OK",
      "level": "ok",
      "message": "DEPENDENCY_GRAPH.md contains a non-empty mermaid block.",
      "file": "DEPENDENCY_GRAPH.md"
    }
  ]
}
```

### timeout 2s uv run context-crafter-mcp serve

Server starts and exits gracefully when stdin closes (stdio server).

## Fixes Applied (v0.3.1)

1. **Repo cleanliness**: Removed stale `.tmp/` contents. `.gitignore` already covers `.tmp/`, `dist/`, `__pycache__`, caches, and fixture-generated docs.
2. **MCP resources**: Stopped advertising generic `file://` templates. Implemented `context-crafter://latest/<filename>` URIs. `read_resource()` only reads from `_REGISTERED_RESOURCES` populated during generation. `list_resources()` returns actual registered docs. Tests added for allowed/denied access.
3. **Validation**: Extended beyond file existence. New `validation.py` module checks Markdown links, verifies DEPENDENCY_GRAPH.md has a non-empty mermaid block, and reports machine-readable warning/error codes (`BROKEN_LINK`, `MERMAID_MISSING`, `MERMAID_EMPTY`, `READ_ERROR`).
4. **Demo examples**: `examples/demo-repo/` is now a tiny real Python package (`greeter`) with `pyproject.toml`, `src/greeter/`, and `tests/`. `examples/outputs/` regenerated from demo-repo. Exact command documented in `examples/demo-repo/README.md`.
5. **Doctor polish**: Reports `mcp` and `langgraph` as "installed" even when version metadata is unavailable. Added CLI entrypoint check and temp output write check.
6. **Benchmark script**: Added `scripts/bench_scan.py` which creates a synthetic fixture, runs `Scanner.scan()`, and outputs JSON timing/stats.
7. **Version**: Bumped to `0.3.1` in `__init__.py`, `pyproject.toml`.

## Remaining Work Matrix

| Item | State | Blocker for v1.0? |
|------|-------|-------------------|
| Tree-sitter parser spike | Not started | No (optional) |
| Profile density actually affects content | Partial (parameter accepted, content mostly same) | No (nice-to-have) |
| Dependabot / CodeQL | Not configured | No (CI already green) |
| README badge images are markdown links, not shields.io | Current | No |
| Real-world multi-repo benchmark | Not done | No |
| Publishing to PyPI | Manual only | No |
