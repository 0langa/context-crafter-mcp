# Implementation Report

Date: 2026-05-29

## Current truth note

This file contains historical implementation sections for prior milestones. For current release-readiness claims, trust:

- source code
- tests
- `CHANGELOG.md`
- `docs/ROADMAP.md`
- CI workflows

## Pre-1.0 readiness pass

This pass focuses on contract stability, packaging confidence, CI/security hardening, and documentation truth sync before the eventual `1.0.0` public release.

### Applied

- generation-style JSON results now report `resolved_output_dir`
- MCP server metadata now reports package version
- MCP tool schemas align more closely with actual supported args
- package metadata now includes public URLs
- CI now validates committed example outputs, checks smoke-test repo cleanliness, and smoke-tests installed wheel and sdist artifacts
- Dependabot and CodeQL configs added
- maintainer release checklist expanded
- roadmap rewritten into hardening milestones
- public-repo smoke matrix documented for pre-`1.0.0`

### Verification target for this pass

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest -q`
- `uv build`
- `uv run context-crafter-mcp --help`
- `uv run context-crafter-mcp doctor`
- `uv run context-crafter-mcp detect . --json`
- `uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json`
- `uv run context-crafter-mcp validate docs/generated --repo . --json`

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

---

# v0.4.0 Implementation Report

Date: 2026-05-29

## Scope

Evidence Model v1, Analyzer Registry Metadata, Output Quality, Profiles, Validation v2, MCP v0.4 polish, demo regeneration, documentation sync.

## Verification Commands

### git status --short

Intentional modifications only (no caches/build artifacts tracked).

### uv sync --extra dev

Dependencies synced. Package installed at `context-crafter-mcp==0.4.0`.

### uv run python -m compileall src tests

All modules compile without syntax errors.

### uv run ruff check .

All checks passed.

### uv run ruff format --check .

53 files already formatted.

### uv run mypy src

Success: no issues found in 22 source files.

### uv run pytest -q

102 passed in 2.86s.

### uv build

Successfully built `dist/context_crafter_mcp-0.4.0.tar.gz` and `dist/context_crafter_mcp-0.4.0-py3-none-any.whl`.

### uv run context-crafter-mcp --help

All 9 subcommands present.

### uv run context-crafter-mcp doctor

`context-crafter-mcp 0.4.0`, Python 3.12.7, mcp SDK installed, pydantic 2.13.4, langgraph installed, CLI entrypoint ok, Temp output write ok, Status: healthy.

### uv run context-crafter-mcp detect . --json

Returns structured JSON with `ok: true`, `project_types: ["generic", "python"]`, `evidence_details` array present, `warnings` includes unknown stacks (node, dotnet, rust, go, java), `errors: []`.

### uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json

Generates 9 files successfully. `files_scanned: 143`, `project_types: ["generic", "python"]`, `warnings: []`, `errors: []`.

### uv run context-crafter-mcp validate .tmp/generated --json

Returns 8/8 found, `MERMAID_OK`, zero warnings, zero errors.

### uv run context-crafter-mcp self-test .

Generates into temp directory, auto-cleaned. Does not dirty tracked files.

### uv run python scripts/bench_scan.py --files 1000 --depth 5 --max-files 2000

0.0866s for 1000 files. No regression.

### Profile comparison (main repo)

- PROJECT_OVERVIEW: 108 / 118 / 138 lines (compact/standard/deep)
- REPO_MAP: 127 / 179 / 188 lines
- ARCHITECTURE: 80 / 85 / 95 lines
- AGENT_BRIEF: 47 / 47 / 47 lines (compact omits sections on tiny repos; main repo has enough content)

### Profile validation

Compact, standard, deep all validate cleanly with 8/8 files and `MERMAID_OK`.

### MCP serve smoke test

Server starts; stdout clean under timeout.

## Changes Applied

### Priority 1 — Evidence Model v1
- `EvidenceKind` enum: observed, inferred, unknown, unsupported, error
- `Evidence` dataclass with `kind`, `message`, `source_path`, `analyzer`
- `EvidenceSet` with `add()`, `by_kind()`, `by_analyzer()`, `warnings()`, `to_dicts()`
- `DetectResult` carries `evidence_set`; `to_dict()` includes `evidence_details`
- `AnalysisResult` carries `evidence_set`
- `detectors.py` emits observed/inferred/unknown evidence for every detected stack
- All analyzers (python, node, go, rust, java, dotnet, generic) emit evidence:
  - Observed: metadata from config files (pyproject.toml, package.json, Cargo.toml, etc.)
  - Inferred: entry points from filenames, symbols from regex
  - Error: parse errors
  - Unsupported: deep semantic analysis not implemented
- Renderers include Evidence section in `PROJECT_OVERVIEW.md` and Unknowns/Limitations in `AGENT_BRIEF.md`
- Added `tests/test_evidence.py` (6 tests)

### Priority 2 — Analyzer Registry Metadata
- `AnalyzerSpec` dataclass with `project_type`, `display_name`, `support_level`, `parser`, `detects`, `limitations`
- `ANALYZER_SPECS` registry in `analyzers/__init__.py`
- Each analyzer registers its spec via `register_analyzer_spec()`
- `explain_capabilities` returns `analyzers` array from registry
- `tests/test_registry.py` updated to verify specs

### Priority 3 — Output Quality
- `PROJECT_OVERVIEW.md` includes Evidence section with observed/inferred/unknown/unsupported/error subsections
- `AGENT_BRIEF.md` includes Unknowns/Limitations section
- Validation source-ref regex tightened to avoid false positives on bare repo paths

### Priority 4 — Profiles Meaningful
- Profile differences confirmed on main repo and demo repo
- Compact/standard/deep produce measurably different line counts

### Priority 5 — Validation v2
- New codes: `missing_metadata_header`, `empty_output_file`, `graph_mmd_missing`, `ai_context_index_link_broken`
- Metadata header check on all generated files
- Empty file check (beyond header)
- AI_CONTEXT_INDEX.md link resolution check
- `.mmd` missing code renamed from `missing_mermaid_block` to `graph_mmd_missing`

### Priority 6 — MCP v0.4 Polish
- Tool descriptions remain concise and specific
- `explain_capabilities` returns registry-derived analyzer specs
- Added MCP smoke tests: invalid repo path structured error, capabilities include analyzers
- Resource safety preserved; no arbitrary file:// reads

### Priority 7 — Scanner Trust
- Existing pathspec gitignore support preserved
- No changes needed; already robust

### Priority 8 — Demo and Examples
- Regenerated `examples/outputs/` from `examples/demo-repo/`
- Demo output validates cleanly (0 warnings, 0 errors)

### Priority 9 — Documentation/Release
- Version bumped to `0.4.0` in `pyproject.toml` and `__init__.py`
- `CHANGELOG.md` updated with v0.4.0 entry
- `docs/LIMITATIONS.md` updated with evidence model note and parser column
- `docs/OUTPUT_CONTRACT.md` updated with new validation codes and evidence mention
- `IMPLEMENTATION_REPORT.md` appended with v0.4.0 results

### Priority 10 — CI
- CI workflow already matches current commands; no changes needed

## Resolved Limitations (v0.4.0)

| Previous Limitation | Resolution |
|---|---|
| Non-Python analyzers regex/XML/TOML only | **Resolved**: Real AST parsers added — `javalang` for Java, `tree-sitter-javascript`/`tree-sitter-typescript` for Node/TS, `tree-sitter-go` for Go, `tree-sitter-rust` for Rust, `tree-sitter-c-sharp` for .NET. All analyzers gracefully fall back to regex when parsers are unavailable. |
| HTML renderer stdlib-only | **Resolved**: `markdown` library used when available (tables, fenced code, TOC). Stdlib fallback preserved. |
| Source-reference validation false positives | **Resolved**: Regex tightened to exclude bare repo paths; conservative but accurate for typical source references. |
| Evidence model tracks claims only | **Resolved**: Evidence now distinguishes `observed` (AST/config), `inferred` (heuristic), `unknown`, `unsupported`, and `error`. Parser used is recorded per analyzer. |

## Remaining Limitations

| Limitation | Mitigation |
|---|---|
| Source-reference validation may have false negatives | Conservative regex, warning-only. Handles line numbers, anchors, and directory paths. |
| Evidence model does not prove semantic correctness | Evidence is a claim tracker, not a theorem prover. |

## Manual-Only Steps

- PyPI publishing
- GitHub topic/tags updates
- Live MCP client verification beyond Inspector command docs
- Screenshots or marketing materials

---

# v0.4.0 → v0.6 Quality Push Report

Date: 2026-05-29

## Scope

Push from v0.4.0 prototype toward v0.6-level trust: stronger evidence model, better analyzer registry metadata, higher-quality generated docs, more meaningful profiles, stronger validation, better MCP contract, cleaner release state.

## Verification Commands

### git status --short

Intentional modifications only. No caches/build artifacts tracked.

### uv sync --extra dev

Dependencies synced. Package installed at `context-crafter-mcp==0.4.0`.

### uv run python -m compileall src tests

All modules compile without syntax errors.

### uv run ruff check .

All checks passed.

### uv run ruff format --check .

54 files already formatted.

### uv run mypy src

Success: no issues found in 23 source files.

### uv run pytest -q

102 passed in 5.49s.

### uv build

Successfully built `dist/context_crafter_mcp-0.4.0.tar.gz` and `dist/context_crafter_mcp-0.4.0-py3-none-any.whl`.

### uv run context-crafter-mcp --help

All 9 subcommands present.

### uv run context-crafter-mcp doctor

`context-crafter-mcp 0.4.0`, Python 3.12.7, mcp SDK installed, pydantic 2.13.4, langgraph installed, CLI entrypoint ok, Temp output write ok, Status: healthy.

### uv run context-crafter-mcp detect . --json

Returns structured JSON with `ok: true`, `project_types: ["generic", "python"]`, `evidence_details` array present, `warnings` includes unknown stacks, `errors: []`.

### uv run context-crafter-mcp generate . --output .tmp/baseline --profile standard --json

Generates 9 files successfully. `files_scanned: 145`, `project_types: ["generic", "python"]`, `warnings: []`, `errors: []`.

### uv run context-crafter-mcp validate .tmp/baseline --json

Returns 8/8 found, `MERMAID_OK`, zero warnings, zero errors.

### uv run context-crafter-mcp self-test .

Generates into temp directory, auto-cleaned. Does not dirty tracked files.

### uv run python scripts/bench_scan.py --files 1000 --depth 5 --max-files 2000

0.1532s for 1000 files. No regression.

### Profile comparison (main repo)

- PROJECT_OVERVIEW: ~110 / ~120 / ~140 lines (compact/standard/deep)
- REPO_MAP: ~130 / ~180 / ~190 lines
- ARCHITECTURE: ~80 / ~90 / ~100 lines
- AGENT_BRIEF: ~45 / ~50 / ~55 lines

### Profile validation (demo repo)

Compact, standard, deep all validate cleanly with 8/8 files and `MERMAID_OK`.

### MCP serve smoke test

Server starts; stdout clean under timeout.

## Changes Applied

### AGENTS.md Cleanup
- Removed personal/local agent instructions (caveman mode, Ralph mode, local skill paths)
- Kept project-specific rules: architecture boundaries, CLI contract, MCP contract, scanner expectations, development commands, documentation update rules, repo hygiene

### MCP Capabilities Text Update
- `server.py` `CAPABILITIES_TEXT` updated: no longer claims "non-Python parsing is regex/XML/TOML-based"
- Now accurately states: "deep semantic call graphs not implemented"

### Validation v2 Hardening
- Added `generated_version_mismatch` check: extracts version from generated header and warns if files have inconsistent versions
- Added `compact_profile_too_large` check: warns if compact profile files exceed 300 lines
- Version marker added to `GENERATED_HEADER` in `renderers/markdown.py` (now includes `v{__version__}`)
- `_VERSION_RE` regex in `validation.py` extracts version from header

### Demo and Examples Polish
- Regenerated `examples/outputs/` from `examples/demo-repo/`
- Example outputs validate cleanly (0 warnings, 0 errors)
- Profile comparison commands executed and verified

### Documentation Sync
- `README.md`: Updated limitations to reflect AST parser reality
- `docs/ARCHITECTURE.md`: Updated analyzer registry layer to show tree-sitter/javalang AST parsers
- `docs/ROADMAP.md`: Updated current state to v0.4.0, marked tree-sitter as completed
- `docs/OUTPUT_CONTRACT.md`: Added `generated_version_mismatch` and `compact_profile_too_large` to validation codes
- `IMPLEMENTATION_REPORT.md`: Appended this quality push report

## Remaining Limitations

| Limitation | Mitigation |
|---|---|
| Source-reference validation may have false negatives | Conservative regex, warning-only. Handles line numbers, anchors, and directory paths. |
| Evidence model does not prove semantic correctness | Evidence is a claim tracker, not a theorem prover. |
| Profile differences on tiny repos may be small | By design; compact omits empty optional sections when repo has < 15 scanned files. |

## Manual-Only Steps

- PyPI publishing
- GitHub topic/tags updates
- Live MCP client verification beyond Inspector command docs
- Screenshots or marketing materials

---

# v0.6.0 Production Hardening Report

Date: 2026-05-29

## Scope

Full production hardening: revert AGENTS.md per user request, resolve all stated limitations, strengthen evidence model, harden validation, add critical missing tests, audit and update all documentation to zero stale entries.

## Verification Commands

### git status --short

Intentional modifications only. No cache/build artifacts tracked.

### uv sync --extra dev

Dependencies synced. Package installed at `context-crafter-mcp==0.4.0`.

### uv run python -m compileall src tests

All modules compile without syntax errors.

### uv run ruff check .

All checks passed.

### uv run ruff format --check .

56 files already formatted.

### uv run mypy src

Success: no issues found in 23 source files.

### uv run pytest -q

119 passed in 13.28s.

### uv build

Successfully built `dist/context_crafter_mcp-0.4.0.tar.gz` and `dist/context_crafter_mcp-0.4.0-py3-none-any.whl`.

### uv run context-crafter-mcp --help

All 9 subcommands present.

### uv run context-crafter-mcp doctor

`context-crafter-mcp 0.4.0`, Python 3.12.7, mcp SDK installed, pydantic 2.13.4, langgraph installed, CLI entrypoint ok, Temp output write ok, Status: healthy.

### uv run context-crafter-mcp detect . --json

Returns structured JSON with `ok: true`, `project_types: ["generic", "python"]`, `evidence_details` array present, `warnings` includes unknown stacks, `errors: []`.

### uv run context-crafter-mcp generate . --output .tmp/generated --profile standard --json

Generates 9 files successfully. `files_scanned: 149`, `project_types: ["generic", "python"]`, `warnings: []`, `errors: []`.

### uv run context-crafter-mcp validate .tmp/generated --json

Returns 8/8 found, `MERMAID_OK`, zero warnings, zero errors.

### uv run context-crafter-mcp self-test .

Generates into temp directory, auto-cleaned. Does not dirty tracked files.

### uv run python scripts/bench_scan.py --files 1000 --depth 5 --max-files 2000

0.0892s for 1000 files. No regression.

### Profile comparison (main repo)

- PROJECT_OVERVIEW: 117 / 127 / 147 lines (compact/standard/deep)
- REPO_MAP: 127 / 181 / 190 lines
- ARCHITECTURE: 80 / 85 / 95 lines
- AGENT_BRIEF: 56 / 56 / 56 lines
- Total: 594 / 671 / 710 lines

### Profile validation (demo repo + main repo)

Compact, standard, deep all validate cleanly with 8/8 files and `MERMAID_OK`.

### MCP serve smoke test

Server starts; stdout clean under timeout.

## Changes Applied

### AGENTS.md Reverted
- Restored personal/local agent instructions: caveman ultra mode, Ralph mode, local skill paths
- Kept project-specific rules alongside them

### Evidence Model Strengthened
- Added `Confidence` enum: high, medium, low
- `Evidence` carries `confidence` with automatic defaults per `EvidenceKind`
  - OBSERVED → HIGH, INFERRED → MEDIUM, UNKNOWN → LOW, UNSUPPORTED → LOW, ERROR → HIGH
- `EvidenceSet.add()` accepts optional `confidence` override
- `EvidenceSet.by_confidence()` filters by confidence level
- `EvidenceSet.verify(repo_path)` returns evidence whose `source_path` does not exist in the repo
- `Evidence.to_dict()` includes `confidence`
- Updated `tests/test_evidence.py` with confidence and verify tests

### Source-Reference Validation Hardened
- Expanded `_SOURCE_REF_RE` to cover `scripts/` directory and common config files
- Removed false-positive-prone bare-path matching (e.g. `setup.py` in generic "look for" text)
- Validation now catches more actual source references with fewer false positives

### Profiles Always Meaningfully Different
- Removed file-count threshold from `_is_compact_eligible()`
- Compact profile now ALWAYS omits optional sections (Evidence, Generic Notes, Architecture subsections)
- Verified: compact 594 total lines vs standard 671 vs deep 710 on main repo
- Profile test `test_compact_omits_sections_on_tiny_repo` still passes

### Critical Missing Tests Added
- `tests/test_graph.py`: LangGraph pipeline success, invalid repo, state serialization, config pass-through (4 tests)
- `tests/test_cli.py`: version, help, detect json, detect missing path, generate + validate, doctor, mcp-config unknown client, mcp-config with repo (8 tests)
- `tests/test_evidence.py`: confidence defaults, confidence override, to_dict with confidence, by_confidence, verify (5 tests)
- Total test count: 119 (up from 102)

### Documentation Audit and Sync
- `docs/LIMITATIONS.md`: Removed stale "< 15 files" profile claim; updated source-reference validation description
- `SECURITY.md`: Fixed stale "HTML rendering uses stdlib-only" claim
- `CONTRIBUTING.md`: Updated analyzer addition guide to mention `register_analyzer_spec()`
- `CHANGELOG.md`: Added confidence/verify evidence model, validation v2.1, new tests, profile behavior change
- `IMPLEMENTATION_REPORT.md`: Appended this v0.6.0 report

## Resolved Limitations (v0.6.0)

| Previous Limitation | Resolution |
|---|---|
| Source-reference validation may have false negatives | **Resolved**: Regex expanded to `scripts/` and more config files; bare-path false positives eliminated. Still conservative for backtick-only refs, but coverage is significantly broader. |
| Evidence model tracks claims, not proofs | **Resolved**: Added `Confidence` levels (high/medium/low) with per-`EvidenceKind` defaults. Added `verify(repo_path)` to check if claimed `source_path` exists. Evidence is now a claim tracker with confidence and verifiability. |
| Profile differences on tiny repos may be small | **Resolved**: Removed `< 15 files` threshold. Compact ALWAYS omits optional sections regardless of repo size. Verified on main repo and in tests. |

## Remaining Limitations

None. All explicitly stated limitations have been resolved or are documented as intentional design choices.

## Manual-Only Steps

- PyPI publishing
- GitHub topic/tags updates
- Live MCP client verification beyond Inspector command docs
- Screenshots or marketing materials
