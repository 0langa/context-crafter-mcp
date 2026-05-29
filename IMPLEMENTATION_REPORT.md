# Implementation Report

Date: 2026-05-29

## Scope

This pass targets v0.3.2/v0.4.0 quality: cleanup, validation hardening, scanner enrichment, profile modes, MCP polish, and documentation accuracy.

## Verification Commands

### git status --short

Intentional modifications only:
- Modified: pyproject.toml, src/context_crafter_mcp/__init__.py, cli.py, models.py, state.py, scanner.py, server.py, validation.py, renderers, analyzers, tests, example outputs, docs
- Untracked: AGENTS.md, tests/test_validation_extended.py, tests/test_profiles.py, tests/test_scanner_binary.py
- No cache/build artifacts tracked

### uv sync --extra dev

Dependencies synced. Package installed at `context-crafter-mcp==0.3.2`.

### uv run python -m compileall src tests

All modules compile without syntax errors.

### uv run ruff check .

All checks passed.

### uv run ruff format --check .

All files already formatted.

### uv run mypy src

Success: no issues found in 22 source files.

### uv run pytest -q

92 passed in 3.06s.

### uv build

Successfully built `dist/context_crafter_mcp-0.3.2.tar.gz` and `dist/context_crafter_mcp-0.3.2-py3-none-any.whl`.
Stale `0.3.1` artifacts removed from `dist/`.

### uv run context-crafter-mcp --help

All 9 subcommands present: version, doctor, detect, generate, validate, self-test, mcp-config, serve.

### uv run context-crafter-mcp doctor

```
context-crafter-mcp 0.3.2
Python: 3.12.7
mcp SDK: installed
pydantic: installed (2.13.4)
langgraph: installed
CLI entrypoint: ok
Temp output write: ok
Status: healthy
```

### uv run context-crafter-mcp detect . --json

Returns structured JSON with `ok: true`, `project_types: ["generic", "python"]`, `warnings: []`, `errors: []`.

### uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json

Generates 9 files successfully. `files_scanned: 141`, `project_types: ["generic", "python"]`, `warnings: []`, `errors: []`.

### uv run context-crafter-mcp validate .tmp/generated --json

Returns 8/8 found, `MERMAID_OK`, zero warnings, zero errors.

### uv run context-crafter-mcp self-test .

Generates into a temp directory inside the repo (`tmp<random>`), auto-cleaned on exit. Does not dirty tracked files.

### uv run python scripts/bench_scan.py --files 1000 --depth 5 --max-files 2000

0.1102s for 1000 files. No regression from scanner enrichment.

### Profile comparison

Compact/standard/deep produce measurably different line counts on the main repo:
- PROJECT_OVERVIEW: 89 / 94 / 104 lines
- REPO_MAP: 126 / 186 / 195 lines

### MCP serve smoke test

Server starts and responds correctly to JSON-RPC initialize:
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":false}},"serverInfo":{"name":"context-crafter","version":"1.27.1"}}}
```

## Changes Applied

### v0.3.2 Cleanliness Pass
- Version bumped to `0.3.2` in `pyproject.toml` and `src/context_crafter_mcp/__init__.py`
- Stale `0.3.1` dist artifacts removed from `dist/`
- `Development Status` classifier changed from `4 - Beta` to `3 - Alpha`
- `ruff format .` applied; 3 files reformatted, all 52 files now clean
- AGENTS.md hygiene: skipped per explicit user request

### Priority 1 — Repo and Export Hygiene
- Removed stale dist artifacts (0.2.0, 0.3.0)
- Removed `.tmp/`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache` from working tree
- `.gitignore` covers `.tmp/`, caches, `dist/`, build artifacts

### Priority 2 — self-test Does Not Dirty Repo
- `cmd_self_test` uses `tempfile.TemporaryDirectory(dir=repo)` by default
- Added `--output` option for persistent output when desired
- Added `test_self_test_default_does_not_persist`

### Priority 3 — Validation Hardening
- New codes: `missing_required_file`, `broken_markdown_link`, `missing_mermaid_block`, `empty_mermaid_block`, `mermaid_no_diagram_keyword`, `referenced_source_missing`, `fixture_path_primary_claim`, `oversized_section`, `validation_internal_error`
- `.mmd` existence check
- Markdown link resolution check
- Source path reference check (conservative, strips `::`, `(`, `#` suffixes and `:123` line numbers, trailing `/` for directories)
- Fixture/demo pollution detection
- Rough file-size warnings
- Mermaid syntax validation: checks for recognized diagram keywords (graph, flowchart, sequenceDiagram, etc.)
- `ValidationResult.to_dict()` now returns `summary`, `warnings`, `errors`, `checks`
- CLI `validate` accepts `--repo` for source-reference validation

