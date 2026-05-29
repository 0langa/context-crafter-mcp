# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-05-29

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

## [0.2.0] - 2025-05-29

### Added

- Initial package structure with `context_crafter_mcp` import name.
- MCP stdio server with `detect_project`, `generate_project_overview`, `generate_repo_map`, `generate_dependency_graph`, `generate_architecture_summary`, `generate_all`.
- Analyzers for Python, Node/JS, .NET, Rust, Go, Java, and generic fallback.
- Markdown, Mermaid, and HTML renderers.
- LangGraph-based generation pipeline.
- Basic test suite and GitHub Actions CI.
