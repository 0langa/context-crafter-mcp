# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-05-29

### Added

- **MCP resources**: Safe generated-resource listing with `context-crafter://latest/<filename>` URIs. `read_resource()` only reads files registered by the current server session.
- **Validation module** (`src/context_crafter_mcp/validation.py`): Extended validation beyond file existence.
  - Markdown relative-link checking.
  - Non-empty mermaid block verification in `DEPENDENCY_GRAPH.md`.
  - Machine-readable warning/error codes (`BROKEN_LINK`, `MERMAID_MISSING`, `MERMAID_EMPTY`, `READ_ERROR`).
- **Demo examples**: `examples/demo-repo/` is now a tiny real Python package (`greeter`) with `pyproject.toml`, `src/greeter/`, and `tests/`.
- **Benchmark script**: `scripts/bench_scan.py` creates a synthetic fixture and outputs JSON timing/stats.
- **Doctor checks**: CLI entrypoint verification and temp output write test.

### Changed

- `doctor` now reports `mcp` and `langgraph` as "installed" even when version metadata is unavailable.
- `examples/outputs/` regenerated from `examples/demo-repo/` instead of the full context-crafter repo.
- Stopped advertising generic `file://` resource templates.

### Fixed

- `list_resources()` now returns actual registered generated docs instead of an empty list.

## [0.3.0] - 2026-05-29

### Added

- **CLI**: Full command-line interface via `context-crafter-mcp` console script.
  - `version`, `doctor`, `detect`, `generate`, `validate`, `self-test`, `mcp-config`, `serve`.
  - `--json` output support for machine-readable integration.
  - `--profile compact|standard|deep` for token/detail control.
- **Generated output contract**: 8 standardized output files.
  - `AI_CONTEXT_INDEX.md`, `PROJECT_OVERVIEW.md`, `REPO_MAP.md`, `DEPENDENCY_GRAPH.md`, `ARCHITECTURE_SUMMARY.md`, `AGENT_BRIEF.md`, `VALIDATION_REPORT.md`, `SCAN_REPORT.md`.
- **Scanner boundary**: `Scanner.scan(root, options) -> RepoSnapshot`.
  - `ScannerOptions`, `RepoSnapshot`, `SnapshotFile`, `SnapshotDirectory`, `SkippedEntry`, `ScanError`, `ScanStats`, `GitMetadata`.
  - Safe defaults: no symlinks, bounded depth/files/bytes, ignored dirs, optional gitignore respect.
- **MCP protocol quality**:
  - New tools: `generate_context` (one-shot), `validate_generated_context`, `explain_capabilities`.
  - Resource templates for reading generated docs by URI.
  - Prompt template: `generate_context`.
  - Stdout safety: suppressed library warnings to protect stdio protocol.
- **Fixture repos and golden tests**:
  - `tests/fixtures/python_basic`, `node_ts_basic`, `dotnet_basic`, `rust_basic`, `go_basic`, `java_basic`, `generic_unknown`, `mixed_monorepo`.
  - `tests/test_fixtures.py` verifies detection and generation across all fixtures.
- **Safety tests** (`tests/test_safety.py`):
  - Symlink skip, binary/large file skip, ignored dir skip, max depth/files bounds.
  - Output traversal blocking, deterministic ordering, static-only audit.
- **MCP smoke tests** (`tests/test_mcp_smoke.py`): `tools/list` and key tool call validation.
- **Documentation**:
  - Rewrote README with badges, quick start, MCP client configs, Inspector command, safety model, architecture, limitations.
  - `SECURITY.md` with threat model, safe defaults, secret handling, reporting process.
  - `CONTRIBUTING.md` with dev workflow and analyzer addition guide.
  - `MANUAL_STEPS.md` for maintainer-only actions.
  - `docs/adr/0001-python-product-layer-replaceable-scanner.md` documenting architecture decision.
  - `LICENSE` (MIT).
  - GitHub issue templates for bug reports and feature requests.
- **CI updates**:
  - Matrix: Windows + Ubuntu, Python 3.11/3.12/3.13.
  - Added package build check, CLI smoke tests, minimal workflow permissions.

### Changed

- Package description aligned with product statement.
- `ScanConfig` extended with `profile` and `max_file_bytes`.
- `detectors.py` and `analyzers/generic.py` migrated to consume `RepoSnapshot`.

### Fixed

- **MCP resource safety**: `read_resource()` now uses a whitelist populated only by generation. Arbitrary paths are blocked.
- **Detection pollution**: Fixture/example directories (`tests/fixtures/`, `examples/`, `docs/generated/`) are excluded from primary project detection and analysis.
- **Validation report**: No longer lists itself as missing during generation.
- **Scanner architecture**: `safe_scan()` is now a thin wrapper around `Scanner.scan()`.
- **Evidence model**: Added `observed/inferred/unknown` evidence levels to `DetectResult` and generated docs.
- **Repo cleanliness**: Removed 72 accidentally committed generated files from fixture directories.

## [0.2.0] - 2025-05-29

### Added

- Initial package structure with `context_crafter_mcp` import name.
- MCP stdio server with `detect_project`, `generate_project_overview`, `generate_repo_map`, `generate_dependency_graph`, `generate_architecture_summary`, `generate_all`.
- Analyzers for Python, Node/JS, .NET, Rust, Go, Java, and generic fallback.
- Markdown, Mermaid, and HTML renderers.
- LangGraph-based generation pipeline.
- Basic test suite and GitHub Actions CI.
