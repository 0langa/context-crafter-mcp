# MCP Clients

## Quick config

### Published package path

Use `uvx` when the package is published and you want a zero-install client config:

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

### Local development path

Use the repo checkout directly during development:

```sh
uv run context-crafter-mcp mcp-config --client kimi --repo /path/to/this/repo
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

| Client | Config target | Verification level |
|--------|--------------|--------------------|
| claude-desktop | generic-stdio | manual smoke |
| claude-code | generic-stdio | manual smoke |
| kimi | generic-stdio | manual smoke |
| cline | generic-stdio | manual smoke |
| roo | generic-stdio | manual smoke |
| vscode | generic-stdio | manual smoke |
| codex | generic-stdio | manual smoke |

## Tools

All tools return structured JSON in `TextContent` with `ok`, `summary`, `warnings`, `errors`, plus relevant fields for the operation.

| Tool | Purpose |
|------|---------|
| `detect_project` | Detect stacks for a repo path |
| `generate_context` | Generate the full 8-file suite |
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
- arbitrary local paths and traversal are denied
- `list_resources()` is empty before the first generation

## Safety notes

- stdio-only; no HTTP daemon
- no stdout logging in MCP mode
- output confined to repository root
- arbitrary path reads blocked by session-scoped registry

