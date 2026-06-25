# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `scripts/validate_public_surface.py` and wired it into the local release gate so CLI version/help, MCP client config snippets, and MCP stdio startup are checked before release.
- Added docs-truth checks for documented MCP clients, tools, and generated output files to keep public docs aligned with code.
- Added `scripts/validate_release_docs.py` and wired it into the local release gate so release checklist wording, roadmap state, and workflow action baselines stay aligned.
- Added `CONTEXT_MANIFEST.json` as an additive machine-readable manifest for generated context bundles.

### Changed

- Clarified that `generate_context` writes 8 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`.
- Updated GitHub Actions workflow dependencies to Node 24-compatible baselines, including `actions/checkout@v7`, `actions/setup-python@v6`, and immutable `astral-sh/setup-uv@v8.2.0`.

## [0.7.0b1] - 2026-06-25

### Added

- **Local release gate** (`scripts/local_release_gate.ps1`): Windows-friendly command bundle for project-state validation, Ruff, mypy, pytest, doctor, self-test, generate, and validate.
- **Generic fallback honesty regression tests** (`tests/test_generic_fallback_honesty.py`): prove ambiguous repos stay generic when language-like files only appear in low-trust docs/tests/examples/tooling paths.
- **Fresh beta smoke evidence**: fixed real-repo smoke automation passed for `pallets/click`, `sindresorhus/ky`, `spf13/cobra`, and `serde-rs/json`.

### Changed

- **Detection honesty**: stack detection now promotes marker/extension evidence only from trusted primary-surface paths; low-trust hints are recorded as non-promoting unknown evidence.
- **Generic entry-point filtering**: agent-facing generic entry points now use the same primary-surface trust boundary.
- **Release docs**: pre-`1.0.0` gate and roadmap now treat the retired D-drive battle-testing platform as historical context and use the local gate for current progress.

## [0.6.0] - 2026-06-02

### Fixed

- **Scan-count truth drift**: Language analyzers no longer inflate `AnalysisResult.files_scanned`. `files_scanned` now consistently reflects the scanner truth (`scan_summary.files_scanned`). Analyzer coverage is tracked separately in the new `analyzer_files_parsed` field.
- **Doctor reliability**: `doctor` now correctly sets unhealthy status and returns exit code 1 when the CLI entrypoint check fails.
- **Generated vs vendor classification**: `out`, `output`, `generated`, `gen`, and `autogen` segments are now classified as `PathCategory.GENERATED` instead of `VENDOR`, making the `GENERATED` branch reachable while preserving de-weighting behavior.
- **RUN_STATE wording drift**: docs and comments now consistently describe `RUN_STATE.json` as machine-readable automation metadata instead of overstating scheduling/trigger semantics.
- **Smoke-matrix drift**: the public smoke matrix now reflects the current observed smoke counts more honestly and notes that counts vary with scanner config and repo state.

### Added

- **Metric consistency regression tests** (`test_metric_consistency.py`): Prove same generation run yields identical scan counts across all rendered docs and JSON surfaces; prove analyzers cannot inflate scanner count; prove mixed-language repos report stable counts.
- **Doctor failure-path tests** (`test_cli.py`): Verify `cmd_doctor` returns nonzero exit and prints the issue when the CLI entrypoint check fails.
- **Generated path classification tests** (`test_ranking.py`): Cover `out/`, `output/`, `generated/`, `gen/`, and `autogen/` → `GENERATED`.
- **Stress fixture regression tests** (`test_stress_fixture.py`): 500-file mixed-stack deep repo with vendor-like noise; asserts generation completes without crash, scan counts remain bounded and stable, and generated directories are classified correctly.
- **Real-repo smoke automation** (`scripts/smoke_repos.py`, `.github/workflows/smoke-repos.yml`): clones the fixed public smoke set, runs `detect` / `generate` / `validate`, writes a deterministic JSON summary, and handles Windows cleanup safely.
- **RUN_STATE diagnostics**: `RUN_STATE.json` now exposes canonical `scan_summary`, `analyzer_summary`, `validation_summary`, `evidence_counts`, and backward-compatible legacy fields for downstream automation.
- **RUN_STATE schema marker**: `RUN_STATE.json` now includes `schema_mode: "additive"` to make the additive compatibility contract explicit for consumers.
- **RUN_STATE regression tests** (`test_run_state.py`): cover structured fields, bounded-scan signaling, evidence counts, tool-result alignment, schema marker presence, and legacy-field compatibility.

### Changed

- **Docs truthfulness**: roadmap, smoke-matrix, output-contract, architecture, limitations, manual-release guidance, and implementation-report docs were updated to reflect the `0.6.0` hardening line rather than implying local `main` still matches the public `0.5.0` tag.

## [0.5.0] - 2026-05-31

### Added

- **Shared analyzer snapshot flow**: graph analysis now builds one deep `RepoSnapshot` and reuses it across generic, Python, Node, .NET, Rust, Go, and Java analyzers instead of rescanning per analyzer.
- **Snapshot-based detector API**: `detect_project_from_snapshot(snapshot)` lets the registry and graph detect stacks from an existing scan boundary.
- **Snapshot-boundary regression proof**: new tests verify snapshot-based registry behavior and guard that a mixed Python+Node generation run performs exactly one scanner pass.

### Changed

- **Graph order**: pipeline now scans first, then detects from the shared snapshot, then runs language analyzers.
- **Analyzer registry truthfulness**: `AnalyzerRegistry.detect()` and `AnalyzerRegistry.analyze()` now actually consume the provided `RepoSnapshot`.
- **Language analyzers**: Python, Node, .NET, Rust, Go, and Java analyzers now iterate snapshot files instead of launching their own bounded directory walks.
- Bumped version to `0.5.0`.

## [0.4.0] - 2026-05-31

### Added

- **Signal Ranking & Path Classification (`ranking.py`)**: New module classifies paths as product, tooling, vendor, generated, fixture, test, docs, or unknown, and scores importance by depth, category, markers, and entrypoints.
- **Scanner deterministic file ordering**: Files within each directory are sorted by importance (manifests → tier-1 entrypoints → tier-2 entrypoints → config → text → binary) before caps apply, guaranteeing reproducible scans.
- **Scanner priority reserve**: When the global `max_files` cap is hit, 20% of the budget (up to 1000 files) is reserved exclusively for product directories. Vendor/build/cache files cannot consume this reserve. `ScanStats.budget_exhausted` signals when the cap is hit.
- **Tiered entrypoint priority**: Entrypoints are split into tier 1 (core: `main`, `index`, `app`, `cli`, ...) and tier 2 (secondary: `worker`, `gateway`, `driver`, `engine`, ...). Tier 1 is retained ahead of tier 2 under tight caps.
- **Validation deep-path filtering**: Bare-filename deep search uses a cached, directory-pruning `os.walk` that skips fixture/vendor/generated/demo subtrees entirely. Unrelated subtrees cannot silence real warnings.
- **Hard vendor/generated directory exclusion**: Scanner now skips `vendor`, `vendors`, `third_party`, `thirdparty`, `3rdparty`, `aa_vendor_mirror`, `vendor_mirror`, `mirrors`, `mirror`, `generated`, `gen`, and `autogen` directories at the walk level, preventing bounded scan budgets from being consumed by vendor noise.
- **Scan composition reporting**: `ScanStats.category_counts` and `BoundedScanSummary.category_counts` classify scanned files by `PathCategory` (product, vendor, generated, tooling, test, docs, unknown, fixture). `SCAN_REPORT.md` renders a "Scan composition" breakdown. `ARCHITECTURE_SUMMARY.md` and `AGENT_BRIEF.md` warn when vendor/generated files dominate the scanned sample.
- **Polyglot Source Layout in PROJECT_OVERVIEW.md**: `Source Layout` now always shows `source_directories` for all detected stacks. Python module detail is rendered as a `### Python modules` subsection rather than replacing the entire layout. Fixes hidden non-Python directories in mixed monorepos.
- **Context-aware fixture classification**: `fixtures` segments are only classified as `FIXTURE` when under test/example/demo context. `src/fixtures/` and `lib/fixtures/` are classified as `PRODUCT`; `vendor/fixtures/` remains `VENDOR`.
- **Vendor/Generated De-weighting**: Detector extension hits inside vendor/generated zones are filtered from markers and evidence; analyzers skip vendor files from package counts.
- **Workspace/Monorepo Interpretation**: Node analyzer discovers all `package.json` files, classifies each as product/tooling/vendor, detects pnpm/npm workspaces, and renders a "Workspace / Monorepo Layout" section in `ARCHITECTURE_SUMMARY.md`.
- **Deep Python Discovery**: Python analyzer discovers the highest-scored `pyproject.toml` at any depth, extracting metadata, console scripts, and dependencies from deep subprojects.
- **Node Role & Framework Inference**: Node analyzer infers `role` (`app` | `service` | `library` | `tool`), `frameworks` (web-server, frontend, cli), `local_deps` (intersection with local package names), and `likely_entry_points` from `package.json` fields.
- **Ranked Output**: Source directories, entry points, and package groups are now ordered by importance score rather than alphabetically.
- **Category Tags**: `ARCHITECTURE_SUMMARY.md` and `AGENT_BRIEF.md` tag source directories and entry points with `[product]`, `[tooling]`, etc.
- **Per-Language Dependency Sections**: `PROJECT_OVERVIEW.md` now shows runtime/development dependencies per language (Python, Node, Rust, Go, Java) instead of falling through to a single list.
- **Evidence Model v1**: `EvidenceKind`, `Evidence`, `EvidenceSet` with `add`, `by_kind`, `by_analyzer`, `warnings` helpers.
- **Rich evidence in analyzers**: All analyzers (Python, Node, Go, Rust, Java, .NET, Generic) now emit observed/inferred/unknown/unsupported/error evidence.
- **Evidence in generated docs**: `PROJECT_OVERVIEW.md` includes an Evidence section; `AGENT_BRIEF.md` lists Unknowns/Limitations.
- **Analyzer Registry Metadata**: `AnalyzerSpec` with `project_type`, `display_name`, `support_level`, `parser`, `detects`, `limitations`.
- **`explain_capabilities`** returns registry-derived analyzer metadata.
- **Validation v2**: New codes `missing_metadata_header`, `empty_output_file`, `graph_mmd_missing`, `ai_context_index_link_broken`.
- **MCP tests**: Invalid repo path structured error, capabilities include analyzers.
- **Tests**: `test_evidence.py` covers evidence serialization and queries.
- **Confidence levels**: `Evidence` carries `confidence` (high/medium/low) with defaults per `EvidenceKind`; `EvidenceSet.verify(repo_path)` checks source_path existence.
- **Validation v2.1**: `generated_version_mismatch` and `compact_profile_too_large` checks.
- **Tests**: `test_graph.py` (LangGraph pipeline), `test_cli.py` (CLI commands).
- `resolved_output_dir` in generation-style JSON results for CLI and MCP calls.
- Package metadata URLs for homepage, repository, issues, and changelog.
- Dependabot config for Python dependencies and GitHub Actions.
- CodeQL workflow for Python.
- Public real-repo smoke matrix document for release confidence tracking.

