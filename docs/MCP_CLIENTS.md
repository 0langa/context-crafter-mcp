# MCP Clients

## Quick Config

### Claude Desktop / Claude Code / Kimi / Cline / Roo / VS Code / Codex

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

### Local development (with repo path)

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

## Supported Clients

| Client | Config target | Tested |
|--------|--------------|--------|
| claude-desktop | generic-stdio | manual |
| claude-code | generic-stdio | manual |
| kimi | generic-stdio | manual |
| cline | generic-stdio | manual |
| roo | generic-stdio | manual |
| vscode | generic-stdio | manual |
| codex | generic-stdio | manual |

## Tools

All tools return structured JSON with `ok`, `summary`, `warnings`, `errors`, and relevant stats.

| Tool | Purpose |
|------|---------|
| `detect_project` | Detect stacks for a repo path |
| `generate_context` | Generate the full 8-file suite |
| `generate_project_overview` | Generate `PROJECT_OVERVIEW.md` |
| `generate_repo_map` | Generate `REPO_MAP.md` |
| `generate_dependency_graph` | Generate `DEPENDENCY_GRAPH.md` + `.mmd` |
| `generate_architecture_summary` | Generate `ARCHITECTURE_SUMMARY.md` |
| `validate_generated_context` | Validate output directory |
| `explain_capabilities` | Return capabilities overview |

## Resources

After `generate_context`, generated files are registered as MCP resources:

- URI format: `context-crafter://latest/<filename>`
- Only files from the current server session are readable
- Arbitrary `file://` paths and `../` traversal are denied
- `list_resources()` is empty before the first generation

## Safety Notes

- stdio-only; no HTTP daemon
- No stdout logging
- Output confined to repo root
- Arbitrary path reads blocked
