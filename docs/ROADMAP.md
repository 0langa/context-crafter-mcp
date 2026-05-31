# Roadmap

## Current state

Package is at **v0.4.0**. The project has a working scanner boundary, CLI, MCP server, analyzer registry, parser abstraction, validation layer, safety tests, golden fixture tests, challenge-repo regression coverage, and a public smoke matrix.

`0.5.0`–`0.8.0` hardening is substantially complete. Current work is the **pre-`1.0.0` reviewer experience and final integration** pass.

`1.0.0` remains the first public release.

## Completed since last roadmap update

- `AnalyzerRegistry` class with `register`, `detect`, `analyze`, `merge`
- `ParserBackend` abstraction; Tree-sitter moved to optional `[parsers]` extra
- Metadata block in every generated file: `Source repo`, `Git commit`, `Profile`, `Scanner` bounds
- Deterministic generation via `CONTEXT_CRAFTER_FROZEN_TIME`
- Markdown backtick escaping and Mermaid label escaping
- MCP stdio quietness runtime test
- Source-text injection safety tests
- Golden/snapshot tests for all 8 fixture repos
- Basic secret file awareness in scan reports
- Draft release workflow
- README client config snippets, limitations matrix, AICtx comparison
- `CODE_OF_CONDUCT.md`

## Active path to 1.0.0

### 1. Final integration

- Ensure CI runs the exact concrete acceptance test from the main roadmap.
- Ensure installed wheel/sdist artifacts pass the same smoke matrix.
- Verify no docs overclaim maturity or understate limitations.

### 2. Reviewer experience

- First screen of README must be strong and honest.
- Example outputs must be current with renderer changes.
- MCP client onboarding must be practical and accurate.

### 3. Known limitations to keep honest

- Java and .NET analysis depth is below the Python/Node/Go/Rust trust bar.
- Secret detection is heuristic only (filename patterns), not content scanning.
- Determinism is structural, not bit-for-bit (timestamps vary between runs).
- Tree-sitter requires optional `[parsers]` extra.

## 1.0.0 exit criteria

- All concrete acceptance commands pass on clean checkout.
- CI green on Windows + Ubuntu, Python 3.11/3.12/3.13.
- Challenge-repo output is truthful, not merely valid.
- Public smoke matrix green with only documented, accepted limitations.
- Docs match real behavior and do not overclaim.
