# Output Contract

## Generated files

| File | Purpose |
|------|---------|
| `AI_CONTEXT_INDEX.md` | Master index linking all docs |
| `PROJECT_OVERVIEW.md` | Metadata, stacks, entry points, dependencies, evidence |
| `REPO_MAP.md` | Directory tree, config files, entry points, tests |
| `DEPENDENCY_GRAPH.md` | Mermaid graph and external dependencies |
| `ARCHITECTURE_SUMMARY.md` | Patterns, abstractions, risks |
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
- `files_scanned`
- `project_types`
- `resolved_output_dir`

`resolved_output_dir` is the actual directory used after output confinement is applied.

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

- `missing_required_file`
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

## Rules

- deterministic ordering
- no invented purpose
- warnings remain visible
- evidence-backed claims where feasible
- output is source-grounded, compact, and explicit about limitations