### Changed

- **Node Analyzer**: Now creates a `NodePackage` per discovered `package.json` instead of one mega-package; product packages are listed before tooling packages. Each package carries `role`, `frameworks`, `local_deps`, `likely_entry_points`, `package_type`, and `peer_dependencies`.
- **Java & Go Nested Build Discovery**: Analyzers now scan up to depth 5 for `pom.xml` / `build.gradle` / `go.mod` instead of assuming root presence, eliminating false "not found" evidence on repos with nested build files.
- **Renderer Honesty**: `AGENT_BRIEF.md` and `ARCHITECTURE_SUMMARY.md` now warn when scan budget is exhausted or many files are skipped. `PROJECT_OVERVIEW.md` only mentions Java build files (`pom.xml`, `build.gradle`) that were actually detected.
- **Architecture Pattern De-overfit**: Removed "MCP stdio server" parenthetical from server-pattern detection; now emits generic "Server/API pattern detected."
- **Detector Evidence**: Extension-inferred evidence is capped at 10 items with an overflow note to avoid flooding from large directories.
- Bumped version to `0.4.0`.
- MCP server now reports the package version in server metadata.
- MCP tool schemas now match actual supported arguments more closely.
- CI now validates committed example outputs, checks CLI smoke commands for unexpected repo dirtiness, and smoke-tests installed wheel and sdist artifacts.
- `detectors.py` emits detailed `EvidenceSet` for every detected stack.
- Validation source-reference regex expanded to cover `scripts/`, `docs/`, and more config files.
- Demo examples regenerated with versioned headers.
- Compact profile now always omits optional sections (no longer depends on repo file count).
- README, output contract, limitations, MCP client docs, security policy, and manual steps updated to reflect current release policy and output confinement behavior.
- Removed tracked local agent/customization artifacts and private session exports from the repository.
- Replaced the stale implementation report with a short archive note keyed to actual git/tag history.

