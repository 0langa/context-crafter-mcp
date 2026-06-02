# Output Contract

## Generated files

| File | Purpose |
|------|---------|
| `AI_CONTEXT_INDEX.md` | Master index linking all docs |
| `PROJECT_OVERVIEW.md` | Metadata, stacks, entry points, dependencies, evidence |
| `REPO_MAP.md` | Directory tree, config files, entry points, tests |
| `DEPENDENCY_GRAPH.md` | Mermaid graph and external dependencies |
| `ARCHITECTURE_SUMMARY.md` | Patterns, abstractions, risks, workspace/monorepo layout, category-tagged source directories |
| `AGENT_BRIEF.md` | Concise 1-page agent summary with unknowns/limitations |
| `VALIDATION_REPORT.md` | Output completeness check |
| `SCAN_REPORT.md` | Coverage, skipped items, safety notes |

`DEPENDENCY_GRAPH.mmd` is also written as the raw Mermaid source.

## Generation result fields

Generation-style JSON results are additive-only and include:

- `ok`
- `summary`
- `warnings`
- `errors`
- `written`
- `generated_files`
- `files_scanned` (deprecated as standalone truth; prefer `scan_summary.files_scanned`)
- `scan_summary` — canonical scanner metrics (files_scanned, dirs_scanned, files_skipped, dirs_skipped, budget_exhausted, skipped_reasons, category_counts)
- `analyzer_files_parsed` — number of files successfully parsed by language analyzers (may be less than scanner truth)
- `project_types`
- `resolved_output_dir`

`resolved_output_dir` is the actual directory used after output confinement is applied.

## RUN_STATE.json

`RUN_STATE.json` is a machine-readable run metadata file written alongside the Markdown outputs. Its schema evolves additively; automation consumers should parse defensively. It contains:

- `version`, `timestamp`, `repo_path`, `project_types`, `profile`, `scan_config`
- `scan_summary` — canonical scanner metrics
- `analyzer_summary` — analyzers_run and files_parsed
- `validation_summary` — output_files_count, errors_count, warnings_count, bounded_scan
- `evidence_counts` — counts by OBSERVED / INFERRED / UNKNOWN / UNSUPPORTED / ERROR
- `warnings` — warning messages from analysis evidence
- `output_files` and `errors`

Legacy `files_scanned` and `analyzers_run` fields remain for backward compatibility.

## Output confinement

Requested `output_dir` values are resolved against the target repository root.

- if the path stays inside the repository, it is used
- if the path would escape the repository, output is confined to `docs/generated`

Consumers should trust `resolved_output_dir`, not the raw requested path.

## Metadata headers

Every generated Markdown file includes:

- generator name and package version
- generated-at ISO timestamp

Generated Markdown files do not currently embed every evidence level or source path in their header. Evidence details appear in the body of the relevant reports.

## Profiles

| Profile | Effect |
|---------|--------|
| compact | Shorter directory tree, fewer entry points, fewer dependency details, concise brief, trimmed optional sections |
| standard | Default balanced detail |
| deep | More tree depth, symbol counts, analyzer details, warnings/unknowns, and graph edges |

Profiles measurably change output size on repositories with enough content. On tiny repositories the difference can be small.

## Validation codes

Validation can report these machine-readable codes:

- `broken_markdown_link`
- `missing_mermaid_block`
- `empty_mermaid_block`
- `mermaid_no_diagram_keyword`
- `referenced_source_missing`
- `fixture_path_primary_claim`
- `oversized_section`
- `validation_internal_error`
- `missing_metadata_header`
- `empty_output_file`
- `graph_mmd_missing`
- `ai_context_index_link_broken`
- `generated_version_mismatch`
- `compact_profile_too_large`

## Workspace and Monorepo Layout

When multiple `package.json` files or workspace patterns (pnpm/npm workspaces) are detected, `ARCHITECTURE_SUMMARY.md` includes a **Workspace / Monorepo Layout** section listing packages with their classification (product, tooling, vendor) and file/dependency counts.

## Category Tags

Source directories and entry points in `ARCHITECTURE_SUMMARY.md` and `AGENT_BRIEF.md` may carry category tags such as `[product]`, `[tooling]`, `[vendor]`, `[generated]`, `[fixture]`, or `[test]` to help agents distinguish runtime surfaces from noise.

## Rules

- deterministic ordering
- no invented purpose
- warnings remain visible
- evidence-backed claims where feasible
- output is source-grounded, compact, and explicit about limitations

