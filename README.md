# Context Crafter MCP

[![CI](https://github.com/0langa/context-crafter-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/0langa/context-crafter-mcp/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Local-first MCP server that turns source repositories into compact AI-agent context: project overviews, repo maps, dependency graphs, architecture notes, and validation reports.

## What it generates

| File | Purpose |
|------|---------|
| `AI_CONTEXT_INDEX.md` | Master index linking all generated docs |
| `PROJECT_OVERVIEW.md` | Detected stacks, root files, source layout, entry points |
| `REPO_MAP.md` | Compact directory tree with config and test directories |
| `DEPENDENCY_GRAPH.md` | Mermaid dependency graph + external dependency list |
| `ARCHITECTURE_SUMMARY.md` | Architecture patterns, risks, and unknowns |
| `AGENT_BRIEF.md` | Concise 1-page summary optimized for coding agents |
| `VALIDATION_REPORT.md` | Output completeness and analysis health |
| `SCAN_REPORT.md` | Scan coverage, skipped items, and safety notes |

## Quick start

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/0langa/context-crafter-mcp.git
cd context-crafter-mcp
uv sync --extra dev
uv run context-crafter-mcp --help
```

Run a self-test against the current directory (uses a temp directory by default):

```sh
uv run context-crafter-mcp self-test .
```

Generate context docs for any repository:

```sh
uv run context-crafter-mcp generate /path/to/repo --output docs/generated --profile standard
```

Validate the generated output:

```sh
uv run context-crafter-mcp validate docs/generated
```

## Profiles

| Profile | Use case |
|---------|----------|
| compact | Quick AI context; shorter trees, fewer symbols, concise briefs |
| standard | Default balanced detail |
| deep | Maximum detail for manual review or large repos |

## Use with MCP clients

Add this to your MCP client config:

```json
{
  "mcpServers": {
    "context-crafter": {
      "command": "uvx",
      "args": ["context-crafter-mcp", "serve"]
    }
  }
}
```

Or generate a client-specific snippet:

```sh
uv run context-crafter-mcp mcp-config --client kimi
```

Supported clients: `claude-desktop`, `claude-code`, `kimi`, `cline`, `roo`, `vscode`, `codex`, `generic-stdio`.

### MCP Inspector

Test the server with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```sh
npx @modelcontextprotocol/inspector uv run context-crafter-mcp serve
```

### MCP tools

- `detect_project` — detect stacks for a repo path
- `generate_context` — generate the full 8-file suite
- `generate_project_overview`
- `generate_repo_map`
- `generate_dependency_graph`
- `generate_architecture_summary`
- `validate_generated_context`
- `explain_capabilities`

### MCP resources

After `generate_context`, generated files are exposed as `context-crafter://latest/<filename>` resources. Only files from the current session are readable; arbitrary local paths are denied.

## Example output

See [`examples/outputs/`](examples/outputs/) for real generated files from the demo repository.

Quick preview of `AGENT_BRIEF.md`:

- **Entry points**: `src/context_crafter_mcp/cli.py`, `src/context_crafter_mcp/server.py`
- **Stacks**: Python (MCP server, LangGraph pipeline, static analyzers)
- **Key dependencies**: `mcp`, `langgraph`, `pydantic`

## Safety model

- **Read-only analysis** — never executes code in the target repository.
- **Output confined to repo** — `output_dir` is resolved and validated so it cannot escape the repository root.
- **No network** — no HTTP calls, no model inference, no API keys.
- **Bounded scans** — depth, file count, and file size limits with safe defaults.
- **No symlinks followed** — prevents infinite loops and directory escaping.
- **No stdout logging in MCP mode** — stdio protocol is protected from corrupting output.

See [`SECURITY.md`](SECURITY.md) for the full threat model and reporting process.

## Supported stacks

| Stack | Detection | Analysis depth |
|-------|-----------|----------------|
| Python | `pyproject.toml`, `requirements.txt`, `*.py` | AST-based imports, classes, functions |
| Node/TypeScript | `package.json`, `tsconfig.json`, `*.js/ts` | Regex-based static imports, scripts, deps |
| .NET | `*.sln`, `*.csproj` | XML-based project/package references |
| Rust | `Cargo.toml`, `*.rs` | TOML deps, module/entry detection |
| Go | `go.mod`, `*.go` | Module deps, package/main detection |
| Java | `pom.xml`, `build.gradle` | XML/Gradle deps, class/main detection |
| Generic | Any directory | Honest fallback with directory tree and root files |

## Architecture

- **Scanner boundary** — `Scanner.scan(root, options) -> RepoSnapshot`. Everything above the scanner consumes `RepoSnapshot`, making the scanner replaceable without changing analyzers.
- **Python product layer** — MCP server, CLI, analyzers, and renderers are Python. A lower-level scanner (Rust/Go) is only considered if benchmarks prove Python traversal is the bottleneck.
- **LangGraph pipeline** — `validate_repo -> detect -> scan -> analyze -> render`.
- **Analyzer registry** — Language analyzers are registered and run based on detected project types.
- **Enriched snapshot** — `SnapshotFile` carries `extension`, `language_hint`, and `is_text` for richer analysis.

See [`docs/adr/0001-python-product-layer-replaceable-scanner.md`](docs/adr/0001-python-product-layer-replaceable-scanner.md).

## Development

```sh
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
uv run context-crafter-mcp self-test .
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Limitations

- Static analysis only; no runtime behavior or dynamic imports.
- No deep syntax parsing for non-Python languages (uses regex/XML/TOML).
- HTML rendering is stdlib-only and may not handle complex Markdown perfectly.
- Secret redaction is not implemented; review generated output before sharing.
- Tree-sitter integration is experimental and not required for core installation.
- Nested `.gitignore` files are supported via `pathspec` with deepest-matching-wins semantics.

## License

MIT. See [`LICENSE`](LICENSE).
