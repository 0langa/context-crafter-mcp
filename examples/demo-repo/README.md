# Demo Repo

This project uses the repository itself as the demo and example source.

Real generated outputs from this repo are committed to `examples/outputs/` so reviewers can see the tool's output without running it.

To regenerate:

```sh
uv run context-crafter-mcp generate . --output examples/outputs --profile standard
```