## [0.3.2] - 2026-05-29

### Added

- **Scanner enrichment**: `SnapshotFile` now carries `extension`, `language_hint`, and `is_text`.
- **Gitignore semantics**: Root `.gitignore` parsing uses `pathspec` with Git-style wildmatch support (`*.log`, `build/`, `foo/**`, negation).
- **Profile modes**: `compact`, `standard`, and `deep` now produce measurably different output depths and list limits.
- **Validation hardening**:
  - `.mmd` existence check.
  - Source path reference validation (conservative backtick parsing).
  - Fixture/demo pollution warnings.
  - File-size sanity checks.
  - New machine-readable codes: `missing_required_file`, `broken_markdown_link`, `missing_mermaid_block`, `empty_mermaid_block`, `referenced_source_missing`, `fixture_path_primary_claim`, `oversized_section`, `validation_internal_error`.
- **Structured MCP tool results**: All tools return JSON with `ok`, `summary`, `warnings`, `errors`, `generated_files` where relevant.
- **Tests**: `test_validation_extended.py`, `test_profiles.py`, additional scanner gitignore tests, MCP resource traversal/empty-list tests.

### Changed

- `self-test` defaults to a temporary directory; added `--output` option for persistent output.
- `ValidationResult.to_dict()`, `DetectResult.to_dict()`, `RenderResult.to_dict()`, `RepoState.to_tool_result()` all include `summary`, `warnings`, `errors`.
- `explain_capabilities` returns structured JSON.
- `validate` CLI accepts `--repo` for source-reference checks.

### Fixed

- False positives in source-reference validation from `path::Class` backtick syntax.
- Validation JSON serialization error when `warnings`/`errors` contained dataclass objects.

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

## [0.2.0] - 2026-05-11

### Added

- Initial package structure with `context_crafter_mcp` import name.
- MCP stdio server with `detect_project`, `generate_project_overview`, `generate_repo_map`, `generate_dependency_graph`, `generate_architecture_summary`, `generate_all`.
- Analyzers for Python, Node/JS, .NET, Rust, Go, Java, and generic fallback.
- Markdown, Mermaid, and HTML renderers.
- LangGraph-based generation pipeline.
- Basic test suite and GitHub Actions CI.
