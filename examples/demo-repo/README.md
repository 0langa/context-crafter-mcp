# Demo Greeter

A tiny Python package used to demonstrate `context-crafter-mcp` output.

## Regenerate example outputs

Output is confined to the repository root for safety, so generate inside `demo-repo` and copy the results:

```sh
uv run context-crafter-mcp generate examples/demo-repo --output docs/generated --profile standard
rm -rf examples/outputs/*
cp -r examples/demo-repo/docs/generated/* examples/outputs/
```

The generated files in `examples/outputs/` are committed so reviewers can inspect the tool's output without running it.
