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
    |-- Python (AST)
    |-- Node/JS (regex)
    |-- .NET (XML)
    |-- Rust (TOML)
    |-- Go (regex)
    |-- Java (XML/regex)
    |-- Generic (fallback)
    |
    v
Scanner Boundary
    Scanner.scan(root, options) -> RepoSnapshot
```

## Scanner Boundary

The scanner is a strict replaceable boundary. Everything above it consumes `RepoSnapshot`, not raw filesystem traversal.

- `ScannerOptions` controls safety defaults
- `RepoSnapshot` contains `SnapshotFile`, `SnapshotDirectory`, `SkippedEntry`, `ScanError`, `ScanStats`, `GitMetadata`
- `safe_scan` in `filesystem.py` is a thin compatibility wrapper around `Scanner`

## Safety Model

- Static-only analysis
- No target code execution
- No network calls
- Bounded scans (depth, files, bytes)
- No symlink following
- Output confined to repo root
- MCP stdio protected from stdout pollution
