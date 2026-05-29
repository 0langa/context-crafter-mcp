# Manual Steps

Steps that cannot be automated by this repo and require maintainer action.

## GitHub repository settings

- Update repository description to:
  > Local-first MCP server that turns source repositories into compact AI-agent context: project overviews, repo maps, dependency graphs, architecture notes, and validation reports.
- Add topics: `mcp`, `documentation`, `static-analysis`, `ai-agents`, `repository-tools`.
- Pin repository only after v1.0 readiness criteria are met.

## Publishing

- Publishing to PyPI is manual and requires maintainer review.
- Do not enable automatic publishing workflows without review.

## Screenshots

- If adding screenshots to README, generate them manually after running `context-crafter-mcp generate . --output docs/generated --profile standard`.
