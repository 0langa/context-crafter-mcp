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
