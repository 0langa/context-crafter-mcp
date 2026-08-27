# MCP Clients

## Quick config

### Fastest path

Claude Code and Codex register the server themselves:

```sh
claude mcp add context-crafter -- uvx context-crafter-mcp serve
codex mcp add context-crafter -- uvx context-crafter-mcp serve
```

### Published package path

`mcp-config` emits the format the requested client actually reads. Clients in the JSON group share
one stdio config:

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

Codex reads `~/.codex/config.toml`, so `--client codex` emits a TOML table instead:

```sh
uv run context-crafter-mcp mcp-config --client codex
```

```toml
[mcp_servers.context-crafter]
command = "uvx"
args = ["context-crafter-mcp", "serve"]
```

### Local development path

Point to the repo checkout directly during development:

```sh
uv run context-crafter-mcp mcp-config --client claude-desktop --repo /path/to/this/repo
```

This emits a client-specific config with the local directory, still in that client's own format:

```json
{
  "mcpServers": {
    "context-crafter": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/this/repo",
        "run",
        "context-crafter-mcp",
        "serve"
      ]
    }
  }
}
```

### MCP Inspector

```sh
npx @modelcontextprotocol/inspector uv run context-crafter-mcp serve
```

For local repo inspection:

```sh
npx @modelcontextprotocol/inspector uv --directory /path/to/this/repo run context-crafter-mcp serve
```

## Supported clients

| Client | Config placement | Notes |
|--------|-----------------|-------|
| claude-desktop | `claude_desktop_config.json` → `mcpServers` | Restart Claude Desktop after editing |
| claude-code | `.mcp.json` in project root or `~/.claude-code/` | Per-project or global; `claude mcp add` writes it for you |
| kimi | Kimi Code settings → MCP servers | GUI-based entry |
| cline | Cline settings → MCP servers | Hot reloads without restart |
| roo | Roo settings → MCP servers | GUI-based entry |
| vscode | `.vscode/mcp.json` or user settings | Workspace-scoped or global |
| codex | `~/.codex/config.toml` → `[mcp_servers.context-crafter]` | TOML, not JSON; `codex mcp add` writes it for you |
| generic-stdio | Any client accepting stdio JSON | Baseline stdio MCP config |

## Tools

All tools return structured JSON in `TextContent` with `ok`, `summary`, `warnings`, `errors`, plus relevant fields for the operation.

| Tool | Purpose |
|------|---------|
| `detect_project` | Detect stacks for a repo path |
| `generate_context` | Generate 9 required Markdown files plus `DEPENDENCY_GRAPH.mmd`, `EVIDENCE_LEDGER.json`, `CONTEXT_MANIFEST.json`, and `RUN_STATE.json` |
| `generate_project_overview` | Generate `PROJECT_OVERVIEW.md` and optional HTML |
| `generate_repo_map` | Generate `REPO_MAP.md` |
| `generate_dependency_graph` | Generate `DEPENDENCY_GRAPH.md` and `DEPENDENCY_GRAPH.mmd` |
| `generate_architecture_summary` | Generate `ARCHITECTURE_SUMMARY.md` |
| `validate_generated_context` | Validate output directory; optional `repo_path` improves source-reference checks |
| `explain_capabilities` | Return capabilities overview and analyzer metadata |

Generation tools report `resolved_output_dir`. If the requested output path would escape the repository root, writes are confined to `docs/generated`.

## Resources

After `generate_context`, generated files are registered as MCP resources:

- URI format: `context-crafter://latest/<filename>`
- only files from the current server session are readable
- listed/read resources use file-appropriate MIME types (`text/markdown`, `text/vnd.mermaid`, `application/json`, or `text/html`)
- arbitrary local paths and traversal are denied
- `list_resources()` is empty before the first generation

## Safety notes

- stdio-only; no HTTP daemon
- no stdout logging in MCP mode
- output confined to repository root
- arbitrary path reads blocked by session-scoped registry
