# repo-docs-mcp

A universal, global, stdio-based MCP server that generates repository documentation and lightweight visual architecture artifacts for any project path passed to it.

## What it does

`repo-docs-mcp` analyzes a target repository using only static inspection (no execution, no network calls) and produces:

- **Project Overview** (`PROJECT_OVERVIEW.md`) — detected stacks, root files, source layout, entry points, and language-specific summaries.
- **Repository Map** (`REPO_MAP.md`) — a compact, depth-limited directory tree with config files, entry points, test directories, and docs.
- **Dependency Graph** (`DEPENDENCY_GRAPH.mmd` + `.md`) — Mermaid diagrams of internal module/project references with an external dependency summary.
- **Architecture Summary** (`ARCHITECTURE_SUMMARY.md`) — static-analysis-based architecture notes, risks, and unknowns.

All tools accept `repo_path` and write artifacts into `<repo_path>/<output_dir>` (default: `docs/generated`).

## Supported stacks

| Stack   | Detection markers                                 | Analysis depth                        |
|---------|---------------------------------------------------|---------------------------------------|
| Python  | `pyproject.toml`, `requirements.txt`, `*.py`      | AST-based imports, classes, functions |
| Node/JS | `package.json`, `tsconfig.json`, `*.js/ts`        | Regex-based static imports            |
| .NET    | `*.sln`, `*.csproj`, `*.fsproj`, `*.vbproj`       | XML-based project references          |
| Rust    | `Cargo.toml`, `*.rs`                              | TOML deps, module/entry detection     |
| Go      | `go.mod`, `*.go`                                  | Module deps, package/main detection   |
| Java    | `pom.xml`, `build.gradle`                         | XML/Gradle deps, class/main detection |
| Generic | Any existing directory                            | Directory tree, root files, configs   |

## Global MCP config

Add this to your MCP client config (e.g., Kimi CLI, Claude Desktop, etc.):

```json
{
  "mcpServers": {
    "repo-docs": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/repo-docs-mcp",
        "run",
        "python",
        "-m",
        "repo_docs_mcp.server"
      ]
    }
  }
}
```

Replace `/path/to/repo-docs-mcp` with the absolute path where you cloned this repository.

## Example tool calls

### detect_project
```json
{
  "repo_path": "/path/to/target-repo"
}
```

### generate_all with options
```json
{
  "repo_path": "/path/to/target-repo",
  "output_dir": "docs/generated",
  "scan_depth": 6,
  "max_files_per_dir": 200,
  "html": true
}
```

### Rust project
```json
{
  "repo_path": "/path/to/rust-project",
  "scan_depth": 5
}
```

### Go project
```json
{
  "repo_path": "/path/to/go-project",
  "scan_depth": 5
}
```

### Java project
```json
{
  "repo_path": "/path/to/java-project",
  "scan_depth": 5
}
```

## Optional features

### HTML output
Set `html: true` in `generate_project_overview` or `generate_all` to also produce `PROJECT_OVERVIEW.html`. This uses a lightweight stdlib-only markdown-to-HTML conversion.

### Mermaid image export
If the `mmdc` CLI (Mermaid CLI) is installed and on your PATH, the dependency graph renderer will also produce `DEPENDENCY_GRAPH.png` and `DEPENDENCY_GRAPH.svg` automatically. This step is entirely optional and external.

### Configurable scanning limits
Override defaults via `scan_depth` (1-20, default 4) and `max_files_per_dir` (1-5000, default 80). Values outside safe bounds are rejected.

## Plugin architecture for analyzers

Analyzers are registered in a central registry (`repo_docs_mcp.analyzers.ANALYZER_REGISTRY`). To add a new analyzer:

1. Create a module under `src/repo_docs_mcp/analyzers/`.
2. Implement a function with the signature:
   ```python
   def analyze_mylang(repo_path: str, analysis: AnalysisResult | None, config: ScanConfig) -> AnalysisResult:
       ...
   ```
3. Register it:
   ```python
   from repo_docs_mcp.analyzers import register_analyzer
   register_analyzer("mylang", analyze_mylang)
   ```
4. Update `repo_docs_mcp/detectors.py` to detect your language markers.

No changes to `graph.py` or `server.py` are required.

## Safety model

- **Read-only analysis** — never executes code in the target repository.
- **Output confined to repo** — `output_dir` is resolved and validated so it cannot escape the repository root.
- **No network** — no HTTP calls, no model inference, no API keys.
- **Bounded scans** — ignores `.git`, `node_modules`, `venv`, `__pycache__`, `dist`, `build`, `target` (Rust), `bin`, `obj`, etc.
- **No symlinks followed** — prevents infinite loops and directory escaping.
- **Graceful errors** — individual parse failures do not crash the entire run. Errors are collected and surfaced in reports.
- **No shell execution** — except for the optional `mmdc` subprocess, which is only invoked if the binary is present.

## Verification commands

Run these from the project root:

```sh
uv sync --extra dev
uv run python -m compileall src tests
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

Smoke test against the current repository:

```sh
uv run python -m repo_docs_mcp.server --self-test .
```

Or using the installed console script:

```sh
repo-docs-mcp-self-test .
```

## CI integration

A GitHub Actions workflow is included in `.github/workflows/ci.yml`. It runs linting, type checking, and tests on Python 3.11-3.13.

To regenerate docs in CI, add a step like:

```yaml
- name: Generate repo docs
  run: uv run python -m repo_docs_mcp.server --self-test .
```

To use as a pre-commit hook, create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: repo-docs-mcp
        name: Generate repository docs
        entry: repo-docs-mcp-self-test
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'repo_docs_mcp'`
- Ensure you ran `uv sync` from the project root.
- Use `uv run python -m repo_docs_mcp.server` so the virtual environment is active.

### Wrong `uv` environment
- Check that `.venv` exists in the project root.
- If you have multiple `uv` projects, make sure your shell is in the correct directory before running commands.

### MCP client cannot find server
- Verify the `--directory` path in your MCP config matches the absolute path to this repository.
- Ensure `uv` is on the system PATH used by the MCP client.
- Try running the server manually first: `uv run python -m repo_docs_mcp.server --self-test .`

### Target repo path does not exist
- The server returns a clear error JSON and exits gracefully.
- Double-check the path string. In JSON configs, backslashes must be escaped (`\\`).

### New language not detected
- Ensure the language has marker files or extensions registered in `repo_docs_mcp/detectors.py`.
- Check that the analyzer is registered in `repo_docs_mcp/analyzers/__init__.py`.
- Increase `scan_depth` if the project is deeply nested.

### Parse errors in generated reports
- Files that fail to parse (malformed JSON, TOML, XML) are reported in the **Errors** section of outputs.
- The run continues; errors do not block other files.

## Architecture

- `server.py` — MCP stdio server and tool dispatch.
- `graph.py` — LangGraph pipeline (`validate_repo → detect → scan → analyze → render`).
- `filesystem.py` — safe, bounded directory scanning.
- `detectors.py` — project-type detection by markers and extensions.
- `analyzers/` — generic, Python (AST), Node (regex), .NET (XML), Rust (TOML), Go (regex), Java (XML/regex).
- `renderers/` — Markdown, Mermaid, and optional HTML output generation.
- `models.py` — shared typed dataclasses.
- `state.py` — LangGraph state definition.

## License

MIT
