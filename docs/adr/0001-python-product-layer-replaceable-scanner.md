# ADR 0001: Python Product Layer with Replaceable Scanner Boundary

## Status

Accepted

## Context

We need to choose the implementation language for the MCP server, CLI, analyzers, and renderers. We also need to decide how to handle filesystem scanning performance.

## Decision

- **Python** for the MCP server, CLI, analyzer registry, renderers, validation reports, and package workflow.
- **Python-first** for the filesystem scanner, designed behind a strict `Scanner.scan(root, options) -> RepoSnapshot` boundary.
- **Tree-sitter** evaluated before any lower-level scanner rewrite.
- **Rust/Go scanner** only if benchmarks prove Python is the bottleneck.

## Consequences

- Fast iteration and broad ecosystem support.
- MCP SDK has first-class Python support.
- Scanner can be replaced later without changing analyzer contracts.
- Performance is acceptable for typical repos; large repos (>100k files) may need future optimization.

## Benchmark Gate

Do not build a Rust/Go scanner unless:

- 100k-file scan with ignore rules takes >5 seconds on a normal dev machine, or
- memory exceeds 250 MB, or
- scanner complexity becomes harder to reason about than a small helper.
