# Architecture

## Overview

Context Crafter MCP is a local-first Python application with two surfaces:

1. **MCP stdio server** — primary surface for coding clients
2. **CLI** — human/admin/debug surface

## Layers

```
CLI / MCP Server
    |
    v
Graph Pipeline (LangGraph)
    |-- validate_repo
    |-- detect_project
    |-- scan_files
    |-- run_analyzers
    |-- render_outputs
    |
    v
Analyzer Registry
    |-- Python (stdlib AST)
    |-- Node/JS (tree-sitter AST + regex fallback)
    |-- .NET (tree-sitter C# AST + XML + regex fallback)
    |-- Rust (tree-sitter Rust AST + regex fallback)
    |-- Go (tree-sitter Go AST + regex fallback)
    |-- Java (javalang AST + regex fallback)
    |-- Generic (fallback)
    |
    v
Signal Ranking
    |-- classify_path -> product | tooling | vendor | generated | fixture | test | docs | unknown
       (fixture classification is context-aware: test/demo-context only)
    |-- score_path -> importance by depth, category, markers, entrypoints
    |
    v
Scanner Boundary
    Scanner.scan(root, options) -> RepoSnapshot
```

## Scanner Boundary

The scanner is a strict replaceable boundary. Everything above it consumes `RepoSnapshot`, not raw filesystem traversal.

- `ScannerOptions` controls safety defaults
- `RepoSnapshot` contains `SnapshotFile`, `SnapshotDirectory`, `SkippedEntry`, `ScanError`, `ScanStats`, `GitMetadata`
- `SnapshotFile` is enriched with `extension`, `language_hint`, and `is_text`
- `safe_scan` in `filesystem.py` is a thin compatibility wrapper around `Scanner`
- Root `.gitignore` is parsed with `pathspec` (Git-style wildmatch); nested `.gitignore` files are supported via `active_gitignores` stack with deepest-matching-wins semantics
- Deterministic file ordering: files are sorted by importance (manifests → entrypoints → config → text → binary) before caps apply
- Priority reserve: 20% of `max_files` (up to 1000) is reserved for product directories; vendor/build files cannot consume it
- `ScanStats` tracks `skipped_reasons` and `budget_exhausted` for honest bounded-scan reporting

## Profile Pipeline

`ScanConfig.profile` flows through the pipeline:

1. `analyze_generic` adjusts tree depth and collection limits
2. Language analyzers respect profile limits where applicable
3. Renderers slice lists/trees based on `get_profile_limit(profile, key)`

Result: compact/standard/deep produce measurably different output on substantial repositories.

## Safety Model

- Static-only analysis
- No target code execution
- No network calls
- Bounded scans (depth, files, bytes)
- No symlink following
- Output confined to repo root
- MCP stdio protected from stdout pollution
- Resource registry blocks arbitrary local path reads