### Priority 4 — Scanner Model Enrichment
- `SnapshotFile` now has `extension`, `language_hint`, `is_text`
- `_guess_is_text()` uses extension heuristics + null-byte check + binary magic bytes detection (PNG, ELF, PDF, ZIP, etc.)
- `_language_hint()` maps extensions and filenames to stacks
- Benchmark confirms no significant regression

### Priority 5 — .gitignore Semantics
- Added `pathspec` dependency
- Scanner now uses `pathspec.PathSpec.from_lines("gitignore", ...)` for root `.gitignore`
- Supports wildcards (`*.log`), directory patterns (`build/`), double-star (`foo/**`), and negation (`!keep.log`)
- Added 4 scanner safety tests for these patterns
- Nested `.gitignore` files supported via `active_gitignores` stack with "deepest matching wins" semantics
- Added `test_nested_gitignore_pattern`

### Priority 6 — Profiles Meaningful
- `ScanConfig` and `AnalysisResult` carry `profile`
- `get_profile_limit(profile, key)` provides numeric limits per profile
- `analyze_generic` adjusts tree depth and collection limits
- Markdown and Mermaid renderers use profile limits for all slices
- Added `test_profiles.py` proving measurable differences on substantial repos
- Compact profile on tiny repos (< 15 files) omits empty optional sections: Architecture Patterns, Key Abstractions, Module Relationships, Generic Notes, Source layout, Test layout in AGENT_BRIEF

### Priority 7 — MCP Resource Polish
- Existing `context-crafter://latest/<filename>` design preserved
- `_REGISTERED_RESOURCES` blocks arbitrary reads
- Added tests: traversal denial (`../`), empty list before generation

### Priority 5b — Non-Python Analyzer Depth Improvements
- **Node/JS**: Added export, class, and function detection via regex; populated `NodePackage.exports`, `.classes`, `.functions`
- **Go**: Added struct and interface detection; populated `GoModule.structs`, `.interfaces`
- **Java**: Added method and annotation detection; populated `JavaProject.methods`, `.annotations`
- **Rust**: Added trait and impl block detection; populated `RustCrate.traits`, `.impls`
- **.NET**: Fixed `OutputType` detection, added `AssemblyName` parsing, added class detection from `.cs` files; populated `DotNetProject.output_type`, `.assembly_name`, `.classes`
- Markdown renderer updated to display all new symbol counts in PROJECT_OVERVIEW language summaries

### Priority 5c — Cross-Language Architecture Detection
- `_extract_architecture_notes()` now detects patterns across all supported stacks:
  - Go: interface-heavy design, CLI/service architecture
  - Java: Spring framework annotations (`@Component`, `@Service`, `@Controller`, `@Entity`, etc.)
  - Node: web framework (express, fastify, nest) and frontend framework (react, vue, angular, svelte, next) detection
  - Rust: trait-based polymorphism, tokio async runtime

### Priority 8 — MCP Tool Schemas
- All tool results now structured JSON with `ok`, `summary`, `warnings`, `errors`
- `DetectResult.to_dict()`, `RenderResult.to_dict()`, `RepoState.to_tool_result()`, `ValidationResult.to_dict()` all updated
- `explain_capabilities` returns structured JSON instead of plain text

### Priority 9 — MCP Inspector and Client Docs
- Updated README.md, docs/MCP_CLIENTS.md, docs/ARCHITECTURE.md, docs/LIMITATIONS.md
- Documented stdio-first config, resource behavior, tool list, verified vs best-effort claims

### Priority 10 — Demo Repo and Examples
- Regenerated `examples/outputs/` from `examples/demo-repo/`
- Documented exact regeneration command (accounting for output confinement)

### Priority 11 — Reports and Docs
- Updated IMPLEMENTATION_REPORT.md, CHANGELOG.md, README.md, docs/ROADMAP.md, docs/ARCHITECTURE.md, docs/SCANNER.md, docs/MCP_CLIENTS.md, docs/OUTPUT_CONTRACT.md, docs/LIMITATIONS.md, SECURITY.md, MANUAL_STEPS.md

## Remaining Limitations

| Limitation | Mitigation |
|---|---|
| Non-Python analyzers use regex/XML/TOML only | Documented; AST depth only for Python. Regex-based symbol extraction is as deep as feasible without full parsers. |
| HTML renderer is stdlib-only | Documented; inline formatting, lists, blockquotes, code blocks supported |
| Tree-sitter integration not required for core | Listed as optional future work |
| Source-reference validation may have false negatives | Conservative regex, warning-only. Handles line numbers, anchors, and directory paths. |

## Manual-Only Steps

- PyPI publishing
- GitHub topic/tags updates
- Live MCP client verification beyond Inspector command docs
- Screenshots or marketing materials
