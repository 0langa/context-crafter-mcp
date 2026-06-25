# Public Surface Freeze

This document records the public surface that is intended to stay stable through the `0.9.0` release-candidate line and into `1.0.0`, except for additive-compatible changes.

## CLI

The supported CLI commands are:

- `context-crafter-mcp version`
- `context-crafter-mcp doctor`
- `context-crafter-mcp detect`
- `context-crafter-mcp generate`
- `context-crafter-mcp validate`
- `context-crafter-mcp self-test`
- `context-crafter-mcp mcp-config`
- `context-crafter-mcp serve`

Machine-readable outputs use JSON objects with `ok`, `summary`, `warnings`, and `errors` where applicable. New fields may be added; existing fields should not be renamed or removed before `1.0.0`.

## MCP

The supported MCP tool names are:

- `detect_project`
- `generate_context`
- `generate_project_overview`
- `generate_repo_map`
- `generate_dependency_graph`
- `generate_architecture_summary`
- `validate_generated_context`
- `explain_capabilities`

After `generate_context`, session-scoped generated resources use the URI scheme `context-crafter://latest/<filename>`. Resource reads are limited to files generated in the current server session.

## Generated Bundle

Generation creates 13 file(s): 9 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`.

The 9 required Markdown files are:

- `AI_CONTEXT_INDEX.md`
- `PROJECT_OVERVIEW.md`
- `REPO_MAP.md`
- `DEPENDENCY_GRAPH.md`
- `ARCHITECTURE_SUMMARY.md`
- `AGENT_BRIEF.md`
- `COMMANDS.md`
- `SCAN_REPORT.md`
- `VALIDATION_REPORT.md`

Machine-readable outputs are `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`. Their schemas are additive: consumers should parse defensively and tolerate new fields.

## Known Non-1.0 Gaps

- Real-repo smoke confidence is strongest for Python, Node, Go, and Rust. Java/.NET support remains fixture-backed until fresh public real-repo smoke is added.
- Security behavior includes conservative redaction for obvious key/token/password values, but Context Crafter MCP is not a full secret-scanning engine.
- The scanner is static only. It does not execute target repository code and does not require network access during generation.
