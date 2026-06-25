# Context Crafter MCP

[![CI](https://github.com/0langa/context-crafter-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/0langa/context-crafter-mcp/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.7.0b1-blue)]

Local-first MCP server that turns source repositories into compact AI-agent context: project overviews, repo maps, dependency graphs, architecture notes, and validation reports.

## What it generates

| File | Purpose |
|------|---------|
| `AI_CONTEXT_INDEX.md` | Master index linking all generated docs |
| `PROJECT_OVERVIEW.md` | Detected stacks, root files, source layout, entry points |
| `REPO_MAP.md` | Compact directory tree with config and test directories |
| `DEPENDENCY_GRAPH.md` | Mermaid dependency graph + external dependency list |
| `DEPENDENCY_GRAPH.mmd` | Raw Mermaid dependency graph source |
| `ARCHITECTURE_SUMMARY.md` | Architecture patterns, risks, and unknowns |
| `AGENT_BRIEF.md` | Concise 1-page summary optimized for coding agents |
| `COMMANDS.md` | Statically inferred setup, test, and build commands |
| `VALIDATION_REPORT.md` | Output completeness and analysis health |
| `SCAN_REPORT.md` | Scan coverage, skipped items, and safety notes |
| `EVIDENCE_LEDGER.json` | Machine-readable observed/inferred/unknown evidence ledger |
| `CONTEXT_MANIFEST.json` | Machine-readable bundle manifest for agents and automation |
| `RUN_STATE.json` | Machine-readable run metadata for downstream automation and tracking |

## Quick start

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

### From a repo checkout

```sh
git clone https://github.com/0langa/context-crafter-mcp.git
cd context-crafter-mcp
uv sync --extra dev
uv run context-crafter-mcp --help
```

### From an installed artifact

Current beta git tag is `0.7.0b1`. Until a package release is published to an installer-friendly index, install from a built wheel:

```sh
uv build
uv tool install --from dist/context_crafter_mcp-*.whl context-crafter-mcp
context-crafter-mcp --help
```

For MCP clients, the published-package path uses `uvx`:

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

Run a self-test against the current directory (uses a temp directory by default):

```sh
uv run context-crafter-mcp self-test .
```

Generate context docs for any repository:

```sh
uv run context-crafter-mcp generate /path/to/repo --output docs/generated --profile standard
```

On Windows:

```powershell
uv run context-crafter-mcp generate C:\path\to\repo --output docs\generated --profile standard
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

Generate a client-specific snippet:

```sh
uv run context-crafter-mcp mcp-config --client kimi
```

Supported clients: `claude-desktop`, `claude-code`, `kimi`, `cline`, `roo`, `vscode`, `codex`, `generic-stdio`.

### Published package config

All clients use the same stdio config when installed via `uvx`:

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

### Local development config

Point to the repo checkout directly:

```sh
uv run context-crafter-mcp mcp-config --client claude-desktop --repo /path/to/this/repo
```

### Client placement

| Client | Where to place the config |
|--------|--------------------------|
| claude-desktop | `claude_desktop_config.json` → `mcpServers` |
| claude-code | `.mcp.json` in project root or `~/.claude-code/` |
| kimi | Kimi Code settings → MCP servers |
| cline | Cline settings → MCP servers (hot reload) |
| roo | Roo settings → MCP servers |
| vscode | `.vscode/mcp.json` or user settings |
| codex | `codex.toml` or Codex settings |
| generic-stdio | Any client that accepts stdio JSON |

### MCP Inspector

Test the server with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```sh
npx @modelcontextprotocol/inspector uv run context-crafter-mcp serve
```

For local repo inspection:

```sh
npx @modelcontextprotocol/inspector uv --directory /path/to/this/repo run context-crafter-mcp serve
```

### MCP tools

- `detect_project` — detect stacks for a repo path
- `generate_context` — generate 9 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json`
- `generate_project_overview`
- `generate_repo_map`
- `generate_dependency_graph`
- `generate_architecture_summary`
- `validate_generated_context`
- `explain_capabilities`

### MCP resources

After `generate_context`, generated files are exposed as `context-crafter://latest/<filename>` resources. Only files from the current session are readable; arbitrary local paths are denied.
Resources are advertised with file-appropriate MIME types, including `text/markdown`, `text/vnd.mermaid`, `application/json`, and `text/html` for optional HTML output.

Generation results also report `resolved_output_dir`. If the requested `output_dir` would escape the repository root, output is confined to `docs/generated`.

## Example output

See [`examples/outputs/`](examples/outputs/) for real generated files from the demo repository.

Quick preview of `AGENT_BRIEF.md`:

- **Entry points**: `src/context_crafter_mcp/cli.py`, `src/context_crafter_mcp/server.py`
- **Stacks**: Python (MCP server, LangGraph pipeline, static analyzers)
- **Key dependencies**: `mcp`, `langgraph`, `pydantic`

## What makes this different

| Capability | Context Crafter MCP | Generic AI context generators |
|------------|---------------------|------------------------------|
| Local-first | Runs entirely on your machine | Often cloud-based or API-dependent |
| Static-only | No code execution, no network calls | May run code or call LLMs |
| Deterministic | Same input → same output structure | Often non-deterministic |
| No API keys | Zero external dependencies | Usually requires API keys |
| MCP-native | First-class MCP server with tools, resources, prompts | Ad-hoc integration |
| Validation | Built-in validation reports with machine-readable codes | Rarely validated |
| Evidence model | Observed / inferred / unknown labels on every claim | Often overconfident |

## Safety model

- **Read-only analysis** — never executes code in the target repository.
- **Output confined to repo** — `output_dir` is resolved and validated so it cannot escape the repository root.
- **Resolved path reported** — generation JSON explicitly reports the actual output directory used after confinement.
- **No network** — no HTTP calls, no model inference, no API keys.
- **Bounded scans** — depth, file count, and file size limits with safe defaults.
- **No symlinks followed** — prevents infinite loops and directory escaping.
- **No stdout logging in MCP mode** — stdio protocol is protected from corrupting output.
- **Basic secret awareness** — flags potential secret files (`.env`, `credentials.json`) in scan reports.

See [`SECURITY.md`](SECURITY.md) for the full threat model and reporting process.

## Supported stacks

| Stack | Detection | Analysis depth | Optional extra |
|-------|-----------|----------------|----------------|
| Python | `pyproject.toml`, `requirements.txt`, `*.py` | stdlib AST (imports, classes, functions) | — |
| Node/TypeScript | `package.json`, `tsconfig.json`, `*.js/ts` | tree-sitter AST + regex fallback | `parsers` |
| .NET | `*.sln`, `*.csproj`, `*.cs` | tree-sitter C# AST + XML + regex fallback | `parsers` |
| Rust | `Cargo.toml`, `*.rs` | tree-sitter Rust AST + regex fallback | `parsers` |
| Go | `go.mod`, `*.go` | tree-sitter Go AST + regex fallback | `parsers` |
| Java | `pom.xml`, `build.gradle`, `build.gradle.kts`, `*.java` | javalang AST + regex fallback (nested build files discovered) | `parsers` |
| Generic | Any directory | Directory and filename heuristics | — |

> **Trust bar note:** Python, Node/TypeScript, Go, and Rust have the highest real-repo smoke coverage. Java and .NET are supported and tested on fixtures, but their analysis depth has not yet reached the same hardening standard.

Install deeper parser support:

```sh
uv sync --extra parsers
```

## Architecture

- **Scanner boundary** — `Scanner.scan(root, options) -> RepoSnapshot`. Everything above the scanner consumes `RepoSnapshot`, making the scanner replaceable without changing analyzers.
- **Python product layer** — MCP server, CLI, analyzers, and renderers are Python. A lower-level scanner (Rust/Go) is only considered if benchmarks prove Python traversal is the bottleneck.
- **LangGraph pipeline** — `validate_repo -> detect -> scan -> analyze -> render`.
- **Analyzer registry** — `AnalyzerRegistry` with `register`, `detect`, `analyze`, `merge`. Language analyzers run based on detected project types.
- **Parser abstraction** — `ParserBackend` protocol with concrete implementations (Tree-sitter, javalang, stdlib AST, regex fallback).
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

| Limitation | Detail |
|------------|--------|
| Static analysis only | No runtime behavior, dynamic imports, or conditional architecture |
| Non-Python depth | Real AST parsers with regex fallback, not full semantic analysis |
| HTML rendering | Uses `markdown` library when available; stdlib fallback otherwise |
| Secret redaction | Conservative generated-output redaction for obvious key/token/password values; review generated output before sharing |
| Gitignore nesting | Supported via `pathspec` with deepest-matching-wins semantics |
| Determinism | Timestamps vary between runs; content and ordering are stable |
| Compact profile | Intentionally omits sections even when a small repo could fit more |

See [`docs/REAL_REPO_SMOKE_MATRIX.md`](docs/REAL_REPO_SMOKE_MATRIX.md) for the current pre-`1.0.0` hardening confidence set.

## License

MIT. See [`LICENSE`](LICENSE).
