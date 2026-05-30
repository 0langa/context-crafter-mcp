---
description: "Repo-specific rules for tests in context-crafter-mcp. Use when editing pytest coverage, fixtures, regression tests, challenge-repo tests, and MCP smoke tests."
applyTo: "tests/**/*.py"
---

# Context Crafter Test Rules

## Test strategy

- Regression-first for bug fixes.
- Prefer focused tests near changed subsystem.
- Add challenge-repo regression only when issue generalizes.
- Test truthfulness, not flattering output.

## Good assertions

- public contract keys exist
- warnings/errors are explicit
- primary surfaces are evidence-backed
- vendor/fixture/tooling noise does not dominate
- confinement/safety boundaries hold

## Naming

- test names should state behavior clearly
- prefer user-intent names over implementation-detail names

## Avoid

- brittle assertions on incidental prose unless wording is contract
- repo-specific hacks encoded into tests
- skipping validation of edge/error paths

## Validation

When changing MCP surface, prefer updating:

- `tests/test_mcp_smoke.py`
- `tests/test_mcp_tools.py`
- subsystem test file closest to change
